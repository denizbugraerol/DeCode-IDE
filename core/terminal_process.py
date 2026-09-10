import os
import sys

import pyte
from PyQt6.QtCore import QObject, pyqtSignal

if sys.platform == "win32":
    from core.pty_windows import WindowsTransport as _Transport
else:
    from core.pty_posix import PosixTransport as _Transport


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
    """ Bir süreci sözde-terminal üzerinde başlatıp çıktısını pyte ile
    yorumlayan bileşen. Platforma özgü iş (spawn, okuma döngüsü, winsize,
    kill) bir transport nesnesine devredilmiştir: POSIX'te
    core/pty_posix.py, Windows'ta core/pty_windows.py. Qt widget'ından
    bağımsızdır -- çizimi ui/components/terminal_panel.py yapar. """

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
        self.argv = argv        # None -> kullanıcının varsayılan kabuğu (':term')
        self.cwd = cwd          # None -> sürecin mevcut çalışma dizini
        self.exit_code = None
        self.screen = None
        self._stream = None
        self._transport = _Transport(parent=self)

    def is_running(self):
        return self._transport.is_alive()

    def shell_name(self):
        """ Sekme başlığında görünen kabuk adı. Windows'ta '.exe' atılır;
        sekmede 'powershell.exe' değil 'powershell' yazsın. """
        name = os.path.basename(self._transport.default_shell_argv()[0])
        return name[:-4] if name.lower().endswith(".exe") else name

    def start(self):
        if self.is_running():
            return
        env = child_environment()
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"

        argv = (list(self.argv) if self.argv is not None
                else self._transport.default_shell_argv())

        self.exit_code = None
        # Ekran spawn'DAN ÖNCE kuruluyor: Windows'ta okuma thread'i spawn
        # içinde başlıyor ve ilk parça ana döngüye kuyruklanabiliyor. Ekran
        # o an hazır değilse _on_data None bir stream'e feed eder.
        self.screen = _PtyBackedScreen(self.cols, self.rows, write_back=self.write)
        self._stream = pyte.ByteStream(self.screen)

        self._transport.spawn(argv, self.cwd, env, self.rows, self.cols,
                              self._on_data, self._on_eof)

    def _on_data(self, data):
        try:
            self._stream.feed(data)
        except Exception:
            pass  # pyte'ın çözemediği zararsız bir kaçış dizisi; devam et
        self.output_ready.emit()

    def _on_eof(self):
        self.exit_code = self._transport.exit_code()
        self.finished.emit()
        self.exited.emit(self.exit_code)

    def resize(self, rows, cols):
        """ Ölçüyü her hâlükârda saklar. PTY boyutu spawn sırasında kurulduğu
        için, süreç henüz başlamamışken gelen ölçü ATILIRSA komut sekmesi 80
        sütunla başlar ve 'pio'nun ilk çıktısı yanlış sarmalanır; bu yüzden
        erken dönüş yalnız ekran/winsize kısmını atlıyor. """
        if rows == self.rows and cols == self.cols:
            return
        self.rows, self.cols = rows, cols
        if not self.is_running():
            return
        # DİKKAT: Screen() constructor'ı (columns, lines) sırasında ama
        # resize() metodu (lines, columns) sırasında bekliyor.
        self.screen.resize(lines=rows, columns=cols)
        self._transport.set_size(rows, cols)

    def write(self, data: bytes):
        self._transport.write(data)

    def close(self):
        """ Panel gizlenirken DEĞİL, sadece uygulama tamamen kapanırken
        çağrılır (bkz. IDEWindow.closeEvent). """
        self._transport.close(timeout=0.5)
