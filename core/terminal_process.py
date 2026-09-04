import fcntl
import os
import pty
import signal
import struct
import sys
import termios
import time

import pyte
from PyQt6.QtCore import QObject, QSocketNotifier, pyqtSignal


# PyInstaller ile dondurulmuş süreçte bootloader'ın ezdiği, çocuk sürece
# SIZMAMASI gereken değişkenler. Orijinal değeri "<AD>_ORIG" altında saklar.
_FROZEN_VARS = ("LD_LIBRARY_PATH", "LD_PRELOAD")


def child_environment(env=None, frozen=None):
    """ PTY çocuğuna verilecek ortam: PyInstaller'ın izleri geri alınır.

    "<AD>_ORIG" varsa "<AD>" ona döner ve _ORIG anahtarı düşer; yoksa donmuş
    süreçte "<AD>" tamamen silinir (bootloader değeri kabuğa sızmasın).
    Donmamış süreçte ortam değişmeden geçer.

    Neden gerekiyor: bootloader LD_LIBRARY_PATH'i paketin açıldığı geçici
    dizine çevirir; pty.fork() ile doğan kabuk bunu miras alırsa içeriden
    çalıştırılan pio/git/ls paketlenmiş kütüphanelerle çakışır. ':pio build'
    de bu yoldan geçtiği için bu, uygulamanın varlık sebebine dokunur.

    env ve frozen parametre olarak alınıyor ki bu yol DONMADAN test
    edilebilsin; aksi halde yalnız yayınlanmış binary'de sınanabilirdi. """
    result = dict(os.environ if env is None else env)
    is_frozen = getattr(sys, "frozen", False) if frozen is None else frozen

    for name in _FROZEN_VARS:
        original = result.pop(f"{name}_ORIG", None)
        if original is not None:
            result[name] = original
        elif is_frozen:
            result.pop(name, None)

    return result


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
    finished = pyqtSignal()       # child süreç sona erdi
    exited = pyqtSignal(int)      # child sürecin çıkış kodu

    # DİKKAT: 'finished' ARGÜMANSIZ kalmalı. TerminalView onu doğrudan
    # QWidget.update'e bağlıyor; sinyale int eklenirse Qt update(int)
    # overload'ı arar ve bağlantı sessizce kopar (terminal çizmeyi bırakır).
    # Çıkış kodu bu yüzden ayrı 'exited' sinyaliyle taşınıyor.

    def __init__(self, rows=9, cols=80, argv=None, cwd=None, parent=None):
        super().__init__(parent)
        self.rows, self.cols = rows, cols
        self.argv = argv        # None -> kullanıcının login shell'i (':term')
        self.cwd = cwd          # None -> sürecin mevcut çalışma dizini
        self.exit_code = None
        self._pid = None
        self._master_fd = None
        self._notifier = None
        self.screen = None
        self._stream = None

    def is_running(self):
        return self._pid is not None

    def start(self):
        """ pty.fork() ile gerçek bir sözde-terminal (pseudo-terminal) üzerinde
        bir süreç başlatır: argv verilmemişse kullanıcının kendi shell'ini
        (SHELL ortam değişkeni, yoksa /bin/bash) login shell olarak, verilmişse
        doğrudan o komutu (':pio build' gibi). """
        if self.is_running():
            return
        env = child_environment()
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"

        if self.argv is None:
            shell = os.environ.get("SHELL", "/bin/bash")
            argv = [shell, "-l"]
        else:
            argv = list(self.argv)

        self.exit_code = None
        pid, master_fd = pty.fork()
        if pid == 0:
            # Child süreç: pty.fork() setsid + TIOCSCTTY + 0/1/2 dup işini
            # zaten kendi içinde halletti. Burada tek iş exec etmek.
            try:
                if self.cwd:
                    os.chdir(self.cwd)
                os.execvpe(argv[0], argv, env)
            except Exception:
                # 127: kabuk geleneğinde "komut bulunamadı"; sekme başlığında
                # '✗ (127)' olarak görünsün diye 1 değil bu.
                os._exit(127)

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
        """ Ölçüyü her hâlükârda saklar. PTY boyutu start() sırasında
        kurulduğu için, süreç henüz başlamamışken gelen ölçü ATILIRSA komut
        sekmesi 80 sütunla başlar ve 'pio'nun ilk çıktısı yanlış sarmalanır;
        bu yüzden erken dönüş yalnız ioctl/screen kısmını atlıyor. """
        if rows == self.rows and cols == self.cols:
            return
        self.rows, self.cols = rows, cols
        if not self.is_running():
            return
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
        if self._pid is None:
            return          # close() zaten temizlemiş
        if self._notifier:
            self._notifier.setEnabled(False)
        try:
            # WNOHANG DEĞİL: PTY'de EOF ile çocuğun reap edilebilir hâle
            # gelmesi arasında yarış var, WNOHANG (0, 0) dönüp çıkış kodunu
            # kaçırabiliyor. EOF geldiyse çocuk zaten ölmek üzere olduğundan
            # bloklayan bekleme pratikte anında dönüyor.
            _pid, status = os.waitpid(self._pid, 0)
            # Sinyalle ölen süreçte (ör. Ctrl+C -> SIGINT) negatif değer döner.
            self.exit_code = os.waitstatus_to_exitcode(status)
        except (ChildProcessError, OSError):
            self.exit_code = -1
        # Reap edildi: is_running() artık dürüst olsun. Bayat bir _pid,
        # "biten sekme yeniden çalışmasın" korumasını sessizce üstlenir ve
        # TerminalView'daki asıl koruma (_finished) ölü kodmuş gibi görünür.
        self._pid = None
        self.finished.emit()
        self.exited.emit(self.exit_code)

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
