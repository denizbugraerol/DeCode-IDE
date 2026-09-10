# Windows Portu ve Dağıtımı — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** DeCode IDE Windows'ta çalışsın ve GitHub Releases'ten tek bir `.exe` olarak yayınlansın — `:term` ve bütün `:pio` alt komutları dahil.

**Architecture:** `core/terminal_process.py` bir *transport dikişine* ayrılıyor. Platformdan bağımsız her şey (`pyte` ekranı, çıkış kodu semantiği, `child_environment`, `resize`'ın ölçüyü saklaması) `TerminalProcess`'te tek yerde kalıyor; platforma özgü dört iş `core/pty_posix.py` ve `core/pty_windows.py`'ye iniyor ve import anında biri seçiliyor. Windows tarafı ConPTY (`pywinpty`) ve bloklayan okuma yapan bir `QThread` kullanıyor, çünkü `QSocketNotifier` orada yalnız socket tanıtıcılarıyla çalışıyor.

**Tech Stack:** Python 3.12, PyQt6, `pyte`, `pywinpty` (yalnız Windows), PyInstaller 6.22+, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-10-windows-portu-design.md`

## Global Constraints

- **Dil:** Yorumlar, docstring'ler, commit mesajları ve `docs/` **Türkçe**. Mevcut dosyaların üslubuna uy.
- **Test komutu:** `.venv/bin/python -m pytest -q` (console script'lerin shebang'i bayat — hep `-m` ile çağır).
- **Yeşil taban çizgisi:** 273 test. Hiçbir task bu sayıyı düşürmemeli.
- **Transport sözleşmesi** (iki modül de birebir sunar):
  `spawn(argv, cwd, env, rows, cols, on_data, on_eof)` · `write(data: bytes)` · `set_size(rows, cols)` · `is_alive() -> bool` · `exit_code() -> int | None` · `close(timeout: float)` · `default_shell_argv() -> list[str]`
- **Güvence 1:** `on_data`/`on_eof` **her zaman ana iş parçacığında** çağrılır.
- **Güvence 2:** `close()` hiçbir platformda ana iş parçacığında **süresiz bloklanmaz**.
- **Çıkış kodu 127** = "komut bulunamadı", her iki platformda aynı anlam.
- **Bağımlılık satırı:** `pywinpty>=2.0 ; sys_platform == "win32"` — Linux/macOS kurulumu değişmemeli.
- **Renk sabiti yasağı:** `ui/` ve `core/` içine `#rrggbb` yazma (`tests/test_no_hardcoded_colors.py` bunu tarıyor).
- **Platform dallarını parametreyle test et:** `main._qt_platform_hint(platform_name, current)` deseni — yeni platform dalları da `platform_name=` parametresi alacak ki Linux CI'da sınanabilsinler.

---

### Task 1: Testlerdeki POSIX'e sabit komutları platforma bağla

Windows'ta `/bin/echo` yok. Bu task davranış değiştirmiyor; yalnız testleri taşınabilir kılıyor, böylece sonraki task'lar Windows runner'ında koşabilir.

**Files:**
- Create: `tests/platform_commands.py`
- Modify: `tests/test_terminal_process.py`
- Modify: `tests/test_terminal_command.py`

**Interfaces:**
- Consumes: yok (ilk task).
- Produces: `tests/platform_commands.py` → `echo_argv(metin) -> list[str]`, `exit_argv(kod) -> list[str]`, `pwd_argv() -> list[str]`, `missing_argv() -> list[str]`, `exe_name(taban) -> str`, `WINDOWS: bool`. Task 3 ve Task 4 bunları kullanıyor.

- [ ] **Step 1: Yardımcı modülü yaz**

`tests/platform_commands.py`:

```python
""" Testlerdeki kabuk komutlarını platforma göre çözen yardımcı.

Testler eskiden '/bin/echo', '/bin/sh -c exit 1' gibi POSIX'e sabit yollar
kullanıyordu; Windows'ta bunların hiçbiri yok ve testler orada import bile
edilemeden anlamsızlaşıyordu.

'/bin/false' bilinçli olarak KULLANILMIYOR: macOS'ta o dosya /usr/bin'de,
/bin'de değil -- orada exec 127 ile başarısız olur ve test ölçmek istediği
şeyi değil kendi taşınabilirsizliğini ölçer. '/bin/sh' POSIX güvencesiyle
her iki sistemde de var. """
import sys

WINDOWS = sys.platform == "win32"


def echo_argv(metin):
    """ Verilen metni basıp 0 ile çıkan komut. """
    if WINDOWS:
        return ["cmd", "/c", "echo", metin]
    return ["/bin/echo", metin]


def exit_argv(kod):
    """ Hiçbir şey basmadan verilen kodla çıkan komut. """
    if WINDOWS:
        return ["cmd", "/c", f"exit {kod}"]
    return ["/bin/sh", "-c", f"exit {kod}"]


def pwd_argv():
    """ Çalışma dizinini basan komut ('cwd uygulanıyor mu' testi için).
    Windows'ta argümansız 'cd' bunu yapar. """
    if WINDOWS:
        return ["cmd", "/c", "cd"]
    return ["/bin/pwd"]


def missing_argv():
    """ Var olmayan komut: spawn/exec başarısız olmalı, çıkış kodu 127. """
    if WINDOWS:
        return ["decode-testi-olmayan-komut"]
    return ["/olmayan/komut"]


def exe_name(taban):
    """ Sahte çalıştırılabilir dosya adı. Windows'ta shutil.which yalnız
    PATHEXT uzantılı dosyaları bulur, yani 'pio' değil 'pio.exe' aranır. """
    return f"{taban}.exe" if WINDOWS else taban
```

- [ ] **Step 2: `test_terminal_process.py`'yi yardımcıya geçir**

`tests/test_terminal_process.py` içinde import ekle ve dört çağrıyı değiştir:

```python
from tests.platform_commands import echo_argv, exit_argv, missing_argv, pwd_argv
```

| Eski | Yeni |
|---|---|
| `["/bin/echo", "merhaba"]` | `echo_argv("merhaba")` |
| `["/bin/sh", "-c", "exit 1"]` | `exit_argv(1)` |
| `["/olmayan/komut"]` | `missing_argv()` |
| `["/bin/pwd"]` | `pwd_argv()` |
| `["/bin/sh", "-c", "exit 0"]` | `exit_argv(0)` |

Yorumlardaki `/bin/false` açıklaması artık `platform_commands.py`'de duruyor; testteki uzun yorumu şuna indir:

```python
def test_basarisiz_komutun_cikis_kodu(qapp, bekle):
    # Komutun kendisi platforma göre seçiliyor; gerekçe için bkz.
    # tests/platform_commands.py.
    surec, kodlar = _calistir(bekle, exit_argv(1))
```

- [ ] **Step 3: `test_terminal_command.py`'yi yardımcıya geçir**

```python
from tests.platform_commands import echo_argv, exit_argv
```

`["/bin/echo", "merhaba"]` → `echo_argv("merhaba")`, `["/bin/echo", "bir"]` → `echo_argv("bir")`, `["/bin/echo", "iki"]` → `echo_argv("iki")`, `["/bin/sh", "-c", "exit 1"]` → `exit_argv(1)`. Modül docstring'indeki "`/bin/echo` ve `/bin/false` yetiyor" cümlesini "platforma göre seçilen minik kabuk komutları yetiyor (bkz. `tests/platform_commands.py`)" yap.

- [ ] **Step 4: Testleri çalıştır**

Run: `.venv/bin/python -m pytest -q`
Expected: `273 passed` — davranış değişmedi, yalnız komutlar dolaylandı.

- [ ] **Step 5: Commit**

```bash
git add tests/platform_commands.py tests/test_terminal_process.py tests/test_terminal_command.py
git commit -m "test: kabuk komutlarını platforma bağla

Windows'ta /bin/echo ve /bin/sh yok. Testler artık komutu
tests/platform_commands.py üzerinden alıyor; davranış değişmedi."
```

---

### Task 2: Transport dikişi (POSIX)

Saf yeniden yapılandırma: davranış **hiç** değişmiyor, 273 test yeşil kalıyor. Windows kodu bu task'ta yok.

**Files:**
- Create: `core/pty_posix.py`
- Modify: `core/terminal_process.py`
- Modify: `ui/components/terminal_panel.py` (`shell_name` delegasyonu)
- Create: `tests/test_pty_transport.py`
- Modify: `tests/test_terminal_process.py` (`close` testi transport'a taşınıyor)

**Interfaces:**
- Consumes: Task 1 → `echo_argv`, `exit_argv`, `missing_argv`, `pwd_argv`.
- Produces: `core/pty_posix.PosixTransport` (Global Constraints'teki sözleşme). `core/terminal_process.TerminalProcess.shell_name() -> str`. Task 3 aynı sözleşmeyi `WindowsTransport` ile karşılayacak.

- [ ] **Step 1: Sözleşme testlerini yaz (başarısız olacaklar)**

`tests/test_pty_transport.py`:

```python
""" Transport sözleşmesinin testleri.

DİKKAT: bunlar AKTİF transport'a karşı koşar -- Linux/macOS'ta
PosixTransport, Windows runner'ında WindowsTransport. Yani tek dosya iki
uygulamayı da sınıyor ve sözleşme ihlali hangi platformda olursa olsun
burada yakalanıyor. Bu yüzden skipif YOK.

Sözleşme TerminalProcess üzerinden sınanıyor, transport sınıfı doğrudan
kurulmuyor: dışarıya verilen davranış bu ve iki katmanın birlikte doğru
çalışması asıl mesele. """
import os

from core.terminal_process import TerminalProcess
from tests.platform_commands import echo_argv, exit_argv, missing_argv, pwd_argv


def _calistir(bekle, argv, cwd=None, cols=200):
    surec = TerminalProcess(rows=6, cols=cols, argv=argv, cwd=cwd)
    kodlar = []
    surec.exited.connect(kodlar.append)
    surec.start()
    bekle(lambda: bool(kodlar))
    return surec, kodlar


def test_sozlesme_cikti_okunuyor(qapp, bekle):
    surec, kodlar = _calistir(bekle, echo_argv("merhaba"))
    try:
        assert kodlar == [0]
        assert "merhaba" in "".join(surec.screen.display)
    finally:
        surec.close()


def test_sozlesme_turkce_karakter_bozulmuyor(qapp, bekle):
    """ UTF-8 sınır riski: çok baytlı bir karakter iki okuma arasında
    bölünebilir. pyte.ByteStream artık tutan bir decoder taşıdığı için
    doğru birleşmeli -- bu test onu her iki transport'ta da doğruluyor. """
    metin = "ığüşöçİĞÜŞÖÇ" * 20
    surec, kodlar = _calistir(bekle, echo_argv(metin))
    try:
        assert kodlar == [0]
        ekran = "".join(surec.screen.display)
        assert "ığüşöçİĞÜŞÖÇ" in ekran
        assert "\ufffd" not in ekran, "UTF-8 çözümü bozuldu (replacement char)"
    finally:
        surec.close()


def test_sozlesme_cikis_kodu(qapp, bekle):
    surec, kodlar = _calistir(bekle, exit_argv(1))
    try:
        assert kodlar == [1]
        assert surec.exit_code == 1
    finally:
        surec.close()


def test_sozlesme_olmayan_komut_127(qapp, bekle):
    """ 'Komut bulunamadı' = 127, iki platformda da aynı anlam: sekme
    başlığında '✗ (127)' olarak görünüyor. """
    surec, kodlar = _calistir(bekle, missing_argv())
    try:
        assert kodlar == [127]
    finally:
        surec.close()


def test_sozlesme_cwd_uygulanir(qapp, bekle, tmp_path):
    hedef = os.path.realpath(str(tmp_path))
    surec, _kodlar = _calistir(bekle, pwd_argv(), cwd=hedef)
    try:
        assert os.path.basename(hedef) in "".join(surec.screen.display)
    finally:
        surec.close()


def test_sozlesme_close_donuyor_ve_is_running_dusuyor(qapp):
    surec = TerminalProcess(rows=6, cols=40)
    surec.start()
    assert surec.is_running()
    surec.close()
    assert not surec.is_running()


def test_sozlesme_close_sonrasi_gec_veri_sinyal_yaymiyor(qapp, bekle):
    """ Kapanıştan sonra gelen veri output_ready yaymamalı: Windows'ta
    reader thread bırakılabildiği için bu gerçek bir risk, POSIX'te de
    notifier kapatılmış olmalı. """
    surec = TerminalProcess(rows=6, cols=40, argv=echo_argv("bir"))
    surec.start()
    surec.close()

    sayac = []
    surec.output_ready.connect(lambda: sayac.append(1))
    bekle(lambda: False, zaman_asimi=0.3)   # olay döngüsünü bir süre döndür
    assert sayac == []


def test_sozlesme_set_size_kosarken_ve_kosmazken(qapp):
    """ PTY boyutu spawn sırasında kuruluyor; süreç yokken gelen ölçü
    ATILIRSA komut sekmesi 80 sütunla başlar ve ilk çıktı yanlış sarmalanır. """
    surec = TerminalProcess(rows=6, cols=40, argv=exit_argv(0))
    surec.resize(9, 120)
    assert (surec.rows, surec.cols) == (9, 120)

    surec.start()
    try:
        surec.resize(10, 100)
        assert (surec.rows, surec.cols) == (10, 100)
        assert surec.screen.columns == 100
    finally:
        surec.close()
```

- [ ] **Step 2: Testleri çalıştır, geçtiklerini gör**

Run: `.venv/bin/python -m pytest tests/test_pty_transport.py -q`
Expected: PASS — bu testler bugünkü `TerminalProcess`'te de geçmeli. **Bu bilinçli:** sözleşme testleri yeniden yapılandırmanın *emniyet ağı*, hedefi değil. Geçmiyorlarsa önce testi düzelt; yeniden yapılandırmaya yeşil taban olmadan başlama.

- [ ] **Step 3: `core/pty_posix.py`'yi yaz**

Gövdeler bugünkü `TerminalProcess`'ten **birebir** taşınıyor; hiçbir davranış değişmiyor.

```python
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
```

- [ ] **Step 4: `core/terminal_process.py`'yi dikişe geçir**

`fcntl`, `pty`, `signal`, `struct`, `termios`, `time` import'ları ve `QSocketNotifier` **kalkıyor** (hepsi transport'ta). Dosyanın yeni hâli:

```python
import os
import sys

import pyte
from PyQt6.QtCore import QObject, pyqtSignal

if sys.platform == "win32":
    from core.pty_windows import WindowsTransport as _Transport
else:
    from core.pty_posix import PosixTransport as _Transport
```

`_FROZEN_VARS`, `child_environment` ve `_PtyBackedScreen` **olduğu gibi kalıyor**. `TerminalProcess` gövdesi:

```python
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
```

`_write_to_master` metodu **siliniyor** — `_PtyBackedScreen`'in `write_back`'i artık doğrudan `self.write`.

- [ ] **Step 5: `shell_name()` delegasyonunu bağla**

`ui/components/terminal_panel.py` içindeki `TerminalView.shell_name` gövdesini değiştir:

```python
    def shell_name(self):
        """ Kabuk adını sürece soruyor: '$SHELL' yalnız POSIX'te var, Windows'ta
        kabuk seçimi transport'un işi (bkz. core/pty_windows.py). """
        return self._process.shell_name()
```

Dosyanın başındaki `import os` başka bir yerde kullanılmıyorsa kaldır — kullanılıyorsa dokunma (`grep -n "os\." ui/components/terminal_panel.py` ile bak).

- [ ] **Step 6: `close` testini transport'a taşı**

`tests/test_terminal_process.py` içindeki `test_close_toplanamayan_cocukta_asili_kalmaz` artık `surec._pid` / `surec._master_fd` iç alanlarını kurcalıyor; bunlar transport'a taşındı. Testi şuna **değiştir** (aynı değişmezi, doğru katmanda ölçüyor):

```python
def test_close_toplanamayan_cocukta_asili_kalmaz(qapp, monkeypatch):
    """ close() hiçbir koşulda BLOKLAYAN waitpid çağırmamalı.

    macOS CI'da yaşanan kilit buydu: pty.fork() çok iş parçacıklı bir süreçten
    çağrıldığında çocuk, fork ile exec arasında sıkışıp yarım saniyede
    toplanabilir hâle gelmiyor. close() o zaman SIGKILL'in ardından zaman
    aşımsız bir os.waitpid(pid, 0)'a giriyor ve dönmüyor -- bu çağrı ANA İŞ
    PARÇACIĞINDA (IDEWindow.closeEvent) olduğu için uygulama kapanışta
    sonsuza kadar donuyor.

    Test gerçek bir öldürülemez süreç kuramaz; onun yerine değişmezi
    doğruluyor: çocuk hiç toplanmasa bile close() dönmeli ve her waitpid
    çağrısı WNOHANG taşımalı.

    Transport'a DOĞRUDAN bakıyor: dikişten sonra süreç kimliği ve fd orada
    yaşıyor, TerminalProcess'te değil. """
    from core.pty_posix import PosixTransport

    transport = PosixTransport()
    transport._pid = 424242        # gerçek bir süreç değil; sistem çağrıları taklit
    transport._master_fd = None

    bayraklar = []

    def sahte_waitpid(pid, flags):
        bayraklar.append(flags)
        return (0, 0)              # "henüz toplanamadı" -- hiç toplanmayacak

    monkeypatch.setattr(os, "waitpid", sahte_waitpid)
    monkeypatch.setattr(os, "kill", lambda pid, sig: None)

    transport.close(timeout=0.05)

    assert bayraklar, "close() çocuğu hiç yoklamamış"
    assert all(f & os.WNOHANG for f in bayraklar), (
        f"close() bloklayan waitpid çağırdı (bayraklar={bayraklar})")
    assert transport._pid is None
```

Dosyanın en üstüne bu testi POSIX'e sınırlayan bir işaret ekle (Windows'ta `pty_posix` import bile edilemez):

```python
import pytest

pytestmark_posix = pytest.mark.skipif(
    sys.platform == "win32",
    reason="PosixTransport'un iç davranışı; Windows'ta modül import edilemez")
```

ve testin üstüne `@pytestmark_posix` koy. `import sys` ve `import pytest` satırlarını ekle.

- [ ] **Step 7: Bütün testleri çalıştır**

Run: `.venv/bin/python -m pytest -q`
Expected: `281 passed` (273 + 8 yeni sözleşme testi). Bir kırılma varsa yeniden yapılandırma davranış değiştirmiş demektir — düzelt, testi gevşetme.

- [ ] **Step 8: Commit**

```bash
git add core/pty_posix.py core/terminal_process.py ui/components/terminal_panel.py tests/test_pty_transport.py tests/test_terminal_process.py
git commit -m "refactor: TerminalProcess'i transport dikişine ayır

Platformdan bağımsız her şey (pyte ekranı, çıkış kodu semantiği,
child_environment, resize'ın ölçüyü saklaması) TerminalProcess'te
kalıyor; pty.fork/fcntl/termios core/pty_posix.py'ye iniyor ve import
anında seçiliyor. Davranış değişmedi.

Sözleşme iki güvence taşıyor: callback'ler her zaman ana iş
parçacığında çağrılır, ve close() ana iş parçacığında süresiz
bloklanmaz."
```

---

### Task 3: ConPTY transport (Windows)

Bu task'ın kodu Linux'ta **koşturulamaz**. Adım 1 bir ölçüm ve **Windows makinesinde** yapılıyor; sonucu koda giriyor.

**Files:**
- Create: `core/pty_windows.py`
- Modify: `requirements.txt`
- Modify: `core/terminal_process.py` (import dalı + `_UnavailableTransport`, Adım 4)
- Modify: `tests/test_pty_transport.py` (yedek transport testi, Adım 4)

**Interfaces:**
- Consumes: Task 2 → Global Constraints'teki transport sözleşmesi; `TerminalProcess` `_Transport(parent=self)` ile kuruyor ve `spawn(argv, cwd, env, rows, cols, on_data, on_eof)` çağırıyor.
- Produces: `core/pty_windows.WindowsTransport` ve `core/terminal_process._UnavailableTransport` — ikisi de aynı sözleşmeyi karşılıyor.

- [ ] **Step 1: `pywinpty`'nin okuma tipini ÖLÇ (Windows makinesinde)**

`pip install pywinpty` sonrası şunu çalıştır ve çıktıyı not al:

```python
# olcum.py -- Windows'ta çalıştır, sonucu Adım 3'e gireceğiz
from winpty import PtyProcess

p = PtyProcess.spawn('cmd /c echo ığüşöçİĞÜŞÖÇığüşöçİĞÜŞÖÇığüşöçİĞÜŞÖÇ')
parcalar = []
while p.isalive():
    try:
        parcalar.append(p.read(16))   # KÜÇÜK okuma: sınır bölünmesini zorlar
    except EOFError:
        break

print("tip       :", {type(x).__name__ for x in parcalar})
print("parça     :", len(parcalar))
birlesik = "".join(parcalar) if parcalar and isinstance(parcalar[0], str) else b"".join(parcalar)
print("replacement char var mı:", "\ufffd" in (birlesik if isinstance(birlesik, str) else birlesik.decode("utf-8", "replace")))
print(birlesik)
```

Sonucu üç dala göre yorumla (tasarım dokümanı §C tablosu):

| Ölçüm | Yapılacak |
|---|---|
| `bytes` | Doğrudan geçir; `pyte.ByteStream` sınırları zaten hallediyor. Adım 3'teki `_to_bytes` olduğu gibi kalır. |
| `str`, replacement char **yok** | `.encode("utf-8")` kayıpsız. Adım 3'teki `_to_bytes` olduğu gibi kalır. |
| `str`, replacement char **var** | Bozulma pywinpty'nin içinde; dışarıdan tampon düzeltmez. Alt seviye `winpty.PTY` API'sine in (bytes verir) ve Adım 3'ü ona göre yaz. **Bu dala düşerseniz durun ve planı güncelleyin.** |

- [ ] **Step 2: Bağımlılığı ekle**

`requirements.txt`:

```
PyQt6>=6.4
pyte>=0.8.2
pywinpty>=2.0 ; sys_platform == "win32"
```

Ortam işaretçisi kritik: Linux/macOS'ta `pip install -r requirements.txt` bu satırı atlar, yani mevcut kurulumlar ve CI adımları hiç değişmez.

- [ ] **Step 3: `core/pty_windows.py`'yi yaz**

```python
""" Windows transport: ConPTY (pywinpty) tabanlı sözde-terminal.

Sözleşme ve iki güvencesi için bkz. core/pty_posix.py'nin docstring'i.

Neden POSIX'ten yapısal olarak farklı: QSocketNotifier Windows'ta yalnız
SOCKET tanıtıcılarıyla çalışır, ConPTY ise boru verir. Bu yüzden okuma,
bloklayan bir QThread'de yapılıp sonuç KUYRUKLU bağlantıyla ana thread'e
taşınıyor -- 1. güvence böyle sağlanıyor. Desen depoda zaten var:
core/file_index.py, FileIndexWorker. """
import os
import shutil
import subprocess
import time

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from winpty import PtyProcess


# close() süre dolduğu için BIRAKTIĞI thread'ler. Modül düzeyinde referans
# tutuluyor: sahibi yok edilirken hâlâ koşan bir QThread, Qt'de
# "QThread: Destroyed while thread is still running" ile süreci çökertir.
# Başıboş bir thread, çöken bir kapanıştan iyidir (POSIX'te zombiyi bırakma
# kararının aynı gerekçesi).
_BIRAKILAN_THREADLER = []


class _ReaderThread(QThread):
    """ ConPTY'den bloklayarak okur; her parçayı sinyalle ana thread'e taşır.

    Kendi UTF-8 tamponunu TUTMUYOR ve tutmamalı: pyte.ByteStream zaten artık
    tutan bir incremental decoder taşıyor (codecs.getincrementaldecoder), yani
    çok baytlı bir karakter iki parçaya bölünse bile doğru birleşiyor. Burada
    ikinci bir tampon kurmak yalnız aynı işi iki kez yapardı. """

    data_received = pyqtSignal(bytes)
    eof = pyqtSignal()

    def __init__(self, pty, parent=None):
        super().__init__(parent)
        self._pty = pty
        self._durduruldu = False

    def durdur(self):
        """ Döngü bayrağını düşürür. Okuma o an bloklu olabilir; asıl
        uyandırma pty'nin kapatılmasından gelir (bkz. WindowsTransport.close). """
        self._durduruldu = True

    def run(self):
        while not self._durduruldu:
            try:
                parca = self._pty.read(65536)
            except Exception:
                break          # EOF ya da kapatılmış pty; ikisi de normal çıkış
            if not parca:
                break
            if not self._durduruldu:
                self.data_received.emit(_to_bytes(parca))
        self.eof.emit()


def _to_bytes(parca):
    """ pywinpty str döndürüyorsa UTF-8'e geri kodlar. Sözleşme bytes;
    sınır birleştirme işi pyte.ByteStream'in. """
    if isinstance(parca, bytes):
        return parca
    return parca.encode("utf-8", errors="replace")


class WindowsTransport(QObject):
    """ QObject: reader thread'in sinyalini kuyruklu bağlantıyla almak için
    bir QObject'e ihtiyaç var (POSIX transport'un QObject olmasına gerek yok,
    bu asimetri bilinçli). """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pty = None
        self._reader = None
        self._exit_code = None
        self._on_data = None
        self._on_eof = None

    def default_shell_argv(self):
        """ Windows'ta '$SHELL' yok. PowerShell 7 -> Windows PowerShell ->
        cmd.exe sırası: ilki en yetenekli, sonuncusu her kurulumda var. """
        for name in ("pwsh.exe", "powershell.exe"):
            yol = shutil.which(name)
            if yol:
                return [yol]
        return [os.environ.get("COMSPEC", "cmd.exe")]

    def spawn(self, argv, cwd, env, rows, cols, on_data, on_eof):
        self._on_data, self._on_eof = on_data, on_eof
        self._exit_code = None

        # ConPTY argv listesi değil tek bir KOMUT SATIRI dizesi alıyor.
        # list2cmdline, boşluklu yolları ('C:\Program Files\...') MS C çalışma
        # zamanı kurallarına göre tırnaklayan tek doğru yol; elle ' '.join
        # sessizce bozar.
        komut = subprocess.list2cmdline(argv)
        try:
            self._pty = PtyProcess.spawn(komut, dimensions=(rows, cols),
                                         cwd=cwd, env=env)
        except Exception:
            # POSIX'te exec başarısızlığı child'da os._exit(127) oluyor;
            # burada exception geliyor. Aynı anlamı taşısın diye 127.
            self._pty = None
            self._exit_code = 127
            on_eof()
            return

        self._reader = _ReaderThread(self._pty, parent=self)
        # Kuyruklu bağlantı: thread'den gelen veri ANA iş parçacığında
        # işlensin (sözleşmenin 1. güvencesi). QThread'in kendisi bu nesnenin
        # thread'inde yaşadığı için Qt bağlantıyı otomatik olarak kuyruklu
        # seçiyor; yine de açıkça yazmıyoruz ki varsayılan davranış değişirse
        # sessizce bozulmasın -- bkz. testler.
        self._reader.data_received.connect(self._on_reader_data)
        self._reader.eof.connect(self._on_reader_eof)
        self._reader.start()

    def _on_reader_data(self, data):
        if self._on_data:
            self._on_data(data)

    def _on_reader_eof(self):
        if self._pty is not None:
            # EOF ile çıkış kodunun okunabilir hâle gelmesi arasında yarış
            # var -- POSIX'teki waitpid yarışının birebir karşılığı. Orada
            # bloklayan bir waitpid kullanılıyor ("EOF geldiyse çocuk zaten
            # ölmek üzere"); burada aynı gerekçeyle KISA ve SÜRELİ yokluyoruz.
            # Yoklamazsak exitstatus None gelir ve sekme gerçek kodu yerine
            # '✗ (-1)' gösterir.
            #
            # Bu ana iş parçacığında çalışıyor ama üst sınırı 0.5 saniye ve
            # yalnız süreç ölürken bir kez; 2. güvence close() hakkında.
            son = time.monotonic() + 0.5
            while time.monotonic() < son:
                try:
                    if not self._pty.isalive():
                        break
                except Exception:
                    break
                time.sleep(0.02)
            try:
                self._exit_code = self._pty.exitstatus
            except Exception:
                self._exit_code = None
        if self._exit_code is None:
            self._exit_code = -1
        self._pty = None
        if self._on_eof:
            self._on_eof()

    def set_size(self, rows, cols):
        if self._pty is None:
            return
        try:
            # DİKKAT: PtyProcess.setwinsize (rows, cols) sırasında, alt seviye
            # winpty.PTY.set_size ise (cols, rows) sırasında bekliyor. Depoda
            # pyte.Screen'in aynı tuzağı zaten belgeli.
            self._pty.setwinsize(rows, cols)
        except Exception:
            pass  # süreç tam o anda öldüyse sessizce yok say

    def write(self, data: bytes):
        if self._pty is None:
            return
        try:
            self._pty.write(data.decode("utf-8", errors="replace"))
        except Exception:
            pass

    def is_alive(self):
        return self._pty is not None

    def exit_code(self):
        return self._exit_code

    def close(self, timeout=0.5):
        """ Üç adım, hepsi SÜRELİ -- sözleşmenin 2. güvencesi.

        Sıra önemli: bağlantı ÖNCE kesiliyor ki 3. adımda bırakılan bir
        thread silinmiş bir nesneye sinyal gönderemesin. """
        if self._reader is not None:
            self._reader.durdur()
            try:
                self._reader.data_received.disconnect()
                self._reader.eof.disconnect()
            except TypeError:
                pass          # zaten bağlı değil

        if self._pty is not None:
            try:
                self._pty.terminate(force=False)
            except Exception:
                pass
            if self._pty is not None and self._pty.isalive():
                try:
                    self._pty.terminate(force=True)
                except Exception:
                    pass
            self._pty = None

        if self._reader is not None:
            # Süre dolarsa thread BIRAKILIYOR. POSIX'te zombiyi bırakma
            # kararının birebir karşılığı ve aynı gerekçeyle: donmuş bir
            # arayüz, başıboş bir thread'den kesinlikle kötüdür. Bu kod
            # IDEWindow.closeEvent'ten, yani ANA İŞ PARÇACIĞINDA çalışıyor.
            if not self._reader.wait(int(timeout * 1000)):
                # Ebeveynlikten çıkarıp modül düzeyinde tutuyoruz: bu nesne
                # yok edilirken hâlâ koşan bir çocuk QThread, Qt'de süreci
                # çökertir.
                self._reader.setParent(None)
                _BIRAKILAN_THREADLER.append(self._reader)
            self._reader = None
```

- [ ] **Step 4: `pywinpty` yoksa uygulama çökmesin**

Spec §Hata yolları: "`pywinpty` import edilemiyor → tek satır uyarı; editör çalışmaya devam eder." Bu olmadan `from core.pty_windows import ...` bir `ImportError` fırlatır ve zincir yine import anında çöker — yani bu portun düzeltmek için var olduğu hatanın ta kendisi, farklı sebeple.

`core/terminal_process.py`'deki seçim bloğunu değiştir:

```python
if sys.platform == "win32":
    try:
        from core.pty_windows import WindowsTransport as _Transport
    except ImportError as _hata:      # pywinpty kurulu değil
        _IMPORT_HATASI = _hata
        _Transport = None
    else:
        _IMPORT_HATASI = None
else:
    from core.pty_posix import PosixTransport as _Transport
    _IMPORT_HATASI = None
```

`child_environment` tanımından sonra yedek transport'u ekle:

```python
class _UnavailableTransport:
    """ Terminal desteği kurulamadığında kullanılan yedek.

    Sözleşmenin TAMAMINI sunar ama hiçbir şey yapmaz: spawn tek satırlık bir
    uyarı basıp anında EOF verir ve çıkış kodu 127 olur ('komut bulunamadı'
    ile aynı konvansiyon). Böylece ':term' bir sekme açar, sekme '✗ (127)'
    der ve kullanıcı nedenini konsolda görür.

    Neden çökmek yerine bu: import anında çökmek, bu portun düzeltmek için
    var olduğu hatanın kendisiydi. Terminalin yokluğu editörü de
    götürmemeli. """

    def __init__(self, parent=None):
        self._exit_code = None

    def default_shell_argv(self):
        return ["yok"]

    def spawn(self, argv, cwd, env, rows, cols, on_data, on_eof):
        print(f"Terminal desteği kullanılamıyor: {_IMPORT_HATASI}")
        self._exit_code = 127
        on_eof()

    def write(self, data):
        pass

    def set_size(self, rows, cols):
        pass

    def is_alive(self):
        return False

    def exit_code(self):
        return self._exit_code

    def close(self, timeout=0.5):
        pass


_Transport = _Transport or _UnavailableTransport
```

Testi `tests/test_pty_transport.py`'ye ekle (Linux'ta koşar):

