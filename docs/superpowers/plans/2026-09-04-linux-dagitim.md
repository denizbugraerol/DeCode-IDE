# Linux Tek Dosya Dağıtımı (Faz 5 / Sprint 11) — Uygulama Planı

> **Ajan işçiler için:** ZORUNLU ALT BECERİ: Bu planı görev görev uygulamak için
> `superpowers:subagent-driven-development` (önerilen) ya da
> `superpowers:executing-plans` kullanın. Adımlar takip için checkbox (`- [ ]`)
> sözdizimiyle yazılmıştır.

**Hedef:** DeCode IDE'nin ilk halka açık sürümünü (v0.1.0) GitHub Releases'te tek
bir çalıştırılabilir dosya olarak yayınlamak; kullanıcı indirip `chmod +x` yapıp
çalıştırsın, Python/pip/bağımlılık kurmasın.

**Mimari:** Uygulama koduna dokunan iki küçük değişiklik var — `core/version.py`
(sürümün tek kaynağı) ve `core/terminal_process.py`'ye eklenen saf
`child_environment()` (PyInstaller'ın ortam izlerini PTY çocuğuna sızdırmaz).
Geri kalan her şey depo çevresidir: `packaging/decode.spec` PyInstaller
yapılandırması, iki GitHub Actions workflow'u (test + release), LİSANS ve
belgeler. Build **CI'da** yapılır, geliştirici makinesinde değil: bu makine
glibc 2.44 (CachyOS) ve burada derlenen binary Ubuntu/Debian'da çalışmaz.

**Teknoloji:** Python (PyInstaller 6.22+ ile donduruluyor), PyQt6, pyte,
GitHub Actions, `gh` CLI. **Yeni çalışma zamanı bağımlılığı yok** —
`requirements.txt` değişmez, PyInstaller yalnız build aracıdır.

**Spec:** [`docs/superpowers/specs/2026-09-04-linux-dagitim-design.md`](../specs/2026-09-04-linux-dagitim-design.md)

## Global Kısıtlar

Aşağıdakiler her görevin gereksinimlerine örtük olarak dahildir:

- **Sürüm:** `0.1.0`; git tag `v0.1.0`. Binary `--version` çıktısı tam olarak
  `DeCode IDE 0.1.0` (tag'in baştaki `v`'si yok).
- **Lisans:** GPL-3.0. Telif satırı: `Copyright (C) 2026 Deniz Buğra Erol`.
- **Dil:** Yorumlar, docstring'ler, commit mesajları ve `docs/` Türkçe (bkz.
  `CLAUDE.md`). Test adları da Türkçe (`test_donmus_ortamda_...`).
- **Mimari:** yalnız `x86_64`. ARM build'i yok.
- **Release runner:** `ubuntu-22.04` (glibc tabanını düşürmek için). Image
  artık sunulmuyorsa en eski mevcut olana düşülür ve README'deki taban
  güncellenir.
- **`console=True`** — `--windowed` kullanılmaz; uygulama tanılarını `print`
  ediyor.
- **Yeni çalışma zamanı bağımlılığı yok:** `requirements.txt` bu planda hiç
  değişmez.
