# DeCode IDE — Yol Haritası

## Vizyon

DeCode IDE, Vim'in modal giriş modelini PyQt6'nın hafifliğiyle birleştiren bir
editör. Uzun vadeli hedef, gömülü (PlatformIO) geliştirme için gereken her şeyi
— kod, terminal, derleme, seri monitör — tek pencerede toplayan bir IDE olmak.
İki değişmez ilke: **her şey klavyeden yönetilebilir** ve **arayüz Tokyo Night
paletine sadık kalır**.

Geçmiş işlerin ayrıntısı için [sprint günlüğüne](sprint/README.md) bakın.

## Bugünkü durum — v0.2

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
- **Dosya ağacı** — CWD'ye köklenmiş sidebar, `:cd` ile kök değiştirme, Esc ile
  odağı editöre döndürme ([Sprint 01](sprint/sprint-01.md), [02](sprint/sprint-02.md))
- **Sözdizimi renklendirme** — C/C++ ve Python (çok satırlı docstring dahil)
- **Ayar dosyası** (`~/.config/decode/config.toml`) — renk paleti (17 token),
  font ailesi/boyutu, sekme genişliği, `expand_tabs`, satır numarası açık/kapalı
  ve terminal satır sayısı özelleştirilebiliyor; `:reload` uygulamayı
  kapatmadan yeniden uyguluyor ([Sprint 09](sprint/sprint-09.md))
- **Test altyapısı** — pytest, `QT_QPA_PLATFORM=offscreen` ile ekransız çalışan
  112 test ([Sprint 06](sprint/sprint-06.md), [09](sprint/sprint-09.md))

Henüz yok: Vim tarzı düzenleme komutları (`dd`, `yy`, `x`, `o`/`O`, sayı
önekleri), VISUAL mod, geri al/yinele + `.` ile son komutu tekrar, oturum geri
yükleme, PlatformIO/seri monitör entegrasyonu, lint. Harf tabanlı hareket
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

- **`embedded/pio_cli.py`** — PlatformIO CLI sarmalayıcısı: `build`, `upload`,
  `clean`, `monitor`. Çıktı, mevcut terminal paneline (`TerminalPanel`) yeni bir
  sekme olarak akacak; ayrı bir çıktı penceresi yazılmayacak.
- **Komutlar** — `:pio build`, `:pio upload`, `:pio monitor`; öneri listesine
  ve tamamlamaya eklenecek.
- **`embedded/serial_reader.py`** — seri monitör: port/baud seçimi, gelen
  veriyi terminal sekmesi gibi çizme.
- **Kart ve port seçimi** — `platformio.ini` okunarak ortamların listelenmesi.
- **Derleme hatasından koda atlama** — çıktıdaki `dosya:satır` eşleşmelerini
  yakalayıp ilgili sekmede o satıra gitme.

## Faz 5 — Dağıtım

- `pyproject.toml` ile kurulabilir paket ve `decode` komutu.
- Linux masaüstü girdisi (`.desktop`) ve uygulama ikonu.
- Sürüm etiketleri + kısayol/komut referansının `docs/` altında belgelenmesi.

## Teknik borç

| Konu | Durum | Nerede |
|---|---|---|
| `__pycache__` deposu kirletiyor | Çözüldü ([Sprint 06](sprint/sprint-06.md)): kural eklendi, 14 `.pyc` takipten çıkarıldı | `.gitignore` |
| Lint altyapısı yok | Test var (112 test, pytest); lint/format aracı hâlâ seçilmedi | — |
| `CLAUDE.md` güncel değil | Çözüldü ([Sprint 07](sprint/sprint-07.md)): komut satırı modeli, sekmeler, terminal ve Faz 2 modülleri yazıldı | `CLAUDE.md` |
| Boş yer tutucular | `pio_cli.py`, `serial_reader.py` | Faz 4 |
| Bulanık skorlama açgözlü | Soldan ilk eşleşmeyi alır, en iyi hizalamayı aramaz | `core/fuzzy.py` |
| C/C++ sembol çıkarma sezgisel | Çok satıra yayılan imzalar kaçabilir | `core/symbols.py` |
| `forkpty()` çok iş parçacıklı süreçte | `:ts` taraması sürerken `:term` açmak uyarı üretiyor | `core/terminal_process.py` |
| Tema kodda sabit | Çözüldü ([Sprint 09](sprint/sprint-09.md)): renkler `ui/theme.py`'deki tek palete taşındı, ayar dosyasının `[colors]` bölümünden özelleştirilebiliyor | `ui/theme.py` |

## Sürüm kilometre taşları

Tarih verilmiyor; sıra ve çıkış kriteri veriliyor.

| Sürüm | Kapsam | Çıkış kriteri |
|---|---|---|
| **v0.1** | Faz 0–1 | Python/C++ dosyaları pencereden çıkmadan düzenlenip kaydedilebiliyor, terminal içeride |
| **v0.2** (bugün) | Faz 2 | `:ts` ile dosya bulunuyor, dosya içi arama/değiştirme çalışıyor |
| **v0.3** | Faz 3 | Düzenleme komutları (`dd`/`yy`/`x`/`o`/`O`) + VISUAL mod; ayar dosyası ✅ (Sprint 09), oturum geri yükleniyor |
| **v0.4** | Faz 4 | PlatformIO derle/yükle/monitör tek komutla; seri monitör açılıyor |
| **v1.0** | Faz 5 | Kurulabilir paket ve belgelenmiş komut/kısayol referansı |
