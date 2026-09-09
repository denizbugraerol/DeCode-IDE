""" Qt kabuğu (ui/keys.py) ve kısayolların uçtan uca yapılandırılması. """
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtTest import QTest

import core.keymap as keymap
import ui.keys as keys

ALT_SHIFT = Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier
CTRL = Qt.KeyboardModifier.ControlModifier


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

    QTest.keyClick(pencere.editor, Qt.Key.Key_A)
    assert pencere.editor.current_mode == "INSERT"


def test_yeniden_atandiktan_sonra_eski_tus_metin_yazmaz(pencere):
    """ NORMAL modda bağlanmamış yazılabilir tuş YUTULUR (bugünkü davranış);
    metne düşmemeli. """
    pencere.show()
    harita, _u = keymap.build({"insert_mode": "a"})
    pencere.editor_tabs.apply_keymap(harita)

    QTest.keyClick(pencere.editor, Qt.Key.Key_I)
    assert pencere.editor.current_mode == "NORMAL"
    assert pencere.editor.toPlainText() == ""


def test_insert_modunda_harf_hala_yazilabiliyor(pencere):
    """ K6'nın koruduğu şey: panel kısayolu değiştirici içermek zorunda
    olduğu için hiçbir harf INSERT modunda kaçırılamaz. """
    pencere.show()
    QTest.keyClick(pencere.editor, Qt.Key.Key_I)
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

    QTest.keyClick(editor, Qt.Key.Key_X)
    assert editor.extraSelections() == []