- **Testler:** `.venv/bin/python -m pytest -q` (venv'in console script'lerinin
  shebang'i bayat — `-m` ile çağır). Görev sonunda süitin tamamı yeşil olmalı;
  başlangıç: 188 test.

---

### Task 1: Dal, depo hijyeni ve LİSANS

Depo GitHub'da lisanssız ve `.gitignore`'sız duruyor. Bu görev release'in
hukuki ve hijyen zeminini kurar; kod değiştirmez.

**Files:**
- Create: `LICENSE`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: yok (ilk görev)
- Produces: `faz-5-dagitim` dalı — sonraki bütün görevler bu dalda çalışır.

- [ ] **Step 1: Çalışma dalını aç**

```bash
git checkout -b faz-5-dagitim
```

- [ ] **Step 2: `.gitignore`'ı kendi kendini gizlemekten çıkar**

Şu anki dosya `.gitignore` ve `.git` satırlarını içeriyor. `.gitignore`
kendini ignore ettiği için depoda **hiç yok**; yani `*.claude`, `CLAUDE.md` ve
`__pycache__` kuralları yalnız bu makinede geçerli. `.git` satırı ise
anlamsız (git kendi dizinini zaten izlemez). Dosyanın tamamını şununla
değiştir:

```gitignore
*.claude
CLAUDE.md
.venv
__pycache__/
*.pyc
.pytest_cache/
.superpowers/
```

- [ ] **Step 3: Kuralların gerçekten çalıştığını doğrula**

Run:
```bash
git check-ignore -v .claude CLAUDE.md .superpowers
git status --short
```
Expected: üç yol da bir kuralla eşleşiyor; `git status` yalnız `.gitignore` ve
`LICENSE`'ı (bir sonraki adımdan sonra) gösteriyor, `__pycache__` ya da
`.claude` görünmüyor.

- [ ] **Step 4: Yerel `__pycache__` klasörlerini temizle**

Takipte zaten yoklar (Sprint 06'da çıkarılmış); bu yalnız çalışma dizinini
temizler.

```bash
find . -path ./.venv -prune -o -name __pycache__ -type d -print -exec rm -rf {} +
```

- [ ] **Step 5: GPL-3.0 metnini indir**

```bash
curl -fsSL https://www.gnu.org/licenses/gpl-3.0.txt -o LICENSE
```

- [ ] **Step 6: LİSANS'ın tam indiğini doğrula**

Run: `head -3 LICENSE; wc -l LICENSE`
Expected: ilk satır `                    GNU GENERAL PUBLIC LICENSE`, dosya
600'den fazla satır. Kısa/boş dosya inmişse `curl` başarısız olmuştur, tekrarla.

- [ ] **Step 7: Commit**

```bash
git add .gitignore LICENSE
git commit -m "chore: .gitignore takibe alındı ve GPL-3.0 lisansı eklendi

.gitignore kendini ignore ettiği için '*.claude', 'CLAUDE.md' ve
'__pycache__' kuralları yalnız geliştirici makinesinde vardı; depoyu
klonlayan kimse onları almıyordu.

PyQt6 GPL-3.0-only olduğu için binary dağıtan bu proje de GPL-3.0."
```

---

### Task 2: Sürümün tek kaynağı ve `--version` bayrağı

CI, ürettiği binary'yi `--version` ile duman testinden geçirecek. Bu yüzden
bayrak `QApplication`'dan **ve** `config.ensure_exists`'ten önce işlenmeli:
ekransız koşmalı ve ev dizinine ayar dosyası yazmamalı.

**Files:**
- Create: `core/version.py`
- Create: `tests/test_version.py`
- Modify: `main.py`

**Interfaces:**
- Consumes: Task 1'in `faz-5-dagitim` dalı
- Produces: `core.version.__version__` (str, `"0.1.0"`) — Task 4 (`decode.spec`
  çıktı adı), Task 6 (duman testi) ve Task 7 (belgeler) bunu kullanır.
  `main.main(argv=None) -> int` — çıkış kodunu **döndürür**, artık kendi içinde
  `sys.exit` çağırmaz.

- [ ] **Step 1: Başarısız testleri yaz**

Create `tests/test_version.py`:

```python
""" Sürüm tek kaynağı ve '--version' bayrağı.

CI, ürettiği binary'yi 'QT_QPA_PLATFORM=offscreen ./DeCode --version' ile
duman testinden geçirir. Bu yüzden bayrağın iki sözleşmesi var: sürümü tam
olarak beklenen biçimde basmak ve GUI/ev dizini yan etkisi üretmemek. """
import re

import main
from core import config
from core.version import __version__


def test_surum_semver_bicimli():
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)


def test_version_bayragi_surumu_basip_sifir_doner(capsys):
    kod = main.main(["--version"])
    assert kod == 0
    assert capsys.readouterr().out.strip() == f"DeCode IDE {__version__}"


def test_version_bayragi_ayar_dosyasi_yazmaz(monkeypatch, capsys):
    """ ensure_exists ev dizinine yazan TEK yer; --version onu çağırmamalı,
    yoksa CI runner'ında (ve sürümü soran her kullanıcıda) dosya yaratır. """
    cagrildi = []
    monkeypatch.setattr(config, "ensure_exists", lambda *a, **k: cagrildi.append(a))

    main.main(["--version"])

    assert cagrildi == []
    capsys.readouterr()
```

- [ ] **Step 2: Testleri çalıştır, kırmızı olduklarını gör**

Run: `.venv/bin/python -m pytest tests/test_version.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.version'`

- [ ] **Step 3: Sürüm modülünü yaz**

Create `core/version.py`:

```python
""" Sürümün tek kaynağı. Saf Python, Qt yok — 'main.py --version' bunu
QApplication kurulmadan basabilsin diye (CI duman testi bu yoldan geçiyor).

Buradaki değer git tag'iyle aynı olmalı: tag 'v0.1.0' ise burası '0.1.0'.
release.yml ikisini karşılaştırır ve uyuşmazsa release'i kırar. """

__version__ = "0.1.0"
```

- [ ] **Step 4: `main.py`'yi bayrağı önce işleyecek biçimde düzenle**

`main.py`'nin tamamını şununla değiştir:

```python
import sys
import os
from PyQt6.QtWidgets import QApplication

from core import config
from core.version import __version__
from ui.main_window import IDEWindow


def main(argv=None):
    """ Çıkış kodunu DÖNDÜRÜR (sys.exit çağırmaz) ki '--version' yolu testten
    çağrılabilsin. """
    argv = sys.argv[1:] if argv is None else argv

    # DİKKAT: bu dal QApplication'dan ve ensure_exists'ten ÖNCE olmalı.
    # CI, binary'yi ekransız runner'da '--version' ile duman testinden
    # geçiriyor: Qt platform plugin'i aranmamalı ve ev dizinine ayar dosyası
    # yazılmamalı.
    if "--version" in argv:
        print(f"DeCode IDE {__version__}")
        return 0

    # Wayland üzerinde sorunsuz çalışması için Qt'ye ipucu veriyoruz
    os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

    # Ayar dosyası yoksa yorumlu şablonu yaz; ardından oku. Ev dizinine yazan
    # tek yer burası (IDEWindow oluşturmak dosya yaratmaz).
    path = config.config_path()
    if config.ensure_exists(path):
        print(f"Ayar dosyası oluşturuldu: {path}")

    settings, warnings = config.load(path)
    for warning in warnings:
        print(warning)

    app = QApplication(sys.argv)

    window = IDEWindow(settings=settings)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Testleri çalıştır, yeşil olduklarını gör**

Run: `.venv/bin/python -m pytest tests/test_version.py -q`
Expected: PASS (3 test)

- [ ] **Step 6: Uygulamanın hâlâ açıldığını doğrula**

Run: `.venv/bin/python main.py --version`
Expected: `DeCode IDE 0.1.0`, çıkış kodu 0, `~/.config/decode/config.toml`
**oluşturulmadı** (zaten varsa dokunulmadı).

- [ ] **Step 7: Tüm süiti çalıştır**

Run: `.venv/bin/python -m pytest -q`
Expected: 191 passed

- [ ] **Step 8: Commit**

```bash
git add core/version.py tests/test_version.py main.py
git commit -m "feat: sürümün tek kaynağı ve '--version' bayrağı

CI duman testi binary'yi '--version' ile çalıştıracak; bayrak bu yüzden
QApplication ve ensure_exists'ten önce işleniyor: ekransız koşmalı ve ev
dizinine ayar dosyası yazmamalı. main() artık çıkış kodunu döndürüyor."
```

---

### Task 3: Donmuş ortamın PTY çocuğuna sızmasını önleme

Release'in uygulama davranışına dokunan tek yeri burası ve en kritik parçası:
PyInstaller bootloader'ı `LD_LIBRARY_PATH`'i paketin açıldığı dizine çevirir,
orijinali `LD_LIBRARY_PATH_ORIG`'a saklar. `pty.fork()` ile doğan kabuk bunu
miras alır; içeriden çalıştırılan `pio`, `git`, `ls` paketlenmiş
kütüphanelerle çakışıp `GLIBCXX ... not found` benzeri hatalarla patlayabilir.
`:pio build` de aynı yoldan geçtiği için bu, uygulamanın varlık sebebine
dokunuyor.

`start()` zaten `env` sözlüğü kurup `os.execvpe`'ye veriyor — değişiklik tek
satır; asıl iş saf fonksiyon ve testleri.

**Files:**
- Create: `tests/test_frozen_env.py`
- Modify: `core/terminal_process.py` (import satırları ve `start()` içindeki
  `env = dict(os.environ)`)

**Interfaces:**
- Consumes: Task 2'nin dalı
- Produces: `core.terminal_process.child_environment(env=None, frozen=None) -> dict`

- [ ] **Step 1: Başarısız testleri yaz**

Create `tests/test_frozen_env.py`:

```python
""" PyInstaller ile dondurulmuş binary'de PTY çocuğuna verilen ortam.

Bootloader LD_LIBRARY_PATH'i paketin açıldığı dizine çevirir ve orijinali
'<AD>_ORIG' altında saklar. Bu ortam kabuğa miras kalırsa içeriden
çalıştırılan sistem binary'leri (pio, git, ls) paketlenmiş kütüphanelerle
çakışır. child_environment saf tutuluyor ki bu yol DONMADAN test edilebilsin
— aksi halde yalnız yayınlanmış binary'de sınanabilirdi. """
from core.terminal_process import child_environment


def test_donmus_ortamda_ld_library_path_geri_alinir():
    ortam = {
        "PATH": "/usr/bin",
        "LD_LIBRARY_PATH": "/tmp/_MEI123456",
        "LD_LIBRARY_PATH_ORIG": "/usr/local/lib",
    }

    sonuc = child_environment(ortam, frozen=True)

    assert sonuc["LD_LIBRARY_PATH"] == "/usr/local/lib"
    assert "LD_LIBRARY_PATH_ORIG" not in sonuc


def test_donmus_ortamda_orig_yoksa_degisken_silinir():
    """ Kullanıcının LD_LIBRARY_PATH'i hiç yoktuysa bootloader _ORIG yazmaz;
    o zaman değişken tamamen kaldırılmalı, bootloader değeri sızmamalı. """
    ortam = {"PATH": "/usr/bin", "LD_LIBRARY_PATH": "/tmp/_MEI123456"}

    sonuc = child_environment(ortam, frozen=True)

    assert "LD_LIBRARY_PATH" not in sonuc


def test_donmamis_ortam_degismeden_gecer():
    """ Geliştirme ortamında (python3 main.py) davranış bugünküyle birebir
    aynı kalmalı. """
    ortam = {"PATH": "/usr/bin", "LD_LIBRARY_PATH": "/opt/kendi/lib"}

    sonuc = child_environment(ortam, frozen=False)

    assert sonuc == ortam


def test_ld_preload_da_geri_alinir():
    ortam = {"LD_PRELOAD": "/tmp/_MEI123456/libz.so", "LD_PRELOAD_ORIG": "/lib/libx.so"}

    sonuc = child_environment(ortam, frozen=True)

    assert sonuc["LD_PRELOAD"] == "/lib/libx.so"
    assert "LD_PRELOAD_ORIG" not in sonuc


def test_ilgisiz_degiskenler_korunur():
    ortam = {"PATH": "/usr/bin", "HOME": "/home/deniz", "SHELL": "/usr/bin/fish"}

    sonuc = child_environment(ortam, frozen=True)

    assert sonuc == ortam


def test_kaynak_sozluk_degistirilmez():
    """ Kopya döndürülmeli; çağıranın os.environ'ı bozulmamalı. """
    ortam = {"LD_LIBRARY_PATH": "/tmp/_MEI1", "LD_LIBRARY_PATH_ORIG": "/usr/lib"}

    child_environment(ortam, frozen=True)

    assert ortam["LD_LIBRARY_PATH"] == "/tmp/_MEI1"
```

- [ ] **Step 2: Testleri çalıştır, kırmızı olduklarını gör**

Run: `.venv/bin/python -m pytest tests/test_frozen_env.py -q`
Expected: FAIL — `ImportError: cannot import name 'child_environment'`

- [ ] **Step 3: Saf fonksiyonu ekle**

`core/terminal_process.py`'de `import fcntl` satırının altına `import sys`
ekle (dosyada henüz yok), sonra `_PtyBackedScreen` sınıfının **üstüne** şunu
koy:

```python
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
```

- [ ] **Step 4: Testleri çalıştır, yeşil olduklarını gör**

Run: `.venv/bin/python -m pytest tests/test_frozen_env.py -q`
Expected: PASS (6 test)

- [ ] **Step 5: `start()`'ı fonksiyonu kullanacak şekilde bağla**

`core/terminal_process.py` içinde `start()` metodunda tek satır:

```python
        env = dict(os.environ)
```

şununla değiştirilir:

```python
        env = child_environment()
```

Altındaki `env["TERM"] = ...` / `env["COLORTERM"] = ...` satırları ve
`os.execvpe(argv[0], argv, env)` çağrısı olduğu gibi kalır — shell sekmesi de
komut sekmesi (`:pio ...`) de aynı daldan geçtiği için bu tek satır ikisini
birden kapsar.

- [ ] **Step 6: Terminalin hâlâ çalıştığını doğrula**

Run: `.venv/bin/python -m pytest tests/test_terminal_process.py tests/test_terminal_command.py -q`
Expected: PASS — gerçek PTY testleri, bu değişikliğin kabuğu bozmadığını
kanıtlar.

- [ ] **Step 7: Tüm süiti çalıştır**

Run: `.venv/bin/python -m pytest -q`
Expected: 197 passed

- [ ] **Step 8: Commit**

```bash
git add core/terminal_process.py tests/test_frozen_env.py
git commit -m "fix: PyInstaller ortam izleri PTY çocuğuna sızmasın

Dondurulmuş binary'de bootloader LD_LIBRARY_PATH'i paketin açıldığı dizine
çevirir; pty.fork() ile doğan kabuk bunu miras alırsa içeriden çalıştırılan
pio/git/ls paketlenmiş kütüphanelerle çakışır. child_environment saf
tutuldu ki donmadan test edilebilsin."
```

---

### Task 4: PyInstaller yapılandırması ve yerel build doğrulaması

Burada üretilen binary **dağıtılmaz** (bu makine glibc 2.44; başka
dağıtımlarda açılmaz) — amaç `.spec` dosyasının doğruluğunu ve exclude
listesinin binary'yi bozmadığını kanıtlamak. Dağıtılacak binary Task 6'da
CI'da üretilir.

**Files:**
- Create: `packaging/decode.spec`
- Modify: `requirements-dev.txt`

**Interfaces:**
- Consumes: `core.version.__version__` (Task 2), `child_environment` (Task 3)
- Produces: `dist/DeCode-v0.1.0-x86_64` — Task 6'nın CI'da ürettiği ve duman
  testinden geçirdiği dosyanın aynısı.

- [ ] **Step 1: PyInstaller'ı dev bağımlılıklarına ekle**

`requirements-dev.txt`'in sonuna ekle (çalışma zamanı bağımlılığı **değil**,
`requirements.txt` değişmez):

```
pyinstaller>=6.22
```

- [ ] **Step 2: PyInstaller'ı kur**

Run: `.venv/bin/python -m pip install -r requirements-dev.txt`
Expected: `pyinstaller-6.22.2` (ya da daha yenisi) kuruldu.

- [ ] **Step 3: `.spec` dosyasını yaz**

Create `packaging/decode.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-
""" PyInstaller yapılandırması: tek dosya Linux çalıştırılabiliri.

console=True bilinçli: uygulama ayar dosyası uyarılarını ve "pio bulunamadı"
gibi tanıları print ediyor; --windowed bunları yutardı.

excludes listesi boyutun ana kaldıracı. Uygulama yalnız QtCore/QtGui/QtWidgets
kullanıyor (QtTest sadece testlerde), oysa PyQt6 260 MB ve içinde Quick, Qml,
Designer, ShaderTools, Quick3D, Pdf var. QtNetwork/QtDBus/QtOpenGL DIŞLANMIYOR:
Qt Widgets yığını bunları çalışma anında dolaylı arayabilir, kazancı riskine
değmez. """
import os
import sys

ROOT = os.path.dirname(SPECPATH)          # noqa: F821 - PyInstaller enjekte eder
sys.path.insert(0, ROOT)

from core.version import __version__      # noqa: E402


a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt6.QtQml", "PyQt6.QtQuick", "PyQt6.QtQuick3D",
        "PyQt6.QtQuickWidgets", "PyQt6.QtQuickControls2",
        "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtPdf", "PyQt6.QtPdfWidgets", "PyQt6.QtDesigner",
        "PyQt6.QtMultimedia", "PyQt6.QtMultimediaWidgets",
        "PyQt6.QtCharts", "PyQt6.QtDataVisualization",
        "PyQt6.QtBluetooth", "PyQt6.QtNfc", "PyQt6.QtPositioning",
        "PyQt6.QtSql", "PyQt6.QtTest",
        "tkinter", "unittest", "pydoc",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)                          # noqa: F821

exe = EXE(                                 # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f"DeCode-v{__version__}-x86_64",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

- [ ] **Step 4: Build et**

Run: `.venv/bin/python -m PyInstaller --clean --noconfirm packaging/decode.spec`
Expected: `dist/DeCode-v0.1.0-x86_64` oluştu, hata yok.

Build kırılırsa exclude listesi fazla agresiftir: hata mesajında adı geçen
modülü listeden çıkar ve tekrarla (spec K6, risk R3).

- [ ] **Step 5: Duman testini yerelde koştur**

Run:
```bash
chmod +x dist/DeCode-v0.1.0-x86_64
QT_QPA_PLATFORM=offscreen ./dist/DeCode-v0.1.0-x86_64 --version
ls -lh dist/DeCode-v0.1.0-x86_64
```
Expected: `DeCode IDE 0.1.0`; boyut kabaca 50–80 MB. Belirgin şekilde
büyükse exclude listesi tutmamıştır — `build/decode/Analysis-00.toc` içinde
hangi Qt kütüphanelerinin girdiğine bak.

- [ ] **Step 6: GUI'yi gerçekten aç (offscreen duman testinin YAKALAYAMADIĞI şey)**

Run: `./dist/DeCode-v0.1.0-x86_64`
Expected: pencere açılıyor. Açılmıyorsa `wayland`/`xcb` platform plugin'i
pakete girmemiştir (risk R4) — çıktıdaki `qt.qpa.plugin` hatasını oku,
`.spec`'e ilgili plugin'i `datas`/`binaries` ile ekle ve 4. adımdan tekrarla.

- [ ] **Step 7: Task 3'ün sahada sınavı — binary'nin içinden kabuk ve `pio`**

Açılan uygulamada sırayla:
1. `:term` → kabuk açılıyor
2. Kabukta `ls` ve `git status` → normal çalışıyor
3. Kabukta `pio --version` → PlatformIO bulunuyor

Expected: üçü de `GLIBCXX`/`symbol lookup error` vermeden çalışıyor. Bu,
`child_environment`'ın gerçekten işe yaradığının kanıtıdır; hata alırsan
Task 3'e dön, `_FROZEN_VARS` listesini genişlet.

- [ ] **Step 8: Build çıktılarını ignore et**

`.gitignore`'a ekle:

```gitignore
build/
dist/
```

- [ ] **Step 9: Commit**

```bash
git add packaging/decode.spec requirements-dev.txt .gitignore
git commit -m "build: PyInstaller tek dosya yapılandırması

Kullanılmayan Qt modülleri (Quick, Qml, Designer, Pdf, ...) dışlanıyor;
uygulama yalnız QtCore/QtGui/QtWidgets kullanıyor. console=True bilinçli:
uygulama tanılarını print ediyor."
```

---

### Task 5: CI — test workflow'u

Release workflow'undan önce testlerin CI'da yeşil koştuğunu görmek gerek;
release ancak yeşil bir ağaçtan etiketlenir.

**Files:**
- Create: `.github/workflows/tests.yml`

**Interfaces:**
- Consumes: Task 3'ün genişlettiği test süiti
- Produces: her push/PR'da koşan `pytest` job'ı; Task 6 aynı `apt-get` adımını
  tekrar kullanır.

- [ ] **Step 1: Workflow'u yaz**

Create `.github/workflows/tests.yml`:

```yaml
name: Testler

on: [push, pull_request]

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      # PyQt6 wheel'i Qt kütüphanelerini getirir ama onların bağlı olduğu
      # SİSTEM kütüphaneleri runner'da kurulu değil. Bunlar olmadan testler
      # 'could not load the Qt platform plugin' ile kırılır -- offscreen
      # platformda bile.
      - name: Qt sistem kütüphaneleri
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            libegl1 libgl1 libdbus-1-3 libxkbcommon-x11-0 \
            libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 \
            libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0

      - name: Bağımlılıklar
        run: pip install -r requirements-dev.txt

      - name: Testler
        run: python -m pytest -q
        env:
          QT_QPA_PLATFORM: offscreen
```

- [ ] **Step 2: Commit ve gönder**

```bash
git add .github/workflows/tests.yml
git commit -m "ci: her push ve PR'da pytest

PyQt6 wheel'i Qt'yi getiriyor ama bağlı olduğu sistem kütüphaneleri
runner'da yok; apt adımı olmadan offscreen testler bile kırılıyor."
git push -u origin faz-5-dagitim
```

- [ ] **Step 3: CI'ın yeşil olduğunu doğrula**

Run: `gh run watch` (ya da `gh run list --workflow=tests.yml --limit 1`)
Expected: `pytest` job'ı başarılı, 197 test geçti.

Kırılırsa: `apt-get` listesinde eksik bir kütüphane vardır — job log'undaki
`qt.qpa.plugin` satırı hangi `.so`'nun bulunamadığını söyler; listeye ekle ve
tekrar gönder. **Bu adım yeşil olmadan Task 6'ya geçme.**

---

### Task 6: CI — release workflow'u

**Files:**
- Create: `.github/workflows/release.yml`

**Interfaces:**
- Consumes: `packaging/decode.spec` (Task 4), `--version` bayrağı (Task 2),
  Task 5'te doğrulanmış `apt-get` listesi
- Produces: `v*` tag'i itildiğinde binary'yi üretip GitHub Release'e yükleyen
  otomasyon.

- [ ] **Step 1: Workflow'u yaz**

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: write        # gh release create için

jobs:
  linux:
    # Bilinçli olarak 'latest' DEĞİL: binary, üzerinde derlendiği glibc'yi
    # taban alır. Eski image = düşük taban = daha çok dağıtımda çalışır.
    # Bu image emekliye ayrılmışsa en eski mevcut olana düş ve README'deki
    # glibc tabanını güncelle.
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Qt sistem kütüphaneleri
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            libegl1 libgl1 libdbus-1-3 libxkbcommon-x11-0 \
            libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 \
            libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0

      - name: Bağımlılıklar
        run: pip install -r requirements.txt pyinstaller

      - name: Build
        run: python -m PyInstaller --clean --noconfirm packaging/decode.spec

      # Bozuk bir binary yayınlanmasın: bu adım kırılırsa Release HİÇ
      # oluşturulmaz. Tag 'v0.1.0', binary çıktısı 'DeCode IDE 0.1.0' --
      # karşılaştırma baştaki 'v' atılarak yapılıyor.
      - name: Duman testi
        run: |
          BINARY=$(ls dist/DeCode-*)
          chmod +x "$BINARY"
          CIKTI=$(QT_QPA_PLATFORM=offscreen "$BINARY" --version)
          BEKLENEN="DeCode IDE ${GITHUB_REF_NAME#v}"
          echo "çıktı   : $CIKTI"
          echo "beklenen: $BEKLENEN"
          test "$CIKTI" = "$BEKLENEN"
          ls -lh "$BINARY"

      - name: Release oluştur
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh release create "$GITHUB_REF_NAME" dist/DeCode-* \
            --title "DeCode IDE $GITHUB_REF_NAME" \
            --notes "$(cat <<'NOTLAR'
          ## Kurulum

          ```bash
          chmod +x DeCode-*-x86_64
          ./DeCode-*-x86_64
          ```

          Python, pip ya da bağımlılık kurulumu gerekmez.

          ## Gereksinimler

          - Linux x86_64, glibc 2.35+ (Ubuntu 22.04+, Debian 12+, Fedora, Arch)
          - Wayland ya da X11 oturumu

          Değişiklikler için `CHANGELOG.md`'ye bakın.
          NOTLAR
          )"
```

- [ ] **Step 2: YAML'ın geçerli olduğunu doğrula**

Run: `.venv/bin/python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/release.yml')); print('YAML geçerli')"`
Expected: `YAML geçerli`. (`yaml` kurulu değilse: `python -m pip install pyyaml`
— yalnız bu kontrol için, `requirements-dev.txt`'e **eklenmez**.)

- [ ] **Step 3: Commit ve gönder**

```bash
git add .github/workflows/release.yml
git commit -m "ci: v* tag'inde tek dosya binary üretip Release'e yükle

Runner bilinçli olarak ubuntu-22.04: binary üzerinde derlendiği glibc'yi
taban alıyor, eski image daha çok dağıtımı kapsıyor. Duman testi
kırılırsa Release hiç oluşturulmuyor."
git push
```

---

### Task 7: Belgeler

**Files:**
- Create: `README.md`
- Create: `CHANGELOG.md`
- Create: `docs/sprint/sprint-11.md`
- Modify: `docs/Roadmap.md`
- Modify: `docs/sprint/README.md`

**Interfaces:**
- Consumes: `__version__` (Task 2), Release kurulum akışı (Task 6)
- Produces: yayına hazır depo yüzeyi.

- [ ] **Step 1: `README.md` yaz**

Create `README.md`. Şu bölümleri içermeli (içeriği `docs/Roadmap.md`'nin
"Bugünkü durum" bölümünden özetle, uydurma):

- Bir cümlelik tanım: PyQt6 ile yazılmış, Vim'in modal giriş modelini izleyen,
  gömülü (PlatformIO) geliştirme için bir editör.
- **Kurulum (binary):** Releases'ten indir, `chmod +x`, çalıştır. Gereksinim:
  Linux x86_64, glibc 2.35+, Wayland ya da X11.
- **Sorun giderme (spec riski R6):** Tek dosya çalıştırılabilir kendini açmak
  için `/tmp`'yi kullanır. Sertleştirilmiş bazı sistemlerde `/tmp` `noexec`
  bağlıdır ve uygulama açılmaz; çözüm başka bir dizin göstermek:
  `TMPDIR=~/.cache ./DeCode-v0.1.0-x86_64`
- **Kaynaktan çalıştırma:** `pip install -r requirements.txt` + `python3 main.py`.
- **Komutlar:** Roadmap'teki `:` komut listesi (`:w`, `:q`, `:ts`, `:find`,
  `:replace`, `:openfile`, `:sym`, `:cd`, `:term`, `:termnew`, `:reload`,
  `:pio build|upload|monitor|clean|env`, ...).
- **Kısayollar:** Alt+Shift `T`/`N`/`W`/`←`/`→`; navigasyonun ok tuşlarında
  olduğu ve bunun bilinçli bir tasarım kararı olduğu notu.
- **Ayarlar:** `~/.config/decode/config.toml`, `:reload`.
- **Geliştirme:** `pytest` ile testler.
- **Lisans:** GPL-3.0, `Copyright (C) 2026 Deniz Buğra Erol`. PyQt6'nın
  GPL-3.0-only olduğu ve lisans seçiminin bundan geldiği bir cümleyle.

- [ ] **Step 2: `CHANGELOG.md` yaz**

Create `CHANGELOG.md`:

```markdown
# Değişiklik Günlüğü

## v0.1.0 — 04 Eyl 2026

İlk halka açık sürüm. Tek dosya Linux çalıştırılabiliri olarak yayınlanıyor.

### Özellikler
- Modal editör (NORMAL / INSERT / COMMAND), çoklu sekme, satır numarası gutter'ı
- Gerçek `:` komut satırı: Tab tamamlama, kaydırılabilir öneri listesi
- Bulanık dosya arama (`:ts`), dosya içi arama/değiştirme (`:find`, `:replace`),
  sembol atlama (`:sym`), yol tamamlamalı `:openfile`
- Gömülü terminal: gerçek PTY, sekmeli, ANSI renkleri Tokyo Night'a eşlenmiş
- PlatformIO: `:pio build|upload|monitor|clean|env`, sekme başlığında `✓`/`✗`
- Ayar dosyası (`~/.config/decode/config.toml`): 17 renk tokeni, font, sekme
  genişliği, terminal satır sayısı; `:reload` ile kapatmadan uygulama
- C/C++ ve Python sözdizimi renklendirme

### Bilinen sınırlar
- Yalnız Linux x86_64 (glibc 2.35+). macOS ve Windows henüz yok.
- Vim düzenleme komutları (`dd`, `yy`, `x`, `o`/`O`) ve VISUAL mod yok
- Derleme hatasından koda atlama ve kendi seri monitörümüz yok
```

- [ ] **Step 3: `docs/Roadmap.md`'yi güncelle**

Dört düzenleme:
1. "Bugünkü durum — v0.2" başlığını **v0.1.0** yap ve altına bir cümle: iç faz
   numaralandırması ile yayınlanan sürüm numaraları ayrı; v0.1.0 ilk halka açık
   sürümdür.
2. "Sürüm kilometre taşları" tablosunu buna göre düzelt (v0.1/v0.2 satırları
   yayınlanmış sürüm değil, geçmiş iç kilometre taşlarıydı).
3. "Faz 5 — Dağıtım" maddesinde çalıştırılabilir + sürüm etiketi kısmını
   **tamamlandı** işaretle; `pyproject.toml`, `.desktop` ve ikon açık kalsın.
4. Teknik borç tablosuna satır: "CI yok" → **Çözüldü** (`.github/workflows/`).
   Ayrıca Sprint 11/12 referanslarını 12/13'e kaydır (bu iş Sprint 11'i aldı).

