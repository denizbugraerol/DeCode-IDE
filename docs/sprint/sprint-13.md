# Sprint 13 — Kısayol yapılandırması
**Tarih:** 09 Eyl 2026 · **Durum:** Tamamlandı · **Commit(ler):** `27d8f57` saf tuş haritası çekirdeği — eylem tablosu ve parse(), `f06fcda` Keymap, build() ve çakışma çözümü (ilk gelen kazanır), `88257c3` QKeyEvent → bağlama çeviren ince Qt kabuğu, `2075419` ayar dosyasına [shortcuts] bölümü, `c3eb767` editör tuş dağıtımı haritadan geçiyor, `e2fd8a7` terminal tuş dağıtımı haritadan geçiyor, `7040b22` karşılama sayfası tuş haritasını kullanıyor ve gösteriyor, `16c1ccf` tuş haritası apply_settings'ten dağıtılıyor, + bu commit (Görev 9: belgeler)

## Hedef
Kısayollar ayar dosyasından özelleştirilebilir hale geldi.

## Çıktılar
- [x] `core/keymap.py`: 10 eylemlik `ACTIONS` tablosu (ad, grup, varsayılan, açıklama), `parse`/`build`/`defaults`, `Keymap` (`binding_of`, `action_for`, `label`) — saf Python, Qt'siz
- [x] İlk-gelen-kazanır çakışma çözümü (`Keymap.__init__`): iki eylem aynı tuşa düşerse `ACTIONS` sırasında önce gelen kazanır, kaybeden için açılışta bir uyarı basılır
- [x] `ui/keys.py`: `QKeyEvent`'i keymap'in bağlama biçimine çeviren ince Qt kabuğu (`panel_binding`, `normal_binding`, `match`)
- [x] `core/config.py`: `[shortcuts]` bölümü doğrulaması — yalnız "boş olmayan dize" denetler, eylem adı/tuş geçerliliği `keymap.build`'in işi (`[colors]`/`build_palette` ile aynı ayrım)
- [x] Üç widget'ın tuş dağıtımı haritadan geçiyor, hepsi `apply_keymap(keymap)` alıyor: `ui/components/code_editor.py` (`ModalEditor`), `ui/components/terminal_panel.py` (`TerminalView`), `ui/components/welcome_page.py` (`WelcomePage`)
- [x] Karşılama sayfası ipuçları artık keymap'ten üretiliyor (`WelcomePage._refresh_hints`, `Keymap.label`) — sabit metin değil
- [x] `IDEWindow.apply_settings`: haritayı kuruyor (`keymap.build(settings["shortcuts"])`) ve üç widget'a dağıtıyor; açılış ve `:reload` tek yoldan geçtiği için canlı yeniden atama ayrıca bir iş gerektirmiyor
- [x] 58 yeni test (211 → 269) — `tests/test_keymap.py`, `tests/test_shortcut_config.py`, `tests/test_config.py` ekleri
- [x] README / CLAUDE.md / Roadmap belgeleri güncellendi (bu görev)
- [x] Yeşil CI (Linux ve macOS: 273/273) ve v0.3.0 sürümü — macOS'ta ortaya
      çıkan kapanış kilidi sürüm öncesi düzeltildi (bkz. CHANGELOG v0.3.0)

## Teknik notlar
- **K6'nın gerekçesi.** Panel kısayolları her modda ve mod dağıtımından ÖNCE
  okunuyor; değiştiricisiz bir bağlama (`tab_new = "i"`) o harfi INSERT
  modunda yazılamaz hale getirirdi. Shift tek başına da yetmez —
  `tab_new = "shift+n"` bağlanabilseydi INSERT modunda `N` yazılamazdı. Bu
  yüzden panel bağlaması `ctrl`/`alt`/`meta`'dan en az birini içermek
  ZORUNDA; NORMAL mod bağlaması ise tam tersi, hiçbir değiştirici öneki
  ALAMAZ (Shift zaten karakterin kendisinde — `n` ≠ `N`).
- **K3'ün kabul edilen bedeli.** Çakışmaya izin veriliyor: iki eylem aynı
  tuşa düşerse `ACTIONS` sırasında önce gelen kazanır, kaybeden sessizce
  ölmüyor ama nedeni yalnız açılış uyarısında görünüyor
  (`shortcuts.<eylem>: <tuş> zaten <kazanan> eylemine bağlı; bu kısayol
  çalışmayacak.`). K6+K7 bu bedeli sınırlıyor: paneldeki-değiştiricili /
  normaldeki-çıplak ayrımı gruplar arası çakışmayı imkânsız kılıyor, çakışma
  en fazla aynı grup içinde ve en fazla bir kısayolu öldürür.
- **İki grubun büyük/küçük harf asimetrisi.** Panel dağıtımı `event.key()`
  ile yapılır ve Qt tuş kodu harf büyüklüğü taşımaz, o yüzden tuş adı küçük
  harfe indirilir (`alt+shift+T` ile `alt+shift+t` AYNI bağlamadır). NORMAL
  grubu `event.text()` ile çalışır ve harf büyüklüğü olduğu gibi korunur
  (`n` ile `N` FARKLI bağlamadır) — `search_next`/`search_prev`'in ayrı
  eylemler olarak kalabilmesinin nedeni bu.
- **Kayma bekçisi.** `core/keymap.NAMED_KEYS` ile `ui/keys._QT_NAMED_KEYS`
  iki ayrı tablo; biri güncellenip öteki unutulursa isimli bir tuş (ör.
  `pagedown`) sessizce çözülmez hale gelirdi.
  `tests/test_shortcut_config.test_isimli_tus_tablolari_ortusuyor` iki
  tabloyu karşılaştırarak bunu bekçiliyor.
- Test yazarken bir plan düzeltmesi gerekti (`b30824e`): `QTest.keyClick`'in
  `text=` anahtar sözcüğü PyQt6 6.11'de yok; Qt, değiştiricisiz bir harf
  tuşu için `text()`'i zaten kendisi üretiyor, olay aynı kalıyor — düzeltme
  yalnızca test çağrısında kaldı.

## Devreden
Tam tuş haritasını gösteren bir `:keys` komutu tasarım aşamasında kapsam
dışı bırakıldı, sonraki sprinte kaldı (bu sprintte yalnız karşılama sayfası
ipuçları keymap'ten üretilmeye başladı, ayrı bir komut değil). Kabul
edilmiş kalıcı sınırlar: çok tuşlu diziler/chord'lar (`g g`, `Ctrl+K
Ctrl+S`) desteklenmiyor, harita küresel (sekme/dosya türü başına ayrı
harita yok), terminalin kendi tuş çevirisi (`TerminalView._KEY_SEQUENCES`)
yapılandırılamaz, ve grafik bir kısayol düzenleyici yok — yalnız ayar
dosyası.
