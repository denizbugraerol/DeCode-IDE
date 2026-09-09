# Kısayol Yapılandırması (Faz 3 / Sprint 13) — Tasarım

**Tarih:** 09 Eyl 2026 · **Durum:** Onay bekliyor · **Faz:** 3 — Editör olgunluğu

## Hedef

Kullanıcı kendi tuş haritasını `~/.config/decode/config.toml`'un yeni
`[shortcuts]` bölümünden belirlesin. Kapsam iki grup:

- **panel grubu** (her modda, odağın bulunduğu yere uygulanır): `terminal_focus`,
  `tab_new`, `tab_close`, `tab_next`, `tab_prev`.
- **normal grubu** (yalnız NORMAL modda, çıplak tuşlar): `insert_mode`,
  `command_line`, `search_next`, `search_prev`, `clear_search`.

Dosya yoksa ya da `[shortcuts]` boşsa bugünkü tuşlar birebir korunur — bu iş
varsayılan tuş haritasını **değiştirmiyor**, yalnız değiştirilebilir kılıyor.

İkincil ama bedava gelen kazanç: bugün `_PANEL_MODIFIERS` dört dosyada, aynı
`{Qt.Key.Key_T: ...}` sözlüğü üç dosyada kopyalanmış durumda
(`ui/components/code_editor.py`, `ui/components/terminal_panel.py`,
`ui/components/welcome_page.py`). Bu iş o tekrarı tek kaynağa indiriyor.

## Kapsam dışı

- **Terminalin kendi tuş çevirisi.** `TerminalView._KEY_SEQUENCES` (Enter,
  Backspace, oklar → ANSI dizileri) shell'in malı; yapılandırılabilir olmayacak.
- **Komut adları.** `:find`, `:openfile`, `:replace` gibi sözcük komutları bu
  bölümün konusu değil; onlar `core/state_machine.py`'de kalır.
- **Çok tuşlu diziler / chord'lar** (`g g`, `Ctrl+K Ctrl+S`). Her bağlama tek
  bir tuş kombinasyonudur.
- **Harf tabanlı hareketler** (`h/j/k/l`, `w/b`, `gg`). Roadmap'te kalıcı
  hedef-dışı; yapılandırılabilir hale getirmek onları geri getirmez.
- **Sekme başına / dosya türüne göre tuş haritası.** Tek küresel harita.
- **Grafik kısayol düzenleyici.** Yalnız ayar dosyası.
- **`:keys` komutu.** Karşılama sayfası ipuçları keymap'ten üretilecek (K4);
  tam tuş haritasını gösteren ayrı bir komut sonraki sprinte bırakıldı.

## Kararlar