- [ ] **Step 4: `docs/sprint/sprint-11.md` yaz**

`docs/sprint/README.md`'deki şablonu kullan: Hedef, Çıktılar (bu planın
görevleri), Teknik notlar (glibc/CI kararı, `child_environment` tuzağı,
offscreen duman testinin `wayland`/`xcb` eksikliğini yakalayamaması), Devreden.

- [ ] **Step 5: `docs/sprint/README.md`'yi güncelle**

Tabloya `| [11](sprint-11.md) | 04 Eyl 2026 | Linux tek dosya dağıtımı | Tamamlandı |`
satırını ekle ve "Aktif sprint" satırını güncelle.

- [ ] **Step 6: Bağlantıların kırık olmadığını doğrula**

Run:
```bash
grep -o "](\([^)]*\.md\)" README.md docs/Roadmap.md docs/sprint/README.md \
  | sed 's/.*](//' | sort -u
```
Expected: listelenen her yol gerçekten var (elle göz gezdir).

- [ ] **Step 7: Commit**

```bash
git add README.md CHANGELOG.md docs/
git commit -m "docs: README, CHANGELOG ve Sprint 11 kaydı

Roadmap'in sürüm tablosu v0.1.0 ile uyumlandı: iç faz numaralandırması
ile yayınlanan sürümler ayrı şeyler."
git push
```

