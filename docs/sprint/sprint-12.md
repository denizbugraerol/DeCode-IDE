# Sprint 12 — macOS (Apple Silicon) derlemesi
**Tarih:** 04 Eyl 2026 · **Durum:** Aktif · **Commit(ler):** —

## Hedef
Release hattını çok platformlu hale getirmek: aynı tag'den Linux ve macOS
(Apple Silicon) binary'leri üretilsin, test süiti her iki işletim sisteminde
koşsun.

## Çıktılar
- [x] `QT_QPA_PLATFORM` ipucu Linux'a koşullandı ve kullanıcının değeri
      artık ezilmiyor — `main.py`, `tests/test_qt_platform.py`
- [x] `.spec` çıktı adı platform + mimari taşıyor — `packaging/decode.spec`
- [x] `tests.yml` matrisi: `ubuntu-latest` + `macos-latest`
- [x] `release.yml` matrisi + varlıkları tek Release'de toplayan ayrı job
- [x] README / CHANGELOG / Roadmap
- [ ] CI'da yeşil doğrulama ve sürüm çıkarma

## Teknik notlar

**macOS neden ucuzdu.** Ölçüm: uygulama kodunun 3898 satırından yalnız
`core/terminal_process.py` (238 satır) Unix'e özgü modül kullanıyor —
`fcntl`, `pty`, `termios` — ve **bunların üçü de macOS'ta var**. `pty.fork`,
`termios.TIOCSWINSZ`, `fcntl.ioctl`, `SIGHUP`/`SIGKILL`, `os.execvpe`: hepsi
çalışıyor. Windows'ta ise yoklar ve uygulama import anında çökeceği için o
bir port işi, paketleme işi değil.

**Sessiz bir tuzak ortaya çıktı: `QT_QPA_PLATFORM` koşulsuz eziliyordu.**
`main.py` değişkeni her durumda `wayland;xcb` yapıyordu. Bunun iki sonucu
vardı: (1) macOS'ta olmayan plugin'ler aranırdı, (2) daha kötüsü, Sprint
11'de yaptığım "X11'de açılıyor" doğrulaması **geçersizdi** —
`QT_QPA_PLATFORM=xcb ./DeCode` çalıştırmak yine `wayland;xcb` demekti, yani
X11 hiç sınanmamıştı. Artık kullanıcının değeri korunuyor; sahte bir platform
adının reddedildiği (kod 134) ve `xcb`'nin gerçekten çalıştığı ayrı ayrı
doğrulandı.

**Varlık adları platform taşımak zorunda.** `.spec` adı `sys.platform` ve
`platform.machine()`'den türetiyor. PyInstaller çapraz derleme yapamadığı
için her dosya üzerinde derlendiği sistemi anlatır; ad da bunu söylemeli.
Maliyeti: `DeCode-v0.1.1-x86_64` → `DeCode-vX.Y.Z-linux-x86_64`.

**Yarım sürüm yayınlamıyoruz.** Release job'ı `needs: build` ile iki
platformu birden bekliyor. `fail-fast: false` sayesinde bir platformun
kırılması ötekinin build'ini iptal etmiyor (ikisinin de sonucunu görmek
istiyoruz), ama biri kırılırsa Release hiç oluşmuyor — sessizce eksik bir
sürüm dağıtmaktansa tag'in durması yeğ.

**Doğrulama boşluğu, açıkça.** Projenin bir Mac'i yok. macOS güvencesi
tamamen otomatik testlerden geliyor — ki bunlar gerçek PTY açan testleri de
içeriyor, yani gömülü terminalin macOS'ta çalıştığına dair anlamlı bir
kanıt. Ama "pencere açılıyor mu, `:pio build` yürüyor mu" elle denenmedi ve
bu README ile release notlarında yazılı.

**Sprint numarası rezerve etmeyi bıraktık.** Roadmap "Sprint 12 = hatadan
koda atlama" diyordu; araya giren her iş bu numaraları kaydırıyordu (bu
ikinci oluşuydu). Artık numara iş yapıldığında veriliyor, plan maddeleri
yalnız "açık" diyor.

## Devreden
- CI'da yeşil doğrulama ve macOS'lu ilk sürümün çıkarılması
- Intel Mac (`macos-13` matris satırı)
- Windows portu (ConPTY / `pywinpty`)
- `.app` paketi, `.desktop` girdisi, ikon, `pyproject.toml`
