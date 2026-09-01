# PlatformIO Çalıştırma Çekirdeği (Faz 4 / Sprint 10) — Tasarım

**Tarih:** 01 Eyl 2026 · **Durum:** Onay bekliyor · **Faz:** 4 — Gömülü hedef

## Hedef

`:pio build`, `:pio upload`, `:pio clean`, `:pio monitor` komutlarının DeCode
IDE'nin içinden, gömülü terminal panelinde gerçek bir PTY üzerinde çalışması;
`platformio.ini`'deki ortamların okunup `:pio env` ile seçilebilmesi ve seçili
ortamın statusline'da görünmesi.

Bu, Roadmap'teki "Faz 4 — Gömülü hedef" maddesinin **A + B + C** parçalarıdır
(sırasıyla: çalıştırma, komut yüzeyi, ortam seçimi). Faz 4'ün diğer iki parçası
ayrı sprintlere bırakıldı:

| Parça | İş | Nerede |
|---|---|---|
| A | `pio` süreçlerini çalıştırma, çıktı terminal sekmesine | **Bu sprint** |
| B | `:pio <alt-komut>` + tamamlama | **Bu sprint** |
| C | `platformio.ini` ortamları, aktif ortam, rozet | **Bu sprint** |
| E | Derleme hatasından koda atlama (`dosya:satır`) | Sprint 11 |
| D | Seri monitör (kendi port/baud yönetimiyle) | Sprint 12 |

## Kapsam dışı

- **Hata → koda atlama (E).** Bu sprintte yok; ama çalıştırma yolu, ham çıktının
  ekran tamponundan bağımsız olarak dinlenebileceği şekilde kuruluyor (bkz.
  *Sprint 11'e bırakılan kanca*).
- **Kendi seri monitörümüz (D).** `:pio monitor` bu sprintte `pio device monitor`
  sürecini terminal sekmesinde çalıştırır — yani seri monitör *çalışır*, ama
  `embedded/serial_reader.py` hâlâ boştur; port/baud yönetimi PlatformIO'nun
  işidir.
- **Klavye kısayolu.** Karar: yok. Alt+Shift ailesi sekme yönetimine ayrılmış
  kalır, PlatformIO işleri yalnız `:pio ...` üzerinden yapılır.
- Kart/kütüphane yükleme (`pio pkg`), `pio test`, proje oluşturma (`pio init`).

## Kararlar

| # | Karar | Gerekçe |
|---|---|---|
| K1 | Komut yüzeyi tek aile: `:pio <alt-komut>` | Roadmap'in yazdığı biçim; ana komut listesini 4 satır şişirmez, ileride `:pio test` eklemek bedava |
| K2 | Süreç, **kendi PTY'sinde doğrudan** çalışır (shell'e komut yazılmaz) | Renkli çıktı (`pio` `isatty()` görür), gerçek Ctrl+C/SIGINT, çıkış kodu okunabilir, ham çıktı ekran tamponundan bağımsız dinlenebilir |
| K3 | Aktif ortam kavramı var; `:pio env` paletiyle seçilir, statusline'da görünür | Çok ortamlı projede ne derlendiği her an ekranda; tek ortamlı projede kimseyi `:pio env` yazmaya zorlamaz (bkz. K5) |
| K4 | Aynı komut ikinci kez çalışınca **aynı sekme** yeniden kullanılır | Sekme çöplüğü olmaz; "son derleme" hep aynı yerde |
| K5 | Ortam seçilmemişse `-e` **hiç verilmez** | PlatformIO kendi `default_envs`'ini uygular; IDE, ini'nin kararını ezmez |
| K6 | PlatformIO `requirements.txt`'e girmez | Harici bir araçtır, IDE'nin Python bağımlılığı değil; yokluğu birinci sınıf hata yolu |

## Mimari

Üç katman; yeni saf mantık `embedded/` altında, Qt'ye dokunmadan.

