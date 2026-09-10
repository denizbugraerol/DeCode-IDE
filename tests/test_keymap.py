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


# --- build / Keymap / label ---

def test_bos_ayar_varsayilan_haritayi_verir():
    harita, uyarilar = keymap.build({})
    assert uyarilar == []
    assert harita.binding_of("tab_new") == (frozenset({"alt", "shift"}), "n")
    assert harita.action_for("panel", (frozenset({"alt", "shift"}), "n")) == "tab_new"
    assert harita.action_for("normal", (frozenset(), "i")) == "insert_mode"


def test_defaults_build_ile_ayni():
    assert keymap.defaults().binding_of("tab_new") == keymap.build({})[0].binding_of("tab_new")


def test_gecerli_yeniden_atama_yalniz_o_eylemi_degistirir():
    harita, uyarilar = keymap.build({"tab_new": "ctrl+t"})
    assert uyarilar == []
    assert harita.action_for("panel", (frozenset({"ctrl"}), "t")) == "tab_new"
    # Eski tuş artık bağlı değil
    assert harita.action_for("panel", (frozenset({"alt", "shift"}), "n")) is None
    # Diğerleri varsayılanda
    assert harita.binding_of("tab_close") == (frozenset({"alt", "shift"}), "w")


def test_bilinmeyen_eylem_adi_uyarir():
    harita, uyarilar = keymap.build({"tab_neww": "ctrl+t"})
    assert len(uyarilar) == 1
    assert "tab_neww" in uyarilar[0]
    assert harita.binding_of("tab_new") == (frozenset({"alt", "shift"}), "n")


def test_gecersiz_baglama_varsayilana_duser_ve_uyarir():
    harita, uyarilar = keymap.build({"tab_new": "alt+shift+q9"})
    assert len(uyarilar) == 1
    assert "tab_new" in uyarilar[0] and "q9" in uyarilar[0]
    assert "alt+shift+n" in uyarilar[0]           # varsayılan uyarıda yazıyor
    assert harita.binding_of("tab_new") == (frozenset({"alt", "shift"}), "n")


def test_k6_ihlali_varsayilana_duser():
    harita, uyarilar = keymap.build({"tab_new": "i"})
    assert len(uyarilar) == 1
    assert harita.binding_of("tab_new") == (frozenset({"alt", "shift"}), "n")


def test_cakismada_once_gelen_kazanir():
    """ K3: ACTIONS sırasında tab_new, tab_close'dan önce geliyor. """
    harita, uyarilar = keymap.build({"tab_new": "alt+shift+w"})

    assert harita.action_for("panel", (frozenset({"alt", "shift"}), "w")) == "tab_new"
    assert len(uyarilar) == 1
    assert "tab_close" in uyarilar[0] and "alt+shift+w" in uyarilar[0]


def test_cakisma_gruplar_arasinda_olamaz():
    """ K6+K7 birlikte gruplar arası çakışmayı imkânsız kılıyor: panel
    bağlaması değiştirici İÇERMEK, normal bağlaması İÇERMEMEK zorunda.
    'alt+shift+i' panelde geçerli, normalde reddedilir; ikisi asla aynı
    bağlamaya düşemez. """
    harita, uyarilar = keymap.build({"terminal_focus": "alt+shift+i"})

    assert uyarilar == []
    assert harita.action_for("panel", (frozenset({"alt", "shift"}), "i")) == "terminal_focus"
    assert harita.action_for("normal", (frozenset(), "i")) == "insert_mode"


def test_normal_grubu_icinde_cakisma_bildirilir():
    """ insert_mode ACTIONS'ta search_next'ten ÖNCE: 'n' insert_mode'a gider,
    search_next bağsız kalır ve bir uyarı üretilir. """
    harita, uyarilar = keymap.build({"insert_mode": "n"})

    assert harita.action_for("normal", (frozenset(), "n")) == "insert_mode"
    assert len(uyarilar) == 1
    assert "search_next" in uyarilar[0]


def test_label_gosterim_bicimi():
    harita = keymap.defaults()
    assert harita.label("terminal_focus") == "Alt+Shift+T"
    assert harita.label("tab_next") == "Alt+Shift+→"
    assert harita.label("tab_prev") == "Alt+Shift+←"
    assert harita.label("insert_mode") == "i"
    assert harita.label("search_prev") == "N"
    assert harita.label("clear_search") == "Esc"


def test_label_ctrl_ve_fonksiyon_tuslari():
    harita, _u = keymap.build({"tab_new": "ctrl+f5"})
    assert harita.label("tab_new") == "Ctrl+F5"


def test_text_ayar_dosyasi_bicimini_verir():
    assert keymap.text((frozenset({"shift", "alt"}), "w")) == "alt+shift+w"