| # | Karar | Gerekçe |
|---|---|---|
| K1 | Kapsam: panel ailesi **+** NORMAL mod çıplak tuşları | Sahibinin seçimi. Modal çekirdek (`i`, `:`, `n`, `N`, Esc) ürünün kimliği; kas hafızasına göre değiştirilebilmesi bu işin asıl değeri. Terminal tarafı dışarıda (yukarı bkz.) |
| K2 | `ctrl`'e **izin verilir**, varsayılanlar **değişmez** | Sahibinin seçimi. "Ctrl kısayolu kullanılmaz" projenin varsayılan kimliği olarak kalır; ayrıştırıcı buna teknik bir engel koymaz. README/CLAUDE.md cümlesi "varsayılanda Ctrl kullanılmaz" olarak düzeltilir |
| K3 | Çakışmaya **izin verilir**; sabit `ACTIONS` sırasında **ilk gelen kazanır**, kaybeden için uyarı basılır | Sahibinin seçimi. Kabul edilen bedel: çakışmada ölen kısayolun nedeni yalnız açılış uyarısında görünür. K6+K7 bu bedeli gruplar arası çakışmayı imkânsız kılarak sınırlıyor |
| K4 | Karşılama sayfası ipuçları keymap'ten **üretilir** | Sahibinin seçimi. Sabit `HINTS` listesi kısayol değişince yalan söylerdi |
| K5 | Saf `core/keymap.py` + ince Qt kabuğu `ui/keys.py` | CLAUDE.md'nin kuralı ("gerçek mantık saf `core/` modülünde, Qt katmanı ince kabuk"); `fuzzy`, `search`, `symbols`, `config` ile aynı desen. Değerlendirilen alternatifler: **`QKeySequence`/`QShortcut`** — NORMAL mod tuşlarını hiç kapsayamaz (INSERT modunda da ateşler, `i` yazılamaz hale gelir) ve macOS'ta "Ctrl"ü Command'a çevirir; **ayrı modül yok** — bugünkü üçlü tekrarı kalıcılaştırır ve doğrulama mantığını Qt'ye bağlı testlere hapseder |
| K6 | **Panel bağlaması `ctrl`, `alt` ya da `meta`'dan en az birini içermek zorundadır** | Panel kısayolları her modda ve mod dağıtımından **önce** okunur. `tab_new = "i"` yazılabilseydi INSERT modunda `i` harfi yazılamaz hale gelirdi; `tab_new = "shift+n"` yazılabilseydi `N` yazılamazdı. Kural aynı zamanda K3'ü güvenli kılar: gruplar arası çakışma imkânsızlaşır, çakışma grup içinde kalır ve en fazla bir kısayolu öldürür — asla yazmayı bozmaz. **Sahibinin gözden geçirmesi istenen kural budur** |
| K7 | Normal bağlaması **tek karakter** ya da `escape`; değiştirici öneki reddedilir | K6'nın karşılığı. Shift zaten karakterin kendisinde (`n` ≠ `N`). `alt+i` gibi bir şey istenseydi `handle_normal_mode`'un dağıtım kapısını da değiştirmek gerekirdi — ayrı ve daha büyük bir iş |
| K8 | `core/config.py` yalnız "boş olmayan dize" doğrular; eylem adı ve tuş adı geçerliliği `core/keymap.py`'nin işidir | `[colors]` ile birebir aynı ayrım: config token *adlarını* bilmez, yalnız `#rrggbb` biçimine bakar; token geçerliliği `ui/theme.build_palette`'in işidir. Aynı sınırı burada da koruyoruz |
| K9 | Keymap dağıtımı **yalnız** `IDEWindow.apply_settings()` üzerinden | Açılış ve `:reload` tek yoldan geçiyor (sprint-09 kararı). Keymap de aynı yoldan dağıtılırsa `:reload` ile canlı yeniden atama bedavaya gelir |
| K10 | Bu iş **Sprint 13** olur | Aktif sprint yok; son iş Sprint 12 |

## Mimari

Yeni iki modül, üç widget'ta dağıtım noktası, bir config bölümü.

```
core/keymap.py   (saf, Qt yok)      ← eylem tablosu, ayrıştırma, doğrulama, etiket
        ↑
ui/keys.py       (ince Qt kabuğu)   ← QKeyEvent → (değiştiriciler, tuş adı)
        ↑
ModalEditor / TerminalView / WelcomePage
        ↑
IDEWindow.apply_settings()          ← keymap.build(settings["shortcuts"])
```

### `core/keymap.py` (saf Python, Qt yok)

```python
Action = namedtuple("Action", "name group default description")

ACTIONS = (   # SIRA ANLAMLI: çakışmada önce gelen kazanır (K3)
    Action("terminal_focus", "panel",  "alt+shift+t",     "odağı terminale/editöre taşı"),
    Action("tab_new",        "panel",  "alt+shift+n",     "yeni sekme"),
    Action("tab_close",      "panel",  "alt+shift+w",     "sekmeyi kapat"),
    Action("tab_next",       "panel",  "alt+shift+right", "sonraki sekme"),
    Action("tab_prev",       "panel",  "alt+shift+left",  "önceki sekme"),
    Action("insert_mode",    "normal", "i",               "INSERT moduna geç"),
    Action("command_line",   "normal", ":",               "komut satırını aç"),
    Action("search_next",    "normal", "n",               "sonraki eşleşme"),
    Action("search_prev",    "normal", "N",               "önceki eşleşme"),
    Action("clear_search",   "normal", "escape",          "arama vurgusunu temizle"),
)

MODIFIERS      = ("ctrl", "alt", "shift", "meta")
PANEL_REQUIRED = ("ctrl", "alt", "meta")          # K6
NAMED_KEYS     = ("right", "left", "up", "down", "escape", "tab", "space",
                  "home", "end", "pageup", "pagedown", "backspace", "delete",
                  "return", "f1"–"f12")
```

