""" ModalEditor'ın arama davranışı: seçim, ilerleme, sarma, vurgu. """
from ui.components.code_editor import ModalEditor

METIN = "bir foo\niki foo\nuc"


def _editor(qapp):
    editor = ModalEditor()
    editor.setPlainText(METIN)
    return editor


def test_search_ilk_eslesmeyi_secer(qapp):
    editor = _editor(qapp)
    assert editor.search("foo") is True
    assert editor.textCursor().selectedText() == "foo"


def test_search_next_bir_sonrakine_gider(qapp):
    editor = _editor(qapp)
    editor.search("foo")
    ilk = editor.textCursor().selectionStart()
    editor.search_next()
    assert editor.textCursor().selectionStart() > ilk


def test_search_next_sona_gelince_sarar(qapp):
    editor = _editor(qapp)
    editor.search("foo")
    ilk = editor.textCursor().selectionStart()
    editor.search_next()
    editor.search_next()
    assert editor.textCursor().selectionStart() == ilk


def test_tum_eslesmeler_vurgulanir(qapp):
    editor = _editor(qapp)
    editor.search("foo")
    assert len(editor.extraSelections()) == 2


def test_clear_search_vurguyu_siler(qapp):
    editor = _editor(qapp)
    editor.search("foo")
    editor.clear_search()
    assert editor.extraSelections() == []


def test_desen_yoksa_search_next_false(qapp):
    editor = _editor(qapp)
    assert editor.search_next() is False


def test_normal_modda_escape_vurguyu_temizler(qapp):
    """ Escape'in event.text()'i boş değil ('\\x1b'); tuş dağıtımında
    'yazılabilir tuş' dalına düşerse vurgu temizlenmez — regresyon testi. """
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    editor = _editor(qapp)
    editor.search("foo")
    assert len(editor.extraSelections()) == 2

    QTest.keyClick(editor, Qt.Key.Key_Escape)
    assert editor.extraSelections() == []
    assert editor.current_mode == "NORMAL"
