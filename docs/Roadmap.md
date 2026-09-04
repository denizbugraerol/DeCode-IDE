# DeCode IDE — Yol Haritası

## Vizyon

DeCode IDE, Vim'in modal giriş modelini PyQt6'nın hafifliğiyle birleştiren bir
editör. Uzun vadeli hedef, gömülü (PlatformIO) geliştirme için gereken her şeyi
— kod, terminal, derleme, seri monitör — tek pencerede toplayan bir IDE olmak.
İki değişmez ilke: **her şey klavyeden yönetilebilir** ve **arayüz Tokyo Night
paletine sadık kalır**.

Geçmiş işlerin ayrıntısı için [sprint günlüğüne](sprint/README.md) bakın.

## Bugünkü durum — v0.1.0 (ilk yayınlanan sürüm)

Aşağıdaki "Sürüm kilometre taşları" tablosundaki numaralar **iç faz
kilometre taşlarıdır**; yayınlanan sürüm numaralarıyla aynı şey değildir.
Depodan yayınlanan ilk sürüm **v0.1.0**'dır ([Sprint 11](sprint/sprint-11.md)):
tek dosya Linux çalıştırılabiliri. Yayınlanan sürümler için
[CHANGELOG.md](../CHANGELOG.md).


Çalışan özellikler:

- **Modal editör** — NORMAL / INSERT / COMMAND modları, imleç genişliğiyle mod
  göstergesi, satır numarası gutter'ı ([Sprint 02](sprint/sprint-02.md), [04](sprint/sprint-04.md))
- **Gerçek `:` komut satırı** — ekranın ortasında yüzen kutu, Enter'la çalışan
  komutlar, Tab/Shift+Tab tamamlama, kaydırılabilir öneri listesi
  ([Sprint 03](sprint/sprint-03.md), [05](sprint/sprint-05.md))
- **Komutlar** — `i`, `:w`, `:d`, `:b`, `:y`, `:p`, `:cd <yol>`, `:42`, `:q`, `:wq`,
  `:qa`, `:wqa`, `:tabnew`, `:tabclose`, `:tabnext`, `:tabprev`, `:term`, `:termnew`,
  `:ts`, `:find <desen>`, `:replace eski yeni`, `:openfile <yol>`, `:sym`, `:reload`
- **Arama ve gezinme** — bulanık dosya arama paleti (`:ts`), dosya içi arama
  (`:find` + çıplak `n`/`N`, tüm eşleşmeler vurgulu, Esc temizler), değiştirme
  (`:replace`), yol tamamlamalı dosya açma (`:openfile`) ve sembol paleti
  (`:sym`) ([Sprint 06](sprint/sprint-06.md), [07](sprint/sprint-07.md))
- **Çoklu sekme** — her sekmenin kendi editörü ve modu, `●` ile kaydedilmemiş
  değişiklik göstergesi ([Sprint 05](sprint/sprint-05.md)). Son sekme kapanınca
  uygulama kapanmıyor: komut satırı çalışan bir karşılama sayfasında kalıyor
  ([Sprint 08](sprint/sprint-08.md))
- **Alt+Shift kısayolları** — `T` editör/terminal odağı, `N` yeni sekme,
  `W` kapat, `←`/`→` sekme değiştir; hem editör hem terminal sekmelerinde,
  komut odağın bulunduğu yere uygulanır ([Sprint 08](sprint/sprint-08.md))
- **Gömülü terminal** — gerçek PTY üzerinde `pyte` ile çizilen, sekmeli shell
  paneli; Alt+Shift kısayollarıyla yönetiliyor ([Sprint 05](sprint/sprint-05.md))
- **PlatformIO** — `:pio build|upload|monitor|clean` gömülü terminalde kendi
  sekmesinde çalışıyor (renkli çıktı, gerçek Ctrl+C, sekme başlığında `✓`/`✗`,
  aynı komut ikinci kez çalışınca sekme yeniden kullanılıyor); `:pio env`
  `platformio.ini`'deki ortamı seçiyor ve seçim statusline'da görünüyor
  ([Sprint 10](sprint/sprint-10.md))
- **Dosya ağacı** — CWD'ye köklenmiş sidebar, `:cd` ile kök değiştirme, Esc ile
  odağı editöre döndürme ([Sprint 01](sprint/sprint-01.md), [02](sprint/sprint-02.md))
- **Sözdizimi renklendirme** — C/C++ ve Python (çok satırlı docstring dahil)
- **Ayar dosyası** (`~/.config/decode/config.toml`) — renk paleti (17 token),
  font ailesi/boyutu, sekme genişliği, `expand_tabs`, satır numarası açık/kapalı
  ve terminal satır sayısı özelleştirilebiliyor; `:reload` uygulamayı
  kapatmadan yeniden uyguluyor ([Sprint 09](sprint/sprint-09.md))