```python
def test_terminal_destegi_yoksa_uygulama_cokmez(qapp):
    """ pywinpty kurulu değilse uygulama AÇILMAMALI değil -- yalnız terminal
    çalışmamalı. Bu dal her platformda sınanabiliyor çünkü yedek transport
    import dalından bağımsız bir sınıf. """
    from core import terminal_process as tp

    surec = tp.TerminalProcess(rows=6, cols=40, argv=["olsun"])
    surec._transport = tp._UnavailableTransport()
    kodlar = []
    surec.exited.connect(kodlar.append)
    surec.start()

    assert kodlar == [127]
    assert not surec.is_running()
    assert surec.shell_name() == "yok"
```

- [ ] **Step 5: Linux'ta hiçbir şeyin bozulmadığını doğrula**

Run: `.venv/bin/python -m pytest -q`
Expected: `282 passed` (281 + yedek transport testi). `core/pty_windows.py` Linux'ta hiç import edilmiyor (`terminal_process.py`'deki dal), yani `winpty` kurulu olmasa da testler geçmeli. Geçmiyorsa dal yanlış yazılmış demektir.

- [ ] **Step 6: Windows makinesinde sözleşme testlerini koştur**

Windows'ta, depo kökünde:

```
py -m venv .venv-win
.venv-win\Scripts\python -m pip install -r requirements-dev.txt
.venv-win\Scripts\python -m pytest tests/test_pty_transport.py -v
```