```
embedded/pio_project.py   (saf)  platformio.ini: kök bulma + ortam listesi
embedded/pio_cli.py       (saf)  pio çalıştırılabiliri + argv üretimi + alt komut tablosu
        |
core/terminal_process.py  (Qt)   PTY: artık argv/cwd alıyor, çıkış kodu yayıyor
core/state_machine.py     (Qt)   ':pio' komutu ve tamamlaması
        |
ui/components/terminal_panel.py  komut sekmesi: başlık, ✓/✗, yeniden kullanım
ui/main_window.py                orkestrasyon: kök -> ortam -> argv -> sekme; rozet
ui/components/bottom_panel.py    statusline'da ortam etiketi
```

Veri akışı (`:pio build`):

```
ModalEditor(':pio build') -> StateMachine -> pio_requested('build')
  -> EditorTabs._relay -> IDEWindow._on_pio_requested('build')
      1. pio_project.find_project_root(os.getcwd())      -> yoksa dur
      2. pio_cli.find_executable()                       -> yoksa dur
      3. pio_cli.build_argv('build', exe, env=self.pio_env)
      4. TerminalPanel.run_command(argv, 'pio build', cwd=root)
          -> TerminalView(argv=..., title=..., cwd=...) -> TerminalProcess
```

### `embedded/pio_project.py` (saf Python, Qt yok)

```python
INI_NAME = "platformio.ini"

def find_project_root(start_dir):        # -> str | None
def parse_environments(ini_text):        # -> (info, warnings)
def read_project(root):                  # -> (info, warnings)
```

`info` sözlüğü: `{"environments": ["esp32dev", ...], "default_envs": [...]}`.
`(veri, warnings)` ikilisi `core/config.parse`'ın sözleşmesiyle aynı: modül
yazdırmaz, çağıran yazdırır.

- `find_project_root` verilen dizinden başlayıp `platformio.ini` bulana kadar
  yukarı çıkar (dosya sistemi köküne kadar), bulamazsa `None`.
- `environments`, `[env:...]` bölüm adlarından dosyadaki sırayla türetilir.
- `default_envs`, `[platformio]` bölümünden; virgül ya da satır sonuyla ayrılmış
  olabilir, ikisi de desteklenir.
- **Tuzak:** `ConfigParser` interpolasyonu `read_string`'de değil `get()`
  çağrısında çalışır — yani bölüm adları her hâlükârda okunur, ama `get()`
  ettiğimiz `default_envs` değeri `%` içeriyorsa varsayılan parser
  `InterpolationSyntaxError` fırlatır (PlatformIO ini'lerinde `-D FMT="%d"`
  gibi değerler yaygın). **`interpolation=None`** bu ihtimali tamamen kaldırır
  ve `${sysenv.HOME}` gibi PlatformIO'ya ait ifadeleri ham hâliyle verir —
  zaten çözmüyoruz. Aynı savunma refleksiyle **`strict=False`**: kopyala-yapıştır
  ini'lerdeki tekrarlanan anahtar `DuplicateOptionError` ile çökertmesin.
