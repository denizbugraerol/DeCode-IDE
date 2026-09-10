# Windows Portu ve Dağıtımı (Faz 5 / Sprint 14) — Tasarım

**Tarih:** 10 Eyl 2026 · **Durum:** Onay bekliyor · **Faz:** 5 — Dağıtım

## Hedef

DeCode IDE'nin Windows sürümünü yayınlamak: kullanıcı GitHub Releases'ten tek
bir `.exe` indirsin, çalıştırsın; Python, pip ya da bağımlılık kurulumu
gerekmesin — ve uygulamanın **varlık sebebi olan gömülü akış** (`:term`,
`:pio build|upload|monitor|clean|env|init`) orada da tam çalışsın.

Bu bir paketleme işi değil, bir **porttur**. Release altyapısı (PyInstaller
spec'i, matris, duman testi, `gh release create`) zaten hazır ve Windows'a bir
matris satırı eklemek 10 satırlık iş. Asıl engel tek dosya:
`core/terminal_process.py` modül düzeyinde `fcntl`, `pty` ve `termios` import
ediyor — bu üçü Windows'ta yok, dolayısıyla `ui/main_window.py` →
`terminal_panel` → `terminal_process` zinciri **import anında** çöküyor.
Uygulama Windows'ta bugün hiç açılmıyor.

| Parça | İş | Nerede |
|---|---|---|
| A | Transport dikişi: `TerminalProcess` ortak, platform ayrı | **Bu sprint** |
| B | `core/pty_posix.py` — bugünkü davranışın birebir taşınması | **Bu sprint** |
| C | `core/pty_windows.py` — ConPTY (`pywinpty`) + reader thread | **Bu sprint** |
| D | Taşınabilirlik düzeltmeleri (ayar yolu, `pio` yolu, kabuk adı) | **Bu sprint** |
| E | `packaging/decode.spec` — Windows adı, `hide_console`, DLL toplama | **Bu sprint** |
| F | GitHub Actions: `windows-latest` satırları | **Bu sprint** |
| G | README / CHANGELOG / Roadmap / sprint günlüğü | **Bu sprint** |
| H | Kod imzalama, notarization, installer (Inno Setup / MSI) | Kapsam dışı |
| I | Windows on ARM (`arm64`) | Kapsam dışı |

## Kapsam dışı

- **Kod imzalama.** İmzasız `.exe`, SmartScreen'in "Windows protected your PC"
  ekranını doğurur. Kullanıcı "More info" → "Run anyway" ile geçer; sürüm
  notlarında yazacak. macOS'ta da (`xattr -d com.apple.quarantine`) aynı
  bilinçli tercih yapıldı — sertifika ücretli ve yıllık yenilemeli.
- **Installer.** Çıktı, öteki iki platformdaki gibi **tek dosya** kalıyor.
  Installer ayrı bir alt proje; tutarlılık ve bakım yükü bugün ağır basıyor.
- **Windows on ARM.** `platform.machine()` orada `ARM64` döner ve ayrı bir
  runner gerekir. Intel Mac'te (`macos-13`) verilen kararla aynı gerekçe.
- **Kendi seri monitörümüz** (`embedded/serial_reader.py`). Bugün olduğu gibi
  `:pio monitor` PlatformIO'nun kendi monitörünü çalıştırıyor; ConPTY üstünde
  o da çalışacak.

## Kararlar

1. **Tam port, yarım değil.** ConPTY ile `:term` ve bütün `:pio` alt komutları
   Windows'ta çalışacak. Boru tabanlı (`QProcess`) bir ara çözüm elendi: iki
   ayrı çalıştırıcı modeli bakımda kalırdı ve ConPTY yine de sonradan
   gerekirdi.
2. **Yapı: transport nesnesi** (§Mimari A). `TerminalProcess` tek public sınıf
   kalır; yalnız platforma özgü dört iş ayrı modüle iner. İki ayrı tam sınıf
   yazmak elendi — çıkış kodu semantiği, `_finished` koruması, `resize`'ın
   ölçüyü saklaması ve `child_environment` iki yerde yaşayıp zamanla ayrışırdı.
3. **Konsol: `console=True` + `hide_console='hide-early'`.** Konsol gerçekten
   var (`sys.stdout` çalışır, `--version` duman testi hiç değişmeden geçer) ama
   bootloader kendi açtığı pencereyi anında gizler. Çift tıklamayla açılışta
   siyah kutu yok; `cmd`'den çalıştırılırsa mevcut konsol devralınır ve çıktı
   görünür. `console=False` elendi: ayar dosyası uyarıları ve "pio bulunamadı"
   tanıları sessizce kaybolurdu.
4. **Ayar dosyası: `%APPDATA%\decode\config.toml`.** Windows'un kendi kuralı;
   kullanıcının baktığı yer. `XDG_CONFIG_HOME` yine önceliğini korur.
5. **Elle doğrulama var.** macOS'un aksine (projenin Mac'i yok) Windows
   makinesine düzenli erişim var. Sürüm notlarına "elle denenmedi" uyarısı
   **girmeyecek**; karşılığında §Elle doğrulama listesi release'in ön koşulu.

