""" Ayarların pencereye uygulanması. """
import core.config as config
from ui.main_window import IDEWindow


def test_varsayilan_ayarlarla_acilir(pencere):
    assert pencere.settings == config.DEFAULTS


def test_renk_ayari_stylesheete_gecer(qapp):
    ayarlar = config.default_settings()
    ayarlar["colors"] = {"bg": "#11111b"}

    pencere = IDEWindow(settings=ayarlar)
    try:
        assert "#11111b" in pencere.styleSheet()
    finally:
        pencere.terminal_panel.shutdown()
        pencere.close()
        pencere.deleteLater()
        qapp.processEvents()


def test_font_ayari_stylesheete_gecer(qapp):
    """ Font'u QSS sahipleniyor; ayarın oraya ulaştığını doğruluyoruz. """
    ayarlar = config.default_settings()
    ayarlar["editor"]["font_family"] = "JetBrains Mono"
    ayarlar["editor"]["font_size"] = 20

    pencere = IDEWindow(settings=ayarlar)
    try:
        qss = pencere.styleSheet()
        assert "'JetBrains Mono'" in qss
        assert "font-size: 20px" in qss     # editör
        assert "font-size: 16px" in qss     # statusline (-4)
    finally:
        pencere.terminal_panel.shutdown()
        pencere.close()
        pencere.deleteLater()
        qapp.processEvents()


def test_bilinmeyen_renk_tokeni_uyarir(qapp, capsys):
    ayarlar = config.default_settings()
    ayarlar["colors"] = {"pembe": "#ff00ff"}

    pencere = IDEWindow(settings=ayarlar)
    try:
        assert "pembe" in capsys.readouterr().out
    finally:
        pencere.terminal_panel.shutdown()
        pencere.close()
        pencere.deleteLater()
        qapp.processEvents()
