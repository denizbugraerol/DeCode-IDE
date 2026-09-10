""" POSIX transport: pty.fork tabanlı sözde-terminal.

core/terminal_process.py'nin platformdan bağımsız gövdesi import anında bu
modülü ya da (Windows'ta) core/pty_windows.py'yi seçer; ikisi aynı sözleşmeyi
sunar:

    spawn(argv, cwd, env, rows, cols, on_data, on_eof)
    write(data: bytes)      set_size(rows, cols)
    is_alive() -> bool      exit_code() -> int | None
    close(timeout)          default_shell_argv() -> list[str]

Sözleşmenin iki güvencesi var ve ikisi de bozulduğunda hata SESSİZ olur:

1. on_data / on_eof HER ZAMAN ana iş parçacığında çağrılır. Burada bedava
   (QSocketNotifier zaten ana döngüde); Windows tarafı bunu kuyruklu
   bağlantıyla sağlıyor. pyte.Screen ve TerminalPanel bu güvenceye
   dayanarak tek iş parçacıklı kalıyor.
2. close() ana iş parçacığında SÜRESİZ bloklanmaz -- bkz. close(). """
import fcntl
import os
import pty
import signal
import struct
import termios
import time

from PyQt6.QtCore import QSocketNotifier


class PosixTransport:
    def __init__(self, parent=None):
        self._parent = parent          # QSocketNotifier'a verilecek QObject
        self._pid = None
        self._master_fd = None
        self._notifier = None
        self._exit_code = None
        self._on_data = None
        self._on_eof = None

    def default_shell_argv(self):
        return [os.environ.get("SHELL", "/bin/bash"), "-l"]

    def spawn(self, argv, cwd, env, rows, cols, on_data, on_eof):
        self._on_data, self._on_eof = on_data, on_eof
        self._exit_code = None

        pid, master_fd = pty.fork()
        if pid == 0:
            # Child: pty.fork() setsid + TIOCSCTTY + 0/1/2 dup işini zaten
            # halletti. Burada tek iş exec etmek.
            try:
                if cwd:
                    os.chdir(cwd)
                os.execvpe(argv[0], argv, env)
            except Exception:
                # 127: kabuk geleneğinde "komut bulunamadı"; sekme başlığında
                # '✗ (127)' olarak görünsün diye 1 değil bu.
                os._exit(127)

        self._pid = pid
        self._master_fd = master_fd
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        self.set_size(rows, cols)

        self._notifier = QSocketNotifier(master_fd, QSocketNotifier.Type.Read,
                                         self._parent)
        self._notifier.activated.connect(self._drain)

    def set_size(self, rows, cols):
        if self._master_fd is None:
            return
        # struct winsize: ws_row, ws_col, ws_xpixel, ws_ypixel
        packed = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(self._master_fd, termios.TIOCSWINSZ, packed)
        # Not: TIOCSWINSZ çekirdek tarafından ön plandaki process group'a
        # otomatik SIGWINCH gönderir; elle sinyal yollamaya gerek yok.

    def write(self, data):
        if self._master_fd is None:
            return
        try:
            os.write(self._master_fd, data)
        except OSError:
            pass  # shell tam o anda öldüyse (EPIPE/EIO) sessizce yok say

    def is_alive(self):
        return self._pid is not None

    def exit_code(self):
        return self._exit_code

    def _drain(self, *_args):
        try:
            data = os.read(self._master_fd, 65536)
        except OSError:
            data = b""  # PTY'de EOF genelde b"" değil EIO olarak gelir
        if not data:
            self._handle_exit()
            return
        self._on_data(data)

    def _handle_exit(self):
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
            self._exit_code = os.waitstatus_to_exitcode(status)
        except (ChildProcessError, OSError):
            self._exit_code = -1
        # Reap edildi: is_alive() artık dürüst olsun. Bayat bir _pid,
        # "biten sekme yeniden çalışmasın" korumasını sessizce üstlenir ve
        # TerminalView'daki asıl koruma (_finished) ölü kodmuş gibi görünür.
        self._pid = None
        self._on_eof()

    def _reap(self, timeout):
        """ Çocuğu en fazla 'timeout' saniye WNOHANG ile yoklar. Toplandıysa
        -- ya da zaten bizim çocuğumuz değilse -- True, süre dolduysa False.
        BLOKLAYAN waitpid bilinçli olarak hiç kullanılmıyor; bkz. close(). """
        son = time.monotonic() + timeout
        while True:
            try:
                if os.waitpid(self._pid, os.WNOHANG)[0] != 0:
                    return True
            except (ChildProcessError, OSError):
                return True
            if time.monotonic() >= son:
                return False
            time.sleep(0.02)

    def close(self, timeout=0.5):
        if self._notifier:
            self._notifier.setEnabled(False)
            self._notifier.deleteLater()
            self._notifier = None
        if self._pid is not None:
            try:
                os.kill(self._pid, signal.SIGHUP)
            except ProcessLookupError:
                pass
            if not self._reap(timeout):
                try:
                    os.kill(self._pid, signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    pass
                # SIGKILL'den sonra da YALNIZ yoklayarak bekliyoruz. Burada
                # eskiden bloklayan bir os.waitpid(pid, 0) vardı ve macOS'ta
                # gerçekten asılı kalıyordu: pty.fork() çok iş parçacıklı bir
                # süreçten çağrıldığında çocuk fork ile exec arasında sıkışıp
                # toplanabilir hâle gelmiyor. Bu kod ANA İŞ PARÇACIĞINDA
                # (IDEWindow.closeEvent) çalıştığı için sonucu uygulamanın
                # kapanışta sonsuza kadar donmasıydı.
                #
                # Süre dolarsa çocuğu bırakıyoruz: SIGKILL almış bir süreç
                # zaten ölüyor, biz toplamazsak da süreç çıkışında init
                # topluyor. Geride kalan bir zombi, donmuş bir arayüzden
                # kesinlikle iyidir.
                self._reap(timeout)
            self._pid = None
        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None