## Mimari

### A — Transport sözleşmesi ve dosya yerleşimi

| Dosya | İçerik |
|---|---|
| `core/terminal_process.py` | `TerminalProcess` (public, tek), `child_environment`, `_PtyBackedScreen`, üç sinyal, çıkış kodu semantiği, `resize`'ın ölçüyü saklaması — **platformdan bağımsız her şey** |
| `core/pty_posix.py` | `PosixTransport` — `pty.fork`, `fcntl`, `termios`, `SIGHUP`/`SIGKILL` |
| `core/pty_windows.py` | `WindowsTransport` — ConPTY (`pywinpty`), reader thread |

Seçim import anında, tek yerde:

```python
# core/terminal_process.py
if sys.platform == "win32":
    from core.pty_windows import WindowsTransport as _Transport
else:
    from core.pty_posix import PosixTransport as _Transport
```

`pty_posix.py` Windows'ta **hiç import edilmez** — bugünkü çökmenin kökü tam
olarak bu. Simetrik olarak `pty_windows.py` POSIX'te hiç import edilmez, yani
`pywinpty` Linux/macOS'a bağımlılık olarak sızmaz.

Sözleşme (ikisi de aynısını sunar):

```python
spawn(argv, cwd, env, rows, cols, on_data, on_eof)
write(data: bytes)          set_size(rows, cols)
is_alive() -> bool          exit_code() -> int | None
close(timeout: float)       default_shell_argv() -> list[str]
```

Akış tek yönlü: transport `on_data` ile byte yayar, süreç bitince `on_eof`
çağırır; `TerminalProcess` bunun üzerine `exit_code()` sorup bugünkü gibi
`finished` ve `exited(int)` sinyallerini yayar. Yani çocuğu toplama işi
(POSIX'te `waitpid`, Windows'ta `exitstatus`) transport'un içinde kalır,
`TerminalProcess` yalnız sonucu okur.

Sözleşmenin taşıdığı iki güvence — ikisi de yorumla dosyaya yazılacak:

**1. `on_data` / `on_eof` HER ZAMAN ana iş parçacığında çağrılır.** POSIX'te bu
bedava (`QSocketNotifier` zaten orada); Windows'ta reader thread'in kendi
sinyalini **kuyruklu bağlantıyla** ana thread'e taşımasıyla sağlanır. Bu
sayede `TerminalProcess`, `pyte` ve `TerminalPanel` bugünkü gibi **tek iş
parçacıklı** kalır; thread yalnız `pty_windows.py`'nin içinde vardır ve dışarı
sızmaz. Bu güvence düşerse `pyte.Screen` iki thread'den güncellenir ve bozulma
sessiz olur.

**2. `close()` hiçbir platformda ana iş parçacığında SÜRESİZ bloklanmaz.**
macOS kapanış kilidinden (`a039d53`) çıkan dersin genelleştirilmiş hâli.
Windows'ta risk daha büyük: orada bloklayan okuma yapan bir thread'i de
toplamak gerekiyor.

