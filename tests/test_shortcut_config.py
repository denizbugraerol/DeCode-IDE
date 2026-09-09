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