Expected: `tests/test_pty_transport.py`'deki 9 testin hepsi PASS. Özellikle `test_sozlesme_turkce_karakter_bozulmuyor` ve `test_sozlesme_olmayan_komut_127`.

- [ ] **Step 7: Windows'ta tüm test paketini koştur**

Run: `.venv-win\Scripts\python -m pytest -q`
Expected: PASS. Kırılanlar bu noktada Task 4'ün konusu olabilir (`config_path`, `pio_cli`); listesini not al, düzeltmeyi Task 4'e bırak.

- [ ] **Step 8: Commit**

```bash
git add core/pty_windows.py requirements.txt
git commit -m "feat: ConPTY transport'u (Windows)

QSocketNotifier Windows'ta yalnız socket tanıtıcılarıyla çalıştığı için
okuma bloklayan bir QThread'de yapılıp kuyruklu bağlantıyla ana
thread'e taşınıyor. Kendi UTF-8 tamponu yok: pyte.ByteStream zaten
artık tutan bir decoder taşıyor.

close() üç adımda ve hepsi süreli; bağlantı önce kesiliyor ki süre
dolduğunda bırakılan thread silinmiş bir nesneye sinyal göndermesin."
```

---

### Task 4: Terminal dışı taşınabilirlik düzeltmeleri