`TerminalPanel` ve `TerminalView` bu bölümde **hiç değişmez** — kullandıkları
yüzey (`start`/`close`/`write`/`resize`/`is_running`/`screen`/`argv`/`cwd` +
`output_ready`/`finished`/`exited`) aynen duruyor. Tek istisna `shell_name()`,
§D'de.

### B — `core/pty_posix.py`

Bugünkü `TerminalProcess.start`/`_apply_winsize`/`_drain_master`/`close`
gövdelerinin taşınması. **Davranış değişmiyor** — özellikle şunlar korunuyor,
her biri bir hata sonucu yazılmıştı:

- `_handle_child_exit` içindeki **bloklayan** `waitpid` (WNOHANG değil): PTY'de
  EOF ile çocuğun reap edilebilir hâle gelmesi arasında yarış var.
- `close()` içindeki **yalnız WNOHANG** ile bekleme ve süre dolunca çocuğu
  bırakma: macOS'ta kapanışı donduran şey buydu.
- `_pid`'in reap sonrası `None`'a çekilmesi, ki `is_running()` dürüst kalsın.
- `os.O_NONBLOCK` ve `TIOCSWINSZ`.

### C — `core/pty_windows.py`

**Okuma döngüsü.** `QSocketNotifier` Windows'ta yalnız *socket* tanıtıcılarıyla
çalışır, boru/handle ile değil; ConPTY ise boru verir. Bu yüzden bloklayan
okuma yapan bir `QThread` gerekiyor: `read()` → `data_received(bytes)` →
kuyruklu bağlantıyla ana thread. Desen depoda zaten var:
`core/file_index.py:43`, `FileIndexWorker`.

**İlk iş: `pywinpty`'nin okuma tipini ölçmek.** `pywinpty` 2.x'in `read()`'i
`str` mi `bytes` mi döndürdüğü **doğrulama maddesi**, varsayım değil.
Sözleşme bytes olduğu için transport normalize edecek.

Burada kritik bir olgu var ve tasarımı basitleştiriyor: **`pyte.ByteStream`
zaten kendi içinde artık tutan bir UTF-8 decoder'ı taşıyor**
(`codecs.getincrementaldecoder("utf-8")("replace")`, bkz. `pyte/streams.py`),
yani çok baytlı bir karakter iki `feed()` çağrısı arasında bölünse bile doğru
birleşiyor. Dolayısıyla transport'un kendi tamponunu tutmasına **gerek yok**.
Ölçümün üç olası sonucu:

| Ölçüm | Karşılık |
|---|---|
| `bytes` döndürüyor | Doğrudan geçir. `pyte.ByteStream` sınırları zaten hallediyor — **ek iş yok**, risk ortadan kalkıyor. |
| `str`, içeride tamponluyor | `.encode("utf-8")` kayıpsız; ByteStream yeniden çözer. Ek iş yok. |
| `str`, tamponlamıyor | Bozulma **pywinpty'nin içinde** olmuş demektir; dışarıdan tampon tutmak onu düzeltemez. Tek çıkar yol, bytes veren alt seviye `winpty.PTY` API'sine inmek. |

Yani gerçek risk yalnız üçüncü satır ve karşılığı "kendi tamponumuzu yazmak"
değil, "alt seviye API'ye inmek". Ölçüm bunu ilk adımda kesinleştirecek.

**argv → komut satırı.** `pty.fork` + `execvpe` yerine ConPTY tek bir komut
satırı *dizesi* alır. `subprocess.list2cmdline(argv)` kullanılacak — boşluklu
yolları (`C:\Program Files\...`) MS C çalışma zamanı kurallarına göre doğru
tırnaklayan tek doğru yol; elle `" ".join` sessizce bozar.

**"Komut bulunamadı" = 127.** POSIX'te `execvpe` patlayınca `os._exit(127)`
ediliyor ve sekme `✗ (127)` gösteriyor. Windows'ta başarısız spawn *exception*
fırlatır; transport onu yakalayıp **127 raporlayacak**, böylece sekme başlığı
sözleşmesi platformlar arası aynı şeyi anlatır.

**Kapanış** — en riskli yer; üç adım, hepsi süreli:

