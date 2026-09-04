# Linux Tek Dosya Dağıtımı (Faz 5 / Sprint 11) — Tasarım

**Tarih:** 04 Eyl 2026 · **Durum:** Onay bekliyor · **Faz:** 5 — Dağıtım

## Hedef

DeCode IDE'nin ilk halka açık sürümünü (**v0.1.0**) yayınlamak: kullanıcı GitHub
Releases'ten tek bir dosya indirsin, `chmod +x` yapıp çalıştırsın; Python, pip,
sanal ortam ya da bağımlılık kurulumu gerekmesin.

Bu, Roadmap'teki "Faz 5 — Dağıtım" maddesinin **çalıştırılabilir + sürüm
etiketi** parçasıdır. Fazın diğer parçaları ayrı sprintlere bırakıldı:

| Parça | İş | Nerede |
|---|---|---|
| A | Depo hijyeni: `main` merge, `.gitignore`, LİSANS | **Bu sprint** |
| B | Sürüm tek kaynağı + `--version` | **Bu sprint** |
| C | PyInstaller tek dosya build | **Bu sprint** |
| D | Donmuş ortamın kabuğa sızmasını önleme | **Bu sprint** |
| E | GitHub Actions: test + release | **Bu sprint** |
| F | README / CHANGELOG / Roadmap | **Bu sprint** |
| G | AppImage, `.desktop`, uygulama ikonu | Sonraki sprint |
| H | `pyproject.toml` + `decode` konsol komutu | Sonraki sprint |

## Kapsam dışı