- **Test altyapısı** — pytest, `QT_QPA_PLATFORM=offscreen` ile ekransız çalışan
  197 test ([Sprint 06](sprint/sprint-06.md), [09](sprint/sprint-09.md),
  [10](sprint/sprint-10.md), [11](sprint/sprint-11.md)); her push'ta GitHub
  Actions'ta koşuyor

Henüz yok: Vim tarzı düzenleme komutları (`dd`, `yy`, `x`, `o`/`O`, sayı
önekleri), VISUAL mod, geri al/yinele + `.` ile son komutu tekrar, oturum geri
yükleme, kendi seri monitörümüz, derleme hatasından koda atlama, lint. Harf tabanlı hareket
komutları (`h/j/k/l`, `w/b`, `gg`/`G`) bu listede değil — bkz. Faz 3, kasıtlı
olarak uygulanmayacak.

## Faz 2 — Arama ve gezinme (tamamlandı)

Amaç klavyeyle hedefe gitmekti; dosya açmanın tek yolu artık sidebar'da
tıklamak değil.

- **Telescope / bulanık dosya arama (`:ts`)** — `ui/components/command_palette.py`
  gerçek palet oldu; kutu `FloatingList` olarak `CommandSuggestions`'la
  paylaşılıyor, dosya listesi arka planda taranıyor.
- **Dosya içi arama** (`:find <desen>`, çıplak `n`/`N` ile sonraki/önceki
  eşleşme, tüm eşleşmeler vurgulu, NORMAL modda Esc vurguyu temizler) ve
  **değiştirme** (`:replace eski yeni`) — çekirdeği `core/search.py`'de.
- **`:openfile <yol>`** ile doğrudan dosya açma; `_path_matches_for` artık hem
  `:cd` (yalnız dizin) hem `:openfile` (dosya dahil) tamamlamasını üretiyor.
- **Sembol atlama (`:sym`)** — açık dosyadaki fonksiyon/sınıf tanımlarına
  atlama; `core/symbols.py`.

## Faz 3 — Editör olgunluğu (sıradaki)

Editörün "günlük sürücü" olabilmesi için eksik olan Vim refleksleri ve
kişiselleştirme.