1. reader thread'in döngü bayrağı düşer ve **sinyal bağlantısı kesilir** (geç
   gelen veri düşsün),
2. `terminate(force=False)` → kısa bekleme → `terminate(force=True)`,
3. `thread.wait(timeout)`; süre dolarsa **thread bırakılır**.

Üçüncü madde POSIX'teki "zombiyi bırak" kararının birebir karşılığı ve aynı
gerekçeyle: donmuş bir arayüz, başıboş bir thread'den kesinlikle kötüdür.
Bağlantı 1. adımda kesildiği için bırakılan thread silinmiş bir nesneye sinyal
gönderemez — sıra bu yüzden bu sıra.

**Argüman sırası tuzağı.** `PtyProcess.setwinsize(rows, cols)` ile alt seviye
`PTY.set_size(cols, rows)` **ters sırada**. Depoda `pyte.Screen`'in aynı tuzağı
zaten belgeli (`Screen()` `(columns, lines)`, `resize()` `(lines, columns)`);
bu da yorumla işaretlenecek.

**Varsayılan kabuk.** POSIX'te `$SHELL` ya da `/bin/bash -l`. Windows'ta
`$SHELL` yok; sıralama `pwsh.exe` → `powershell.exe` → `%COMSPEC%` (cmd.exe).
`-l` karşılığı yok, eklenmiyor.

**Bağımlılık** `requirements.txt`'e ortam işaretçisiyle girer, böylece
Linux/macOS kurulumu hiç değişmez:

```
pywinpty>=2.0 ; sys_platform == "win32"
```

**`child_environment`'ın Windows karşılığı.** PyInstaller'ın Windows
bootloader'ı `LD_LIBRARY_PATH` yazmıyor; DLL aramasını `SetDllDirectory` ile
yapıyor. Yani bilinen bir sızıntı yok ve `child_environment` Windows'ta
doğal olarak no-op (anahtarlar zaten yok). Ama bu **varsayılmayacak**: donmuş
`.exe` içinden `:term` açıp `where python` ile bir kez elle doğrulanacak —
`:pio build`'in doğru `pio`'yu bulması buna bağlı.

### D — Taşınabilirlik düzeltmeleri

Terminal dışında Windows'ta yanlış davranan üç yer. Üçü de küçük ama üçü de
kullanıcıya görünür:

**`core/config.py::config_path()`** — bugün `XDG_CONFIG_HOME` ya da
`~/.config`. Windows'ta `%APPDATA%\decode\config.toml` olacak;
`XDG_CONFIG_HOME` verilmişse yine o kazanır (öncelik sırası korunuyor).
Modülün saf-Python, Qt'siz olma niteliği bozulmuyor.

**`embedded/pio_cli.py::find_executable()`** — iki hata var. Yedek yol
POSIX'e sabit (`~/.platformio/penv/bin/pio`); Windows'taki karşılığı
`~\.platformio\penv\Scripts\pio.exe`. Ayrıca `os.access(path, os.X_OK)`
Windows'ta var olan her dosya için pratikte `True` döner, yani anlamsız bir
kapı — orada `os.path.isfile` kullanılacak. `shutil.which` zaten `PATHEXT`'i
doğru işliyor, o kısım değişmiyor.

**`ui/components/terminal_panel.py::TerminalView.shell_name()`** — bugün
`os.environ.get("SHELL", "/bin/bash")`'in taban adını alıyor; Windows'ta
`SHELL` yok, sekme başlığı "bash" yazardı. `TerminalProcess`'e delege
edilecek, o da transport'un `default_shell_argv()`'ine. Böylece panel
platformdan habersiz kalır — §A'daki "panel değişmez" kuralının tek istisnası
ve gerekçesi bu.

### E — `packaging/decode.spec`

**Mimari adı.** `platform.machine()` Windows'ta `x86_64` değil **`AMD64`**
döner. Bugünkü `_ARCH = platform.machine()` çıktıyı
`DeCode-v0.3.0-windows-AMD64` yapar; duman testindeki
`case "$BINARY" in *${{ matrix.ad }})` kontrolü bunu yakalar ve release kırılır.
Normalleştirme eklenecek:

