# DeCode IDE — Yol Haritası

## Vizyon

DeCode IDE, Vim'in modal giriş modelini PyQt6'nın hafifliğiyle birleştiren bir
editör. Uzun vadeli hedef, gömülü (PlatformIO) geliştirme için gereken her şeyi
— kod, terminal, derleme, seri monitör — tek pencerede toplayan bir IDE olmak.
İki değişmez ilke: **her şey klavyeden yönetilebilir** ve **arayüz Tokyo Night
paletine sadık kalır**.

Geçmiş işlerin ayrıntısı için [sprint günlüğüne](sprint/README.md) bakın.

## Bugünkü durum — v0.1

Çalışan özellikler:

- **Modal editör** — NORMAL / INSERT / COMMAND modları, imleç genişliğiyle mod
  göstergesi, satır numarası gutter'ı ([Sprint 02](sprint/sprint-02.md), [04](sprint/sprint-04.md))
- **Gerçek `:` komut satırı** — ekranın ortasında yüzen kutu, Enter'la çalışan
  komutlar, Tab/Shift+Tab tamamlama, kaydırılabilir öneri listesi
  ([Sprint 03](sprint/sprint-03.md), [05](sprint/sprint-05.md))
- **Komutlar** — `i`, `:w`, `:d`, `:b`, `:y`, `:p`, `:cd <yol>`, `:42`, `:q`, `:wq`,
  `:qa`, `:wqa`, `:tabnew`, `:tabclose`, `:tabnext`, `:tabprev`, `:term`, `:termnew`
- **Çoklu sekme** — her sekmenin kendi editörü ve modu, `●` ile kaydedilmemiş
  değişiklik göstergesi ([Sprint 05](sprint/sprint-05.md))
- **Gömülü terminal** — gerçek PTY üzerinde `pyte` ile çizilen, sekmeli shell
  paneli; Alt+Shift kısayollarıyla yönetiliyor ([Sprint 05](sprint/sprint-05.md))
- **Dosya ağacı** — CWD'ye köklenmiş sidebar, `:cd` ile kök değiştirme, Esc ile
  odağı editöre döndürme ([Sprint 01](sprint/sprint-01.md), [02](sprint/sprint-02.md))
- **Sözdizimi renklendirme** — C/C++ ve Python (çok satırlı docstring dahil)

Henüz yok: dosya arama, dosya içi arama/değiştirme, Vim hareket komutları,
ayar dosyası, PlatformIO/seri monitör entegrasyonu, test altyapısı.

## Faz 2 — Arama ve gezinme (sıradaki)

Bugün bir dosyayı açmanın tek yolu sidebar'da tıklamak; proje büyüdükçe bu
yavaşlıyor. Faz 2'nin amacı klavyeyle hedefe gitmek.

- **Telescope / bulanık dosya arama (`:ts`)** — `ui/components/command_palette.py`
  bugün boş bir yer tutucu; `IDEWindow.open_telescope_search` yalnızca `print`
  ediyor. `CommandSuggestions`'daki yüzen liste deseni yeniden kullanılacak.
- **Dosya içi arama** (`/` ile ileri, `n`/`N` ile sonraki eşleşme) ve
  **değiştirme** (`:s/eski/yeni/`) — `StateMachine` üzerinden.
- **`:e <yol>`** ile doğrudan dosya açma; `:cd` tamamlamasındaki yol
  tamamlaması (`_path_matches_for`) burada da kullanılacak.
- **Sembol/satır atlama** — açık dosyadaki fonksiyon/sınıf tanımlarına atlama.

## Faz 3 — Editör olgunluğu

Editörün "günlük sürücü" olabilmesi için eksik olan Vim refleksleri ve
kişiselleştirme.

- Hareket ve düzenleme komutları: `h/j/k/l`, `w/b`, `gg`/`G`, `dd`, `yy`, `x`,
  `o`/`O` ve sayı önekleri (`3dd`) — bugün navigasyon Qt'nin ok tuşlarına
  bırakılmış durumda.
- Görsel (VISUAL) mod ve seçim üzerinde işlem.
- Geri al/yinele için Vim tarzı davranış ve `.` ile son komutu tekrar.
- **Ayar dosyası** (`~/.config/decode/config.toml` gibi): tema, font, sekme
  genişliği, satır numarası açık/kapalı — bugün hepsi kodda sabit.
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
| `__pycache__` deposu kirletiyor | 11 `.pyc` dosyası takip ediliyor; `.gitignore`'da kural yok | `.gitignore` |
| Test ve lint altyapısı yok | Doğrulama şimdilik elle / offscreen betiklerle | — |
| `CLAUDE.md` güncel değil | Tuş tamponu modelini anlatıyor; sekmeler ve terminal yok | `CLAUDE.md` |
| Boş yer tutucular | `command_palette.py`, `pio_cli.py`, `serial_reader.py` | Faz 2 ve Faz 4 |
| Tema kodda sabit | Renkler `IDEWindow._apply_theme` içinde string olarak | Faz 3 |

## Sürüm kilometre taşları

Tarih verilmiyor; sıra ve çıkış kriteri veriliyor.

| Sürüm | Kapsam | Çıkış kriteri |
|---|---|---|
| **v0.1** (bugün) | Faz 0–1 | Python/C++ dosyaları pencereden çıkmadan düzenlenip kaydedilebiliyor, terminal içeride |
| **v0.2** | Faz 2 | `:ts` ile dosya bulunuyor, dosya içi arama/değiştirme çalışıyor |
| **v0.3** | Faz 3 | Temel Vim hareketleri + ayar dosyası; oturum geri yükleniyor |
| **v0.4** | Faz 4 | PlatformIO derle/yükle/monitör tek komutla; seri monitör açılıyor |
| **v1.0** | Faz 5 | Kurulabilir paket ve belgelenmiş komut/kısayol referansı |
