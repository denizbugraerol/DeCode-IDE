""" Qt kabuğu (ui/keys.py) ve kısayolların uçtan uca yapılandırılması. """
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtTest import QTest

import core.keymap as keymap
import ui.keys as keys
import core.config as config
from ui.main_window import IDEWindow

ALT_SHIFT = Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier
CTRL = Qt.KeyboardModifier.ControlModifier


def _olay(key, modifiers=Qt.KeyboardModifier.NoModifier, text=""):
    return QKeyEvent(QKeyEvent.Type.KeyPress, key, modifiers, text)


def test_isimli_tus_tablolari_ortusuyor():
    """ Kayma bekçisi: core/keymap.py hangi adların GEÇERLİ olduğunu söyler,
    ui/keys.py onları Qt.Key'e çevirir. İkisi ayrışırsa ayar dosyasında
    geçerli görünen bir tuş sessizce çalışmaz. """
    assert set(keys._QT_NAMED_KEYS) == set(keymap.NAMED_KEYS)


def test_panel_baglamasi_olaydan_uretilir():
    olay = _olay(Qt.Key.Key_T, ALT_SHIFT)
    assert keys.panel_binding(olay) == (frozenset({"alt", "shift"}), "t")


def test_panel_baglamasi_isimli_tusu_cozer():
    olay = _olay(Qt.Key.Key_Right, ALT_SHIFT)
    assert keys.panel_binding(olay) == (frozenset({"alt", "shift"}), "right")


def test_panel_baglamasi_bilinmeyen_tusa_none_der():
    assert keys.panel_binding(_olay(Qt.Key.Key_Ampersand, ALT_SHIFT)) is None


def test_normal_baglamasi_metni_kullanir():
    assert keys.normal_binding(_olay(Qt.Key.Key_N, text="n")) == (frozenset(), "n")
    assert keys.normal_binding(
        _olay(Qt.Key.Key_N, Qt.KeyboardModifier.ShiftModifier, "N")) == (frozenset(), "N")


def test_normal_baglamasi_escape_i_ad_olarak_verir():
    """ Escape'in text()'i boş değil ('\\x1b'); ad üzerinden eşleşmeli. """
    olay = _olay(Qt.Key.Key_Escape, text="\x1b")
    assert keys.normal_binding(olay) == (frozenset(), "escape")


def test_normal_baglamasi_degistiricili_tusa_none_der():
    olay = _olay(Qt.Key.Key_I, Qt.KeyboardModifier.AltModifier, "i")
    assert keys.normal_binding(olay) is None


def test_match_eylemi_bulur():
    harita = keymap.defaults()
    assert keys.match(_olay(Qt.Key.Key_N, ALT_SHIFT), harita, "panel") == "tab_new"
    assert keys.match(_olay(Qt.Key.Key_I, text="i"), harita, "normal") == "insert_mode"
    assert keys.match(_olay(Qt.Key.Key_Z, ALT_SHIFT), harita, "panel") is None


# --- Editör dağıtımı ---

def test_editorde_panel_kisayolu_yeniden_atanabilir(pencere):
    pencere.show()
    harita, _u = keymap.build({"tab_new": "ctrl+t"})
    pencere.editor_tabs.apply_keymap(harita)

    onceki = pencere.editor_tabs.count()
    QTest.keyClick(pencere.editor, Qt.Key.Key_T, CTRL)
    assert pencere.editor_tabs.count() == onceki + 1

    # Eski tuş artık çalışmamalı
    simdiki = pencere.editor_tabs.count()
    QTest.keyClick(pencere.editor, Qt.Key.Key_N, ALT_SHIFT)
    assert pencere.editor_tabs.count() == simdiki


def test_normal_mod_tusu_yeniden_atanabilir(pencere):
    pencere.show()
    harita, _u = keymap.build({"insert_mode": "a"})
    pencere.editor_tabs.apply_keymap(harita)

    QTest.keyClick(pencere.editor, Qt.Key.Key_A)
    assert pencere.editor.current_mode == "INSERT"