| `platform.machine()` | Normalleşmiş |
|---|---|
| `AMD64`, `x86_64` | `x86_64` |
| `ARM64`, `aarch64`, `arm64` | `arm64` |

**`.exe` uzantısı.** PyInstaller Windows'ta adın sonuna `.exe` ekler; yani
gerçek dosya `DeCode-v0.3.0-windows-x86_64.exe`. `ls dist/DeCode-*` bunu yine
yakalar ama sondaki ad kontrolü `.exe`'ye tolerans kazanmalı (§F).

**`hide_console`.** `EXE(...)`'ye yalnız Windows'ta eklenecek. PyInstaller
6.22.2 bunu başka platformlarda "Ignoring hide_console; supported only on
Windows!" uyarısıyla yok sayıyor (`PyInstaller/building/api.py:497`) — çalışır
ama her Linux/macOS build'inin logunu kirletir, o yüzden koşullu.
Geçerli değerler `{hide-early, minimize-early, hide-late, minimize-late}`
(`api.py:582`); seçim **`hide-early`**.

**`pywinpty` toplama.** PyInstaller'ın uzantı modülünü ve yanındaki DLL'leri
otomatik bulacağı varsayılmayacak: Windows dalında `hiddenimports=["winpty"]`
ve `collect_dynamic_libs("winpty")` eklenecek, sonra donmuş `.exe`'de `:term`
ile doğrulanacak. Eksik DLL'in belirtisi, kaynaktan çalışırken sorunsuz olup
**yalnız donmuş binary'de** terminalin açılmamasıdır — CI'ın göremediği tek
boşluk bu; bkz. §F.

`excludes` listesi değişmiyor.

### F — GitHub Actions

**Ortak: kabuk.** `windows-latest` runner'ında `run:` varsayılanı
**PowerShell**'dir; her iki workflow'daki mevcut adımlar ise bash
(`set +e`, `PIPESTATUS`, `tee`, `awk`, `case ... esac`). Her adıma `shell: bash`
serpiştirmek yerine iş düzeyinde tek satır:

```yaml
defaults:
  run:
    shell: bash
```

Git Bash Windows runner'larında kurulu; böylece üç platform da aynı adımları
koşar ve mevcut betikler olduğu gibi kalır.

**`tests.yml`** — matrise `windows-latest` eklenir. `apt-get` ve `fc-list`
adımları zaten `if: runner.os == 'Linux'` ile korunuyor, dokunulmuyor.

**`release.yml`** — matrise bir satır:

```yaml
- os: windows-latest
  ad: windows-x86_64
```

Duman testinde tek değişiklik: ad kontrolü `.exe` uzantısını kabul edecek
(`*${{ matrix.ad }}` **veya** `*${{ matrix.ad }}.exe`).

**CI'ın göremediği boşluk — bilinçli kabul.** `--version` yolu
`QApplication`'dan önce dönüyor (`main.py`'de bilinçli olarak öyle), yani
ConPTY'ye hiç dokunmuyor: eksik bir `winpty` DLL'i duman testinden görünmez
geçer. `tests.yml` ConPTY'yi `windows-latest`'te gerçekten sınıyor ama
**kaynaktan**, donmuş binary'den değil — yani "kaynakta çalışıyor, `.exe`'de
çalışmıyor" hatası ikisinin arasından kaçar. Bu boşluğu kapatmak binary'ye
bir `--selftest` bayrağı eklemeyi gerektirirdi; uygulama yüzeyini bunun için
büyütmüyoruz. Güvence §Elle doğrulama'nın 4. maddesinden geliyor ve o madde
**release'in ön koşulu**. Windows makinesine düzenli erişim olduğu için
(Karar 5) bu takas kabul edilebilir; erişim kaybolursa `--selftest` yeniden
değerlendirilir.

**Release kapısı değişmiyor:** `needs: build` üç matris satırının da
başarısını bekler. Bir platform kırılırsa tag durur, yarım sürüm yayınlanmaz.

**Sürüm notları**'na Windows bölümü eklenir: indir, çalıştır, SmartScreen
"More info" → "Run anyway", Windows 10 1809+ gereksinimi.

### G — Belgeler

