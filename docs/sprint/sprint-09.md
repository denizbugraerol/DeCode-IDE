# Sprint 09 — Ayar dosyası ve :reload
**Tarih:** 31 Ağu 2026 · **Durum:** Tamamlandı · **Commit(ler):** `ace155a` ayar dosyası yükleyicisi, `6e4e688`/`b223076` stylesheet paletten üretiliyor, `c13cfe5` kalan renkler paletle, `a7f030c` ayarlar pencereye uygulanıyor, `430e455` font/sekme/satır no, `58c83c6` terminal satır sayısı, `a88ff46` `:reload`, + bu commit (Görev 8: belgeler ve regresyon testi)

## Hedef
Faz 3'ün "ayar dosyası" maddesini kapatmak: `~/.config/decode/config.toml` ile renk paleti, font, sekme genişliği ve terminal satır sayısının özelleştirilebilmesi; `:reload` ile bunların uygulamayı kapatmadan yeniden uygulanması.

## Çıktılar
- [x] `core/config.py`: TOML okuma/doğrulama/varsayılan üretimi/şablon yazımı (`load`, `parse`, `default_settings`, `ensure_exists`, `config_path`) — Qt'den bağımsız, doğrudan test edilebilir
- [x] `ui/theme.py`: 17 renk tokenlı `DEFAULT_PALETTE` + modül düzeyinde `_current` palet (`color`, `set_palette`, `build_palette`); `stylesheet()` QSS'i `string.Template` ile üretiyor; `tests/test_no_hardcoded_colors.py` sabit renk sızıntısına karşı bekçi
- [x] `IDEWindow(settings=...)`: açılışta ayar dosyası okunuyor (dosya main.py'de oluşturuluyor), palet/QSS/editörler/terminale dağıtılıyor (`apply_settings`)
- [x] `ModalEditor.apply_settings`: `font_family`/`font_size` (QSS üzerinden), `tab_width` (boşluk genişliğine göre piksele çevrilerek), `expand_tabs`, `line_numbers`
- [x] `TerminalPanel.apply_settings`: `rows` — panel yüksekliği ve PTY birlikte yeniden boyutlanıyor
- [x] `:reload` komutu (`IDEWindow.reload_settings`): dosyayı yeniden okuyup paleti/QSS'i/editörleri/terminali yeniden uyguluyor; açık sekmeler, imleçler ve terminal oturumları korunuyor
- [x] Roadmap Faz 3: ayar dosyası tamamlandı olarak işaretlendi, navigasyon kararı (ok tuşları kalıcı) yazıldı, teknik borç tablosu ve "Bugünkü durum" güncellendi — `docs/Roadmap.md`
- [x] `CLAUDE.md`: mimari listesine `core/config.py`/`ui/theme.py`, "Modal editing model"e `:reload`, yeni "Settings" bölümüne navigasyon kararı ve `IDEWindow(settings=None)` sözleşmesi eklendi
- [x] `:reload`'un renklendirici/arama-vurgusu yeniden kurma adımı için regresyon testi (kontrolör kararı, Görev 7 incelemesinden devretti) — `tests/test_settings_reload.py`
- [x] 40 yeni test (72 → 112) — `tests/test_config.py`, `tests/test_theme.py`, `tests/test_no_hardcoded_colors.py`, `tests/test_editor_settings.py`, `tests/test_settings_reload.py`

## Teknik notlar
- Palet (`ui/theme._current`) bilinçli olarak modül düzeyinde tek bir sözlük: tema gerçekten global bir kavram ve bileşenler rengi boyama anında `theme.color(token)` ile okuduğu için `:reload` paleti beş ayrı yapıcıya elden geçirmek zorunda kalmıyor. İstisna `QTextCharFormat`: sözdizimi renklendiricisinin kuralları ve arama eşleşmesi vurgusu rengi bu nesnelere kopyalanıyor, palet değişince kendiliğinden güncellenmiyor — `reload_settings` bunları `set_highlighter_for_file(..., force=True)` ve `_highlight_matches()` ile elle yeniden kuruyor. Bu iki çağrıdan biri düşerse 112 testin hepsi yeşil kalırdı, kod yalnızca stylesheet'te değişirdi; Görev 8'in regresyon testi tam olarak bunu kanıtlıyor (bkz. `tests/test_settings_reload.py`).
- `bool`, Python'da `int`'in alt sınıfı olduğu için `font_size = true` düz bir `isinstance(value, int)` denetimini geçer; `core/config._validated` bu yüzden `bool` durumunu ayrıca ve önce eliyor.
- Font'u QSS sahipleniyor, `setFont` değil: editörün ailesi/boyutu stylesheet'ten geliyor. `ModalEditor.apply_settings` fontu yalnızca sekme genişliğini piksele çevirmek için okuyor, o da `ensurePolished()` çağrısından SONRA — sıra (önce stylesheet, sonra editör ayarları, ölçümden önce polish) bozulursa sekme genişliği sessizce yanlış hesaplanır.
- Ev dizinine yalnız `main.py` yazıyor (`config.ensure_exists`); `IDEWindow(settings=...)` parametresi bunun için var. Testler (`tests/conftest.py`'deki `pencere` fixture'ı ve diğer tüm testler) hep açık `config.default_settings()` veriyor — aksi halde geliştiricinin gerçek `~/.config/decode/config.toml` dosyasına bağımlı kalırlardı.
- **Davranış değişikliği (bilinçli):** sekme genişliği artık 4 karakter; bugüne kadar Qt'nin 80 piksellik varsayılanı yürürlükteydi.
- **Navigasyon kararı (kullanıcı, bu sprintte):** Ok tuşları kalıcı olarak korunuyor — `ModalEditor.handle_normal_mode`'daki `nav_keys` denetimi değiştiriciden bağımsız olarak zaten böyle çalışıyordu (Ok/Home/End/PageUp/PageDown gezinir, Shift+Ok seçer, Ctrl+Ok kelime atlar). `h/j/k/l`, `w/b`, `gg`/`G` gibi harf tabanlı hareket komutları bilinçli olarak uygulanmayacak. Bu karar için kod değişikliği yok, yalnızca Roadmap düzeltmesi (Görev 8).

## Devreden
Faz 3'ün ayar dosyası maddesi kapandı; kalanlar: düzenleme komutları (`dd`, `yy`, `x`, `o`/`O`, sayı önekleri — navigasyondan bağımsız, ayrıca ele alınacak), VISUAL mod, Vim tarzı geri al/yinele + `.` ile son komutu tekrar, oturum geri yükleme (son açık sekmeler ve çalışma dizini). Kabul edilmiş sınırlar: dosya izleme yok (kayıttan sonra `:reload` gerekiyor), aynı süreçte iki farklı temalı pencere açılamıyor (palet modül düzeyinde tek ve global).