**Bağlama gösterimi** her iki grupta da aynı biçim: `(frozenset(değiştirici
adları), tuş adı)`. Normal grubunda değiştirici kümesi her zaman boştur ve tuş
adı yazıldığı gibi tek karakter (ya da `"escape"`).

Gruplar arasında **bilinçli bir asimetri** var ve testle sabitlenecek:

- **panel** tuş adı küçük harfe indirilir — dağıtım `event.key()` ile karşılaştırıyor,
  `Qt.Key` büyük/küçük harf bilmez. `alt+shift+T` ile `alt+shift+t` **aynı** bağlamadır.
- **normal** tuş adı olduğu gibi korunur — dağıtım `event.text()` ile
  karşılaştırıyor. `n` ile `N` **farklı** bağlamadır (bugünkü davranış).

Genel arayüz:

| Ad | Döner | İş |
|---|---|---|
| `parse(value, group)` | `(bağlama, hata_metni)` | Tek bir dizeyi ayrıştırır ve gruba göre doğrular (K6/K7). Hata varsa bağlama `None` |
| `build(user_values)` | `(Keymap, uyarılar)` | Varsayılanların üstüne kullanıcı değerlerini bindirir; bilinmeyen eylem / geçersiz bağlama / çakışma uyarılarını üretir |
| `defaults()` | `Keymap` | Varsayılan harita. Widget'lar `__init__`'te bunu alır, böylece `apply_keymap` çağrılmadan da çalışırlar |

`Keymap` iki yönü birden tutar:

- `binding_of(action)` — etiket ve ipuçları için,
- `action_for(group, binding)` — dağıtım için. Ters tablo `ACTIONS` sırasında
  `setdefault` ile kurulur; **ilk gelen kazanır** (K3) ve kaybeden için `build`
  bir uyarı üretir,
- `label(action)` — `"Alt+Shift+T"`, `"Ctrl+T"`, `"Alt+Shift+→"`, `"i"`, `"Esc"`.
  Değiştirici sırası sabit: Ctrl, Alt, Shift, Meta.

### `ui/keys.py` (ince Qt kabuğu)

Tek işi `QKeyEvent`'i `core.keymap`'in ürettiğiyle **aynı** biçime çevirmek:

- `panel_binding(event)` → `(frozenset(değiştirici adları), tuş adı)` ya da `None`.
  Harf/rakamlar tablosuz çözülür (`Qt.Key.Key_A == ord("A")`); isimli tuşlar
  `_QT_NAMED_KEYS` sözlüğünden.
- `normal_binding(event)` → Escape ise `(frozenset(), "escape")`; değilse
  `event.text()` doluysa ve değiştirici yok/yalnız Shift ise `(frozenset(), text)`.
- `match(event, keymap, group)` → eylem adı ya da `None`.

`keymap.NAMED_KEYS` ile `ui.keys._QT_NAMED_KEYS` arasındaki kaymayı bir bekçi
testi kapatır (iki yönlü: her adın bir `Qt.Key` karşılığı var ve fazlası yok).

**macOS notu:** adlar Qt değiştiricilerine birebir eşlenir; `ctrl` →
`ControlModifier`, `meta` → `MetaModifier`. Qt macOS'ta bu ikisini fiziksel
olarak takas eder (`ControlModifier` = Command). Takası taklit **etmiyoruz** —
`QKeySequence`'in sessizce yaptığı çeviri K5'te bu yüzden reddedildi. Belgeye
bir cümle olarak yazılır.

### Widget'lar

Üçünde de aynı iki satır; fark yalnız eylem → sinyal tablosunda:

```python
action = keys.match(event, self._keymap, "panel")
if action is not None:
    self._PANEL_SIGNALS[action].emit(); return
```

| Widget | Panel eylem → sinyal | Normal grubu |
|---|---|---|
| `ModalEditor` | `terminal_focus_requested`, `tab_new_requested`, `tab_close_requested`, `tab_next_requested`, `tab_prev_requested` | tamamı |
| `TerminalView` | `return_focus_requested`, `new_tab_requested`, `close_tab_requested`, `next_tab_requested`, `prev_tab_requested` | — |
| `WelcomePage` | `ModalEditor` ile aynı adlar | yalnız `command_line` |

`ModalEditor.handle_normal_mode` sırası korunur: önce `nav_keys` / Ctrl geçişi
(bunlar taban widget'a gider — Roadmap'teki kalıcı karar), sonra keymap
araması, sonra `event.ignore()`. **Escape tuzağı kendiliğinden çözülüyor:**
Escape artık `event.text()` (`\x1b`) üzerinden değil, `"escape"` tuş adı
üzerinden eşleşiyor; yine de "yazılabilir tuş dalından önce" yorumu korunur.

`StateMachine.handle_normal_key(event)` → `handle_normal_action(action)` olur;
`if text == "i" / ":" / "n" / "N"` zinciri eylem adına göre dağıtıma dönüşür.
`clear_search` editörün kendi durumu olduğu için `ModalEditor`'de kalır.

`WelcomePage.HINTS` artık `(kind, değer, açıklama)` üçlüsü tutar; `kind`
`"command"` ise değer olduğu gibi (`":ts"`), eylem adıysa `keymap.label(...)`
ile üretilir. `apply_keymap` metni yeniden kurar, böylece `:reload` sonrası da
doğru kalır.

### Dağıtım zinciri

- `EditorTabs.apply_keymap(km)` — haritayı saklar, açık tüm editörlere uygular ve
  `new_tab()` yeni editöre verir. Bugün yeni sekmenin ayarları yalnız
  `_on_tab_count_changed` üzerinden geliyor; keymap için fabrikanın kendisi
  (`new_tab`) daha sağlam bir nokta.
- `TerminalPanel.apply_keymap(km)` — `_rows`/`_font` gibi saklanır ve
  `open_new_tab` / `run_command` ile açılan her `TerminalView`'e verilir.
- `WelcomePage.apply_keymap(km)`.
- `IDEWindow.apply_settings()` üçünü de çağırır (K9), `build`'in uyarılarını
  `print` eder — palet ve font uyarılarıyla aynı desen.

### `core/config.py`

- `DEFAULTS["shortcuts"] = {}` (boş = varsayılan harita; `[colors]` ile aynı).
- `_merge_and_validate` içinde `shortcuts` bölümü `colors` gibi ayrı ele alınır:
  `_validated_shortcuts(values)` yalnız **boş olmayan dize** olmayan değerleri
  uyarıyla eler (K8).
- `TEMPLATE`'e yorumlu bir `[shortcuts]` bloğu eklenir: on eylemin tamamı
  varsayılan değerleriyle yorum satırı olarak, üstünde iki kuralı (K6/K7)
  anlatan iki satır.

## Hata yolları

