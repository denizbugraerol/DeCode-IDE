""" Ayarların editör davranışına yansıması. """
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

import core.config as config
from ui.components.code_editor import ModalEditor


def _editor(qapp, **degisiklikler):
    ayarlar = config.default_settings()["editor"]
    ayarlar.update(degisiklikler)
    editor = ModalEditor()
    editor.apply_settings(ayarlar)
    return editor


def test_sekme_genisligi_uygulanir(qapp):
    dar = _editor(qapp, tab_width=2)
    genis = _editor(qapp, tab_width=8)
    assert genis.tabStopDistance() > dar.tabStopDistance() > 0


def test_expand_tabs_kapaliyken_gercek_tab_yazilir(qapp):
    editor = _editor(qapp, expand_tabs=False)
    QTest.keyClicks(editor, "i")          # INSERT
    QTest.keyClick(editor, Qt.Key.Key_Tab)
    assert editor.toPlainText() == "\t"


def test_expand_tabs_acikken_bosluk_yazilir(qapp):
    editor = _editor(qapp, expand_tabs=True, tab_width=4)
    QTest.keyClicks(editor, "i")
    QTest.keyClick(editor, Qt.Key.Key_Tab)
    assert editor.toPlainText() == "    "


def test_satir_numarasi_kapatilabilir(qapp):
    acik = _editor(qapp, line_numbers=True)
    kapali = _editor(qapp, line_numbers=False)
    assert acik.line_number_area_width() > 0
    assert kapali.line_number_area_width() == 0
    # isVisible() burada anlamsız olurdu: editör hiç show() edilmediği için
    # gutter zaten "görünmüyor" sayılır (ata gösterilmedi), line_numbers=False
    # hiçbir şey yapmasa bile isVisible() False dönerdi. isHidden() ise ata
    # görünürlüğünden bağımsız, widget'ın kendi açık/kapalı durumunu yansıtır.
    assert kapali.line_number_area.isHidden()
    assert not acik.line_number_area.isHidden()


def test_normal_modda_tab_metne_dokunmaz(qapp):
    """ Tab yalnız INSERT modunda yazar; NORMAL modda hiçbir şey olmamalı. """
    editor = _editor(qapp, expand_tabs=True)
    QTest.keyClick(editor, Qt.Key.Key_Tab)
    assert editor.toPlainText() == ""