- Bozuk ini uygulamayı çökertmez: `configparser.Error` yakalanır, boş liste +
  bir uyarı döner (`core/config.py`'nin "kötü dosya asla çökertmez" ilkesi).

### `embedded/pio_cli.py` (saf Python, Qt yok)

```python
SUBCOMMANDS = {          # ':pio ' tamamlamasının TEK kaynağı
    "build":   "projeyi derle",
    "upload":  "karta yükle",
    "monitor": "seri monitörü aç",
    "clean":   "derleme çıktılarını sil",
    "env":     "ortam seç",
}
PROCESS_SUBCOMMANDS = ("build", "upload", "monitor", "clean")   # süreç başlatanlar

def find_executable():                       # -> str | None
def build_argv(subcommand, executable, env=None):   # -> list[str] | None
```

| Alt komut | argv |
|---|---|
| `build` | `<exe> run` |
| `upload` | `<exe> run -t upload` |
| `clean` | `<exe> run -t clean` |
| `monitor` | `<exe> device monitor` |

Ortam seçiliyse hepsine `-e <env>` eklenir. `monitor`'ün `-e` ile koşması
ini'deki `monitor_speed` / `monitor_port` ayarlarını da devreye sokar — baud'u
IDE'nin sorması gerekmez.

`build_argv`, `env` (süreç başlatmayan alt komut) ve bilinmeyen adlar için `None`
döner. `executable` parametre olarak alınır (PATH'ten okunmaz) ki modül testte
dosya sistemine bağımlı olmasın.

`find_executable` sırayla: `shutil.which("pio")`, `shutil.which("platformio")`,
`~/.platformio/penv/bin/pio`. Üçüncüsü, PlatformIO'nun kendi kurucusunun PATH'e
girmeyen kurulumu içindir.

### `core/terminal_process.py` — argv, cwd, çıkış kodu

```python
TerminalProcess(rows=9, cols=80, argv=None, cwd=None, parent=None)
exited = pyqtSignal(int)     # YENİ: çıkış kodu
self.exit_code = None
```

- `argv is None` → bugünkü davranış aynen: `execvpe(SHELL, [SHELL, "-l"], env)`.
- `argv` verildiyse → `execvpe(argv[0], argv, env)`; `cwd` verildiyse exec'ten
  önce child içinde `os.chdir(cwd)`.
- exec başarısızsa child `os._exit(127)` (bugün `1`) — "komut bulunamadı" ayırt
  edilebilsin diye; kabuk geleneğiyle uyumlu.

Üç tuzak — üçü de sessiz bozulma üretir, ikisi bugünkü kodda zaten var:

1. **Mevcut `finished` sinyaline argüman EKLENMEZ.** `TerminalView.__init__`
   içinde `self._process.finished.connect(self.update)` var; sinyal `int`
   taşımaya başlarsa Qt `QWidget.update(int)` overload'ı arar ve bağlantı
   patlar. Bu yüzden çıkış kodu **ayrı** `exited` sinyaliyle taşınıyor.
2. `_handle_child_exit` bugün `os.waitpid(pid, WNOHANG)` sonucunu atıyor. Çıkış
   kodu için dönüş değeri + `os.waitstatus_to_exitcode(status)` gerekiyor; ve
   PTY'de EOF ile çocuğun gerçekten reap edilebilir olması arasında yarış var —
   WNOHANG `(0, 0)` dönebilir. EOF'tan sonra çocuk zaten ölmek üzere olduğu için
   burada **bloklayan** `os.waitpid(pid, 0)` doğru olanı; `ChildProcessError`
   yine yutulur.
3. `close()` bugün SIGHUP → 0.5s bekle → SIGKILL yapıyor ve `_pid`'i `None`'a
   çekiyor; komut sekmesi yeniden çalıştırılırken (K4) aynı yol kullanılır.

### `ui/components/terminal_panel.py` — komut sekmeleri

```python
TerminalView(rows=ROWS, argv=None, title=None, cwd=None, parent=None)
    def title(self)                 # sekme etiketi
    self._finished = False
TerminalPanel.run_command(argv, title, cwd=None)   # -> TerminalView
```

- `title()`: shell sekmesi için bugünkü `shell_name()` (`fish`), komut sekmesi
  için verilen başlık + durum eki: `pio build`, bitince `pio build ✓` ya da
  `pio build ✗ (1)`. `_relabel_tabs` artık `shell_name()` yerine `title()` okur.
- **Tuzak:** `showEvent` bugün "süreç koşmuyorsa başlat" diyor. Bu, biten bir
  komut sekmesinde felakete yol açar: `:term` ile panel gizlenip yeniden
  açıldığında `pio upload` **kendiliğinden tekrar çalışır**. `_finished`
  bayrağı bunu keser (shell sekmesinin davranışı değişmez).
- `run_command`: paneli açar; aynı `title`'a sahip komut sekmesi varsa onu
  yeniden kullanır (K4: eski süreci `close()` ile kapat, `_finished`'i sıfırla,
  yeni PTY başlat — `TerminalProcess.start()` pyte ekranını zaten yeniden
  kurar), yoksa yeni sekme ekler ve ona geçer.
- **Tuzak:** sekme eşleştirmesi **süslenmemiş** başlığa bakar. `title()` bitmiş
  sekmede `pio build ✓` döndüğü için, ikinci `:pio build` çağrısı süslü metinle
  karşılaştırırsa eşleşmeyi kaçırır ve K4'e rağmen yeni sekme açar; view, ham
  başlığı ayrıca saklar.
- Komut sekmesi de Alt+Shift ailesine bağlıdır (`W` kapatır, `←/→` gezinir);
  `Alt+Shift+N` her zaman shell sekmesi açar — komut sekmesi klonlamaz.

### `core/state_machine.py` — `:pio`

- `KNOWN_COMMANDS`'a `"pio"`; `COMMAND_DESCRIPTIONS["pio"] = "PlatformIO
  (:pio build|upload|monitor|clean|env)"`.
- `_matches_for`: `prefix.startswith("pio ")` dalı — `:cd` / `:openfile`
  dallarıyla birebir aynı desen — `pio_cli.SUBCOMMANDS`'tan
  `("pio build", "projeyi derle")` çiftleri üretir, yazılan öneke göre süzer.
- `_execute_command_line`: `text == "pio"` → kullanım satırı yazdırır (hiçbir
  şey çalıştırmaz); `text.startswith("pio ")` → `pio_requested.emit(alt_komut)`.
  Bilinmeyen alt komut (`:pio derle`) da kullanım satırına düşer.
- `core` → `embedded` importu katman kuralına uygun: `embedded/pio_cli.py` saf
  Python, Qt ve `ui` bilmiyor (`core/state_machine.py` zaten `core.search`
  import ediyor).

### Sinyal boru hattı

`pio_requested = pyqtSignal(str)` üç yere eklenir — bugünkü `settings_reload_requested`
ile birebir aynı desen:

1. `ModalEditor` ve `WelcomePage` (aynı ad, iki konak)
2. `EditorTabs._wire` içinde `_relay` satırı + `EditorTabs`'ta dışa açılan sinyal
3. `IDEWindow._connect_modal_host` tablosuna `"pio_requested": self._on_pio_requested`

`WelcomePage.available_commands`'a `"pio"` eklenir: `:pio build` metin tamponu
gerektirmiyor, sekme yokken de çalışmalı.

### `ui/main_window.py` — orkestrasyon

```python
self.pio_env = None            # kullanıcının seçtiği ortam
self.pio_default_envs = []     # ini'den okunan varsayılan (yalnız rozet için)

def _on_pio_requested(self, subcommand)
def _refresh_pio_badge(self)
```

`_on_pio_requested` akışı:

1. `root = pio_project.find_project_root(os.getcwd())` — `None` ise
   "PlatformIO projesi bulunamadı (platformio.ini yok)." yazdır, dur.
2. `subcommand == "env"` → `read_project(root)` → ortam listesini `CommandPalette`
   ile `mode="env"` olarak aç (`:ts`/`:sym` ile aynı palet). Seçim
   `_on_palette_accepted`'ın yeni `env` dalında `self.pio_env` olur, rozet
   tazelenir. Liste boşsa "Bu projede tanımlı ortam yok." yazdır.
3. `exe = pio_cli.find_executable()` — `None` ise "PlatformIO bulunamadı
   (kurulum: `pip install platformio`)." yazdır, dur.
4. `argv = pio_cli.build_argv(subcommand, exe, env=self.pio_env)`;
   `self.terminal_panel.run_command(argv, f"pio {subcommand}", cwd=root)`.

`_refresh_pio_badge` üç yerden çağrılır: açılışta bir kez (`_setup_ui` sonu),
`:pio env` seçiminden sonra ve `:cd`'den sonra. `:cd` başka bir dizine geçince
`pio_env` ayrıca **sıfırlanır** — artık başka bir projedeyiz.

### Statusline rozeti

`StatusLine.set_env(text)` — `file_label` ile `position_label` arasına yeni bir
`QLabel`. Kural:

| Durum | Görünen |
|---|---|
| PlatformIO projesi yok | (boş — etiket görünmez) |
| Proje var, seçim yok, ini'de `default_envs` var | `(esp32dev)` |
| Proje var, seçim yok, `default_envs` yok | `(—)` |
| `:pio env` ile seçilmiş | `esp32dev` |

Parantez = "bunu ben seçmedim, PlatformIO'nun varsayılanı". **Bilinçli olarak
`setStyleSheet` kullanılmıyor:** `set_mode`'un renk/font'u stylesheet'e
KOPYALAMASI yüzünden `apply_settings`'te elle tazelenmesi gerekiyor (Sprint 09,
kod incelemesi Bulgu 1/4). Düz metin bu tuzağı hiç doğurmaz.

## Hata yolları

Hiçbiri çökertmez; hepsi konsola tek satır yazar (projenin bugünkü `:cd` /
`:openfile` hata üslubu).

| Durum | Davranış |
|---|---|
| `platformio.ini` yok | Mesaj; sekme açılmaz |
| `pio` bulunamadı | Mesaj + kurulum ipucu; sekme açılmaz |
| Bozuk `platformio.ini` | Uyarı; ortam listesi boş; `:pio build` yine de çalışır (`-e` verilmez) |
| `exec` başarısız (127) | Sekme başlığı `✗ (127)`; PTY çıktısında hata görünür |
| Derleme hatası (`pio` 1 döner) | Sekme başlığı `✗ (1)`; çıktı sekmede durur |
| Zaten koşan `pio build` varken tekrar çağrı | O sekmedeki süreç kapatılır, yenisi aynı sekmede başlar (K4) |
| `:pio` argümansız / bilinmeyen alt komut | Kullanım satırı |

## Sprint 11'e bırakılan kanca

`TerminalProcess._drain_master` PTY'den okuduğu byte'ları `pyte`'a besliyor.
`pyte.Screen` kaydırma tamponu tutmaz ve ekran 9 satırdır — yani derleme
çıktısının tamamı ekranda **yoktur**. Hata→koda atlama bu yüzden ekranı
kazıyarak yapılamaz. Tasarım buna hazır: `_drain_master`'daki tek `feed()`
noktasından ham byte'lar ayrıca dışarı verilebilir (`output_bytes` sinyali ya da
bir satır tamponu). Sprint 11 oraya bir `dosya:satır:sütun` ayrıştırıcısı
bağlayacak. **Bu sprintte yalnızca kancanın önü açık tutuluyor, kanca
yazılmıyor.**