def test_yeniden_atandiktan_sonra_eski_tus_metin_yazmaz(pencere):
    """ NORMAL modda bağlanmamış yazılabilir tuş YUTULUR (bugünkü davranış);
    metne düşmemeli. """
    pencere.show()
    harita, _u = keymap.build({"insert_mode": "a"})
    pencere.editor_tabs.apply_keymap(harita)

    QTest.keyClick(pencere.editor, Qt.Key.Key_I)
    assert pencere.editor.current_mode == "NORMAL"
    assert pencere.editor.toPlainText() == ""


def test_insert_modunda_harf_hala_yazilabiliyor(pencere):
    """ K6'nın koruduğu şey: panel kısayolu değiştirici içermek zorunda
    olduğu için hiçbir harf INSERT modunda kaçırılamaz. """
    pencere.show()
    QTest.keyClick(pencere.editor, Qt.Key.Key_I)
    QTest.keyClicks(pencere.editor, "insan")
    assert pencere.editor.toPlainText() == "insan"


def test_sonradan_acilan_sekme_guncel_haritayi_alir(pencere):
    pencere.show()
    harita, _u = keymap.build({"tab_new": "ctrl+t"})
    pencere.editor_tabs.apply_keymap(harita)

    yeni = pencere.editor_tabs.new_tab()
    onceki = pencere.editor_tabs.count()
    QTest.keyClick(yeni, Qt.Key.Key_T, CTRL)
    assert pencere.editor_tabs.count() == onceki + 1


def test_escape_yeniden_atanabilir(pencere):
    """ clear_search varsayılan 'escape'; başka bir tuşa alınabilmeli. """
    pencere.show()
    harita, _u = keymap.build({"clear_search": "x"})
    pencere.editor_tabs.apply_keymap(harita)

    editor = pencere.editor
    editor.setPlainText("bir foo iki")
    editor.search("foo")
    assert editor.extraSelections()

    QTest.keyClick(editor, Qt.Key.Key_X)
    assert editor.extraSelections() == []


# --- Terminal dağıtımı ---

def test_terminalde_panel_kisayolu_yeniden_atanabilir(pencere):
    pencere.show()
    pencere.terminal_panel.toggle()          # ':term' — panel açılır, bir sekme kurulur
    harita, _u = keymap.build({"tab_new": "ctrl+t"})
    pencere.terminal_panel.apply_keymap(harita)

    view = pencere.terminal_panel.stack.currentWidget()
    onceki = pencere.terminal_panel.stack.count()
    QTest.keyClick(view, Qt.Key.Key_T, CTRL)
    assert pencere.terminal_panel.stack.count() == onceki + 1


def test_terminalde_yeniden_atanan_tus_shelle_gitmez(pencere):
    """ Kısayol olarak eşleşen tuş terminale bayt olarak YAZILMAMALI. """
    pencere.show()
    pencere.terminal_panel.toggle()
    harita, _u = keymap.build({"terminal_focus": "ctrl+g"})
    pencere.terminal_panel.apply_keymap(harita)

    view = pencere.terminal_panel.stack.currentWidget()
    yazilanlar = []
    view._process.write = lambda data: yazilanlar.append(data)

    QTest.keyClick(view, Qt.Key.Key_G, CTRL)
    assert yazilanlar == []


def test_sonradan_acilan_terminal_sekmesi_guncel_haritayi_alir(pencere):
    pencere.show()
    pencere.terminal_panel.toggle()
    harita, _u = keymap.build({"tab_close": "ctrl+q"})
    pencere.terminal_panel.apply_keymap(harita)

    yeni = pencere.terminal_panel.new_tab()
    assert yeni._keymap.binding_of("tab_close") == (frozenset({"ctrl"}), "q")


# --- Karşılama sayfası ---

def test_karsilama_sayfasinda_panel_kisayolu_yeniden_atanabilir(pencere):
    pencere.show()
    pencere.editor_tabs.close_current_tab()
    harita, _u = keymap.build({"tab_new": "ctrl+t"})
    pencere.welcome_page.apply_keymap(harita)

    QTest.keyClick(pencere.welcome_page, Qt.Key.Key_T, CTRL)
    assert pencere.editor_tabs.count() == 1