- **macOS ve Windows.** Ayrı alt projeler. macOS küçüktür (`pty`/`termios`
  orada da var; asıl engel `main.py`'deki koşulsuz `QT_QPA_PLATFORM =
  "wayland;xcb"` ataması). Windows bir paketleme işi değil, bir porttur:
  `core/terminal_process.py` `fcntl`, `pty`, `termios` ve `SIGHUP` kullanıyor,
  bunların hiçbiri Windows'ta yok — uygulama orada bozuk çalışmaz, **import
  anında** açılmaz. Karşılığı ConPTY (`pywinpty`) üzerine bir yeniden yazımdır.
- **AppImage, `.desktop` girdisi, uygulama ikonu.** Bu sprintte üretilen binary
  masaüstü menüsüne girmez; terminalden ya da dosya yöneticisinden çalıştırılır.
- **`pyproject.toml` ve `decode` konsol komutu.** Roadmap v1.0 kriteri; kaynaktan
  kurulum bu sprintte hâlâ `pip install -r requirements.txt` + `python3 main.py`.
- **Kod imzalama / notarization.** Linux'ta karşılığı yok.
- **Çoklu mimari.** Yalnız `x86_64`. ARM (`aarch64`) build'i yok.
- **Otomatik güncelleme.** Uygulama kendi sürümünü kontrol etmez.

## Kararlar

| # | Karar | Gerekçe |
|---|---|---|
| K1 | Lisans **GPL-3.0** | PyQt6 `GPL-3.0-only`. Binary'ye gömülüp dağıtıldığı an bütün eser GPLv3 şartlarına tabi olur; kaynağa MIT etiketi yapıştırmak bunu değiştirmez, yalnız yanıltır. Tek alternatif Riverbank'tan ticari PyQt lisansı satın almak. Sahibinin isteğini (ücretsiz, herkes değiştirip yayınlayabilsin) birebir karşılar |
| K2 | Sürüm **v0.1.0** — ilk halka açık sürüm | Depoda hiç tag yok; Roadmap'in v0.1/v0.2 satırları yayınlanmış sürümler değil, iç kilometre taşlarıydı. Roadmap tablosu buna göre düzeltilir (bkz. F) |
| K3 | Build **CI'da**, geliştirici makinesinde değil | Bu makine glibc 2.44 (CachyOS); burada derlenen binary Ubuntu/Debian/Mint'te çalışmaz. Ubuntu runner'da taban ~2.35'e iner. Aynı emek, kat kat geniş erişim — ve ileride `macos-latest` satırı eklenerek aynı matris macOS'a genişler |
| K4 | Tek dosya: PyInstaller `--onefile` | En az hareketli parça. AppImage zaten bunun üstüne bir katmandır, atlanarak yapılmıyor |
| K5 | `console=True` (`--windowed` **değil**) | Uygulama ayar dosyası uyarılarını, `pio` bulunamadı hatalarını `print` ediyor; `--windowed` stdout'u yutar ve bu tanılar kaybolur |
| K6 | Kullanılmayan Qt modülleri **exclude edilir**; liste ampirik daraltılır | Uygulama yalnız `QtCore`, `QtGui`, `QtWidgets` kullanıyor (`QtTest` sadece testlerde). PyQt6 260 MB ve içinde Quick 7.9M, Qml 6.5M, Designer 5.8M, ShaderTools 5.5M, Quick3DPhysics 5.0M, Pdf 4.4M var. Fazla agresif bir liste binary'yi açılmaz hâle getirebilir, o yüzden her turdan sonra duman testi |
| K7 | `--version` `QApplication`'dan **ve** `config.ensure_exists`'ten önce işlenir | CI duman testi bunu çalıştıracak; ev dizinine ayar dosyası yazmamalı ve Qt platform plugin'i aramamalı |
| K8 | Donmuş ortam temizliği **saf bir fonksiyonda** | Projenin "saf `core/` + ince Qt kabuğu" ilkesi. Donmadan test edilebilir olması şart: yoksa bu yol yalnız yayınlanmış binary'de sınanabilirdi |
| K9 | Release yükleme `gh` CLI ile, üçüncü parti action olmadan | `gh` runner'da kurulu gelir; tedarik zinciri yüzeyi ve sürüm bakımı küçülür |
| K10 | `.gitignore` **takibe alınır** | Şu an kendini ignore ediyor: `*.claude`, `CLAUDE.md`, `__pycache__` kuralları yalnız bu makinede var, GitHub'daki depoda yok. Sahibinin "`*.claude` repomda gözükmesin, `__pycache__` temiz olsun" isteğini kalıcı kılan adım tam olarak budur |
| K11 | Bu iş **Sprint 11** olur | Roadmap "Sprint 11 = hatadan koda atlama, Sprint 12 = seri monitör" diyordu; ikisi 12 ve 13'e kayar, Roadmap'teki referanslar güncellenir |

## Mimari

Yeni parçaların çoğu depo kökünde ve `.github/`'ta; uygulama koduna dokunan tek
yer D (donmuş ortam) ve B (sürüm) maddeleridir.

```
LICENSE                        GPL-3.0 tam metni
README.md                      ne olduğu, kurulum, komut/kısayol referansı
CHANGELOG.md                   v0.1.0 girdisi
.gitignore                     artık TAKİP EDİLİYOR

core/version.py         (saf)  __version__ = "0.1.0" — tek kaynak
main.py                        --version bayrağı (QApplication'dan önce)
core/terminal_process.py (saf+Qt)  child_environment() + execvpe

packaging/decode.spec          PyInstaller yapılandırması
.github/workflows/tests.yml    push/PR -> pytest
.github/workflows/release.yml  v* tag -> build -> duman testi -> Release
```

### A — Depo hijyeni

1. `faz-4-pio-cekirdegi` → `main` **fast-forward merge** (36 commit).
   Doğrulandı: `main` HEAD'in atası, `faz-2-arama-gezinme` ve
   `faz-3-ayar-dosyasi` dallarının ikisi de HEAD'e dahil. Çakışma riski yok.
2. `.gitignore`'dan yalnız kendi satırı (`.gitignore`) silinir; `*.claude`,
   `CLAUDE.md`, `.venv`, `__pycache__/`, `*.pyc`, `.pytest_cache/`,
   `.superpowers/` satırları **kalır**. Anlamsız `.git` satırı da temizlenir.
   Dosya commit edilir.
3. Yerel `__pycache__` klasörleri silinir (takipte zaten yoklar — Sprint 06).
4. `LICENSE` eklenir: GPL-3.0 tam metni, telif satırı
   `Copyright (C) 2026 Deniz Buğra Erol` (sahibi tarafından teyit edildi).

### B — `core/version.py` ve `--version`

```python
# core/version.py  (saf Python, Qt yok)
__version__ = "0.1.0"
```

Sürümü okuyan üç yer: `main.py --version`, `packaging/decode.spec` (çıktı adı),
README/CHANGELOG (elle, tag ile aynı olduğu release kontrol listesinde
doğrulanır).

`main.py` içinde, **`config.ensure_exists`'ten ve `QApplication`'dan önce**:

```python
if "--version" in sys.argv[1:]:
    print(f"DeCode IDE {__version__}")
    return
```

K7 gereği bu dal ev dizinine yazmaz ve Qt platform plugin'i yüklemez — CI'ın
binary'yi ekransız duman testinden geçirme yolu budur.

### C — `packaging/decode.spec`

`--onefile`, `console=True` (K5), giriş noktası `main.py`, çıktı adı
`DeCode-<sürüm>-x86_64`.

`excludes` başlangıç listesi (K6 gereği ampirik daraltılır): `PyQt6.QtQml`,
`QtQuick`, `QtQuick3D`, `QtQuickWidgets`, `QtQuickControls2`, `QtWebEngineCore`,
`QtWebEngineWidgets`, `QtPdf`, `QtPdfWidgets`, `QtDesigner`, `QtMultimedia`,
`QtMultimediaWidgets`, `QtCharts`, `QtDataVisualization`, `QtBluetooth`,
`QtNfc`, `QtPositioning`, `QtSql`, `QtTest`.

`QtNetwork`, `QtDBus`, `QtOpenGL`, `QtOpenGLWidgets` **dışlanmaz**: Qt Widgets
yığını bunları çalışma anında dolaylı arayabilir; kazancı riskine değmez.

`pyte` saf Python; gizli import beklenmiyor, build çıktısı yine de kontrol
edilir.

**Doğrulanacak, varsayılmayacak:** `wayland` ve `xcb` platform pluginlerinin
pakete girdiği. `main.py` ikisini de istiyor ve bu, aşağıdaki R4 riskidir.

### D — Donmuş ortamın kabuğa sızması

PyInstaller bootloader'ı `LD_LIBRARY_PATH`'i paketin açıldığı dizine çevirir ve
orijinal değeri `LD_LIBRARY_PATH_ORIG`'a saklar. `pty.fork()` ile doğan kabuk bu
ortamı **miras alır**; içeriden çalıştırılan `pio`, `git`, `ls` gibi sistem
binary'leri paketlenmiş kütüphanelerle çakışıp `GLIBCXX ... not found` benzeri
hatalarla patlayabilir. Bu, uygulamanın varlık sebebine dokunur: `:pio build` de
aynı yoldan geçer.

`core/terminal_process.py`'ye modül düzeyinde saf bir fonksiyon:

```python
# PyInstaller'ın donmuş süreçte ezdiği, çocuk sürece SIZMAMASI gereken
# değişkenler. Bootloader orijinali "<AD>_ORIG" altında saklar.
_FROZEN_VARS = ("LD_LIBRARY_PATH", "LD_PRELOAD")


def child_environment(env=None, frozen=None):
    """ PTY çocuğuna verilecek ortam: PyInstaller'ın izleri geri alınır.
    <AD>_ORIG varsa <AD> ona döner, yoksa donmuş süreçte <AD> tamamen
    silinir. Donmamış süreçte ortam değişmeden geçer.

    env/frozen parametre olarak alınıyor ki bu yol donmadan test
    edilebilsin (K8) — aksi halde yalnız yayınlanmış binary'de sınanırdı. """
```

`pty.fork()`'un child dalında `os.execvp(...)` yerine
`os.execvpe(shell, argv, child_environment())` çağrılır. Shell sekmesi de komut
sekmesi (`:pio ...`) de aynı dalı kullandığı için tek değişiklik ikisini birden
kapsar.

### E — GitHub Actions

**`.github/workflows/tests.yml`** — `push` ve `pull_request`'te
`ubuntu-latest`, `pytest`. Testler `QT_QPA_PLATFORM=offscreen` ile ekransız
çalışıyor (`tests/conftest.py`), ama Qt'nin sistem kütüphaneleri runner'da
kurulu değil: `libegl1`, `libxkbcommon-x11-0` ve arkadaşları `apt-get` ile
kurulmalı (R1).

**`.github/workflows/release.yml`** — tetik `push: tags: ["v*"]`.

| Adım | İş |
|---|---|
| 1 | `actions/checkout` |
| 2 | Qt sistem kütüphaneleri (`apt-get`) |
| 3 | `actions/setup-python` — sürüm, PyQt6 + PyInstaller wheel'i olan bir sürüme sabitlenir; uygulama 3.14'e bağlı değil |
| 4 | `pip install -r requirements.txt pyinstaller` |
| 5 | `pyinstaller packaging/decode.spec` |
| 6 | **Duman testi:** `QT_QPA_PLATFORM=offscreen dist/DeCode-* --version`. Çıktı `DeCode IDE 0.1.0`, tag ise `v0.1.0` — karşılaştırma tag'in baştaki `v`'si atılarak yapılır, yoksa adım hep kırılır |
| 7 | `gh release create` (K9), binary + CHANGELOG özeti |

Runner `ubuntu-22.04`'e sabitlenir: glibc tabanını düşürüp Ubuntu 22.04+,
Debian 12+, Mint, Fedora'yı kapsamak için. Image'ın hâlâ sunulduğu uygulama
sırasında doğrulanır (R2).

### F — Belgeler

- **`README.md`** (yok): DeCode nedir, ekran görüntüsü, indir-çalıştır
  talimatı, kaynaktan çalıştırma, komut ve kısayol referansı (Roadmap'teki
  listeden özet), gereksinimler (glibc tabanı, x86_64), lisans.
- **`CHANGELOG.md`**: `v0.1.0 — ilk halka açık sürüm`; Faz 1–4'ün özeti.
- **`docs/Roadmap.md`**: sürüm kilometre taşları tablosu v0.1.0 ile uyumlanır
  (K2), Faz 5 kısmen tamamlandı olarak işaretlenir, teknik borç tablosuna CI
  satırı eklenir, Sprint 11/12 referansları 12/13'e kaydırılır (K11).
- **`docs/sprint/sprint-11.md`** + `docs/sprint/README.md` tablosuna satır.

## Hata yolları

| Durum | Davranış |
|---|---|
| Duman testi başarısız (binary açılmıyor) | Release job'ı **kırılır**, tag durur, Release **oluşturulmaz**. Bozuk binary yayınlanmaz |
| Testler kırmızı | `tests.yml` kırılır; release ayrı bir workflow olduğu için tag atmadan önce yeşil olduğu elle kontrol edilir (kontrol listesinde madde) |
| `--version` çıktısı tag ile uyuşmuyor | Duman testi adımında karşılaştırılır, job kırılır — `core/version.py` güncellenmeden atılan tag'i yakalar |
| Kullanıcının `/tmp`'si `noexec` | Onefile açılamaz; README'de `TMPDIR=~/.cache` ipucu (R6) |

## Test planı

Yeni birim testleri (`tests/test_frozen_env.py`):

| Test | Sav |
|---|---|
| `test_donmus_ortamda_ld_library_path_geri_alinir` | `LD_LIBRARY_PATH_ORIG` varsa `LD_LIBRARY_PATH` ona döner, `_ORIG` anahtarı kalmaz |
| `test_donmus_ortamda_orig_yoksa_degisken_silinir` | Bootloader değeri çocuğa sızmaz |
| `test_donmamis_ortam_degismeden_gecer` | Geliştirme ortamında davranış birebir bugünküyle aynı |
| `test_ilgisiz_degiskenler_korunur` | `PATH`, `HOME`, `SHELL` dokunulmadan geçer |

`tests/test_version.py`:

| Test | Sav |
|---|---|
| `test_surum_semver_bicimli` | `__version__` `MAJOR.MINOR.PATCH` |
| `test_version_bayragi_ayar_dosyasi_yazmaz` | `--version` yolu `config.ensure_exists` çağırmaz (K7) |

CI: `tests.yml` her push'ta tüm süiti koşar. `release.yml` binary'yi duman
testinden geçirir.

**Bilinçli boşluk:** duman testi `offscreen` platformda koştuğu için
`wayland`/`xcb` pluginlerinin eksikliğini **yakalayamaz**. Bu yüzden aşağıdaki
elle doğrulama release'in zorunlu adımıdır, "iyi olurdu" değil.

## Elle doğrulama (release öncesi kontrol listesi)

1. Binary'yi Release'ten indir, `chmod +x`, çalıştır → pencere açılıyor (R4'ü
   kapatan adım; Wayland ve X11 oturumunda ayrı ayrı).
2. Bir dosya aç, düzenle, `:w` ile kaydet.
3. `:term` → kabuk açılıyor, `ls` ve `git status` çalışıyor (D'yi sınar).
4. Kabukta `pio --version` → PlatformIO bulunuyor.
5. Gerçek bir PlatformIO projesinde `:pio build` → derleme yürüyor, sekme
   başlığında `✓` (D'nin asıl sınavı).
6. `~/.config/decode/config.toml` oluşuyor; bir rengi değiştirip `:reload`.
7. İkinci bir makinede (mümkünse Ubuntu) tekrarla → glibc tabanını sınar.

## Riskler

| # | Risk | Karşılık |
|---|---|---|
| R1 | Qt sistem kütüphaneleri CI runner'da yok → testler/build sessizce kırılır | Her iki workflow'da `apt-get install` adımı; ilk koşuda doğrulanır |
| R2 | `ubuntu-22.04` image'ı emekliye ayrılmış olabilir | En eski mevcut image'a düşülür; glibc tabanı yükselir, README'de yazılı taban güncellenir |
| R3 | Exclude listesi fazla agresif → binary açılmıyor | Duman testi yakalar; liste tur tur daraltılır (K6) |
| R4 | `wayland`/`xcb` plugin'i pakete girmemiş → GUI hiç açılmıyor | Duman testi **yakalayamaz** (offscreen); elle doğrulama madde 1 zorunlu |
| R5 | Donmuş ortam kabuğa sızıyor → `:pio build` binary'de patlıyor | D maddesi + 4 birim testi + elle doğrulama madde 3-5 |
| R6 | Kullanıcının `/tmp`'si `noexec` | README'de `TMPDIR` ipucu; nadir |
| R7 | Binary boyutu beklenenden büyük | K6 exclude turları; ölçüm build'de yapılır, önceden söz verilmez |

## Bu sprintten sonra

- **G/H:** AppImage + `.desktop` + ikon, `pyproject.toml` + `decode` komutu →
  Roadmap Faz 5'in kalanı ve v1.0 kriteri.
- **macOS alt projesi:** `main.py`'deki platform koşulu + `macos-latest` matris
  satırı + Gatekeeper notu. Bu sprintte kurulan CI iskeleti taşıyıcısıdır.
- **Windows alt projesi:** `TerminalProcess`'in ConPTY portu. Paketleme değil,
  port; kendi fazı.