## Test planı

Saf katman (Qt yok, hızlı, gerçek `pio` gerekmez):

- `tests/test_pio_project.py` — `[env:...]` adları ve sırası; `default_envs`'in
  virgüllü ve çok satırlı biçimleri; **`%` ve `${...}` içeren ini çökmüyor**
  (interpolasyon regresyon testi); tekrarlanan anahtar çökertmiyor; bozuk ini →
  boş liste + uyarı; `tmp_path`
  ağacında kök arama (alt dizinden yukarı bulur, dışarıda `None` döner).
- `tests/test_pio_cli.py` — dört alt komut × ortamlı/ortamsız argv; `env` ve
  bilinmeyen alt komut `None`; `find_executable` `PATH` monkeypatch'iyle.
- `tests/test_state_machine.py` (mevcut dosyaya) — `:pio build` sinyali doğru
  argümanla yayılıyor; `:pio ` tamamlaması alt komutları veriyor; `:pio`
  argümansız sinyal yaymıyor.

Qt katmanı (`offscreen`, gerçek PTY — `pencere` fixture'ı zaten kapatıyor):

- `tests/test_terminal_command.py` — `run_command(["/bin/echo", "merhaba"])`
  sonrası `exited(0)`, pyte ekranında `merhaba`, sekme başlığı `✓`;
  `/bin/false` → `✗ (1)`; olmayan komut → `✗ (127)`. Olay döngüsü `QTest.qWait`
  ile döndürülür, zaman aşımı korumalı. Ayrıca **biten sekme `hide()`/`show()`
  sonrası yeniden çalışmıyor** (`_finished` regresyon testi).
- `tests/test_pio_window.py` — ini'siz dizinde `:pio build` sekme açmıyor;
  `tmp_path`'te sahte `platformio.ini` + monkeypatch'li `find_executable` ile
  `run_command`'a giden argv ve `cwd` doğru; `:pio env` sonrası rozet metni;
  `:cd` ortamı sıfırlıyor.

Testler `pio`'nun kurulu olmasına **bağlı değildir**; gerçek `pio` yalnız elle
doğrulamada kullanılır.

## Elle doğrulama (gerçek kart)

1. PlatformIO kur (`pip install platformio` ya da resmi kurucu), boş bir
   proje aç (`pio project init -b <kart>`).
2. `:cd <proje>` → statusline'da `(<default_env>)` görünüyor.
3. `:pio env` → palet ortamları listeliyor; seçim rozete yansıyor.
4. `:pio build` → sekme açılıyor, çıktı **renkli** akıyor, bitince `✓`.
5. Derleme hatası üret (`main.cpp`'ye `syntax error;` ekle) → `✗ (1)`.
6. Uzun derlemede Ctrl+C → süreç gerçekten kesiliyor.
7. Kartı tak, `:pio upload` → yükleme gerçekleşiyor.
8. `:pio monitor` → seri çıktı akıyor; Ctrl+C ile çıkılıyor.
9. `:pio build` ikinci kez → yeni sekme açılmıyor, aynı sekme tazeleniyor.
10. Panel `:term` ile gizlenip açılıyor → biten `pio upload` **tekrar
    çalışmıyor**.

Not: kart takıldığında `/dev/ttyUSB0` izni gerekebilir (bu makinede kullanıcı
`uucp` grubunda değil). Bu bir IDE hatası değil; `:pio upload` hatayı sekmede
gösterir.

## Riskler

| Risk | Etki | Önlem |
|---|---|---|
| `finished` sinyalinin argümanlı hale getirilmesi mevcut bağlantıyı bozar | Terminal çizimi sessizce durur | Ayrı `exited` sinyali (yukarıda) |
| Biten komut sekmesi `showEvent`'te yeniden koşar | `pio upload` istemsiz tekrarı — **gerçek donanıma yazar** | `_finished` bayrağı + regresyon testi |
| `%` içeren `default_envs` değerinde `get()` patlar | Ortam listesi hiç gelmez | `interpolation=None` + `strict=False` + regresyon testi |
| PTY testleri CI/SSH'ta kırılgan olabilir | Test paketi gürültülü | `QTest.qWait` + zaman aşımı; saf mantığın tamamı Qt'siz test edilir |
| `pio run` çıktısı 80 sütuna sığmayıp sarmalanır | Okunabilirlik | Terminal zaten pencere genişliğine göre `cols` hesaplıyor; ek iş yok |

## Bu sprintten sonra

- **Sprint 11 (E):** ham çıktıdan `dosya:satır:sütun` yakalama, quickfix listesi
  (`CommandPalette`, `mode="quickfix"`), hatadan koda atlama.
- **Sprint 12 (D):** `embedded/serial_reader.py` — PlatformIO'ya bağımlı olmayan
  kendi seri monitörümüz (port listesi, baud seçimi, yeniden bağlanma).
- Roadmap'te Faz 4 A/B/C işaretlenir, `docs/sprint/sprint-10.md` açılır,
  teknik borç tablosundaki "Boş yer tutucular" satırı güncellenir
  (`serial_reader.py` kalır).