Üçü de küçük, üçü de kullanıcıya görünür. Platform dalları `platform_name=` parametresi alıyor ki **Linux CI'da** sınanabilsinler — `main._qt_platform_hint` deseninin aynısı.

**Files:**
- Modify: `core/config.py:91-94`
- Modify: `embedded/pio_cli.py:35-47`
- Modify: `tests/test_config.py`
- Modify: `tests/test_pio_cli.py`

**Interfaces:**
- Consumes: Task 1 → `tests.platform_commands.exe_name`.
- Produces: `config.config_path(platform_name=None, environ=None) -> str`, `pio_cli.find_executable(platform_name=None) -> str | None`. Davranış varsayılan çağrıda (parametresiz) bugünküyle aynı.

- [ ] **Step 1: `config_path` testlerini yaz**

`tests/test_config.py`'ye ekle (dosyanın başında `import os` yoksa ekle):

```python
def test_config_path_windowsta_appdata_kullanir():
    """ Windows'ta gizli bir nokta-dizin kullanıcının baktığı yer değil.
    platform_name parametre olduğu için bu dal LINUX'ta da sınanabiliyor
    (main._qt_platform_hint ile aynı desen). """
    yol = config.config_path(platform_name="win32",
                             environ={"APPDATA": r"C:\Users\deneme\AppData\Roaming"})
    assert yol == os.path.join(r"C:\Users\deneme\AppData\Roaming",
                               "decode", "config.toml")


def test_config_path_windowsta_da_xdg_onceliklidir():
    yol = config.config_path(platform_name="win32",
                             environ={"XDG_CONFIG_HOME": "/xdg",
                                      "APPDATA": r"C:\AppData"})
    assert yol == os.path.join("/xdg", "decode", "config.toml")


def test_config_path_linux_dali_degismedi(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", "/home/deneme")
    yol = config.config_path(platform_name="linux")
    assert yol == os.path.join("/home/deneme", ".config", "decode", "config.toml")
```

