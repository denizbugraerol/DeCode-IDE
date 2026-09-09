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