- **`README.md`** — indirme tablosuna Windows satırı; "Windows'ta uygulama şu
  an hiç çalışmaz … ConPTY henüz yazılmadı" paragrafı kaldırılır.
- **`CHANGELOG.md`** — yeni sürüm başlığı; Windows desteği ve ayar yolu.
- **`docs/Roadmap.md`** — Faz 5'teki Windows maddesi **tamamlandı**'ya çekilir;
  teknik borç tablosundaki test sayısı güncellenir (197 → mevcut sayı;
  bugünkü ölçüm 273).
- **`docs/sprint/sprint-14.md`** + `docs/sprint/README.md` tablosu ve "Aktif
  sprint" satırı.
- **`CLAUDE.md`** — mimari bölümünde `core/terminal_process.py` maddesi
  transport dikişini anlatacak şekilde güncellenir; `core/config.py` maddesine
  platforma göre ayar yolu eklenir.

## Hata yolları

Hepsi bugünkü kuralı izler: **tek satırlık Türkçe mesaj, sekme açılmaz,
uygulama çökmez.**

| Durum | Davranış |
|---|---|
| `pywinpty` import edilemiyor | `:term`/`:pio` tek satır uyarı basar ("Windows terminal desteği kurulamadı"); editör çalışmaya devam eder. Donmuş binary'de bu **olmamalı**, ama kaynaktan çalıştıran geliştirici için sessiz çökme yerine açık mesaj. |
| ConPTY yok (Windows 10 < 1809) | Aynı yol; sürüm notlarında asgari sürüm yazılı. |
| Spawn başarısız (`pio` yok, yol bozuk) | Çıkış kodu **127**, sekme `✗ (127)` — POSIX'le aynı anlam. |
| Reader thread `wait(timeout)`'ta dönmedi | Thread bırakılır, bağlantı zaten kesilmiştir; uygulama kapanır. |
| Süreç sinyalle/anormal öldü | Windows'un ham çıkış kodu gösterilir (ör. Ctrl+C'de `0xC000013A`). Normalleştirme yapılmıyor — bkz. §Riskler. |

## Test planı

**`tests/platform_commands.py` (yeni)** — testlerdeki POSIX'e sabit komutları
platforma göre çözen küçük bir yardımcı: `echo_argv(metin)`, `exit_argv(kod)`,
`pwd_argv()`. Windows'ta `["cmd", "/c", ...]` karşılıklarını verir.
Etkilenen dosyalar: `tests/test_terminal_process.py` (`/bin/echo`, `/bin/sh -c
exit 1`, `/bin/pwd`, `/bin/sh -c exit 0`), `tests/test_terminal_command.py`
(`/bin/echo`, `/bin/sh -c exit 1`).

**`tests/test_pty_transport.py` (yeni)** — transport sözleşmesinin testleri.
Kritik nokta: **aktif transport'a karşı koşarlar**, yani aynı dosya Linux ve
macOS'ta `PosixTransport`'u, Windows runner'ında `WindowsTransport`'u sınar.
Kapsam:

- çıktı okunuyor (Türkçe karakterli uzun çıktı — UTF-8 sınır bölünmesi riski),
- çıkış kodu doğru (`0`, `1`),
- olmayan komut → `127`,
- `cwd` uygulanıyor,
- `set_size` süreç koşarken ve koşmazken,
- `close()` süre içinde dönüyor ve `is_alive()` sonrasında `False`,
- `close()` sonrası geç veri sinyal yaymıyor.

**`tests/test_pio_cli.py`** — sahte çalıştırılabilir üreten testler (`#!/bin/sh`
yazıp `chmod +x`) Windows'ta anlamsız; platform dalı eklenecek (orada
`pio.exe` adında boş bir dosya yeterli, çünkü kapı artık `os.path.isfile`).

**`tests/test_config.py`** — `%APPDATA%` dalı için yeni test; `XDG_CONFIG_HOME`
önceliğinin Windows'ta da korunduğu ayrıca sınanacak.

**`tests/test_frozen_env.py`** — değişmiyor. Testler `child_environment`'a
açık sözlük veriyor, gerçek ortama bakmıyor; Windows'ta olduğu gibi geçer.

