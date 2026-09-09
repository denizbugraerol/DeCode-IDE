# Kısayol Yapılandırması — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kullanıcı kendi tuş haritasını `~/.config/decode/config.toml`'un `[shortcuts]` bölümünden belirlesin; varsayılan tuşlar birebir korunsun.

**Architecture:** Saf `core/keymap.py` (eylem tablosu, ayrıştırma, doğrulama, çakışma çözümü, etiket) + ince Qt kabuğu `ui/keys.py` (`QKeyEvent` → bağlama). Üç widget (`ModalEditor`, `TerminalView`, `WelcomePage`) tuşu değil **eylemi** dinler; harita `IDEWindow.apply_settings()` üzerinden dağıtılır, böylece `:reload` canlı yeniden atamayı bedavaya verir.

**Tech Stack:** Python 3.11+ (`tomllib`), PyQt6, pytest. Yeni bağımlılık yok.

**Spec:** `docs/superpowers/specs/2026-09-09-kisayol-yapilandirmasi-design.md`

## Global Constraints

- **Dil:** Yorumlar, docstring'ler, uyarı metinleri ve commit mesajları **Türkçe** (depo geleneği, bkz. `CLAUDE.md`).
- **Test komutu:** `.venv/bin/python -m pytest -q` — konsol script'lerinin shebang'i bayat, **her zaman** `-m` ile çağır.
- **Katman kuralı:** `core/keymap.py` Qt import etmez. Qt'ye dokunan her şey `ui/keys.py`'de.
- **Varsayılanlar değişmez (K2):** `alt+shift+t/n/w/right/left`, `i`, `:`, `n`, `N`, `escape`. `tests/test_editor_shortcuts.py` ve `tests/test_welcome_page.py` bu işin regresyon bekçisidir — **değiştirilmeden geçmeli**.
- **K6:** Panel bağlaması `ctrl`, `alt` ya da `meta`'dan en az birini içermek zorunda.
- **K7:** Normal bağlaması tek karakter ya da `escape`; değiştirici öneki reddedilir.
- **K3:** Çakışmaya izin var; `ACTIONS` sırasında ilk gelen kazanır, kaybeden için uyarı.
- **K8:** `core/config.py` yalnız "boş olmayan dize" doğrular; eylem/tuş geçerliliği `core/keymap.py`'nin işi.
- **Hata felsefesi:** Hiçbir bozuk ayar istisna fırlatmaz. Her hata bir Türkçe uyarı satırı + o eylemin varsayılanı.
- **Commit mesajı sonu:** her commit şu iki satırla biter:
  ```
  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01CvQDtnxf6HM5dt9KvWZVVD
  ```