- [ ] **Step 2: Testleri çalıştır, kırıldıklarını gör**

Run: `.venv/bin/python -m pytest tests/test_config.py -q`
Expected: FAIL — `config_path() got an unexpected keyword argument 'platform_name'`

- [ ] **Step 3: `config_path`'i yaz**

`core/config.py` — dosyanın başına `import sys` ekle (yoksa), sonra:

```python
def config_path(platform_name=None, environ=None):
    """ Ayar dosyası yolu.

    XDG_CONFIG_HOME her platformda önceliklidir. Verilmemişse Linux/macOS'ta
    ~/.config, Windows'ta %APPDATA% kullanılır -- Windows'ta gizli bir
    nokta-dizin kullanıcının baktığı yer değil.

    platform_name ve environ parametre olarak alınıyor ki Windows dalı
    LINUX'TA da test edilebilsin; aksi halde yalnız Windows runner'ında
    sınanabilirdi (main._qt_platform_hint ile aynı desen). """
    platform_name = sys.platform if platform_name is None else platform_name
    environ = os.environ if environ is None else environ

    base = environ.get("XDG_CONFIG_HOME")
    if not base:
        if platform_name == "win32":
            base = environ.get("APPDATA") or os.path.join(
                os.path.expanduser("~"), "AppData", "Roaming")
        else:
            base = os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, APP_NAME, FILE_NAME)
```

- [ ] **Step 4: Testleri çalıştır**

Run: `.venv/bin/python -m pytest tests/test_config.py -q`
Expected: PASS — mevcut iki `config_path` testi dahil (parametresiz çağrı davranışı değişmedi).

- [ ] **Step 5: `find_executable` testlerini yaz**

`tests/test_pio_cli.py` — mevcut üç testi platforma bağla ve iki yeni test ekle:

```python
from tests.platform_commands import exe_name


def test_find_executable_pathten_bulur(tmp_path, monkeypatch):
    sahte = tmp_path / exe_name("pio")
    sahte.write_text("#!/bin/sh\n", encoding="utf-8")
    sahte.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert pio_cli.find_executable() == str(sahte)


def test_find_executable_platformio_adini_da_dener(tmp_path, monkeypatch):
    sahte = tmp_path / exe_name("platformio")
    sahte.write_text("#!/bin/sh\n", encoding="utf-8")
    sahte.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert pio_cli.find_executable() == str(sahte)


def test_find_executable_penv_yedegi(tmp_path, monkeypatch):
    """ PlatformIO'nun kendi kurucusu pio'yu PATH'e koymayabiliyor.
    platform_name AÇIKÇA veriliyor: Windows'ta varsayılan dal Scripts/'e
    bakar ve bu test kendi kurduğu dosyayı bulamazdı. """
    penv = tmp_path / ".platformio" / "penv" / "bin"
    penv.mkdir(parents=True)
    sahte = penv / "pio"
    sahte.write_text("#!/bin/sh\n", encoding="utf-8")
    sahte.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path / "bos"))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert pio_cli.find_executable(platform_name="linux") == str(sahte)


def test_find_executable_windows_penv_yedegi(tmp_path, monkeypatch):
    """ Windows'ta penv betikleri 'Scripts' altında ve '.exe' uzantılı.
    Dosyaya çalıştırma izni VERİLMİYOR: os.access(X_OK) Windows'ta var olan
    hemen her dosya için True döndüğü ve hiçbir şey elemediği için kapı
    os.path.isfile olmalı -- bu test tam onu ölçüyor. """
    scripts = tmp_path / ".platformio" / "penv" / "Scripts"
    scripts.mkdir(parents=True)
    sahte = scripts / "pio.exe"
    sahte.write_text("", encoding="utf-8")
    monkeypatch.setenv("PATH", str(tmp_path / "bos"))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert pio_cli.find_executable(platform_name="win32") == str(sahte)


def test_find_executable_windowsta_yoksa_none(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path / "bos"))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert pio_cli.find_executable(platform_name="win32") is None
```

`test_find_executable_yoksa_none` testine de `monkeypatch.setenv("USERPROFILE", str(tmp_path))` ekle ve çağrıyı `pio_cli.find_executable(platform_name="linux")` yap.

- [ ] **Step 6: Testleri çalıştır, kırıldıklarını gör**

Run: `.venv/bin/python -m pytest tests/test_pio_cli.py -q`
Expected: FAIL — `find_executable() got an unexpected keyword argument 'platform_name'`

- [ ] **Step 7: `find_executable`'ı yaz**

`embedded/pio_cli.py` — başına `import sys` ekle, sonra:

```python
def find_executable(platform_name=None):
    """ 'pio' ya da 'platformio'yu PATH'te arar; bulamazsa PlatformIO'nun
    kendi kurucusunun kullandığı penv yolunu dener. Hiçbiri yoksa None --
    çağıran kullanıcıya kurulum ipucu verir.

    platform_name parametre olarak alınıyor ki Windows dalı LINUX'ta da test
    edilebilsin (core.config.config_path ve main._qt_platform_hint ile aynı
    desen). """
    platform_name = sys.platform if platform_name is None else platform_name

    # shutil.which PATHEXT'i zaten doğru işliyor: Windows'ta 'pio' araması
    # 'pio.exe'yi bulur.
    for name in ("pio", "platformio"):
        path = shutil.which(name)
        if path:
            return path

    home = os.path.expanduser("~")
    if platform_name == "win32":
        # Windows'ta penv betikleri 'bin' değil 'Scripts' altında.
        # os.access(X_OK) burada KULLANILMIYOR: orada var olan hemen her
        # dosya için True döner, yani hiçbir şey elemez.
        fallback = os.path.join(home, ".platformio", "penv", "Scripts", "pio.exe")
        return fallback if os.path.isfile(fallback) else None

    fallback = os.path.join(home, ".platformio", "penv", "bin", "pio")
    return fallback if os.access(fallback, os.X_OK) else None
```

