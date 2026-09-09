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