---

### Task 8: `main`'e merge, etiket ve release

Buradan sonrası geri alması zor: tag ve GitHub Release halka açıktır.
**Her adım sahibinin onayıyla yürütülür.**

**Files:** yok (yalnız git işlemleri)

**Interfaces:**
- Consumes: Task 1–7'nin tamamı
- Produces: `main` dalında `v0.1.0` tag'i ve GitHub Release.

- [ ] **Step 1: Ağacın yeşil olduğunu doğrula**

Run: `.venv/bin/python -m pytest -q && gh run list --workflow=tests.yml --limit 1`
Expected: yerelde 197 test geçti, CI'daki son koşu `success`.

- [ ] **Step 2: `main`'e fast-forward merge**

```bash
git checkout main
git merge --ff-only faz-5-dagitim
```
Expected: fast-forward. Reddedilirse **zorlama** — dur ve durumu sahibine
bildir (`main`'e beklenmedik bir commit girmiş demektir).

- [ ] **Step 3: `main`'i gönder**

```bash
git push origin main
```

- [ ] **Step 4: Sürüm ile tag'in uyuştuğunu son kez doğrula**

Run: `grep __version__ core/version.py`
Expected: `__version__ = "0.1.0"` — atılacak tag `v0.1.0` ile uyumlu. CI bunu
zaten kontrol ediyor, ama tag atmadan görmek bir turu kurtarır.

- [ ] **Step 5: Etiketle ve gönder**

```bash
git tag -a v0.1.0 -m "DeCode IDE v0.1.0 — ilk halka açık sürüm"
git push origin v0.1.0
```

- [ ] **Step 6: Release workflow'unu izle**

Run: `gh run watch`
Expected: build → duman testi → Release oluşturuldu. Duman testi kırılırsa
Release **oluşmaz**; tag'i sil (`git push --delete origin v0.1.0`), düzelt,
yeniden etiketle.

- [ ] **Step 7: Yayınlanan binary'yi indirip elle doğrula**

```bash
gh release download v0.1.0
chmod +x DeCode-v0.1.0-x86_64
./DeCode-v0.1.0-x86_64
```

Sırayla kontrol et (spec'in "Elle doğrulama" listesi):
1. Pencere açılıyor — **offscreen duman testinin yakalayamadığı şey budur**
2. Bir dosya aç, düzenle, `:w` ile kaydet
3. `:term` → kabuk açılıyor; `ls`, `git status` çalışıyor
4. Kabukta `pio --version` → PlatformIO bulunuyor
5. Gerçek bir PlatformIO projesinde `:pio build` → derleme yürüyor, sekmede `✓`
6. `~/.config/decode/config.toml` oluştu; bir rengi değiştirip `:reload`
7. Mümkünse ikinci bir makinede (Ubuntu) 1. maddeyi tekrarla → glibc tabanını
   sınar

- [ ] **Step 8: Çalışma dalını temizle**

```bash
git branch -d faz-5-dagitim
git push origin --delete faz-5-dagitim
```