def test_karsilama_sayfasinda_komut_satiri_tusu_yeniden_atanabilir(pencere):
    pencere.show()
    pencere.editor_tabs.close_current_tab()
    harita, _u = keymap.build({"command_line": ","})
    pencere.welcome_page.apply_keymap(harita)

    QTest.keyClicks(pencere.welcome_page, ",")
    assert pencere.welcome_page.current_mode == "COMMAND"


def test_karsilama_ipuclari_varsayilan_haritayi_gosterir(pencere):
    metin = pencere.welcome_page._hints_label.text()
    assert "Alt+Shift+N" in metin
    assert "Alt+Shift+T" in metin


def test_karsilama_ipuclari_haritayi_yansitir(pencere):
    harita, _u = keymap.build({"tab_new": "ctrl+t"})
    pencere.welcome_page.apply_keymap(harita)

    metin = pencere.welcome_page._hints_label.text()
    assert "Ctrl+T" in metin
    assert "Alt+Shift+N" not in metin


# --- Uçtan uca: ayar dosyasından pencereye ---

def test_ayardan_gelen_kisayol_pencereye_ulasir(qapp):
    ayarlar = config.default_settings()
    ayarlar["shortcuts"] = {"tab_new": "ctrl+t"}

    pencere = IDEWindow(settings=ayarlar)
    try:
        pencere.show()
        onceki = pencere.editor_tabs.count()
        QTest.keyClick(pencere.editor, Qt.Key.Key_T, CTRL)
        assert pencere.editor_tabs.count() == onceki + 1
    finally:
        pencere.terminal_panel.shutdown()
        pencere.close()
        pencere.deleteLater()
        qapp.processEvents()


def test_gecersiz_kisayol_uyarir_ve_varsayilanda_birakir(qapp, capsys):
    ayarlar = config.default_settings()
    ayarlar["shortcuts"] = {"tab_new": "i"}          # K6 ihlali

    pencere = IDEWindow(settings=ayarlar)
    try:
        assert "tab_new" in capsys.readouterr().out
        assert pencere.keymap.binding_of("tab_new") == (frozenset({"alt", "shift"}), "n")
    finally:
        pencere.terminal_panel.shutdown()
        pencere.close()
        pencere.deleteLater()
        qapp.processEvents()


def test_reload_kisayolu_canli_degistirir(pencere, tmp_path, monkeypatch):
    """ K9: keymap de apply_settings'ten geçtiği için ':reload' canlı yeniden
    atamayı bedavaya veriyor. """
    yol = tmp_path / "config.toml"
    yol.write_text('[shortcuts]\ntab_new = "ctrl+t"\n', encoding="utf-8")
    monkeypatch.setattr("core.config.config_path", lambda: str(yol))

    pencere.show()
    pencere.reload_settings()

    onceki = pencere.editor_tabs.count()
    QTest.keyClick(pencere.editor, Qt.Key.Key_T, CTRL)
    assert pencere.editor_tabs.count() == onceki + 1


def test_reload_karsilama_ipuclarini_tazeler(pencere, tmp_path, monkeypatch):
    yol = tmp_path / "config.toml"
    yol.write_text('[shortcuts]\ntab_new = "ctrl+t"\n', encoding="utf-8")
    monkeypatch.setattr("core.config.config_path", lambda: str(yol))

    pencere.show()
    pencere.reload_settings()
    assert "Ctrl+T" in pencere.welcome_page._hints_label.text()


def test_reload_terminal_oturumunu_koruyarak_yeniden_atar(pencere, tmp_path, monkeypatch):
    yol = tmp_path / "config.toml"
    yol.write_text('[shortcuts]\ntab_close = "ctrl+q"\n', encoding="utf-8")
    monkeypatch.setattr("core.config.config_path", lambda: str(yol))

    pencere.show()
    pencere.terminal_panel.toggle()
    onceki = pencere.terminal_panel.stack.count()

    pencere.reload_settings()

    assert pencere.terminal_panel.stack.count() == onceki      # oturum korundu
    view = pencere.terminal_panel.stack.currentWidget()
    assert view._keymap.binding_of("tab_close") == (frozenset({"ctrl"}), "q")