- [ ] **Step 8: Bütün testleri çalıştır**

Run: `.venv/bin/python -m pytest -q`
Expected: `287 passed` (282 + 3 config + 2 pio_cli).

- [ ] **Step 9: Commit**

```bash
git add core/config.py embedded/pio_cli.py tests/test_config.py tests/test_pio_cli.py
git commit -m "fix: ayar ve pio yollarını Windows'a taşı

Ayar dosyası Windows'ta %APPDATA%\\decode\\config.toml; XDG_CONFIG_HOME
her platformda önceliğini koruyor. pio yedeği orada 'Scripts\\pio.exe'
ve kapı os.path.isfile -- os.access(X_OK) Windows'ta var olan her dosya
için True döndüğü için hiçbir şey elemiyordu.

İki dal da platform_name parametresi alıyor, böylece Linux CI'da
sınanabiliyorlar (main._qt_platform_hint deseni)."
```

---

### Task 5: PyInstaller spec'i

**Files:**
- Modify: `packaging/decode.spec`
- Create: `tests/test_packaging_spec.py`

**Interfaces:**
- Consumes: yok.
- Produces: `dist/DeCode-v<sürüm>-windows-x86_64.exe` adlı çıktı. Task 6'daki duman testi bu ada bakıyor.

- [ ] **Step 1: Mimari normalleştirme testini yaz**

`tests/test_packaging_spec.py`:

```python
""" packaging/decode.spec'in ad üretimi.

Spec dosyası PyInstaller tarafından enjekte edilen SPECPATH'e dayandığı için
doğrudan import edilemiyor; normalleştirme tablosu buradan sınanıyor. Tablo
spec'te de aynen duruyor ve bu test ikisinin ayrışmasını yakalıyor. """
import re

SPEC = "packaging/decode.spec"


def _tablo():
    """ Spec'teki _ARCH_ADLARI sözlüğünü metinden okur. """
    metin = open(SPEC, encoding="utf-8").read()
    govde = re.search(r"_ARCH_ADLARI\s*=\s*\{(.*?)\}", metin, re.S).group(1)
    return dict(re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', govde))


def test_windows_amd64_x86_64_olur():
    """ platform.machine() Windows'ta 'AMD64' döner. Normalleştirilmezse
    çıktı 'DeCode-v0.3.0-windows-AMD64' olur ve release.yml'deki ad
    kontrolü release'i kırar. """
    assert _tablo()["amd64"] == "x86_64"


def test_mevcut_platform_adlari_degismedi():
    """ Linux ve macOS çıktı adları bugünküyle aynı kalmalı; yoksa
    yayınlanmış sürümlerle tutarsız adlar üretiriz. """
    tablo = _tablo()
    assert tablo["x86_64"] == "x86_64"
    assert tablo["arm64"] == "arm64"
    assert tablo["aarch64"] == "arm64"
```

- [ ] **Step 2: Testi çalıştır, kırıldığını gör**

Run: `.venv/bin/python -m pytest tests/test_packaging_spec.py -q`
Expected: FAIL — `AttributeError: 'NoneType' object has no attribute 'group'` (`_ARCH_ADLARI` henüz yok)

- [ ] **Step 3: Spec'i güncelle**

`packaging/decode.spec` — `_ARCH` satırını değiştir ve iki Windows bloğu ekle.

Docstring'in sonuna ekle:

```
Windows'ta iki ek var: hide_console (konsol GERÇEKTEN var, stdout ve
'--version' çalışıyor, ama bootloader kendi açtığı pencereyi anında
gizliyor) ve pywinpty'nin DLL'lerinin elle toplanması.
```

`_OS` satırından sonra:

```python
# platform.machine() Windows'ta 'x86_64' değil 'AMD64' döner; normalleştirilmezse
# çıktı 'DeCode-v0.3.0-windows-AMD64' olur ve release.yml'deki ad kontrolü
# release'i kırar. Linux ('x86_64') ve macOS ('arm64') adları değişmiyor.
_ARCH_ADLARI = {
    "amd64": "x86_64",
    "x86_64": "x86_64",
    "arm64": "arm64",
    "aarch64": "arm64",
}
_MAKINE = platform.machine().lower()
_ARCH = _ARCH_ADLARI.get(_MAKINE, _MAKINE)
CIKTI_ADI = f"DeCode-v{__version__}-{_OS}-{_ARCH}"

# PyInstaller Windows'ta ada '.exe' ekliyor; gerçek dosya
# 'DeCode-v0.3.0-windows-x86_64.exe' oluyor.

_HIDDEN = []
_BINARIES = []
_EXE_EK = {}

if sys.platform == "win32":
    # PyInstaller pywinpty'nin uzantısını ve yanındaki DLL'leri kendiliğinden
    # bulmayabiliyor. Eksik DLL'in belirtisi sinsi: kaynaktan çalışırken her
    # şey normal, YALNIZ donmuş binary'de terminal açılmıyor.
    from PyInstaller.utils.hooks import collect_dynamic_libs

    _HIDDEN.append("winpty")
    _BINARIES += collect_dynamic_libs("winpty")

    # Konsol gerçekten var (stdout çalışır, '--version' duman testi hiç
    # değişmeden geçer) ama bootloader kendi açtığı pencereyi anında gizler:
    # çift tıklamayla açılışta siyah kutu görünmez, cmd'den çalıştırılırsa
    # mevcut konsol devralınır ve çıktı görünür.
    #
    # Yalnız Windows'ta ekleniyor: PyInstaller başka platformlarda
    # "Ignoring hide_console; supported only on Windows!" uyarısı basıp yok
    # sayar ve her build'in logunu kirletir.
    _EXE_EK["hide_console"] = "hide-early"
```

`Analysis(...)` çağrısında iki satırı değiştir:

```python
    binaries=_BINARIES,
    ...
    hiddenimports=_HIDDEN,
```

`EXE(...)` çağrısının sonuna, `entitlements_file=None,` satırından sonra ekle:

```python
    **_EXE_EK,
```

- [ ] **Step 4: Testi çalıştır**

Run: `.venv/bin/python -m pytest tests/test_packaging_spec.py -q`
Expected: PASS

- [ ] **Step 5: Linux build'inin bozulmadığını doğrula**

Run: `.venv/bin/python -m PyInstaller --clean --noconfirm packaging/decode.spec`
Expected: `dist/DeCode-v0.3.0-linux-x86_64` üretiliyor — **ad bugünküyle birebir aynı**.

Run: `QT_QPA_PLATFORM=offscreen ./dist/DeCode-v0.3.0-linux-x86_64 --version`
Expected: `DeCode IDE 0.3.0`

- [ ] **Step 6: Windows'ta build al ve terminali doğrula**

Windows'ta:
```
.venv-win\Scripts\python -m PyInstaller --clean --noconfirm packaging\decode.spec
dist\DeCode-v0.3.0-windows-x86_64.exe --version
```
Expected: dosya adı tam olarak `DeCode-v0.3.0-windows-x86_64.exe`; `--version` sürümü basıyor.

Sonra `.exe`'ye **çift tıkla** ve şunları doğrula:
- arkada siyah konsol penceresi **yok** (`hide_console`),
- `:term` açılıyor ve PowerShell prompt'u çiziliyor (**`collect_dynamic_libs` doğrulaması — CI bunu göremez**),
- `:term` içinde `where python` PyInstaller'ın `_MEI…` geçici dizinini göstermiyor.

- [ ] **Step 7: Commit**

```bash
git add packaging/decode.spec tests/test_packaging_spec.py
git commit -m "build: spec'i Windows'a hazırla

platform.machine() Windows'ta 'AMD64' döndüğü için mimari adı
normalleştiriliyor; Linux ve macOS çıktı adları değişmiyor.
hide_console='hide-early' ile çift tıklamada siyah konsol penceresi
görünmüyor ama stdout ve '--version' çalışmaya devam ediyor.
pywinpty'nin DLL'leri collect_dynamic_libs ile elle toplanıyor."
```

---

### Task 6: GitHub Actions

**Files:**
- Modify: `.github/workflows/tests.yml`
- Modify: `.github/workflows/release.yml`

**Interfaces:**
- Consumes: Task 5 → `DeCode-v<sürüm>-windows-x86_64.exe` çıktı adı.
- Produces: üç platformlu release.

- [ ] **Step 1: `tests.yml`'a Windows satırı ve bash varsayılanı ekle**

`matrix` satırını değiştir:

```yaml
        os: [ubuntu-latest, macos-latest, windows-latest]
```

`runs-on: ${{ matrix.os }}` satırının hemen altına ekle:

```yaml
    # windows-latest'te 'run:' varsayılanı PowerShell'dir; aşağıdaki adımlar
    # ise bash (set +e, PIPESTATUS, tee, awk). Git Bash Windows runner'larında
    # kurulu, bu yüzden üç platform da aynı betikleri koşabiliyor.
    defaults:
      run:
        shell: bash
```

