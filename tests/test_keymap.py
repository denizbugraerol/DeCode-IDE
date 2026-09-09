""" Tuş haritasının sözleşmesi: ayrıştırma, doğrulama, birleştirme, çakışma.
Qt gerektirmez. """
import core.keymap as keymap


def test_on_eylem_var_ve_sira_anlamli():
    adlar = [a.name for a in keymap.ACTIONS]
    assert adlar == [
        "terminal_focus", "tab_new", "tab_close", "tab_next", "tab_prev",
        "insert_mode", "command_line", "search_next", "search_prev", "clear_search",
    ]


def test_her_varsayilan_kendi_grubunun_kurallarindan_geciyor():
    """ Kendi kuralımıza uyduğumuzun bekçisi: K6/K7 varsayılanları elemez. """
    for action in keymap.ACTIONS:
        baglama, hata = keymap.parse(action.default, action.group)
        assert hata is None, f"{action.name}: {hata}"
        assert baglama is not None


def test_panel_baglamasi_ayrisir():
    baglama, hata = keymap.parse("alt+shift+t", "panel")
    assert hata is None
    assert baglama == (frozenset({"alt", "shift"}), "t")


def test_panel_baglamasi_buyuk_kucuk_harf_ayirmaz():
    """ Dağıtım event.key() ile karşılaştırıyor; Qt.Key harf büyüklüğü bilmez. """
    assert keymap.parse("Alt+Shift+T", "panel")[0] == keymap.parse("alt+shift+t", "panel")[0]


def test_panel_isimli_tuslari_kabul_eder():
    assert keymap.parse("alt+shift+right", "panel")[0] == (frozenset({"alt", "shift"}), "right")
    assert keymap.parse("ctrl+f5", "panel")[0] == (frozenset({"ctrl"}), "f5")


def test_panel_bilinmeyen_degistirici_reddedilir():
    baglama, hata = keymap.parse("hyper+n", "panel")
    assert baglama is None
    assert "hyper" in hata


def test_panel_bilinmeyen_tus_reddedilir():
    baglama, hata = keymap.parse("alt+shift+q9", "panel")
    assert baglama is None
    assert "q9" in hata


def test_panel_degistiricisiz_reddedilir():
    """ K6: değiştiricisiz panel kısayolu o harfi INSERT modunda yazılamaz
    hale getirirdi. """
    baglama, hata = keymap.parse("i", "panel")
    assert baglama is None
    assert "Ctrl, Alt ya da Meta" in hata


def test_panel_yalniz_shift_reddedilir():
    """ K6: 'shift+n' bağlanabilseydi INSERT modunda 'N' yazılamazdı. """
    baglama, hata = keymap.parse("shift+n", "panel")
    assert baglama is None
    assert "Ctrl, Alt ya da Meta" in hata


def test_panel_ctrl_ve_meta_kabul_edilir():
    """ K2: Ctrl varsayılana girmiyor ama yasak da değil. """
    assert keymap.parse("ctrl+t", "panel")[1] is None
    assert keymap.parse("meta+t", "panel")[1] is None


def test_normal_tek_karakter_kabul_eder():
    assert keymap.parse("i", "normal")[0] == (frozenset(), "i")
    assert keymap.parse(":", "normal")[0] == (frozenset(), ":")


def test_normal_buyuk_kucuk_harf_ayirir():
    """ 'n' ile 'N' farklı komut; dağıtım event.text() ile karşılaştırıyor. """
    assert keymap.parse("n", "normal")[0] != keymap.parse("N", "normal")[0]


def test_normal_escape_kabul_eder():
    assert keymap.parse("escape", "normal")[0] == (frozenset(), "escape")


def test_normal_degistirici_reddedilir():
    """ K7: 'alt+i' istenseydi handle_normal_mode'un dağıtım kapısı da
    değişmeliydi — ayrı ve daha büyük bir iş. """
    baglama, hata = keymap.parse("alt+i", "normal")
    assert baglama is None
    assert "tek karakter" in hata
