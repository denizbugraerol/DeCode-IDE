""" Yüzen listenin boyut sözleşmesi: en fazla MAX_VISIBLE_ROWS satır. """
import ui.theme as theme
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


# --- Kod incelemesi bulgusu (Bulgu 4): satırlar 'Fira Code', 13px'i sabit
# kodluyordu; font_family/font_size ayarı bu satırları hiç değiştirmiyordu
# (":ts"/":sym" ve komut önerileri -- uygulamadaki en çok kullanılan yüzen
# arayüz). _row_style artık ui/theme.font_family()/font_size('row') okuyor.

def test_row_style_varsayilan_fira_code_13px():
    """ set_font hiç çağrılmamışken (bugünkü sabit görünüm) bile satırlar
    'Fira Code'da ve 13px'te kalmalı -- varsayılan görünüm byte'ı byte'ına
    aynı olmalı koşulu. """
    liste = FloatingList()
    style = liste._row_style(selected=False)
    assert "font-family: 'Fira Code', 'Consolas', monospace;" in style
    assert "font-size: 13px;" in style


def test_row_style_font_ayarini_takip_eder():
    """ font_family = 'JetBrains Mono' seçildiğinde öneri/telescope
    satırları da değişmeli; eskiden yalnız 'Fira Code' sabitlenmişti. """
    try:
        theme.set_font("JetBrains Mono", 20)
        liste = FloatingList()
        style = liste._row_style(selected=False)
        assert "font-family: 'JetBrains Mono', 'Consolas', monospace;" in style
        assert "font-size: 18px;" in style     # row sapması: 20 - 2
    finally:
        theme.set_font("Fira Code", 15)
