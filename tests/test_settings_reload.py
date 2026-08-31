""" Ayarların pencereye uygulanması. """
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

import core.config as config
import ui.theme as theme
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
        # Palet modül düzeyinde global; sıfırlanmazsa sonraki testlere sızar.
        theme.set_palette(dict(theme.DEFAULT_PALETTE))
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
        # Palet modül düzeyinde global; sıfırlanmazsa sonraki testlere sızar.
        theme.set_palette(dict(theme.DEFAULT_PALETTE))
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
        # Palet modül düzeyinde global; sıfırlanmazsa sonraki testlere sızar.
        theme.set_palette(dict(theme.DEFAULT_PALETTE))
        pencere.terminal_panel.shutdown()
        pencere.close()
        pencere.deleteLater()
        qapp.processEvents()


def test_reload_dosyayi_yeniden_okur(pencere, tmp_path, monkeypatch):
    yol = tmp_path / "config.toml"
    yol.write_text('[colors]\nbg = "#11111b"\n\n[editor]\ntab_width = 8\n',
                   encoding="utf-8")
    monkeypatch.setattr("core.config.config_path", lambda: str(yol))

    pencere.show()
    QTest.keyClicks(pencere.editor, ":reload")
    QTest.keyClick(pencere.editor, Qt.Key.Key_Return)

    assert pencere.settings["editor"]["tab_width"] == 8
    assert "#11111b" in pencere.styleSheet()


def test_reload_acik_sekmeleri_korur(pencere, tmp_path, monkeypatch):
    monkeypatch.setattr("core.config.config_path", lambda: str(tmp_path / "yok.toml"))
    pencere.show()
    pencere.editor.setPlainText("kaybolmamalı")

    pencere.reload_settings()

    assert pencere.editor_tabs.count() == 1
    assert pencere.editor.toPlainText() == "kaybolmamalı"


def test_reload_karsilama_sayfasinda_da_var(pencere):
    pencere.show()
    pencere.editor_tabs.close_current_tab()
    adlar = [ad for ad, _a in pencere.welcome_page.state_machine._matches_for("")]
    assert "reload" in adlar