`fail-fast: false`'ın üstündeki yorumu güncelle:

```yaml
      # Bir platformun kırılması ötekini iptal etmesin: üçünün de sonucunu
      # görmek istiyoruz.
```

- [ ] **Step 2: `release.yml`'a Windows satırı ve bash varsayılanı ekle**

`matrix.include` listesine ekle:

```yaml
          # windows-latest x86_64. Windows on ARM için ayrı bir runner
          # gerekirdi; bilinçli olarak kapsam dışı.
          - os: windows-latest
            ad: windows-x86_64
```

`runs-on: ${{ matrix.os }}` satırının altına `tests.yml`'daki `defaults` bloğunun aynısını ekle.

- [ ] **Step 3: Duman testinin ad kontrolünü `.exe`'ye toleranslı yap**

`release.yml` içindeki `case` bloğunu değiştir:

```bash
          # PyInstaller Windows'ta ada '.exe' ekliyor; ad kontrolü ikisini de
          # kabul etmeli.
          case "$BINARY" in
            *${{ matrix.ad }}|*${{ matrix.ad }}.exe) echo "ad doğru: $BINARY" ;;
            *) echo "::error title=Duman testi::beklenen ad '*${{ matrix.ad }}', bulunan '$BINARY'"; exit 1 ;;
          esac
```

Duman testi adımının başındaki yorum bloğuna ekle:

```bash
          # DİKKAT: '--version' QApplication'dan ÖNCE dönüyor, yani ConPTY'ye
          # hiç dokunmuyor -- eksik bir winpty DLL'i bu testten görünmez geçer.
          # O boşluk bilinçli kabul edildi; güvence tasarım dokümanındaki elle
          # doğrulama listesinin 4. maddesinden geliyor.
```

- [ ] **Step 4: Sürüm notlarına Windows bölümü ekle**

`release.yml`'daki `NOTLAR` heredoc'una, macOS bölümünden sonra ekle:

```markdown
          ### Windows (x86_64)

          `DeCode-*-windows-x86_64.exe` dosyasını indirip çalıştırın.

          Binary imzasız olduğu için Windows SmartScreen ilk açılışta
          "Windows protected your PC" uyarısı gösterir: **More info** →
          **Run anyway**. Kod imzalama bilinçli olarak yapılmıyor.

          Windows 10 sürüm 1809 ya da üstü gerekir (terminal paneli
          ConPTY kullanıyor).
```

Notların sonundaki macOS uyarısının **altına**, Windows için karşılık gelen bir cümle **ekleme** — Windows derlemesi elle deneniyor (bkz. tasarım dokümanı Karar 5).

- [ ] **Step 5: Workflow'ların sözdizimini doğrula**

Run:
```bash
.venv/bin/python -c "
import yaml
for y in ('.github/workflows/tests.yml', '.github/workflows/release.yml'):
    d = yaml.safe_load(open(y, encoding='utf-8'))
    isler = d['jobs']
    for ad, is_ in isler.items():
        print(y, ad, is_.get('defaults'), is_.get('strategy', {}).get('matrix'))
"
```
Expected: her iki dosyada da `{'run': {'shell': 'bash'}}` ve matriste Windows satırı görünüyor. (`yaml` yoksa: `.venv/bin/python -m pip install pyyaml`.)

- [ ] **Step 6: Testleri çalıştır ve commit**

Run: `.venv/bin/python -m pytest -q`
Expected: `289 passed` (287 + Task 5'in 2 spec testi). Workflow değişikliği testleri etkilemez; bu bir regresyon kontrolü.

```bash
git add .github/workflows/tests.yml .github/workflows/release.yml
git commit -m "ci: Windows'u test ve release matrisine ekle

windows-latest'te 'run:' varsayılanı PowerShell olduğu için iş
düzeyinde 'defaults: run: shell: bash' ekleniyor; mevcut bash
betikleri (PIPESTATUS, tee, awk) üç platformda da aynen koşuyor.

Duman testinin ad kontrolü '.exe' uzantısını kabul ediyor. Release
kapısı değişmedi: üç matris satırı da geçmeden sürüm oluşmuyor."
```

---

### Task 7: Belgeler ve sprint kaydı

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/Roadmap.md`
- Modify: `CLAUDE.md`
- Create: `docs/sprint/sprint-14.md`
- Modify: `docs/sprint/README.md`

**Interfaces:**
- Consumes: Task 1–6'nın hepsi.
- Produces: yok (son task).

- [ ] **Step 1: `README.md`**

macOS bloğundan sonraki şu iki paragrafı (`README.md:47-49`) **sil**:

> Intel Mac'ler ve Windows için hazır dosya yok. Windows'ta uygulama şu an hiç
> çalışmıyor: gömülü terminal `pty`/`fcntl`/`termios` kullanıyor ve bunların
> Windows karşılığı (ConPTY) henüz yazılmadı.

Yerine şunu koy:

```markdown
**Windows (x86_64):**

`DeCode-*-windows-x86_64.exe` dosyasını indirip çalıştırın — `chmod` ya da
karantina kaldırma gerekmez.

Binary imzasız olduğu için SmartScreen ilk açılışta "Windows protected your
PC" uyarısı gösterir: **More info** → **Run anyway**. Kod imzalama bilinçli
olarak yapılmıyor — ücretli, yıllık yenilenen bir sertifika gerektirir ve
uygulamanın çalışması için şart değildir.

Gereksinim: Windows 10 sürüm 1809 ya da üstü (terminal paneli ConPTY
kullanıyor).

Intel Mac'ler (x86_64) ve Windows on ARM için hazır dosya yok.
```

`README.md:144`'teki satırı platforma göre yaz:

```markdown
İlk açılışta yorumlu bir şablon oluşturulur: Linux ve macOS'ta
`~/.config/decode/config.toml`, Windows'ta `%APPDATA%\decode\config.toml`
(`XDG_CONFIG_HOME` her platformda önceliklidir).
```

"Sorun giderme" bölümündeki `/tmp` `noexec` notu yalnız Linux'u anlatıyor; başlığındaki "(Linux)" ibaresi zaten doğru, dokunma.

- [ ] **Step 2: `CHANGELOG.md`**

En üste yeni sürüm başlığı ekle (mevcut girişlerin biçimini izle):

```markdown
### Eklendi
- Windows desteği: `:term` ve bütün `:pio` alt komutları ConPTY üzerinde
  çalışıyor; tek dosya `.exe` GitHub Releases'te.

### Değişti
- `TerminalProcess` bir transport dikişine ayrıldı (`core/pty_posix.py`,
  `core/pty_windows.py`). POSIX davranışı değişmedi.
- Ayar dosyası Windows'ta `%APPDATA%\decode\config.toml`.

### Bilinen sınırlar
- Windows on ARM ve Intel Mac (x86_64) için hazır dosya yok.
- `.exe` imzasız: SmartScreen ilk açılışta uyarı gösteriyor.
```

`core/version.py`'deki sürümü **bu task'ta değiştirme** — sürüm yükseltme ve tag atma ayrı bir karar (bkz. Son adımlar).

- [ ] **Step 3: `docs/Roadmap.md`**

Faz 5'teki Windows maddesini değiştir:

```markdown
- **Windows** — **tamamlandı** ([Sprint 14](sprint/sprint-14.md)):
  `terminal_process.py` bir transport dikişine ayrıldı; ConPTY (`pywinpty`)
  portu `core/pty_windows.py`'de, okuma `QSocketNotifier` yerine bir
  `QThread`'de (Windows'ta notifier yalnız socket tanıtıcılarıyla çalışıyor).
  `windows-latest` hem test hem release matrisinde.
```

Teknik borç tablosunda test sayısını güncelle: `197 test` → gerçek sayı (Task 6 sonrası `pytest -q` çıktısındaki değer).

`Intel Mac (x86_64) — açık` maddesinin yanına `Windows on ARM (arm64) — açık` ekle.

- [ ] **Step 4: `CLAUDE.md`**

**DİKKAT: `CLAUDE.md` İNGİLİZCE** — depodaki tek istisna. Türkçe yazma.

`ui/components/terminal_panel.py` / `core/terminal_process.py` maddesinin başındaki "a real shell over `pty.fork` + `QSocketNotifier`" ifadesini değiştir ve maddenin sonuna ekle:

```markdown
  `TerminalProcess` itself is platform-agnostic: the spawn, the read loop, the
  window size and the kill sequence live behind a *transport* it owns, picked
  at import time (`core/pty_posix.py` on POSIX, `core/pty_windows.py` on
  Windows). Everything shared — the `pyte` screen, the exit-code semantics,
  `child_environment`, `resize` storing the size while stopped — stays in
  `terminal_process.py`, deliberately: splitting it in two is how the two
  platforms drift apart.