Hepsi tek satır Türkçe uyarı; ilgili eylem varsayılanında kalır, dosyanın geri
kalanı uygulanır (`core/config.py`'nin kurulu deseni).

| Girdi | Uyarı |
|---|---|
| `shortcuts.tab_neww = "alt+t"` | `Bilinmeyen kısayol eylemi yok sayıldı: shortcuts.tab_neww` |
| `shortcuts.tab_new = 5` | `shortcuts.tab_new metin olmalı; yok sayıldı.` (config.py) |
| `shortcuts.tab_new = "alt+shift+q9"` | `shortcuts.tab_new: bilinmeyen tuş 'q9'; varsayılan kullanıldı (alt+shift+n).` |
| `shortcuts.tab_new = "hyper+n"` | `shortcuts.tab_new: bilinmeyen değiştirici 'hyper'; varsayılan kullanıldı (alt+shift+n).` |
| `shortcuts.tab_new = "i"` (K6) | `shortcuts.tab_new: panel kısayolu Ctrl, Alt ya da Meta içermeli; varsayılan kullanıldı (alt+shift+n).` |
| `shortcuts.tab_new = "shift+n"` (K6) | aynı uyarı |
| `shortcuts.insert_mode = "alt+i"` (K7) | `shortcuts.insert_mode: NORMAL mod kısayolu tek karakter ya da 'escape' olmalı; varsayılan kullanıldı (i).` |
| `shortcuts.tab_new = "alt+shift+w"` (K3) | `shortcuts.tab_close: alt+shift+w zaten tab_new eylemine bağlı; bu kısayol çalışmayacak.` |

## Test planı

Yeni: `tests/test_keymap.py` (saf, Qt yok) ve `tests/test_shortcut_config.py`
(Qt kabuğu + uçtan uca).

**`tests/test_keymap.py`** — `build`/`parse`/`label`, hiç Qt olmadan:

- Boş sözlük → varsayılan harita, uyarı yok; on eylemin tamamı var.
- `ACTIONS` içindeki her varsayılan kendi grubunun kurallarından geçiyor
  (K6/K7 varsayılanları ihlal etmiyor — kendi kuralımıza uyduğumuzun bekçisi).
- Geçerli yeniden atama: `{"tab_new": "ctrl+t"}` → bağlama değişti, uyarı yok,
  diğer dokuz eylem varsayılanda.
- Bilinmeyen eylem adı, bilinmeyen tuş, bilinmeyen değiştirici → uyarı + varsayılan.
- K6: `"i"` ve `"shift+n"` panel eyleminde reddedilir; `"ctrl+t"`, `"meta+t"`,
  `"alt+shift+right"` kabul edilir.
- K7: `"alt+i"` normal eyleminde reddedilir; `"escape"` ve tek karakter kabul edilir.
- Büyük/küçük harf asimetrisi: `alt+shift+T` == `alt+shift+t`; `n` != `N`.
- K3 çakışması: `{"tab_new": "alt+shift+w"}` → `tab_new` kazanır, `tab_close`
  bağsız kalır, tam olarak bir uyarı üretilir.
- `label()`: `alt+shift+t` → `Alt+Shift+T`, `alt+shift+right` → `Alt+Shift+→`,
  `escape` → `Esc`, `N` → `N`.

**`tests/test_shortcut_config.py`** — Qt tarafı, `pencere` fixture'ı üzerinden:

- **Kayma bekçisi:** `keymap.NAMED_KEYS` ile `ui.keys._QT_NAMED_KEYS` iki yönlü
  örtüşüyor.
- `keys.panel_binding` / `normal_binding` bilinen olayları doğru çeviriyor.
- Uçtan uca yeniden atama: `pencere.settings["shortcuts"]["tab_new"] = "ctrl+t"`
  → `apply_settings()` → `Ctrl+T` yeni sekme açıyor, `Alt+Shift+N` **artık
  açmıyor**. Aynısı terminal görünümünde ve karşılama sayfasında.
- NORMAL mod yeniden atama: `insert_mode = "a"` → `a` INSERT'e geçiriyor, `i`
  geçirmiyor; INSERT modunda `i` hâlâ **yazılabiliyor** (K6'nın koruduğu şey).
- `:reload` ile canlı yeniden atama (`config.config_path` monkeypatch'li,
  `tests/test_settings_reload.py`'deki desen) — yeni tuş anında çalışıyor.
- Karşılama sayfası ipuçları keymap'i yansıtıyor ve `:reload` sonrası tazeleniyor.
- Sonradan açılan sekme ve sonradan açılan terminal sekmesi güncel haritayı alıyor.

**Mevcut testler değişmeden geçmeli.** `tests/test_editor_shortcuts.py` ve
`tests/test_welcome_page.py` varsayılan tuşları kullanıyor; varsayılanlar
değişmediği için (K2) bu iki dosya bu işin regresyon bekçisidir.
`tests/test_config.py`'ye `[shortcuts]` için tür doğrulama vakaları eklenir.

## Elle doğrulama

1. Ayar dosyasına `[shortcuts]` yaz: `tab_new = "ctrl+t"`, `insert_mode = "a"`.
2. Uygulamayı aç → `Ctrl+T` yeni sekme açıyor, `Alt+Shift+N` açmıyor.
3. NORMAL modda `a` → INSERT; INSERT modunda `i` ve `a` **yazılabiliyor**.
4. Karşılama sayfası (`:q` ile son sekmeyi kapat) → ipuçlarında `Ctrl+T` yazıyor.
5. Terminali aç (`:term`), odağı terminale al → `Ctrl+T` orada yeni **terminal**
   sekmesi açıyor: komut, odağın bulunduğu yere uygulanır (bugünkü davranış).
6. Ayar dosyasını `tab_new = "i"` yapıp `:reload` → uyarı basılıyor, kısayol
   `alt+shift+n`'e dönüyor, `i` hâlâ INSERT'e geçiriyor.
7. `tab_new = "alt+shift+w"` yapıp `:reload` → çakışma uyarısı basılıyor,
   `Alt+Shift+W` yeni sekme açıyor, sekme kapatma kısayolu ölüyor (K3'ün kabul
   edilmiş bedeli).
8. `[shortcuts]` bölümünü tamamen sil, `:reload` → bugünkü tuşlar geri geliyor.

## Riskler

| Risk | Etki | Önlem |
|---|---|---|
| Panel kısayolu değiştiricisiz atanabilirse o harf INSERT modunda yazılamaz | Editör kullanılamaz hale gelir | K6 + "INSERT modunda `i` yazılabiliyor" regresyon testi |
| `keymap.NAMED_KEYS` ile `ui.keys` tablosu birbirinden kayar | Ayar dosyasında geçerli görünen tuş çalışmaz | İki yönlü kayma bekçisi testi |
| Çakışan atama bir kısayolu sessizce öldürür | Kullanıcı nedenini bulamaz | K3'ün bilinen bedeli; uyarı açılışta basılır, belgede yazılır |
| Yeni sekme / yeni terminal sekmesi eski haritayla açılır | Kısayol bazı sekmelerde çalışmaz | Harita fabrikada (`EditorTabs.new_tab`, `TerminalPanel.open_new_tab`) veriliyor + test |
| macOS'ta `ctrl`/`meta` fiziksel takası şaşırtır | Mac kullanıcısı yanlış tuşa basar | Takas taklit edilmiyor, belgeye yazılıyor |
| `StateMachine.handle_normal_key` imzası değişiyor | `WelcomePage` de bu yoldan geçiyor | İkisi de aynı commit'te; mevcut testler bekçi |

## Bu sprintten sonra

- `README.md` "Kısayollar" bölümü: tablo kalır, altına `[shortcuts]` ile
  değiştirilebildiği ve iki kural (K6/K7) yazılır; "Ctrl kısayolu bilinçli
  olarak kullanılmaz" → "varsayılanda kullanılmaz" (K2).
- `CLAUDE.md`: "Alt+Shift shortcuts … identical dict" paragrafı tek kaynağa
  göre, "No Ctrl shortcuts" cümlesi K2'ye göre güncellenir.
- `docs/Roadmap.md`: Faz 3 ayar dosyası maddesine `[shortcuts]` eklenir.
- `docs/sprint/sprint-13.md` açılır, `docs/sprint/README.md` tablosu güncellenir.
- Sonraki sprint adayı: tam tuş haritasını gösteren `:keys` komutu
  (`FloatingList` altyapısı hazır).

**Bu iş sırasında görülen, kapsam dışı bir kayma:** `CLAUDE.md`'nin Settings
bölümü `:reload` için `editor.set_highlighter_for_file(editor.file_path,
force=True)` diyor; kod artık `force` parametresi taşımıyor, karşılığı
`ModalEditor.refresh_theme()`. Ayrı bir belge düzeltmesi olarak not edildi.