- **Navigasyon ok tuşlarında kalıyor** (bilinçli olarak Vim'den ayrılıyoruz):
  Ok, Home/End, PageUp/PageDown; Shift+Ok seçer, Ctrl+Ok kelime atlar.
  `h/j/k/l`, `w/b`, `gg`/`G` gibi harf tabanlı hareket komutları
  **uygulanmayacak**.
- Düzenleme komutları (`dd`, `yy`, `x`, `o`/`O` ve sayı önekleri) açık
  duruyor; hareketten bağımsız olarak ele alınacak.
- Görsel (VISUAL) mod ve seçim üzerinde işlem.
- Geri al/yinele için Vim tarzı davranış ve `.` ile son komutu tekrar.
- **Ayar dosyası** (`~/.config/decode/config.toml`) — **tamamlandı**
  ([Sprint 09](sprint/sprint-09.md)): `[editor]` altında `font_family`,
  `font_size`, `tab_width`, `expand_tabs`, `line_numbers`; `[terminal]`
  altında `rows`; `[colors]` altında 17 adlandırılmış renk tokeni
  (`#rrggbb`, geçersiz/bilinmeyen anahtarlar uyarıyla varsayılana döner).
  Dosya yoksa ilk açılışta şablonla oluşturuluyor; `:reload` uygulamayı
  kapatmadan yeniden uyguluyor.
- Oturum geri yükleme: son açık sekmeler ve çalışma dizini.

## Faz 4 — Gömülü hedef (PlatformIO)

Projenin varlık sebebi. `embedded/` klasörü ilk commit'ten beri bu faz için
yer tutuyor.

- **`embedded/pio_cli.py` + `embedded/pio_project.py`** — **tamamlandı**
  ([Sprint 10](sprint/sprint-10.md)): `build`, `upload`, `clean`, `monitor`
  argv'leri ve `platformio.ini` ayrıştırma. Çıktı `TerminalPanel`'de kendi
  sekmesine akıyor; ayrı bir çıktı penceresi yazılmadı.
- **Komutlar** — **tamamlandı**: `:pio build|upload|monitor|clean|env|init`, öneri
  listesi ve `:pio ` tamamlamasıyla.
- **Kart ve port seçimi** — **tamamlandı**: `platformio.ini` okunup ortamlar
  `:pio env` paletinde listeleniyor, seçim statusline rozetinde duruyor.
- **`embedded/serial_reader.py`** — açık (Sprint 13): kendi seri monitörümüz
  (port/baud seçimi, yeniden bağlanma). Bugün `:pio monitor` PlatformIO'nun
  kendi monitörünü çalıştırıyor.
- **Derleme hatasından koda atlama** — açık (Sprint 12): çıktıdaki
  `dosya:satır` eşleşmelerini yakalayıp ilgili sekmede o satıra gitme.

## Faz 5 — Dağıtım

- **Tek dosya Linux çalıştırılabiliri** — **tamamlandı**
  ([Sprint 11](sprint/sprint-11.md)): PyInstaller `--onefile`, GitHub Actions'ta
  `ubuntu-22.04` üzerinde derleniyor (geliştirici makinesinde değil — binary
  üzerinde derlendiği glibc'yi taban alır), `v*` tag'i itilince duman
  testinden geçip GitHub Releases'e yükleniyor.
- **Sürüm etiketleri + komut/kısayol referansı** — **tamamlandı**: sürümün tek
  kaynağı `core/version.py`, referans `README.md`'de.
- **Lisans** — **tamamlandı**: GPL-3.0 (PyQt6 `GPL-3.0-only` olduğu için
  binary dağıtan bu projenin başka seçeneği yok).
- `pyproject.toml` ile kurulabilir paket ve `decode` komutu — açık.
- Linux masaüstü girdisi (`.desktop`), uygulama ikonu ve AppImage — açık.
- macOS ve Windows — açık; ayrı alt projeler. macOS küçüktür (`pty`/`termios`
  orada da var), Windows bir port işidir: `core/terminal_process.py` `fcntl`,
  `pty`, `termios` ve `SIGHUP` kullanıyor, karşılığı ConPTY (`pywinpty`).

## Teknik borç

| Konu | Durum | Nerede |
|---|---|---|
| `__pycache__` deposu kirletiyor | Çözüldü ([Sprint 06](sprint/sprint-06.md)): kural eklendi, 14 `.pyc` takipten çıkarıldı | `.gitignore` |
| Lint altyapısı yok | Test var (197 test, pytest); lint/format aracı hâlâ seçilmedi | — |
| CI yok | Çözüldü ([Sprint 11](sprint/sprint-11.md)): her push'ta pytest, `v*` tag'inde release build | `.github/workflows/` |
| `CLAUDE.md` güncel değil | Çözüldü ([Sprint 07](sprint/sprint-07.md)): komut satırı modeli, sekmeler, terminal ve Faz 2 modülleri yazıldı | `CLAUDE.md` |
| Boş yer tutucular | `pio_cli.py` yazıldı ([Sprint 10](sprint/sprint-10.md)); `serial_reader.py` duruyor | Sprint 13 |
| Bulanık skorlama açgözlü | Soldan ilk eşleşmeyi alır, en iyi hizalamayı aramaz | `core/fuzzy.py` |
| C/C++ sembol çıkarma sezgisel | Çok satıra yayılan imzalar kaçabilir | `core/symbols.py` |
| `forkpty()` çok iş parçacıklı süreçte | `:ts` taraması sürerken `:term` açmak uyarı üretiyor | `core/terminal_process.py` |
| Tema kodda sabit | Çözüldü ([Sprint 09](sprint/sprint-09.md)): renkler `ui/theme.py`'deki tek palete taşındı, ayar dosyasının `[colors]` bölümünden özelleştirilebiliyor | `ui/theme.py` |

## Faz kilometre taşları

Tarih verilmiyor; sıra ve çıkış kriteri veriliyor. **Bunlar yayınlanan sürüm
numaraları değildir** — yayınlananlar için [CHANGELOG.md](../CHANGELOG.md).

| Kilometre taşı | Kapsam | Çıkış kriteri | Durum |
|---|---|---|---|
| **M1** | Faz 0–1 | Python/C++ dosyaları pencereden çıkmadan düzenlenip kaydedilebiliyor, terminal içeride | ✅ |
| **M2** | Faz 2 | `:ts` ile dosya bulunuyor, dosya içi arama/değiştirme çalışıyor | ✅ |
| **M3** | Faz 3 | Düzenleme komutları (`dd`/`yy`/`x`/`o`/`O`) + VISUAL mod; ayar dosyası ✅ (Sprint 09), oturum geri yükleniyor | Kısmen |
| **M4** | Faz 4 | PlatformIO derle/yükle/monitör tek komutla ✅ ([Sprint 10](sprint/sprint-10.md)); hatadan koda atlama ve kendi seri monitörümüz kaldı | Kısmen |
| **M5** | Faz 5 | Kurulabilir paket ve belgelenmiş komut/kısayol referansı | Kısmen — çalıştırılabilir + referans ✅ ([Sprint 11](sprint/sprint-11.md)), `pyproject.toml` kaldı |