```

`core/state_machine.py` maddesinden sonra iki yeni madde ekle:

```markdown
- **`core/pty_posix.py` / `core/pty_windows.py`** — the two terminal
  transports, behind one contract (`spawn`, `write`, `set_size`, `is_alive`,
  `exit_code`, `close`, `default_shell_argv`). Two guarantees are part of that
  contract and break *silently* when violated: `on_data`/`on_eof` are **always
  invoked on the main thread** (free on POSIX, where `QSocketNotifier` already
  lives there; on Windows the reader thread's signal is delivered by a queued
  connection) — this is what lets `pyte` and `TerminalPanel` stay
  single-threaded; and `close()` **never blocks the main thread indefinitely**
  on either platform, which is the generalized form of the macOS shutdown
  deadlock (`a039d53`). Windows needs a reader `QThread` at all because
  `QSocketNotifier` there only accepts *socket* descriptors, and ConPTY hands
  you a pipe. Neither module is imported on the other's platform, so
  `pywinpty` never becomes a Linux/macOS dependency. If `pywinpty` is missing,
  `_UnavailableTransport` in `terminal_process.py` keeps the editor running
  and reports 127 — crashing at import is the bug the port exists to fix.
```

`core/config.py` maddesine ekle:

```markdown
  The config path is platform-aware: `%APPDATA%\decode\config.toml` on
  Windows, `~/.config/decode/config.toml` elsewhere, with `XDG_CONFIG_HOME`
  winning everywhere. `config_path(platform_name=None, environ=None)` takes
  both as parameters so the Windows branch is testable *on Linux* — the same
  pattern as `main._qt_platform_hint`.
```

`embedded/pio_cli.py` maddesine ekle:

```markdown
  `find_executable(platform_name=None)` falls back to
  `~\.platformio\penv\Scripts\pio.exe` on Windows and gates it with
  `os.path.isfile`, not `os.access(X_OK)` — the latter returns True for
  practically every existing file on Windows and would filter nothing.
```

- [ ] **Step 5: `docs/sprint/sprint-14.md`**

`<commit hash'leri>` yerine gerçek kısa hash'leri yaz (`git log --oneline`):

```markdown
# Sprint 14 — Windows portu ve dağıtımı
**Tarih:** 10 Eyl 2026 · **Durum:** Tamamlandı · **Commit(ler):** <commit hash'leri>

## Hedef
DeCode IDE'yi Windows'ta çalışır hâle getirip tek dosya `.exe` olarak
yayınlamak — `:term` ve bütün `:pio` alt komutları dahil.

## Çıktılar
- [x] Testlerdeki POSIX'e sabit kabuk komutları platforma bağlandı — `tests/platform_commands.py`
- [x] `TerminalProcess` transport dikişine ayrıldı — `core/terminal_process.py`, `core/pty_posix.py`
- [x] ConPTY transport'u — `core/pty_windows.py`
- [x] `pywinpty` yokken editör çalışmaya devam ediyor — `_UnavailableTransport`
- [x] Ayar dosyası Windows'ta `%APPDATA%` — `core/config.py`
- [x] `pio` yedek yolu ve `isfile` kapısı — `embedded/pio_cli.py`
- [x] Kabuk adı transport'tan geliyor — `ui/components/terminal_panel.py`
- [x] Windows çıktı adı, `hide_console`, DLL toplama — `packaging/decode.spec`
- [x] `windows-latest` test ve release matrisinde — `.github/workflows/`

## Teknik notlar

**Transport dikişi.** Ortak olan her şey (`pyte` ekranı, çıkış kodu
semantiği, `child_environment`, `resize`'ın ölçüyü saklaması)
`TerminalProcess`'te tek yerde kaldı; platforma özgü dört iş ayrı modüllere
indi. İki ayrı tam sınıf yazmak bilinçli olarak elendi: o incelikler iki
yerde yaşasaydı zamanla ayrışırdı.

Sözleşmenin iki güvencesi var ve ikisi de bozulduğunda hata **sessiz**:
`on_data`/`on_eof` her zaman ana iş parçacığında çağrılır (yoksa
`pyte.Screen` iki thread'den güncellenir), ve `close()` ana iş parçacığında
süresiz bloklanmaz (macOS kapanış kilidinin genelleştirilmiş hâli).

**Neden Windows'ta thread var.** `QSocketNotifier` orada yalnız *socket*
tanıtıcılarıyla çalışıyor, ConPTY ise boru veriyor. Okuma bu yüzden
bloklayan bir `QThread`'de yapılıp kuyruklu bağlantıyla ana thread'e
taşınıyor — desen `core/file_index.py`'deki `FileIndexWorker`'ın aynısı.

**`pyte.ByteStream` kendi decoder'ını taşıyor.** İçinde
`codecs.getincrementaldecoder("utf-8")("replace")` var, yani çok baytlı bir
karakter iki `feed()` arasında bölünse bile doğru birleşiyor. Transport'ta
ikinci bir tampon kurmadık; tasarımın ilk hâli bunu öneriyordu ve gereksizdi.

**`platform.machine()` Windows'ta `AMD64` döner.** Normalleştirilmeseydi
çıktı `DeCode-v0.3.0-windows-AMD64` olur ve `release.yml`'deki ad kontrolü
release'i kırardı.

**`windows-latest`'te `run:` varsayılanı PowerShell.** Her iki workflow'daki
mevcut adımlar bash (`PIPESTATUS`, `tee`, `awk`); iş düzeyinde
`defaults: run: shell: bash` ile üçü de aynı betikleri koşuyor.

**CI'ın göremediği boşluk — bilinçli kabul.** `--version` `QApplication`'dan
önce dönüyor, yani ConPTY'ye hiç dokunmuyor: eksik bir `winpty` DLL'i duman
testinden görünmez geçer. `tests.yml` ConPTY'yi sınıyor ama kaynaktan,
donmuş binary'den değil. Boşluğu kapatmak `--selftest` bayrağı gerektirirdi;
uygulama yüzeyini büyütmek yerine güvence elle doğrulamadan alındı.

## Devreden
- Kod imzalama ve notarization (Windows + macOS birlikte)
- Installer (Inno Setup / MSI) ve başlat menüsü girdisi
- Windows on ARM (`arm64`) — ayrı matris satırı
- Intel Mac (`macos-13`) — bu portla ilgisiz, hâlâ açık
```

- [ ] **Step 6: `docs/sprint/README.md`**

Tabloya satır ekle:

```markdown
| [14](sprint-14.md) | 10 Eyl 2026 | Windows portu ve dağıtımı | Tamamlandı |
```

"Aktif sprint" satırını güncelle: `**Aktif sprint:** yok — son iş [Sprint 14](sprint-14.md).`

- [ ] **Step 7: Testleri çalıştır ve commit**

Run: `.venv/bin/python -m pytest -q`
Expected: `289 passed` (`tests/test_no_hardcoded_colors.py` dahil — belge değişiklikleri onu etkilemez).

```bash
git add README.md CHANGELOG.md docs/Roadmap.md CLAUDE.md docs/sprint/sprint-14.md docs/sprint/README.md
git commit -m "docs: Windows portunu kayda geçir (Sprint 14)"
```

---

## Son adımlar (uygulama bittikten sonra)

Bunlar plan task'ı değil; insan kararı gerektiriyor.

1. **Elle doğrulama turu.** Tasarım dokümanındaki 13 maddelik liste (§Elle doğrulama) Windows makinesinde, **donmuş `.exe` üzerinde** koşulacak. Bu, release'in ön koşulu — özellikle 4 (`:term` açılıyor mu, DLL güvencesi), 5 (Türkçe karakter), 6 (`where python`), 12 (kapanışta donma yok).
2. **Sürüm numarası.** `core/version.py` yükseltilecek; tag `v<sürüm>` ile birebir aynı olmalı, yoksa duman testi release'i kırar.
3. **Tag ve release.** `git tag v<sürüm> && git push origin v<sürüm>` — üç platform da geçmeden Release oluşmaz.

---

## Notlar

- **Test sayıları** (273 → 281 → 282 → 287 → 289) yön göstericidir, sözleşme değil. Sayı tutmuyorsa hangi testin eklendiğine/kaybolduğuna bak; *düşmesi* her zaman incelenecek bir işarettir.
- **Task 3 Linux'ta doğrulanamaz.** Adım 4 yalnız "Windows kodu Linux'u bozmadı"yı ölçer; gerçek doğrulama Adım 5–6'da, Windows makinesinde.
- **Task 3 Adım 1 durdurucu olabilir:** ölçüm üçüncü dala (`str` + replacement char) düşerse alt seviye `winpty.PTY` API'sine inmek gerekir ve bu, Adım 3'ün kodunu değiştirir. O noktada dur ve planı güncelle.
