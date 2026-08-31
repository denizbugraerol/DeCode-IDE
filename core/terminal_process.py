import fcntl
import os
import pty
import signal
import struct
import termios
import time

import pyte
from PyQt6.QtCore import QObject, QSocketNotifier, pyqtSignal


class _PtyBackedScreen(pyte.Screen):
    """ pyte.Screen'in normalde no-op olan write_process_input()'unu (DSR /
    cursor position report gibi terminal sorgularının cevabını) gerçek
    PTY'ye yazan bir callback'e bağlar. Aksi halde bazı shell prompt'ları ya
    da araçlar cevap bekleyip küçük görsel bozulmalara yol açabilir. """

    def __init__(self, columns, lines, write_back):
        super().__init__(columns, lines)
        self._write_back = write_back

    def write_process_input(self, data):
        self._write_back(data.encode("utf-8", errors="replace"))


class TerminalProcess(QObject):
    """ Gerçek bir shell'i (pty.fork ile) başlatıp PTY master fd'sini Qt'nin
    event loop'una (QSocketNotifier) bağlayan ve pyte ile gelen byte'ları
    yorumlayan arkaplan bileşeni. Qt widget'ından bağımsızdır — çizim işini
    ui/components/terminal_panel.py yapar, bu sınıf sadece süreç + ekran
    durumunu yönetir. """

    output_ready = pyqtSignal()   # pyte ekranı güncellendi -> panel repaint etsin
    finished = pyqtSignal()       # child shell süreci sona erdi

    def __init__(self, rows=9, cols=80, parent=None):
        super().__init__(parent)
        self.rows, self.cols = rows, cols
        self._pid = None
        self._master_fd = None
        self._notifier = None
        self.screen = None
        self._stream = None

    def is_running(self):
        return self._pid is not None

    def start(self):
        """ pty.fork() ile gerçek bir sözde-terminal (pseudo-terminal) üzerinde
        kullanıcının kendi shell'ini (SHELL ortam değişkeni, yoksa /bin/bash)
        login shell olarak başlatır. """
        if self.is_running():
            return
        shell = os.environ.get("SHELL", "/bin/bash")
        env = dict(os.environ)
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"

        pid, master_fd = pty.fork()
        if pid == 0:
            # Child süreç: pty.fork() setsid + TIOCSCTTY + 0/1/2 dup işini
            # zaten kendi içinde halletti. Burada tek iş shell'i exec etmek.
            try:
                os.execvpe(shell, [shell, "-l"], env)
            except Exception:
                os._exit(1)

        # --- Parent süreç devam ediyor ---
        self._pid = pid
        self._master_fd = master_fd
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        self.screen = _PtyBackedScreen(self.cols, self.rows, write_back=self._write_to_master)
        self._stream = pyte.ByteStream(self.screen)
        self._apply_winsize()

        self._notifier = QSocketNotifier(master_fd, QSocketNotifier.Type.Read, self)
        self._notifier.activated.connect(self._drain_master)

    def _apply_winsize(self):
        if self._master_fd is None:
            return
        # struct winsize: ws_row, ws_col, ws_xpixel, ws_ypixel
        packed = struct.pack("HHHH", self.rows, self.cols, 0, 0)
        fcntl.ioctl(self._master_fd, termios.TIOCSWINSZ, packed)
        # Not: TIOCSWINSZ çekirdek tarafından otomatik olarak ön plandaki
        # process group'a SIGWINCH gönderir; elle sinyal yollamaya gerek yok.

    def resize(self, rows, cols):
        if not self.is_running() or (rows == self.rows and cols == self.cols):
            return
        self.rows, self.cols = rows, cols
        # DİKKAT: Screen() constructor'ı (columns, lines) sırasında ama
        # resize() metodu (lines, columns) sırasında bekliyor.
        self.screen.resize(lines=rows, columns=cols)
        self._apply_winsize()

    def write(self, data: bytes):
        if self._master_fd is None:
            return
        try:
            os.write(self._master_fd, data)
        except OSError:
            pass  # shell tam o anda öldüyse (EPIPE/EIO) sessizce yok say

    def _write_to_master(self, data: bytes):
        self.write(data)

    def _drain_master(self, *_args):
        try:
            data = os.read(self._master_fd, 65536)
        except OSError:
            data = b""  # PTY'de EOF genelde b"" değil EIO olarak gelir
        if not data:
            self._handle_child_exit()
            return
        try:
            self._stream.feed(data)
        except Exception:
            pass  # pyte'ın çözemediği zararsız bir kaçış dizisi; devam et
        self.output_ready.emit()

    def _handle_child_exit(self):
        if self._notifier:
            self._notifier.setEnabled(False)
        try:
            os.waitpid(self._pid, os.WNOHANG)
        except (ChildProcessError, OSError):
            pass
        self.finished.emit()

    def close(self):
        """ Panel gizlenirken DEĞİL, sadece uygulama tamamen kapanırken çağrılır
        (bkz. IDEWindow.closeEvent). Önce SIGHUP, sonra kısa bir bekleme,
        gerekirse SIGKILL ile temizler. """
        if self._notifier:
            self._notifier.setEnabled(False)
            self._notifier.deleteLater()
            self._notifier = None
        if self._pid is not None:
            try:
                os.kill(self._pid, signal.SIGHUP)
            except ProcessLookupError:
                pass
            for _ in range(25):
                try:
                    if os.waitpid(self._pid, os.WNOHANG)[0] != 0:
                        break
                except (ChildProcessError, OSError):
                    break
                time.sleep(0.02)
            else:
                try:
                    os.kill(self._pid, signal.SIGKILL)
                    os.waitpid(self._pid, 0)
                except (ProcessLookupError, ChildProcessError, OSError):
                    pass
            self._pid = None
        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None
