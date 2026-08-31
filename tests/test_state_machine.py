""" Komut satırı ayrıştırmasının davranışı (editör üzerinden, uçtan uca). """
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from ui.components.code_editor import ModalEditor


def _editor(qapp, metin="bir foo\niki foo\nuc"):
    editor = ModalEditor()
    editor.setPlainText(metin)
    return editor


def test_find_komutu_arar(qapp):
    editor = _editor(qapp)
    QTest.keyClicks(editor, ":find foo")
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.search_pattern == "foo"
    assert editor.textCursor().selectedText() == "foo"


def test_n_tusu_sonraki_eslesmeye_gider(qapp):
    editor = _editor(qapp)
    editor.search("foo")
    ilk = editor.textCursor().selectionStart()
    # keyClicks (keyClick değil): tuşun 'text()'ini kesin olarak üretsin —
    # 'n' ile 'N' ayrımı tam da buna dayanıyor.
    QTest.keyClicks(editor, "n")
    assert editor.textCursor().selectionStart() != ilk


def test_buyuk_n_geri_gider(qapp):
    editor = _editor(qapp)
    editor.search("foo")
    editor.search_next()
    konum = editor.textCursor().selectionStart()
    QTest.keyClicks(editor, "N")
    assert editor.textCursor().selectionStart() != konum


def test_find_komutu_oneri_listesinde(qapp):
    editor = _editor(qapp)
    eslesmeler = editor.state_machine._matches_for("fi")
    assert any(ad == "find" for ad, _aciklama in eslesmeler)


def test_replace_komutu_metni_degistirir(qapp):
    editor = _editor(qapp)
    QTest.keyClicks(editor, ":replace foo bar")
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert "foo" not in editor.toPlainText()
    assert editor.toPlainText().count("bar") == 2


def test_replace_tek_geri_al_adimi(qapp):
    editor = _editor(qapp)
    onceki = editor.toPlainText()
    QTest.keyClicks(editor, ":replace foo bar")
    QTest.keyClick(editor, Qt.Key.Key_Return)
    editor.undo()
    assert editor.toPlainText() == onceki
