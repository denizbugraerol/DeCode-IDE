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


import os


def test_cd_tamamlamasi_sadece_dizin(qapp, tmp_path, monkeypatch):
    (tmp_path / "klasor").mkdir()
    (tmp_path / "dosya.py").write_text("x")
    monkeypatch.chdir(tmp_path)

    editor = _editor(qapp)
    metinler = [ad for ad, _a in editor.state_machine._matches_for("cd ")]
    assert "cd klasor/" in metinler
    assert not any("dosya.py" in metin for metin in metinler)


def test_openfile_tamamlamasi_dosyalari_da_verir(qapp, tmp_path, monkeypatch):
    (tmp_path / "klasor").mkdir()
    (tmp_path / "dosya.py").write_text("x")
    monkeypatch.chdir(tmp_path)

    editor = _editor(qapp)
    metinler = [ad for ad, _a in editor.state_machine._matches_for("openfile ")]
    assert "openfile dosya.py" in metinler
    assert "openfile klasor/" in metinler


def test_openfile_komutu_open_path_requested_yayinlar(qapp, tmp_path, monkeypatch):
    (tmp_path / "dosya.py").write_text("x")
    monkeypatch.chdir(tmp_path)

    editor = _editor(qapp)
    yollar = []
    editor.open_path_requested.connect(yollar.append)

    QTest.keyClicks(editor, ":openfile dosya.py")
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert yollar == ["dosya.py"]


def test_openfile_olmayan_yol_sekme_acmaz(qapp, tmp_path, monkeypatch, capsys):
    """ Hatalı yol çökmemeli ve yeni sekme açmamalı; hata konsola yazılır. """
    from ui.main_window import IDEWindow

    monkeypatch.chdir(tmp_path)
    pencere = IDEWindow()
    onceki_sekme = pencere.editor_tabs.count()

    pencere._open_relative_path("yok/olmayan.py")

    assert pencere.editor_tabs.count() == onceki_sekme
    assert "bulunamadı" in capsys.readouterr().out
    pencere.terminal_panel.shutdown()
