""" Alt+Shift ailesi editör sekmelerinde de terminaldeki gibi çalışmalı:
komut, odağın bulunduğu yere uygulanır. """
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

ALT_SHIFT = Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier


def test_alt_shift_n_yeni_editor_sekmesi_acar(pencere):
    pencere.show()
    onceki = pencere.editor_tabs.count()
    QTest.keyClick(pencere.editor, Qt.Key.Key_N, ALT_SHIFT)
    assert pencere.editor_tabs.count() == onceki + 1


def test_alt_shift_w_editor_sekmesini_kapatir(pencere):
    pencere.show()
    pencere.editor_tabs.new_tab()
    onceki = pencere.editor_tabs.count()
    QTest.keyClick(pencere.editor, Qt.Key.Key_W, ALT_SHIFT)
    assert pencere.editor_tabs.count() == onceki - 1


def test_alt_shift_oklar_sekme_degistirir(pencere):
    pencere.show()
    pencere.editor_tabs.new_tab()
    pencere.editor_tabs.new_tab()
    ilk = pencere.editor_tabs.currentIndex()

    QTest.keyClick(pencere.editor, Qt.Key.Key_Right, ALT_SHIFT)
    ikinci = pencere.editor_tabs.currentIndex()
    assert ikinci != ilk

    QTest.keyClick(pencere.editor, Qt.Key.Key_Left, ALT_SHIFT)
    assert pencere.editor_tabs.currentIndex() == ilk


def test_alt_shift_t_terminale_odagi_tasir(pencere):
    """ Panel kapalıyken Alt+Shift+T bilerek bir şey yapmıyor (TerminalPanel.
    focus_terminal); panel ':term' ile açıldıktan sonra odağı taşıyor. """
    pencere.show()
    QTest.keyClick(pencere.editor, Qt.Key.Key_T, ALT_SHIFT)
    assert not pencere.terminal_panel.isVisible()

    pencere.terminal_panel.toggle()
    pencere.editor.setFocus()
    QTest.keyClick(pencere.editor, Qt.Key.Key_T, ALT_SHIFT)
    assert pencere.terminal_panel.isVisible()
    assert not pencere.editor.hasFocus()
