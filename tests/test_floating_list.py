""" Yüzen listenin boyut sözleşmesi: en fazla MAX_VISIBLE_ROWS satır. """
from ui.components.bottom_panel import CommandSuggestions
from ui.components.floating_list import FloatingList


def test_bos_listede_satir_yok(qapp):
    liste = FloatingList()
    assert not liste.has_rows()


def test_yukseklik_max_visible_rows_ile_sinirli(qapp):
    liste = FloatingList()
    liste.set_rows([f"satır {i}" for i in range(20)], 0)
    liste.fit_to(480, 2000)
    uzun = liste.height()

    liste.set_rows(["tek satır"], 0)
    liste.fit_to(480, 2000)
    assert liste.height() < uzun


def test_command_suggestions_eski_apiyi_korur(qapp):
    kutu = CommandSuggestions()
    kutu.set_suggestions([("w", "dosyayı kaydet"), ("q", "sekmeyi kapat")], 1)
    assert kutu.has_suggestions()
