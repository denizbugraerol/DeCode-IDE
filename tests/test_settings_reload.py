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
    # Kurulu OLMAYAN bir aile (eski hâlinde "JetBrains Mono") kullanılamaz:
    # apply_settings artık fontu çözüyor ve QSS istenen aileyi değil ÇÖZÜLMÜŞ
    # aileyi taşıyor (bkz. ui/theme.resolve_font_family). Kurulu olmayan bir
    # ad verildiğinde sonuç fontconfig'in ikame tercihine kalırdı; sistemin
    # kendi mono fontunu sorup onu veriyoruz, böylece test her ortamda aynı
    # şeyi doğruluyor: geçerli bir font ayarı QSS'e aynen ulaşıyor.
    mono, _ = theme.resolve_font_family("Kesinlikle Kurulu Olmayan Font", 20)

    ayarlar = config.default_settings()
    ayarlar["editor"]["font_family"] = mono
    ayarlar["editor"]["font_size"] = 20

    pencere = IDEWindow(settings=ayarlar)
    try:
        qss = pencere.styleSheet()
        assert f"'{mono}'" in qss
        assert "font-size: 20px" in qss     # editör
        assert "font-size: 16px" in qss     # statusline (-4)
    finally:
        # Palet VE font durumu modül düzeyinde global; sıfırlanmazsa sonraki
        # testlere sızar (apply_settings artık theme.set_font'u da çağırıyor).
        theme.set_palette(dict(theme.DEFAULT_PALETTE))
        theme.set_font("Fira Code", 15)
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


# --- Kod incelemesi bulgusu (Bulgu 1): açılış ve ':reload' aynı yoldan
# geçmiyordu. _setup_ui, apply_settings paleti değiştirmeden ÖNCE tüm widget
# ağacını (ilk sekmenin highlighter'ı, statusline rozeti) kuruyor; bu ikisi
# rengi kendi içine KOPYALIYOR, theme.color(...) ile boyama anında OKUMUYOR.
# apply_settings bunları tazelemezse ilk sekme ve rozet uygulama ömrü boyunca
# (ya da ilk mod değişikliğine/dosya açılışına kadar) varsayılan paleti taşır.
# Aşağıdaki iki test bunu kanıtlar; ikisi de bu düzeltmeden ÖNCEKİ HEAD'de
# (aaf6768) kırmızıydı (bkz. fix-wave-report.md).

def test_acilista_ilk_sekmenin_highlighteri_paleti_alir(qapp):
    """ ModalEditor.__init__ (EditorTabs.__init__ -> new_tab, _setup_ui
    içinden) CppHighlighter'ı apply_settings paleti değiştirmeden ÖNCE kurar.
    apply_settings her açık editör için highlighter'ı tazelemezse ilk sekme
    varsayılan moru taşımaya devam eder. """
    ayarlar = config.default_settings()
    ayarlar["colors"] = {"purple": "#00ff00"}

    pencere = IDEWindow(settings=ayarlar)
    try:
        keyword_format = pencere.editor.highlighter.highlighting_rules[1][1]
        assert keyword_format.foreground().color().name() == "#00ff00"
    finally:
        theme.set_palette(dict(theme.DEFAULT_PALETTE))
        pencere.terminal_panel.shutdown()
        pencere.close()
        pencere.deleteLater()
        qapp.processEvents()


def test_acilista_mod_rozeti_paleti_alir(qapp):
    """ _setup_ui, _on_mode_changed(...) ile StatusLine.set_mode'u
    apply_settings paleti değiştirmeden ÖNCE bir kez çağırır; set_mode rengi
    setStyleSheet içine KOPYALAR. apply_settings rozeti yeniden çağırmazsa
    (varsayılan) NORMAL rozeti ilk mod değişikliğine kadar varsayılan
    mavide takılı kalır. """
    ayarlar = config.default_settings()
    ayarlar["colors"] = {"blue": "#ff0000"}

    pencere = IDEWindow(settings=ayarlar)
    try:
        assert "#ff0000" in pencere.status_line.mode_label.styleSheet()
    finally:
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
    try:
        QTest.keyClicks(pencere.editor, ":reload")
        QTest.keyClick(pencere.editor, Qt.Key.Key_Return)

        assert pencere.settings["editor"]["tab_width"] == 8
        assert "#11111b" in pencere.styleSheet()
    finally:
        # Palet modül düzeyinde global; sıfırlanmazsa sonraki testlere sızar.
        theme.set_palette(dict(theme.DEFAULT_PALETTE))


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


def test_reload_highlighter_rengini_yeniler(pencere, tmp_path, monkeypatch):
    """ Regresyon: sözdizimi renklendiricisinin kuralları QTextCharFormat
    içine kopyalanır ve palet değişince kendiliğinden güncellenmez;
    'reload_settings' (apply_settings üzerinden) bunları editor.refresh_theme()
    ile elle yeniden kurar. Bu çağrı düşerse test de düşer — bkz. sprint-09
    teknik notları. """
    yol = tmp_path / "config.toml"
    yol.write_text('[colors]\ngreen = "#00ff00"\n', encoding="utf-8")
    monkeypatch.setattr("core.config.config_path", lambda: str(yol))

    editor = pencere.editor
    editor.file_path = "x.py"
    editor.set_highlighter_for_file("x.py")

    pencere.show()
    try:
        pencere.reload_settings()
        assert editor.highlighter.string_format.foreground().color().name() == "#00ff00"
    finally:
        # Palet modül düzeyinde global; sıfırlanmazsa sonraki testlere sızar.
        theme.set_palette(dict(theme.DEFAULT_PALETTE))


def test_reload_arama_vurgu_rengini_yeniler(pencere, tmp_path, monkeypatch):
    """ Regresyon: arama eşleşmesi vurgusu da bir QTextCharFormat'a
    kopyalanır; 'reload_settings' _highlight_matches() ile yeniden
    kurmazsa eski renkte takılı kalır. """
    yol = tmp_path / "config.toml"
    yol.write_text('[colors]\nsearch = "#ff00ff"\n', encoding="utf-8")
    monkeypatch.setattr("core.config.config_path", lambda: str(yol))

    editor = pencere.editor
    editor.setPlainText("bir foo iki")
    editor.search("foo")

    pencere.show()
    try:
        pencere.reload_settings()
        assert editor.extraSelections()[0].format.background().color().name() == "#ff00ff"
    finally:
        # Palet modül düzeyinde global; sıfırlanmazsa sonraki testlere sızar.
        theme.set_palette(dict(theme.DEFAULT_PALETTE))
