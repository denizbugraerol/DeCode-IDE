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