**Atlama kuralı:** platforma özgü iç testler `@pytest.mark.skipif` ile
korunur; ama sözleşme testleri **atlanmaz** — her platformda kendi
transport'unu sınar. Yeşil taban çizgisi: bugün 273 test.

## Elle doğrulama (release öncesi kontrol listesi)

Windows makinesinde, **donmuş `.exe` üzerinde**:

1. Çift tıkla → uygulama açılıyor, arkada **siyah konsol penceresi yok**.
2. `cmd`'den `DeCode-v*-windows-x86_64.exe --version` → sürümü basıyor.
3. İlk açılışta `%APPDATA%\decode\config.toml` oluşuyor; içerik yorumlu şablon.
4. `:term` → PowerShell açılıyor, prompt doğru çiziliyor.
5. `:term` içinde Türkçe karakterli uzun çıktı (`dir` / uzun bir metin) →
   bozulma yok. *(UTF-8 sınır riski, §C.)*
6. `:term` içinde `where python` → PyInstaller'ın `_MEI…` geçici dizinini
   **göstermiyor**. *(§C, `child_environment`.)*
7. Terminal panelini yeniden boyutlandır → ConPTY resize doğru, sarmalama bozulmuyor.
8. Gerçek bir PlatformIO projesinde `:pio build` → derliyor, çıkış kodu sekmede.
9. Gerçek karta `:pio upload` → yüklüyor.
10. `:pio monitor` → seri çıktı akıyor; Alt+Shift+W ile sekme kapanıyor.
11. `:reload` → ayarlar yeniden uygulanıyor.
12. Terminal açıkken pencereyi kapat → **donma yok**, süreç geride kalmıyor.
    *(§C kapanış sırası; macOS'ta bu tam olarak kırılmıştı.)*
13. İnternetten indirilen `.exe`'de SmartScreen akışı sürüm notlarındaki
    adımlarla geçiliyor.

## Riskler

| Risk | Şiddet | Karşılık |
|---|---|---|
| `pywinpty` `str` döndürüyor **ve** çok baytlı karakteri okuma sınırında tamponlamadan bölüyor | Orta — bozulma sessiz ve aralıklı, ama yalnız bir olasılıkta gerçekleşiyor | `pyte.ByteStream` sınır birleştirmeyi zaten yapıyor (§C tablosu), yani ilk iki olasılıkta risk yok. Üçüncüde alt seviye `winpty.PTY` API'sine inilir. İlk adımda ölçülüyor; sözleşme testi ve elle doğrulama 5 bunu hedefliyor. |
| Reader thread kapanışta dönmüyor | **Yüksek** — kullanıcı uygulamayı kapatamaz | Süreli `wait` + thread'i bırakma; bağlantı önce kesiliyor. Elle doğrulama 12. |
| PyInstaller `winpty` DLL'lerini toplamıyor | Orta — yalnız donmuş binary'de görünür | `collect_dynamic_libs`, ve güvence `--version`'dan değil elle doğrulama 4'ten geliyor (§F). |
| ConPTY gereksinimi (Win10 1809+) | Düşük | Sürüm notunda yazılı, hata yolu açık mesaj basıyor. |
| Windows çıkış kodları çok büyük (`0xC000013A`) | Düşük — kozmetik | Şimdilik ham gösteriliyor; rahatsız ederse ayrı bir iş olarak eşlenir. |
| `forkpty()` çok iş parçacıklı süreçte (mevcut borç) | Düşük | Değişmiyor; POSIX tarafı birebir taşınıyor, borç tablosunda kalmaya devam eder. |

## Bu sprintten sonra

- **Kod imzalama + notarization** (Windows ve macOS birlikte) — ücretli
  sertifika kararı gerektirir.
- **Installer** (Inno Setup ya da MSI) ve Windows başlat menüsü girdisi.
- **Windows on ARM** — ayrı matris satırı.
- **Intel Mac (`macos-13`)** — hâlâ açık, bu portla ilgisiz.
- **`pyproject.toml` + `decode` konsol komutu** — Faz 5'in açık kalan maddesi.