- **Dal:** `kisayol-yapilandirmasi` (zaten açık, spec commit'i üzerinde).

## Dosya yapısı

| Dosya | Sorumluluk | Görev |
|---|---|---|
| `core/keymap.py` | **Yeni.** Eylem tablosu, `parse`, `build`, `Keymap`, `defaults`, `text`, `label`. Qt yok | 1, 2 |
| `tests/test_keymap.py` | **Yeni.** Saf birim testleri | 1, 2 |
| `ui/keys.py` | **Yeni.** `QKeyEvent` → bağlama; `panel_binding`, `normal_binding`, `match` | 3 |
| `tests/test_shortcut_config.py` | **Yeni.** Qt kabuğu + kayma bekçisi + uçtan uca | 3, 8 |
| `core/config.py` | `[shortcuts]` bölümü + `TEMPLATE` | 4 |
| `tests/test_config.py` | `[shortcuts]` biçim doğrulaması | 4 |
| `ui/components/code_editor.py` | Panel + normal dağıtımı keymap'ten; `apply_keymap` | 5 |
| `core/state_machine.py` | `handle_normal_key(event)` → `handle_normal_action(action)` | 5 |
| `ui/components/editor_tabs.py` | Haritayı saklar, yeni sekmeye verir | 5 |
| `ui/components/terminal_panel.py` | `TerminalView` + `TerminalPanel` `apply_keymap` | 6 |
| `ui/components/welcome_page.py` | Panel + `command_line`; ipuçları keymap'ten | 7 |
| `ui/main_window.py` | `apply_settings` haritayı kurar ve dağıtır | 8 |
| `README.md`, `CLAUDE.md`, `docs/Roadmap.md`, `docs/sprint/` | Belgeler | 9 |

---

### Task 1: `core/keymap.py` — eylem tablosu ve `parse()`

**Files:**
- Create: `core/keymap.py`
- Test: `tests/test_keymap.py`

**Interfaces:**
- Consumes: yok (ilk görev).
- Produces:
  - `Action = namedtuple("Action", "name group default description")`
  - `ACTIONS` — 10 `Action`, **sırası anlamlı** (çakışmada ilk gelen kazanır).
  - `MODIFIERS = ("ctrl", "alt", "shift", "meta")`, `PANEL_REQUIRED = ("ctrl", "alt", "meta")`, `NAMED_KEYS` (tuple).
  - `parse(value: str, group: str) -> tuple[binding | None, str | None]` — `(bağlama, hata)`. `binding` = `(frozenset[str], str)`.

- [ ] **Step 1: Testleri yaz (kırmızı olmalı)**

`tests/test_keymap.py`:

```python
""" Tuş haritasının sözleşmesi: ayrıştırma, doğrulama, birleştirme, çakışma.
Qt gerektirmez. """
import core.keymap as keymap


def test_on_eylem_var_ve_sira_anlamli():
    adlar = [a.name for a in keymap.ACTIONS]
    assert adlar == [
        "terminal_focus", "tab_new", "tab_close", "tab_next", "tab_prev",
        "insert_mode", "command_line", "search_next", "search_prev", "clear_search",
    ]


def test_her_varsayilan_kendi_grubunun_kurallarindan_geciyor():
    """ Kendi kuralımıza uyduğumuzun bekçisi: K6/K7 varsayılanları elemez. """
    for action in keymap.ACTIONS:
        baglama, hata = keymap.parse(action.default, action.group)
        assert hata is None, f"{action.name}: {hata}"
        assert baglama is not None


def test_panel_baglamasi_ayrisir():
    baglama, hata = keymap.parse("alt+shift+t", "panel")
    assert hata is None
    assert baglama == (frozenset({"alt", "shift"}), "t")


def test_panel_baglamasi_buyuk_kucuk_harf_ayirmaz():
    """ Dağıtım event.key() ile karşılaştırıyor; Qt.Key harf büyüklüğü bilmez. """
    assert keymap.parse("Alt+Shift+T", "panel")[0] == keymap.parse("alt+shift+t", "panel")[0]


def test_panel_isimli_tuslari_kabul_eder():
    assert keymap.parse("alt+shift+right", "panel")[0] == (frozenset({"alt", "shift"}), "right")
    assert keymap.parse("ctrl+f5", "panel")[0] == (frozenset({"ctrl"}), "f5")


def test_panel_bilinmeyen_degistirici_reddedilir():
    baglama, hata = keymap.parse("hyper+n", "panel")
    assert baglama is None
    assert "hyper" in hata


def test_panel_bilinmeyen_tus_reddedilir():
    baglama, hata = keymap.parse("alt+shift+q9", "panel")
    assert baglama is None
    assert "q9" in hata


def test_panel_degistiricisiz_reddedilir():
    """ K6: değiştiricisiz panel kısayolu o harfi INSERT modunda yazılamaz
    hale getirirdi. """
    baglama, hata = keymap.parse("i", "panel")
    assert baglama is None
    assert "Ctrl, Alt ya da Meta" in hata


def test_panel_yalniz_shift_reddedilir():
    """ K6: 'shift+n' bağlanabilseydi INSERT modunda 'N' yazılamazdı. """
    baglama, hata = keymap.parse("shift+n", "panel")
    assert baglama is None
    assert "Ctrl, Alt ya da Meta" in hata


def test_panel_ctrl_ve_meta_kabul_edilir():
    """ K2: Ctrl varsayılana girmiyor ama yasak da değil. """
    assert keymap.parse("ctrl+t", "panel")[1] is None
    assert keymap.parse("meta+t", "panel")[1] is None


def test_normal_tek_karakter_kabul_eder():
    assert keymap.parse("i", "normal")[0] == (frozenset(), "i")
    assert keymap.parse(":", "normal")[0] == (frozenset(), ":")


def test_normal_buyuk_kucuk_harf_ayirir():
    """ 'n' ile 'N' farklı komut; dağıtım event.text() ile karşılaştırıyor. """
    assert keymap.parse("n", "normal")[0] != keymap.parse("N", "normal")[0]


def test_normal_escape_kabul_eder():
    assert keymap.parse("escape", "normal")[0] == (frozenset(), "escape")


def test_normal_degistirici_reddedilir():
    """ K7: 'alt+i' istenseydi handle_normal_mode'un dağıtım kapısı da
    değişmeliydi — ayrı ve daha büyük bir iş. """
    baglama, hata = keymap.parse("alt+i", "normal")
    assert baglama is None
    assert "tek karakter" in hata
```

- [ ] **Step 2: Testlerin kırmızı olduğunu gör**

Run: `.venv/bin/python -m pytest tests/test_keymap.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.keymap'`

- [ ] **Step 3: `core/keymap.py`'nin ilk yarısını yaz**

```python
""" Tuş haritası: ayar dosyasındaki [shortcuts] bölümü doğrulanır ve
eylem <-> tuş eşlemesine dönüştürülür.

Qt'ye bağımlı DEĞİL — tamamen saf, doğrudan test edilebilir. Bir QKeyEvent'i
buradaki bağlama biçimine çeviren ince kabuk ui/keys.py'dedir.

Bağlama biçimi her iki grupta da aynı: (frozenset(değiştirici adları), tuş adı).
İki grup arasında bilinçli bir asimetri var:

  - 'panel' grubu her modda çalışır ve dağıtımı event.key() ile yapılır;
    Qt.Key harf büyüklüğü bilmediği için tuş adı küçük harfe indirilir
    ('alt+shift+T' ile 'alt+shift+t' AYNI bağlamadır).
  - 'normal' grubu yalnız NORMAL modda çalışır ve dağıtımı event.text() ile
    yapılır; tuş adı olduğu gibi korunur ('n' ile 'N' FARKLI bağlamadır).
"""
from collections import namedtuple

Action = namedtuple("Action", "name group default description")

# SIRA ANLAMLI: iki eylem aynı tuşa düşerse önce gelen kazanır (bkz. Keymap).
ACTIONS = (
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

MODIFIERS = ("ctrl", "alt", "shift", "meta")

# Panel kısayolu bunlardan en az birini içermek ZORUNDA (K6). Panel grubu her
# modda ve mod dağıtımından ÖNCE okunuyor: değiştiricisiz bir bağlama o harfi
# INSERT modunda yazılamaz hale getirirdi. Shift tek başına yetmez, çünkü
# 'shift+n' bağlanırsa 'N' yazılamaz.
PANEL_REQUIRED = ("ctrl", "alt", "meta")

NAMED_KEYS = (
    "right", "left", "up", "down", "escape", "tab", "space", "home", "end",
    "pageup", "pagedown", "backspace", "delete", "return",
) + tuple(f"f{number}" for number in range(1, 13))

_BY_NAME = {action.name: action for action in ACTIONS}


def parse(value, group):
    """ Tek bir ayar değerini ayrıştırır ve grubun kurallarına göre doğrular.
    (bağlama, hata_metni) döndürür; hata varsa bağlama None'dır. """
    return _parse_normal(value) if group == "normal" else _parse_panel(value)


# --- İç işler ---

def _parse_normal(value):
    """ NORMAL mod: tek karakter ya da 'escape'. Değiştirici öneki yok —
    Shift zaten karakterin kendisinde (K7). """
    if value == "escape":
        return (frozenset(), "escape"), None
    if len(value) != 1:
        return None, "NORMAL mod kısayolu tek karakter ya da 'escape' olmalı"
    return (frozenset(), value), None


def _parse_panel(value):
    """ Panel: [değiştirici+]* tuş. Tümü küçük harfe indirilir. """
    parts = [part.strip() for part in value.lower().split("+")]
    modifier_names, key = parts[:-1], parts[-1]

    for name in modifier_names:
        if name not in MODIFIERS:
            return None, f"bilinmeyen değiştirici '{name}'"
    if not _is_key(key):
        return None, f"bilinmeyen tuş '{key}'"

    modifiers = frozenset(modifier_names)
    if not modifiers.intersection(PANEL_REQUIRED):
        return None, "panel kısayolu Ctrl, Alt ya da Meta içermeli"
    return (modifiers, key), None


def _is_key(key):
    """ Harf/rakam ui/keys.py'de tablosuz çözülüyor (Qt.Key_A == ord('A')),
    o yüzden burada da ASCII harf/rakamla sınırlı. """
    if key in NAMED_KEYS:
        return True
    return len(key) == 1 and ("a" <= key <= "z" or "0" <= key <= "9")
```

- [ ] **Step 4: Testlerin yeşile döndüğünü gör**

Run: `.venv/bin/python -m pytest tests/test_keymap.py -q`
Expected: PASS — 14 test.

- [ ] **Step 5: Commit**

```bash
git add core/keymap.py tests/test_keymap.py
git commit -m "feat: saf tuş haritası çekirdeği — eylem tablosu ve parse()"
```

---

### Task 2: `core/keymap.py` — `Keymap`, `build()`, `defaults()`, `label()`

**Files:**
- Modify: `core/keymap.py` (Task 1'in üstüne ekleme)
- Test: `tests/test_keymap.py` (ekleme)

**Interfaces:**
- Consumes: `ACTIONS`, `parse` (Task 1).
- Produces:
  - `class Keymap` — `binding_of(name) -> binding`, `action_for(group, binding) -> str | None`, `label(name) -> str`, `conflicts: list[str]`
  - `build(user_values: dict) -> tuple[Keymap, list[str]]`
  - `defaults() -> Keymap`
  - `text(binding) -> str` (ayar dosyası biçimi: `"alt+shift+w"`)
  - `label(binding) -> str` (gösterim biçimi: `"Alt+Shift+W"`) — modül düzeyinde fonksiyon; `Keymap.label(name)` bunu çağırır.

- [ ] **Step 1: Testleri yaz (kırmızı olmalı)**

`tests/test_keymap.py` sonuna ekle:

```python
# --- build / Keymap / label ---

def test_bos_ayar_varsayilan_haritayi_verir():
    harita, uyarilar = keymap.build({})
    assert uyarilar == []
    assert harita.binding_of("tab_new") == (frozenset({"alt", "shift"}), "n")
    assert harita.action_for("panel", (frozenset({"alt", "shift"}), "n")) == "tab_new"
    assert harita.action_for("normal", (frozenset(), "i")) == "insert_mode"


def test_defaults_build_ile_ayni():
    assert keymap.defaults().binding_of("tab_new") == keymap.build({})[0].binding_of("tab_new")


def test_gecerli_yeniden_atama_yalniz_o_eylemi_degistirir():
    harita, uyarilar = keymap.build({"tab_new": "ctrl+t"})
    assert uyarilar == []
    assert harita.action_for("panel", (frozenset({"ctrl"}), "t")) == "tab_new"
    # Eski tuş artık bağlı değil
    assert harita.action_for("panel", (frozenset({"alt", "shift"}), "n")) is None
    # Diğerleri varsayılanda
    assert harita.binding_of("tab_close") == (frozenset({"alt", "shift"}), "w")


def test_bilinmeyen_eylem_adi_uyarir():
    harita, uyarilar = keymap.build({"tab_neww": "ctrl+t"})
    assert len(uyarilar) == 1
    assert "tab_neww" in uyarilar[0]
    assert harita.binding_of("tab_new") == (frozenset({"alt", "shift"}), "n")


def test_gecersiz_baglama_varsayilana_duser_ve_uyarir():
    harita, uyarilar = keymap.build({"tab_new": "alt+shift+q9"})
    assert len(uyarilar) == 1
    assert "tab_new" in uyarilar[0] and "q9" in uyarilar[0]
    assert "alt+shift+n" in uyarilar[0]           # varsayılan uyarıda yazıyor
    assert harita.binding_of("tab_new") == (frozenset({"alt", "shift"}), "n")


def test_k6_ihlali_varsayilana_duser():
    harita, uyarilar = keymap.build({"tab_new": "i"})
    assert len(uyarilar) == 1
    assert harita.binding_of("tab_new") == (frozenset({"alt", "shift"}), "n")


def test_cakismada_once_gelen_kazanir():
    """ K3: ACTIONS sırasında tab_new, tab_close'dan önce geliyor. """
    harita, uyarilar = keymap.build({"tab_new": "alt+shift+w"})

    assert harita.action_for("panel", (frozenset({"alt", "shift"}), "w")) == "tab_new"
    assert len(uyarilar) == 1
    assert "tab_close" in uyarilar[0] and "alt+shift+w" in uyarilar[0]


def test_cakisma_gruplar_arasinda_olamaz():
    """ K6+K7 birlikte gruplar arası çakışmayı imkânsız kılıyor: panel
    bağlaması değiştirici İÇERMEK, normal bağlaması İÇERMEMEK zorunda.
    'alt+shift+i' panelde geçerli, normalde reddedilir; ikisi asla aynı
    bağlamaya düşemez. """
    harita, uyarilar = keymap.build({"terminal_focus": "alt+shift+i"})

    assert uyarilar == []
    assert harita.action_for("panel", (frozenset({"alt", "shift"}), "i")) == "terminal_focus"
    assert harita.action_for("normal", (frozenset(), "i")) == "insert_mode"


def test_normal_grubu_icinde_cakisma_bildirilir():
    """ insert_mode ACTIONS'ta search_next'ten ÖNCE: 'n' insert_mode'a gider,
    search_next bağsız kalır ve bir uyarı üretilir. """
    harita, uyarilar = keymap.build({"insert_mode": "n"})

    assert harita.action_for("normal", (frozenset(), "n")) == "insert_mode"
    assert len(uyarilar) == 1
    assert "search_next" in uyarilar[0]


def test_label_gosterim_bicimi():
    harita = keymap.defaults()
    assert harita.label("terminal_focus") == "Alt+Shift+T"
    assert harita.label("tab_next") == "Alt+Shift+→"
    assert harita.label("tab_prev") == "Alt+Shift+←"
    assert harita.label("insert_mode") == "i"
    assert harita.label("search_prev") == "N"
    assert harita.label("clear_search") == "Esc"


def test_label_ctrl_ve_fonksiyon_tuslari():
    harita, _u = keymap.build({"tab_new": "ctrl+f5"})
    assert harita.label("tab_new") == "Ctrl+F5"


def test_text_ayar_dosyasi_bicimini_verir():
    assert keymap.text((frozenset({"shift", "alt"}), "w")) == "alt+shift+w"
```

- [ ] **Step 2: Testlerin kırmızı olduğunu gör**

Run: `.venv/bin/python -m pytest tests/test_keymap.py -q`
Expected: FAIL — `AttributeError: module 'core.keymap' has no attribute 'build'`

- [ ] **Step 3: `core/keymap.py`'nin ikinci yarısını yaz**

`_BY_NAME` tanımının hemen altına, `parse`'tan önce ekle:

```python
_MODIFIER_ORDER = ("ctrl", "alt", "shift", "meta")

# Gösterim adları. Buradaki tuşlar NAMED_KEYS'in bir alt kümesi; listede
# olmayanlar (harfler, rakamlar, f1-f12) büyük harfe çevrilerek gösterilir.
_PRETTY = {
    "escape": "Esc", "right": "→", "left": "←", "up": "↑", "down": "↓",
    "pageup": "PageUp", "pagedown": "PageDown", "backspace": "Backspace",
    "delete": "Delete", "return": "Enter", "space": "Space", "tab": "Tab",
    "home": "Home", "end": "End",
}


class Keymap:
    """ Bir tuş haritası. İki yönü de tutar: etiket/ipucu için eylem -> bağlama,
    dağıtım için (grup, bağlama) -> eylem.

    Ters tablo ACTIONS sırasında setdefault ile kurulur, yani iki eylem aynı
    tuşa düşerse ÖNCE GELEN KAZANIR (K3); kaybeden 'conflicts' listesine bir
    uyarı bırakır ve dağıtımda hiç görünmez. Kaybedenin bağlaması gene de
    saklanır: karşılama sayfası ipuçlarında iki eylemin aynı tuşu göstermesi,
    çakışmayı gizlemek yerine gösterir. """

    def __init__(self, bindings):
        self._bindings = dict(bindings)
        self._by_binding = {"panel": {}, "normal": {}}
        self.conflicts = []

        for action in ACTIONS:
            binding = self._bindings[action.name]
            winner = self._by_binding[action.group].setdefault(binding, action.name)
            if winner != action.name:
                self.conflicts.append(
                    f"shortcuts.{action.name}: {text(binding)} zaten {winner} eylemine "
                    f"bağlı; bu kısayol çalışmayacak.")

    def binding_of(self, name):
        return self._bindings[name]

    def action_for(self, group, binding):
        """ Dağıtımın tek sorusu. Bağlama bağlı değilse None. """
        return self._by_binding[group].get(binding)

    def label(self, name):
        return label(self._bindings[name])


def build(user_values):
    """ Varsayılanların üstüne kullanıcı değerlerini bindirir.
    (Keymap, uyarılar) döndürür.

    core/config.py deseni: her bozuk anahtar bir uyarıya dönüşür ve YALNIZ o
    eylem varsayılanında kalır; dosyanın geri kalanı uygulanır. """
    bindings = {}
    warnings = []

    for action in ACTIONS:
        default_binding, _error = parse(action.default, action.group)
        value = user_values.get(action.name)

        if value is None:
            bindings[action.name] = default_binding
            continue

        binding, error = parse(value, action.group)
        if error is not None:
            warnings.append(
                f"shortcuts.{action.name}: {error}; "
                f"varsayılan kullanıldı ({action.default}).")
            binding = default_binding
        bindings[action.name] = binding

    for name in user_values:
        if name not in _BY_NAME:
            warnings.append(f"Bilinmeyen kısayol eylemi yok sayıldı: shortcuts.{name}")

    keymap = Keymap(bindings)
    warnings.extend(keymap.conflicts)
    return keymap, warnings


def defaults():
    """ Varsayılan harita. Widget'lar __init__'te bunu alır, böylece
    apply_keymap çağrılmadan da (testte, ya da apply_settings'ten önce
    kurulan widget ağacında) çalışırlar. """
    keymap, _warnings = build({})
    return keymap


def text(binding):
    """ Ayar dosyasındaki biçim: 'alt+shift+w'. Uyarı metinlerinde kullanılır. """
    modifiers, key = binding
    return "+".join([name for name in _MODIFIER_ORDER if name in modifiers] + [key])


def label(binding):
    """ Gösterim biçimi: 'Alt+Shift+W', 'Ctrl+F5', 'Alt+Shift+→', 'Esc', 'i'.
    Karşılama sayfası ipuçları bunu kullanır. """
    modifiers, key = binding
    if key in _PRETTY:
        pretty = _PRETTY[key]
    elif not modifiers and len(key) == 1:
        pretty = key              # normal grubu: 'n' ile 'N' farklı, dokunma
    else:
        pretty = key.upper()
    names = [name.capitalize() for name in _MODIFIER_ORDER if name in modifiers]
    return "+".join(names + [pretty])
```

- [ ] **Step 4: Testlerin yeşile döndüğünü gör**

Run: `.venv/bin/python -m pytest tests/test_keymap.py -q`
Expected: PASS — 12 yeni test (toplam 26).

- [ ] **Step 5: Tüm paketi koştur (regresyon yok)**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — mevcut 197 test + yeni testler.

- [ ] **Step 6: Commit**

```bash
git add core/keymap.py tests/test_keymap.py
git commit -m "feat: Keymap, build() ve çakışma çözümü (ilk gelen kazanır)"
```

---

### Task 3: `ui/keys.py` — Qt kabuğu ve kayma bekçisi

**Files:**
- Create: `ui/keys.py`
- Test: `tests/test_shortcut_config.py`

**Interfaces:**
- Consumes: `core.keymap.NAMED_KEYS`, `Keymap.action_for` (Task 1-2).
- Produces:
  - `panel_binding(event) -> binding | None`
  - `normal_binding(event) -> binding | None`
  - `match(event, keymap, group) -> str | None`
  - `_QT_NAMED_KEYS: dict[str, Qt.Key]` (kayma bekçisi testi buna bakar)

- [ ] **Step 1: Testleri yaz (kırmızı olmalı)**

`tests/test_shortcut_config.py`:

```python
""" Qt kabuğu (ui/keys.py) ve kısayolların uçtan uca yapılandırılması. """
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

import core.keymap as keymap
import ui.keys as keys

ALT_SHIFT = Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier


def _olay(key, modifiers=Qt.KeyboardModifier.NoModifier, text=""):
    return QKeyEvent(QKeyEvent.Type.KeyPress, key, modifiers, text)


def test_isimli_tus_tablolari_ortusuyor():
    """ Kayma bekçisi: core/keymap.py hangi adların GEÇERLİ olduğunu söyler,
    ui/keys.py onları Qt.Key'e çevirir. İkisi ayrışırsa ayar dosyasında
    geçerli görünen bir tuş sessizce çalışmaz. """
    assert set(keys._QT_NAMED_KEYS) == set(keymap.NAMED_KEYS)


def test_panel_baglamasi_olaydan_uretilir():
    olay = _olay(Qt.Key.Key_T, ALT_SHIFT)
    assert keys.panel_binding(olay) == (frozenset({"alt", "shift"}), "t")


def test_panel_baglamasi_isimli_tusu_cozer():
    olay = _olay(Qt.Key.Key_Right, ALT_SHIFT)
    assert keys.panel_binding(olay) == (frozenset({"alt", "shift"}), "right")


def test_panel_baglamasi_bilinmeyen_tusa_none_der():
    assert keys.panel_binding(_olay(Qt.Key.Key_Ampersand, ALT_SHIFT)) is None


def test_normal_baglamasi_metni_kullanir():
    assert keys.normal_binding(_olay(Qt.Key.Key_N, text="n")) == (frozenset(), "n")
    assert keys.normal_binding(
        _olay(Qt.Key.Key_N, Qt.KeyboardModifier.ShiftModifier, "N")) == (frozenset(), "N")


def test_normal_baglamasi_escape_i_ad_olarak_verir():
    """ Escape'in text()'i boş değil ('\\x1b'); ad üzerinden eşleşmeli. """
    olay = _olay(Qt.Key.Key_Escape, text="\x1b")
    assert keys.normal_binding(olay) == (frozenset(), "escape")


def test_normal_baglamasi_degistiricili_tusa_none_der():
    olay = _olay(Qt.Key.Key_I, Qt.KeyboardModifier.AltModifier, "i")
    assert keys.normal_binding(olay) is None


def test_match_eylemi_bulur():
    harita = keymap.defaults()
    assert keys.match(_olay(Qt.Key.Key_N, ALT_SHIFT), harita, "panel") == "tab_new"
    assert keys.match(_olay(Qt.Key.Key_I, text="i"), harita, "normal") == "insert_mode"
    assert keys.match(_olay(Qt.Key.Key_Z, ALT_SHIFT), harita, "panel") is None
```

- [ ] **Step 2: Testlerin kırmızı olduğunu gör**

Run: `.venv/bin/python -m pytest tests/test_shortcut_config.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'ui.keys'`

- [ ] **Step 3: `ui/keys.py`'yi yaz**

```python
""" QKeyEvent'i core/keymap.py'nin bağlama biçimine çeviren ince kabuk.
Modülün tek işi bu çeviri — kural, doğrulama ve çakışma mantığı orada.

Hangi tuş ADLARININ geçerli olduğunu core/keymap.NAMED_KEYS söyler; burada
yalnız onların Qt karşılığı durur. İki tablonun ayrışmaması
tests/test_shortcut_config.test_isimli_tus_tablolari_ortusuyor ile bekçilenir.

macOS notu: adlar Qt değiştiricilerine BİREBİR eşlenir. Qt macOS'ta
ControlModifier'ı Command tuşuna, MetaModifier'ı fiziksel Control'e bağlar;
bu takası taklit etmiyoruz (QKeySequence'in sessizce yaptığı çeviri tasarımda
tam bu yüzden reddedildi, bkz. spec K5). """
from PyQt6.QtCore import Qt

_MODIFIER_FLAGS = (
    ("ctrl", Qt.KeyboardModifier.ControlModifier),
    ("alt", Qt.KeyboardModifier.AltModifier),
    ("shift", Qt.KeyboardModifier.ShiftModifier),
    ("meta", Qt.KeyboardModifier.MetaModifier),
)

_QT_NAMED_KEYS = {
    "right": Qt.Key.Key_Right, "left": Qt.Key.Key_Left,
    "up": Qt.Key.Key_Up, "down": Qt.Key.Key_Down,
    "escape": Qt.Key.Key_Escape, "tab": Qt.Key.Key_Tab,
    "space": Qt.Key.Key_Space, "home": Qt.Key.Key_Home, "end": Qt.Key.Key_End,
    "pageup": Qt.Key.Key_PageUp, "pagedown": Qt.Key.Key_PageDown,
    "backspace": Qt.Key.Key_Backspace, "delete": Qt.Key.Key_Delete,
    "return": Qt.Key.Key_Return,
}
_QT_NAMED_KEYS.update(
    {f"f{number}": Qt.Key(int(Qt.Key.Key_F1) + number - 1) for number in range(1, 13)})

# int() ile anahtarlanıyor: event.key() düz bir int döndürür.
_NAME_BY_KEY = {int(value): name for name, value in _QT_NAMED_KEYS.items()}


def panel_binding(event):
    """ Panel grubu event.key() ile çalışır (Alt basılıyken event.text()
    güvenilir değildir). Bilmediğimiz dört değiştirici dışındakiler (Keypad,
    GroupSwitch) YOK SAYILIR; bildiklerimiz tam eşleşir. """
    modifiers = frozenset(
        name for name, flag in _MODIFIER_FLAGS if event.modifiers() & flag)

    key = int(event.key())
    name = _NAME_BY_KEY.get(key)
    if name is None:
        if int(Qt.Key.Key_A) <= key <= int(Qt.Key.Key_Z) or \
           int(Qt.Key.Key_0) <= key <= int(Qt.Key.Key_9):
            name = chr(key).lower()
        else:
            return None
    return (modifiers, name)


def normal_binding(event):
    """ NORMAL grubu event.text() ile çalışır — büyük/küçük harf ayrımı
    korunsun diye ('n' ile 'N' farklı komut). Escape'in text()'i boş değil
    ('\\x1b'), o yüzden ondan ÖNCE ad üzerinden ele alınıyor. """
    if event.key() == Qt.Key.Key_Escape:
        return (frozenset(), "escape")

    text = event.text()
    if not text:
        return None
    if event.modifiers() not in (Qt.KeyboardModifier.NoModifier,
                                 Qt.KeyboardModifier.ShiftModifier):
        return None
    return (frozenset(), text)


def match(event, keymap, group):
    """ Widget'ların sorduğu tek soru: bu olay hangi eyleme karşılık geliyor? """
    binding = panel_binding(event) if group == "panel" else normal_binding(event)
    if binding is None:
        return None
    return keymap.action_for(group, binding)
```

- [ ] **Step 4: Testlerin yeşile döndüğünü gör**

Run: `.venv/bin/python -m pytest tests/test_shortcut_config.py -q`
Expected: PASS — 8 test.

- [ ] **Step 5: Commit**

```bash
git add ui/keys.py tests/test_shortcut_config.py
git commit -m "feat: QKeyEvent -> bağlama çeviren ince Qt kabuğu"
```

---

### Task 4: `core/config.py` — `[shortcuts]` bölümü

**Files:**
- Modify: `core/config.py` (`DEFAULTS`, `TEMPLATE`, `_merge_and_validate`, yeni `_validated_shortcuts`)
- Test: `tests/test_config.py` (ekleme)

**Interfaces:**
- Consumes: yok (config `core/keymap.py`'yi import ETMEZ — K8).
- Produces: `settings["shortcuts"]` — `{eylem adı: dize}`. Eylem adının ve tuşun geçerliliğine bakılmaz; o `keymap.build`'in işi.

- [ ] **Step 1: Testleri yaz (kırmızı olmalı)**

`tests/test_config.py` sonuna ekle:

```python
# --- [shortcuts] ---

def test_shortcuts_varsayilanda_bos():
    assert config.DEFAULTS["shortcuts"] == {}


def test_shortcuts_degeri_oldugu_gibi_gecer():
    """ config yalnız BİÇİME bakar: eylem adının ve tuşun geçerliliği
    core/keymap.py'nin işi ([colors] ile aynı ayrım). """
    ayarlar, uyarilar = config.parse('[shortcuts]\ntab_new = "ctrl+t"\n')
    assert ayarlar["shortcuts"] == {"tab_new": "ctrl+t"}
    assert uyarilar == []


def test_shortcuts_bilinmeyen_eylem_adi_config_seviyesinde_gecer():
    """ 'tab_neww' burada elenmez; uyarıyı keymap.build üretir. """
    ayarlar, uyarilar = config.parse('[shortcuts]\ntab_neww = "ctrl+t"\n')
    assert ayarlar["shortcuts"] == {"tab_neww": "ctrl+t"}
    assert uyarilar == []


def test_shortcuts_metin_olmayan_deger_elenir():
    ayarlar, uyarilar = config.parse("[shortcuts]\ntab_new = 5\n")
    assert ayarlar["shortcuts"] == {}
    assert any("tab_new" in u for u in uyarilar)


def test_shortcuts_bos_deger_elenir():
    ayarlar, uyarilar = config.parse('[shortcuts]\ntab_new = "   "\n')
    assert ayarlar["shortcuts"] == {}
    assert any("tab_new" in u for u in uyarilar)


def test_sablonda_shortcuts_bolumu_var():
    assert "[shortcuts]" in config.TEMPLATE
```

- [ ] **Step 2: Testlerin kırmızı olduğunu gör**

Run: `.venv/bin/python -m pytest tests/test_config.py -q`
Expected: FAIL — `KeyError: 'shortcuts'` ve `Bilinmeyen ayar bölümü yok sayıldı: [shortcuts]`

- [ ] **Step 3: `core/config.py`'yi değiştir**

`DEFAULTS` içinde `"terminal"` ile `"colors"` arasına:

```python
    # Eylem adı -> tuş dizesi. Boş = varsayılan tuş haritası. Geçerli eylem
    # adlarını ve tuşları core/keymap.py bilir (bkz. _validated_shortcuts).
    "shortcuts": {},
```

`_merge_and_validate` içinde, `if section == "colors":` bloğunun **hemen üstüne**:

```python
        if section == "shortcuts":
            settings["shortcuts"], shortcut_warnings = _validated_shortcuts(values)
            warnings.extend(shortcut_warnings)
            continue
```

Dosyanın sonuna, `_validated_colors`'ın yanına:

```python
def _validated_shortcuts(values):
    """ Yalnız BİÇİM denetlenir: değer boş olmayan bir dize olmalı. Eylem
    adının ve tuş dizesinin geçerliliğine core/keymap.build bakar — [colors]
    ile birebir aynı ayrım: hangi eylemlerin var olduğu tuş haritasının
    bilgisi, ayar dosyasının değil. """
    shortcuts = {}
    warnings = []
    for name, value in values.items():
        if isinstance(value, str) and value.strip():
            shortcuts[name] = value.strip()
        else:
            warnings.append(f"shortcuts.{name} boş olmayan bir metin olmalı; yok sayıldı.")
    return shortcuts, warnings
```

`TEMPLATE` içinde `[colors]` bölümünün **üstüne**:

```
[shortcuts]
# Kısayolları buradan değiştirebilirsin. İki kural var:
#   - Panel kısayolları (her modda çalışır) ctrl, alt ya da meta İÇERMELİ;
#     yoksa o harf INSERT modunda yazılamaz hale gelirdi.
#   - NORMAL mod kısayolları tek karakter ya da "escape"; büyük/küçük harf
#     ayrımı korunur ("n" ile "N" farklı komut).
# terminal_focus = "alt+shift+t"
# tab_new        = "alt+shift+n"
# tab_close      = "alt+shift+w"
# tab_next       = "alt+shift+right"
# tab_prev       = "alt+shift+left"
# insert_mode    = "i"
# command_line   = ":"
# search_next    = "n"
# search_prev    = "N"
# clear_search   = "escape"

```

- [ ] **Step 4: Testlerin yeşile döndüğünü gör**

Run: `.venv/bin/python -m pytest tests/test_config.py tests/test_settings_reload.py -q`
Expected: PASS. `test_varsayilan_ayarlarla_acilir` (`settings == config.DEFAULTS`) da geçmeli — `DEFAULTS`'a eklediğimiz için karşılaştırma bozulmaz.

- [ ] **Step 5: Commit**

```bash
git add core/config.py tests/test_config.py
git commit -m "feat: ayar dosyasına [shortcuts] bölümü"
```

---

### Task 5: `ModalEditor` + `StateMachine` + `EditorTabs` — editör dağıtımı

**Files:**
- Modify: `ui/components/code_editor.py` (`__init__`, `_PANEL_MODIFIERS` sil, `keyPressEvent`, `handle_normal_mode`, yeni `apply_keymap` / `_panel_signal`)
- Modify: `core/state_machine.py` (`handle_normal_key` → `handle_normal_action`)
- Modify: `ui/components/editor_tabs.py` (`__init__`, `new_tab`, yeni `apply_keymap`)
- Test: `tests/test_shortcut_config.py` (ekleme)

**Interfaces:**
- Consumes: `keys.match`, `keymap.defaults` (Task 2-3).
- Produces:
  - `ModalEditor.apply_keymap(keymap) -> None`
  - `EditorTabs.apply_keymap(keymap) -> None` — haritayı saklar, açık tüm editörlere uygular, `new_tab()` yenisine verir.
  - `StateMachine.handle_normal_action(action: str) -> None` — `handle_normal_key` **kaldırılır**.

- [ ] **Step 1: Testleri yaz (kırmızı olmalı)**

Önce `tests/test_shortcut_config.py`'nin **import bloğuna** ekle:

```python
from PyQt6.QtTest import QTest
```

ve `ALT_SHIFT`'in altına:

```python
CTRL = Qt.KeyboardModifier.ControlModifier
```

Sonra dosyanın sonuna ekle:

```python
# --- Editör dağıtımı ---

def test_editorde_panel_kisayolu_yeniden_atanabilir(pencere):
    pencere.show()
    harita, _u = keymap.build({"tab_new": "ctrl+t"})
    pencere.editor_tabs.apply_keymap(harita)

    onceki = pencere.editor_tabs.count()
    QTest.keyClick(pencere.editor, Qt.Key.Key_T, CTRL)
    assert pencere.editor_tabs.count() == onceki + 1

    # Eski tuş artık çalışmamalı
    simdiki = pencere.editor_tabs.count()
    QTest.keyClick(pencere.editor, Qt.Key.Key_N, ALT_SHIFT)
    assert pencere.editor_tabs.count() == simdiki


def test_normal_mod_tusu_yeniden_atanabilir(pencere):
    pencere.show()
    harita, _u = keymap.build({"insert_mode": "a"})
    pencere.editor_tabs.apply_keymap(harita)

    QTest.keyClick(pencere.editor, Qt.Key.Key_A, text="a")
    assert pencere.editor.current_mode == "INSERT"


def test_yeniden_atandiktan_sonra_eski_tus_metin_yazmaz(pencere):
    """ NORMAL modda bağlanmamış yazılabilir tuş YUTULUR (bugünkü davranış);
    metne düşmemeli. """
    pencere.show()
    harita, _u = keymap.build({"insert_mode": "a"})
    pencere.editor_tabs.apply_keymap(harita)

    QTest.keyClick(pencere.editor, Qt.Key.Key_I, text="i")
    assert pencere.editor.current_mode == "NORMAL"
    assert pencere.editor.toPlainText() == ""


def test_insert_modunda_harf_hala_yazilabiliyor(pencere):
    """ K6'nın koruduğu şey: panel kısayolu değiştirici içermek zorunda
    olduğu için hiçbir harf INSERT modunda kaçırılamaz. """
    pencere.show()
    QTest.keyClick(pencere.editor, Qt.Key.Key_I, text="i")
    QTest.keyClicks(pencere.editor, "insan")
    assert pencere.editor.toPlainText() == "insan"


def test_sonradan_acilan_sekme_guncel_haritayi_alir(pencere):
    pencere.show()
    harita, _u = keymap.build({"tab_new": "ctrl+t"})
    pencere.editor_tabs.apply_keymap(harita)

    yeni = pencere.editor_tabs.new_tab()
    onceki = pencere.editor_tabs.count()
    QTest.keyClick(yeni, Qt.Key.Key_T, CTRL)
    assert pencere.editor_tabs.count() == onceki + 1


def test_escape_yeniden_atanabilir(pencere):
    """ clear_search varsayılan 'escape'; başka bir tuşa alınabilmeli. """
    pencere.show()
    harita, _u = keymap.build({"clear_search": "x"})
    pencere.editor_tabs.apply_keymap(harita)

    editor = pencere.editor
    editor.setPlainText("bir foo iki")
    editor.search("foo")
    assert editor.extraSelections()

    QTest.keyClick(editor, Qt.Key.Key_X, text="x")
    assert editor.extraSelections() == []
```

- [ ] **Step 2: Testlerin kırmızı olduğunu gör**

Run: `.venv/bin/python -m pytest tests/test_shortcut_config.py -q`
Expected: FAIL — `AttributeError: 'EditorTabs' object has no attribute 'apply_keymap'`

- [ ] **Step 3: `ui/components/code_editor.py`'yi değiştir**

Import satırlarına ekle:

```python
from core import keymap
from ui import keys
```

`__init__` içinde, `self.state_machine = StateMachine(self)` satırının altına:

```python
        # Ayar dosyasından gelen tuş haritası (bkz. apply_keymap). Varsayılanla
        # başlıyoruz: bu widget IDEWindow.apply_settings'ten ÖNCE kuruluyor.
        self._keymap = keymap.defaults()
```

`_PANEL_MODIFIERS` sınıf değişkenini ve üstündeki yorumu **sil**; yerine:

```python
    def apply_keymap(self, new_keymap):
        """ Ayar dosyasındaki [shortcuts] bölümünden üretilen harita. Açılışta
        ve ':reload'da EditorTabs üzerinden çağrılır. """
        self._keymap = new_keymap

    def _panel_signal(self, action):
        """ Panel eylemi -> bu widget'ın sinyali. TerminalView ve WelcomePage
        aynı eylemleri kendi sinyal adlarına eşler; komut böylece odağın
        bulunduğu yere uygulanır. """
        return {
            "terminal_focus": self.terminal_focus_requested,
            "tab_new": self.tab_new_requested,
            "tab_close": self.tab_close_requested,
            "tab_next": self.tab_next_requested,
            "tab_prev": self.tab_prev_requested,
        }[action]
```

`keyPressEvent`'in başındaki Alt+Shift bloğunu şununla değiştir:

```python
        # Panel ailesi her modda çalışır; bu yüzden mod dağıtımından önce
        # bakılır. Terminaldeki (TerminalView) ve karşılama sayfasındaki
        # eşleme ile aynı eylemler: komut, odağın bulunduğu yere — burada
        # editör sekmelerine — uygulanır.
        action = keys.match(event, self._keymap, "panel")
        if action is not None:
            self._panel_signal(action).emit()
            return
```

`handle_normal_mode`'un gövdesini şununla değiştir (nav_keys tanımı aynen kalır):

```python
            if event.key() in nav_keys or event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                super().keyPressEvent(event)
                return

            # Escape tuzağı burada kendiliğinden çözülüyor: Escape artık
            # event.text() ('\x1b') üzerinden değil, 'escape' tuş ADI
            # üzerinden eşleşiyor (bkz. ui/keys.normal_binding).
            action = keys.match(event, self._keymap, "normal")
            if action == "clear_search":
                self.clear_search()
            elif action is not None:
                self.state_machine.handle_normal_action(action)
            elif event.text() and event.modifiers() in (Qt.KeyboardModifier.NoModifier,
                                                        Qt.KeyboardModifier.ShiftModifier):
                pass   # yazılabilir ama bağlanmamış tuş: NORMAL modda yutulur
            else:
                event.ignore()
```

- [ ] **Step 4: `core/state_machine.py`'yi değiştir**

`handle_normal_key`'i tamamen şununla değiştir:

```python
    def handle_normal_action(self, action):
        """ NORMAL moddaki bağlanmış eylemler. Hangi TUŞUN hangi eyleme
        karşılık geldiği artık burada değil, ayar dosyasından üretilen tuş
        haritasında (bkz. core/keymap.py); burası yalnız eylemi uygular.

        'clear_search' burada yok: arama vurgusu editörün kendi durumu, onu
        ModalEditor doğrudan ele alıyor. """
        if action == "insert_mode":
            self._enter_insert_mode()
        elif action == "command_line":
            self.start_command_line()
        elif action == "search_next":
            self.editor.search_next()
        elif action == "search_prev":
            self.editor.search_next(backward=True)
```

- [ ] **Step 5: `ui/components/editor_tabs.py`'yi değiştir**

Import satırlarına ekle:

```python
from core import keymap
```

`__init__` içinde, `self.new_tab()` çağrısının **ÜSTÜNE** (sıra önemli — `new_tab` haritayı okuyor):

```python
        # Sekme fabrikası: her yeni ModalEditor güncel haritayı buradan alır.
        self._keymap = keymap.defaults()
```

`new_tab` içinde `self._wire(editor)` satırının altına:

```python
        editor.apply_keymap(self._keymap)
```

Sınıfa yeni metot ekle (`# --- Erişimciler ---` bölümünün üstüne):

```python
    def apply_keymap(self, new_keymap):
        """ Tuş haritasını saklar ve açık tüm editörlere uygular. Saklamak
        şart: sonradan açılan sekmeler de güncel haritayı almalı. """
        self._keymap = new_keymap
        for editor in self.editors():
            editor.apply_keymap(new_keymap)
```

- [ ] **Step 6: `handle_normal_key` çağrısı kalmadığını doğrula**

Run: `grep -rn "handle_normal_key" --include='*.py' .`
Expected: **hiç çıktı yok.**

- [ ] **Step 7: Testleri koştur**

Run: `.venv/bin/python -m pytest tests/test_shortcut_config.py tests/test_editor_shortcuts.py tests/test_state_machine.py tests/test_command_palette.py -q`
Expected: PASS. `tests/test_editor_shortcuts.py` **değiştirilmeden** geçmeli — varsayılanlar değişmedi.

- [ ] **Step 8: Tüm paketi koştur**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add ui/components/code_editor.py core/state_machine.py ui/components/editor_tabs.py tests/test_shortcut_config.py
git commit -m "feat: editör tuş dağıtımı haritadan geçiyor"
```

---

### Task 6: `TerminalView` / `TerminalPanel` — terminal dağıtımı

**Files:**
- Modify: `ui/components/terminal_panel.py` (`TerminalView.__init__`, `_PANEL_MODIFIERS` sil, `keyPressEvent`, yeni `apply_keymap`; `TerminalPanel.__init__`, `_add_view`, yeni `apply_keymap`)
- Test: `tests/test_shortcut_config.py` (ekleme)

**Interfaces:**
- Consumes: `keys.match`, `keymap.defaults`, `EditorTabs.apply_keymap` deseni.
- Produces:
  - `TerminalView.apply_keymap(keymap) -> None`
  - `TerminalPanel.apply_keymap(keymap) -> None` — saklar + açık tüm görünümlere uygular; `_add_view` yenisine verir.

- [ ] **Step 1: Testleri yaz (kırmızı olmalı)**

`tests/test_shortcut_config.py` sonuna ekle:

```python
# --- Terminal dağıtımı ---

def test_terminalde_panel_kisayolu_yeniden_atanabilir(pencere):
    pencere.show()
    pencere.terminal_panel.toggle()          # ':term' — panel açılır, bir sekme kurulur
    harita, _u = keymap.build({"tab_new": "ctrl+t"})
    pencere.terminal_panel.apply_keymap(harita)

    view = pencere.terminal_panel.stack.currentWidget()
    onceki = pencere.terminal_panel.stack.count()
    QTest.keyClick(view, Qt.Key.Key_T, CTRL)
    assert pencere.terminal_panel.stack.count() == onceki + 1


def test_terminalde_yeniden_atanan_tus_shelle_gitmez(pencere):
    """ Kısayol olarak eşleşen tuş terminale bayt olarak YAZILMAMALI. """
    pencere.show()
    pencere.terminal_panel.toggle()
    harita, _u = keymap.build({"terminal_focus": "ctrl+g"})
    pencere.terminal_panel.apply_keymap(harita)

    view = pencere.terminal_panel.stack.currentWidget()
    yazilanlar = []
    view._process.write = lambda data: yazilanlar.append(data)

    QTest.keyClick(view, Qt.Key.Key_G, CTRL)
    assert yazilanlar == []


def test_sonradan_acilan_terminal_sekmesi_guncel_haritayi_alir(pencere):
    pencere.show()
    pencere.terminal_panel.toggle()
    harita, _u = keymap.build({"tab_close": "ctrl+q"})
    pencere.terminal_panel.apply_keymap(harita)

    yeni = pencere.terminal_panel.new_tab()
    assert yeni._keymap.binding_of("tab_close") == (frozenset({"ctrl"}), "q")
```

- [ ] **Step 2: Testlerin kırmızı olduğunu gör**

Run: `.venv/bin/python -m pytest tests/test_shortcut_config.py -q -k terminal`
Expected: FAIL — `AttributeError: 'TerminalPanel' object has no attribute 'apply_keymap'`

- [ ] **Step 3: `TerminalView`'i değiştir**

`ui/components/terminal_panel.py` import satırlarına ekle:

```python
from core import keymap
from ui import keys
```

`TerminalView` içindeki `_PANEL_MODIFIERS = ...` satırını **sil**.

`TerminalView.__init__` içinde `self.setFocusPolicy(...)` satırının altına:

```python
        # Ayar dosyasından gelen tuş haritası; panel _add_view'de günceliyle
        # değiştiriyor (bkz. TerminalPanel.apply_keymap).
        self._keymap = keymap.defaults()
```

`TerminalView.keyPressEvent`'in başındaki Alt+Shift bloğunu şununla değiştir:

```python
        # Panel kısayolları terminale gönderilmez, panele iletilir.
        action = keys.match(event, self._keymap, "panel")
        if action is not None:
            {
                "terminal_focus": self.return_focus_requested,
                "tab_new": self.new_tab_requested,
                "tab_close": self.close_tab_requested,
                "tab_next": self.next_tab_requested,
                "tab_prev": self.prev_tab_requested,
            }[action].emit()
            return
```

`focusNextPrevChild`'ın altına:

```python
    def apply_keymap(self, new_keymap):
        self._keymap = new_keymap
```

- [ ] **Step 4: `TerminalPanel`'i değiştir**

`TerminalPanel.__init__` içinde, `self._rows = TerminalView.ROWS` satırının altına:

```python
        # Sekme fabrikası: her yeni TerminalView güncel haritayı _add_view'den
        # alır (_rows / _font ile aynı desen).
        self._keymap = keymap.defaults()
```

`_add_view` içinde, `if self._font is not None:` bloğunun **üstüne**:

```python
        view.apply_keymap(self._keymap)
```

`apply_settings`'in hemen altına:

```python
    def apply_keymap(self, new_keymap):
        """ Tuş haritasını saklar ve açık tüm oturumlara uygular. Saklamak
        şart: sonradan açılan sekmeler de güncel haritayı almalı. """
        self._keymap = new_keymap
        for i in range(self.stack.count()):
            self.stack.widget(i).apply_keymap(new_keymap)
```

- [ ] **Step 5: `TerminalPanel` docstring'ini düzelt**

Sınıf docstring'i panel işlemlerini sabit `Alt+Shift` ailesi olarak anlatıyor;
artık yapılandırılabilir. Şu cümleyi:

```
panel işlemleri Alt+Shift ailesindedir:
    T odağı editöre döndürür, N yeni sekme, W sekmeyi kapatır,
    Sağ/Sol sekmeler arasında gezer.
```

şununla değiştir:

```
panel işlemleri tuş haritasından gelir (varsayılan Alt+Shift ailesi):
    terminal_focus odağı editöre döndürür, tab_new yeni sekme,
    tab_close sekmeyi kapatır, tab_next/tab_prev sekmeler arasında gezer.
    Bkz. core/keymap.py ve ayar dosyasının [shortcuts] bölümü.
```

- [ ] **Step 6: Testleri koştur**

Run: `.venv/bin/python -m pytest tests/test_shortcut_config.py tests/test_terminal_command.py tests/test_terminal_process.py tests/test_bottom_panel.py -q`
Expected: PASS.

- [ ] **Step 7: Tüm paketi koştur**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add ui/components/terminal_panel.py tests/test_shortcut_config.py
git commit -m "feat: terminal tuş dağıtımı haritadan geçiyor"
```

---

### Task 7: `WelcomePage` — dağıtım ve keymap'ten üretilen ipuçları

**Files:**
- Modify: `ui/components/welcome_page.py` (`_PANEL_MODIFIERS` sil, `HINTS` biçimi, `__init__`, `keyPressEvent`, yeni `apply_keymap` / `_panel_signal` / `_hint_key`)
- Test: `tests/test_shortcut_config.py` (ekleme)

**Interfaces:**
- Consumes: `keys.match`, `keymap.defaults`, `Keymap.label` (Task 2-3).
- Produces: `WelcomePage.apply_keymap(keymap) -> None` — haritayı saklar **ve ipucu metnini yeniden kurar**.

- [ ] **Step 1: Testleri yaz (kırmızı olmalı)**

`tests/test_shortcut_config.py` sonuna ekle:

```python
# --- Karşılama sayfası ---

def test_karsilama_sayfasinda_panel_kisayolu_yeniden_atanabilir(pencere):
    pencere.show()
    pencere.editor_tabs.close_current_tab()
    harita, _u = keymap.build({"tab_new": "ctrl+t"})
    pencere.welcome_page.apply_keymap(harita)

    QTest.keyClick(pencere.welcome_page, Qt.Key.Key_T, CTRL)
    assert pencere.editor_tabs.count() == 1


def test_karsilama_sayfasinda_komut_satiri_tusu_yeniden_atanabilir(pencere):
    pencere.show()
    pencere.editor_tabs.close_current_tab()
    harita, _u = keymap.build({"command_line": ","})
    pencere.welcome_page.apply_keymap(harita)

    QTest.keyClicks(pencere.welcome_page, ",")
    assert pencere.welcome_page.current_mode == "COMMAND"


def test_karsilama_ipuclari_varsayilan_haritayi_gosterir(pencere):
    metin = pencere.welcome_page._hints_label.text()
    assert "Alt+Shift+N" in metin
    assert "Alt+Shift+T" in metin


def test_karsilama_ipuclari_haritayi_yansitir(pencere):
    harita, _u = keymap.build({"tab_new": "ctrl+t"})
    pencere.welcome_page.apply_keymap(harita)

    metin = pencere.welcome_page._hints_label.text()
    assert "Ctrl+T" in metin
    assert "Alt+Shift+N" not in metin
```

- [ ] **Step 2: Testlerin kırmızı olduğunu gör**

Run: `.venv/bin/python -m pytest tests/test_shortcut_config.py -q -k karsilama`
Expected: FAIL — `AttributeError: 'WelcomePage' object has no attribute 'apply_keymap'`

- [ ] **Step 3: `ui/components/welcome_page.py`'yi değiştir**

Import satırlarına ekle:

```python
from core import keymap
from ui import keys
```

`_PANEL_MODIFIERS = ...` satırını ve üstündeki yorumu **sil**.

`HINTS`'i şununla değiştir:

```python
    # (tür, değer, açıklama). Tür 'command' ise değer olduğu gibi gösterilir;
    # 'action' ise geçerli tuş haritasından üretilir — kısayolunu değiştiren
    # kullanıcıya yalan söylemesin (bkz. apply_keymap).
    HINTS = [
        ("command", ":ts", "dosya bul"),
        ("command", ":openfile <yol>", "dosya aç"),
        ("command", ":tabnew", "yeni boş sekme"),
        ("action", "tab_new", "yeni boş sekme"),
        ("action", "terminal_focus", "terminale geç"),
        ("command", ":qa", "çıkış"),
    ]
```

`__init__` içinde `hints` yerel değişkenini şuna çevir:

```python
        self._keymap = keymap.defaults()
        self._hints_label = QLabel()
        self._hints_label.setObjectName("welcomeHints")
        self._hints_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._refresh_hints()
```

ve layout satırını `layout.addWidget(self._hints_label)` yap.

`keyPressEvent`'i şununla değiştir:

```python
    def keyPressEvent(self, event):
        action = keys.match(event, self._keymap, "panel")
        if action is not None:
            self._panel_signal(action).emit()
            return

        if self.current_mode == "COMMAND":
            self.state_machine.handle_command_key(event)
        elif keys.match(event, self._keymap, "normal") == "command_line":
            self.state_machine.start_command_line()
        else:
            # 'insert_mode', 'search_next' gibi tampon gerektiren eylemlerin
            # burada karşılığı yok.
            event.ignore()
```

`focusNextPrevChild`'ın altına:

```python
    def apply_keymap(self, new_keymap):
        """ Haritayı saklar ve ipucu metnini yeniden kurar; ':reload' sonrası
        da doğru kalsın. """
        self._keymap = new_keymap
        self._refresh_hints()

    def _refresh_hints(self):
        self._hints_label.setText("\n".join(
            f"{self._hint_key(kind, value):<16}{description}"
            for kind, value, description in self.HINTS))

    def _hint_key(self, kind, value):
        return value if kind == "command" else self._keymap.label(value)

    def _panel_signal(self, action):
        """ ModalEditor ile aynı eylemler, aynı sinyal adları — IDEWindow
        ikisini de tek tablodan bağlıyor. """
        return {
            "terminal_focus": self.terminal_focus_requested,
            "tab_new": self.tab_new_requested,
            "tab_close": self.tab_close_requested,
            "tab_next": self.tab_next_requested,
            "tab_prev": self.tab_prev_requested,
        }[action]
```

- [ ] **Step 4: Testleri koştur**

Run: `.venv/bin/python -m pytest tests/test_shortcut_config.py tests/test_welcome_page.py -q`
Expected: PASS. `tests/test_welcome_page.py` **değiştirilmeden** geçmeli.

- [ ] **Step 5: Tüm paketi koştur**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ui/components/welcome_page.py tests/test_shortcut_config.py
git commit -m "feat: karşılama sayfası tuş haritasını kullanıyor ve gösteriyor"
```

---

### Task 8: `IDEWindow.apply_settings` — haritayı kur ve dağıt

**Files:**
- Modify: `ui/main_window.py` (import, `apply_settings`)
- Test: `tests/test_shortcut_config.py` (ekleme)

**Interfaces:**
- Consumes: `keymap.build`, üç widget'ın `apply_keymap`'i (Task 2, 5, 6, 7).
- Produces: `IDEWindow.keymap` — geçerli `Keymap`. Açılış ve `:reload` **tek** bu yoldan geçer (K9).

- [ ] **Step 1: Testleri yaz (kırmızı olmalı)**

Önce `tests/test_shortcut_config.py`'nin **import bloğuna** ekle:

```python
import core.config as config
from ui.main_window import IDEWindow
```

Sonra dosyanın sonuna ekle:

```python
# --- Uçtan uca: ayar dosyasından pencereye ---

def test_ayardan_gelen_kisayol_pencereye_ulasir(qapp):
    ayarlar = config.default_settings()
    ayarlar["shortcuts"] = {"tab_new": "ctrl+t"}

    pencere = IDEWindow(settings=ayarlar)
    try:
        pencere.show()
        onceki = pencere.editor_tabs.count()
        QTest.keyClick(pencere.editor, Qt.Key.Key_T, CTRL)
        assert pencere.editor_tabs.count() == onceki + 1
    finally:
        pencere.terminal_panel.shutdown()
        pencere.close()
        pencere.deleteLater()
        qapp.processEvents()


def test_gecersiz_kisayol_uyarir_ve_varsayilanda_birakir(qapp, capsys):
    ayarlar = config.default_settings()
    ayarlar["shortcuts"] = {"tab_new": "i"}          # K6 ihlali

    pencere = IDEWindow(settings=ayarlar)
    try:
        assert "tab_new" in capsys.readouterr().out
        assert pencere.keymap.binding_of("tab_new") == (frozenset({"alt", "shift"}), "n")
    finally:
        pencere.terminal_panel.shutdown()
        pencere.close()
        pencere.deleteLater()
        qapp.processEvents()


def test_reload_kisayolu_canli_degistirir(pencere, tmp_path, monkeypatch):
    """ K9: keymap de apply_settings'ten geçtiği için ':reload' canlı yeniden
    atamayı bedavaya veriyor. """
    yol = tmp_path / "config.toml"
    yol.write_text('[shortcuts]\ntab_new = "ctrl+t"\n', encoding="utf-8")
    monkeypatch.setattr("core.config.config_path", lambda: str(yol))

    pencere.show()
    pencere.reload_settings()

    onceki = pencere.editor_tabs.count()
    QTest.keyClick(pencere.editor, Qt.Key.Key_T, CTRL)
    assert pencere.editor_tabs.count() == onceki + 1


def test_reload_karsilama_ipuclarini_tazeler(pencere, tmp_path, monkeypatch):
    yol = tmp_path / "config.toml"
    yol.write_text('[shortcuts]\ntab_new = "ctrl+t"\n', encoding="utf-8")
    monkeypatch.setattr("core.config.config_path", lambda: str(yol))

    pencere.show()
    pencere.reload_settings()
    assert "Ctrl+T" in pencere.welcome_page._hints_label.text()


def test_reload_terminal_oturumunu_koruyarak_yeniden_atar(pencere, tmp_path, monkeypatch):
    yol = tmp_path / "config.toml"
    yol.write_text('[shortcuts]\ntab_close = "ctrl+q"\n', encoding="utf-8")
    monkeypatch.setattr("core.config.config_path", lambda: str(yol))

    pencere.show()
    pencere.terminal_panel.toggle()
    onceki = pencere.terminal_panel.stack.count()

    pencere.reload_settings()

    assert pencere.terminal_panel.stack.count() == onceki      # oturum korundu
    view = pencere.terminal_panel.stack.currentWidget()
    assert view._keymap.binding_of("tab_close") == (frozenset({"ctrl"}), "q")
```

- [ ] **Step 2: Testlerin kırmızı olduğunu gör**

Run: `.venv/bin/python -m pytest tests/test_shortcut_config.py -q -k "ayardan or gecersiz or reload"`
Expected: FAIL — `Ctrl+T` sekme açmıyor; `AttributeError: 'IDEWindow' object has no attribute 'keymap'`

- [ ] **Step 3: `ui/main_window.py`'yi değiştir**

`from core import config` satırının hemen altına:

```python
from core import keymap as keymap_module
```

> `keymap_module` diye adlandırılıyor çünkü `self.keymap` özniteliği aynı
> adı taşıyor; modülü gölgelememesi için ayrıştırıldı.

`apply_settings` içinde, `self.terminal_panel.apply_settings(...)` satırının **altına**:

```python
        # Tuş haritası da buradan dağıtılıyor: açılış ve ':reload' tek yoldan
        # geçtiği için canlı yeniden atama ayrıca bir iş gerektirmiyor.
        # Uyarılar palet/font uyarılarıyla aynı desende basılıyor.
        self.keymap, keymap_warnings = keymap_module.build(self.settings["shortcuts"])
        for warning in keymap_warnings:
            print(warning)

        self.editor_tabs.apply_keymap(self.keymap)
        self.terminal_panel.apply_keymap(self.keymap)
        self.welcome_page.apply_keymap(self.keymap)
```

- [ ] **Step 4: Testleri koştur**

Run: `.venv/bin/python -m pytest tests/test_shortcut_config.py tests/test_settings_reload.py -q`
Expected: PASS.

- [ ] **Step 5: Tüm paketi koştur**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — mevcut 197 test hiç değişmeden + yeni testler.

- [ ] **Step 6: Elle doğrulama (spec'teki 8 adım)**

```bash
mkdir -p /tmp/decode-kisayol
cat > /tmp/decode-kisayol/config.toml <<'EOF'
[shortcuts]
tab_new = "ctrl+t"
insert_mode = "a"
EOF
XDG_CONFIG_HOME=/tmp/decode-kisayol/xdg python3 main.py
```

Spec'in "Elle doğrulama" bölümündeki 8 maddeyi sırayla geç. `XDG_CONFIG_HOME`
ile çalıştırıldığında `config.config_path()` oraya bakar; gerçek
`~/.config/decode/config.toml` dosyasına dokunulmaz — dosyayı
`$XDG_CONFIG_HOME/decode/config.toml` yoluna koy.

- [ ] **Step 7: Commit**

```bash
git add ui/main_window.py tests/test_shortcut_config.py
git commit -m "feat: tuş haritası apply_settings'ten dağıtılıyor"
```

---

### Task 9: Belgeler

**Files:**
- Modify: `README.md` ("Kısayollar" ve "Ayarlar" bölümleri)
- Modify: `CLAUDE.md` (Alt+Shift paragrafı, "No Ctrl shortcuts" cümlesi, Settings bölümü)
- Modify: `docs/Roadmap.md` (Faz 3 ayar dosyası maddesi)
- Create: `docs/sprint/sprint-13.md`
- Modify: `docs/sprint/README.md` (tablo + "Aktif sprint" satırı)

**Interfaces:**
- Consumes: bitmiş uygulama (Task 1-8).
- Produces: yok (son görev).

- [ ] **Step 1: `README.md`'yi güncelle**

"Kısayollar" bölümünün sonundaki `Ctrl kısayolu bilinçli olarak kullanılmaz.`
satırını şununla değiştir:

```markdown
Varsayılanda Ctrl kısayolu kullanılmaz — ama bu yalnız varsayılan: tüm
kısayollar ayar dosyasının `[shortcuts]` bölümünden değiştirilebilir.

| Eylem | Varsayılan | Grup |
|---|---|---|
| `terminal_focus` | `alt+shift+t` | panel |
| `tab_new` | `alt+shift+n` | panel |
| `tab_close` | `alt+shift+w` | panel |
| `tab_next` | `alt+shift+right` | panel |
| `tab_prev` | `alt+shift+left` | panel |
| `insert_mode` | `i` | NORMAL |
| `command_line` | `:` | NORMAL |
| `search_next` | `n` | NORMAL |
| `search_prev` | `N` | NORMAL |
| `clear_search` | `escape` | NORMAL |

İki kural var:

- **Panel** kısayolları her modda çalışır, bu yüzden `ctrl`, `alt` ya da
  `meta`'dan en az birini içermek zorundadır — yoksa o harf INSERT modunda
  yazılamaz hale gelirdi.
- **NORMAL** mod kısayolları tek karakter ya da `escape`'tir; değiştirici
  öneki alamazlar ve büyük/küçük harf ayrımı korunur (`n` ile `N` farklı
  komut).

İki eylem aynı tuşa düşerse yukarıdaki tablo sırasında önce gelen kazanır ve
diğeri için bir uyarı basılır.
```

"Ayarlar" bölümündeki bölüm listesine `[shortcuts]` ekle:

```markdown
`[editor]` (font ailesi/boyutu, sekme genişliği, `expand_tabs`, satır
numarası), `[terminal]` (satır sayısı), `[shortcuts]` (10 eylemin tuş
ataması) ve `[colors]` (17 adlandırılmış Tokyo Night tokeni) bölümleri vardır.
```

- [ ] **Step 2: `CLAUDE.md`'yi güncelle**

"Modal editing model" bölümündeki Alt+Shift paragrafını şununla değiştir:

```markdown
Panel shortcuts (every mode, default `Alt+Shift`): `T` moves focus editor ↔
terminal, `N` new tab, `W` close tab, `←`/`→` switch tabs. `ModalEditor`,
`TerminalView` and `WelcomePage` all ask the same question — `ui.keys.match(event,
self._keymap, "panel")` — and map the resulting *action* to their own signal
names, so the command applies to whatever currently has focus. `Alt+Shift+T`
from the editor only does something when the terminal panel is already open
(`TerminalPanel.focus_terminal`), by design. **No Ctrl shortcuts are used by
default** — that is a deliberate project decision, as is entering search via
`:find` rather than a bare `/`; but every binding is user-configurable through
the `[shortcuts]` section (see "Settings").
```

Aynı bölümde NORMAL mod cümlesine ekle: bare keys `i`/`:`/`n`/`N` ve Escape'in
artık **yapılandırılabilir** olduğu, `handle_normal_key` yerine
`StateMachine.handle_normal_action(action)`'ın çağrıldığı.

"Architecture" listesine iki madde ekle:

```markdown
- **`core/keymap.py`** — the single source for key bindings: the ordered `ACTIONS`
  table (name, group, default, description), `parse`/`build`/`defaults`, the
  `Keymap` object (`binding_of`, `action_for`, `label`) and conflict resolution.
  Pure Python, no Qt import. Two groups with deliberately different vocabularies:
  `panel` bindings must carry `ctrl`/`alt`/`meta` (otherwise that letter would
  become untypeable in INSERT mode) and are case-insensitive; `normal` bindings
  are a single character or `escape`, take no modifier prefix, and are
  case-sensitive (`n` ≠ `N`).
- **`ui/keys.py`** — the thin Qt shell that turns a `QKeyEvent` into the binding
  shape `core/keymap.py` produces. Which key *names* are valid is `keymap`'s
  knowledge; only their `Qt.Key` values live here, and
  `tests/test_shortcut_config.py` guards the two tables against drift.
```

"Settings" bölümüne `[shortcuts]`'ı ekle ve **bu kaymayı da düzelt:**
`:reload` anlatımındaki `editor.set_highlighter_for_file(editor.file_path,
force=True)` artık yanlış — `force` parametresi yok, karşılığı
`ModalEditor.refresh_theme()`.

- [ ] **Step 3: `docs/Roadmap.md`'yi güncelle**

Faz 3'teki "Ayar dosyası — tamamlandı" maddesine ekle:

```markdown
  `[shortcuts]` altında 10 eylemin tuş ataması ([Sprint 13](sprint/sprint-13.md)).
```

- [ ] **Step 4: `docs/sprint/sprint-13.md`'yi yaz**

`docs/sprint/README.md`'deki şablonu kullan. Hedef: "Kısayollar ayar
dosyasından özelleştirilebilir hale geldi." Çıktılar: `core/keymap.py`,
`ui/keys.py`, `[shortcuts]`, üç widget'ın dağıtımı, keymap'ten üretilen
ipuçları. Teknik notlar: K6'nın gerekçesi (değiştiricisiz panel bağlaması
harfi INSERT modunda yazılamaz kılardı), K3'ün kabul edilmiş bedeli, iki
grubun büyük/küçük harf asimetrisi, kayma bekçisi testi. Devreden: `:keys`
komutu.

- [ ] **Step 5: `docs/sprint/README.md`'yi güncelle**

Tabloya satır ekle:

```markdown
| [13](sprint-13.md) | 09 Eyl 2026 | Kısayol yapılandırması | Tamamlandı |
```

"**Aktif sprint:**" satırını `yok — son iş [Sprint 13](sprint-13.md).` yap.

- [ ] **Step 6: Tüm paketi son kez koştur**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add README.md CLAUDE.md docs/Roadmap.md docs/sprint/sprint-13.md docs/sprint/README.md
git commit -m "docs: kısayol yapılandırması belgeleri ve Sprint 13 günlüğü"
```

---

## Bitiş

Dal `kisayol-yapilandirmasi`, dokuz commit. Birleştirme kararı için
`superpowers:finishing-a-development-branch` skill'ini kullan.
