""" StatusLine'ın mod rozeti: renk paletten, font ui/theme'in font
durumundan (bkz. ui/theme.set_font). Kod incelemesi Bulgu 4: rozetin
font-size'ı (11px) sabit kodluydu, font_size ayarını takip etmiyordu. """
import ui.theme as theme
from ui.components.bottom_panel import StatusLine


def test_set_mode_varsayilan_11px_fira_code(qapp):
    """ set_font hiç çağrılmamışken (bugünkü sabit görünüm) bile rozet
    'Fira Code'da ve 11px'te kalmalı -- varsayılan görünüm byte'ı byte'ına
    aynı olmalı koşulu. """
    status_line = StatusLine()
    style = status_line.mode_label.styleSheet()
    assert "font-family: 'Fira Code', 'Consolas', monospace;" in style
    assert "font-size: 11px;" in style


def test_set_mode_renk_moda_gore_degisir(qapp):
    status_line = StatusLine()
    status_line.set_mode("INSERT")
    assert theme.color("green") in status_line.mode_label.styleSheet()


def test_set_mode_font_ayarini_takip_eder(qapp):
    """ font_size = 20 seçildiğinde rozet de değişmeli; eskiden yalnız
    sabit 11px üretiliyordu. """
    try:
        theme.set_font("JetBrains Mono", 20)
        status_line = StatusLine()
        style = status_line.mode_label.styleSheet()
        assert "font-family: 'JetBrains Mono', 'Consolas', monospace;" in style
        assert "font-size: 16px;" in style      # status sapması: 20 - 4
    finally:
        theme.set_font("Fira Code", 15)
