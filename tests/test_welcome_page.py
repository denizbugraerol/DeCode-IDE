""" Son sekme kapanınca kalan karşılama sayfası: uygulama açık kalmalı ve
komut satırı tampon gerektirmeyen komutlar için çalışmaya devam etmeli. """
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

ALT_SHIFT = Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier


def test_son_sekme_kapaninca_uygulama_kapanmaz(pencere):
    pencere.show()
    while pencere.editor_tabs.count():
        pencere.editor_tabs.close_current_tab()

    assert pencere.isVisible()
    assert pencere.editor_tabs.count() == 0
    assert pencere.welcome_page.isVisible()
    assert not pencere.editor_tabs.isVisible()


def test_karsilama_sayfasi_odagi_alir(pencere):
    pencere.show()
    pencere.editor_tabs.close_current_tab()
    assert pencere.focusWidget() is pencere.welcome_page


def test_karsilama_sayfasinda_komut_satiri_calisir(pencere):
    pencere.show()
    pencere.editor_tabs.close_current_tab()

    QTest.keyClicks(pencere.welcome_page, ":")
    assert pencere.welcome_page.current_mode == "COMMAND"
    assert pencere.command_line.isVisible()


def test_karsilama_sayfasindan_tabnew_sekme_acar(pencere):
    pencere.show()
    pencere.editor_tabs.close_current_tab()

    QTest.keyClicks(pencere.welcome_page, ":tabnew")
    QTest.keyClick(pencere.welcome_page, Qt.Key.Key_Return)

    assert pencere.editor_tabs.count() == 1
    assert not pencere.welcome_page.isVisible()
    assert pencere.editor_tabs.isVisible()


def test_karsilama_sayfasindan_qa_cikis_ister(pencere):
    pencere.show()
    pencere.editor_tabs.close_current_tab()

    cikislar = []
    pencere.welcome_page.quit_requested.connect(lambda: cikislar.append(True))

    QTest.keyClicks(pencere.welcome_page, ":qa")
    QTest.keyClick(pencere.welcome_page, Qt.Key.Key_Return)
    assert cikislar == [True]


def test_oneri_listesi_yalniz_calisan_komutlari_gosterir(pencere):
    pencere.show()
    pencere.editor_tabs.close_current_tab()

    adlar = [ad for ad, _a in pencere.welcome_page.state_machine._matches_for("")]
    assert "ts" in adlar and "tabnew" in adlar and "qa" in adlar
    # Tampon gerektirenler listede olmamalı
    assert "w" not in adlar and "find" not in adlar and "sym" not in adlar


def test_karsilama_sayfasi_alt_shift_n_ile_sekme_acar(pencere):
    pencere.show()
    pencere.editor_tabs.close_current_tab()

    QTest.keyClick(pencere.welcome_page, Qt.Key.Key_N, ALT_SHIFT)
    assert pencere.editor_tabs.count() == 1


def test_statusline_sekme_yok_gosterir(pencere):
    pencere.show()
    pencere.editor_tabs.close_current_tab()
    assert "Sekme yok" in pencere.status_line.file_label.text()
