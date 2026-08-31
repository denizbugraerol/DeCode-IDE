""" Ayar yükleyicinin sözleşmesi: varsayılanlar, birleştirme, doğrulama.
Qt gerektirmez. """
import core.config as config


def test_dosya_yoksa_varsayilanlar_ve_uyari_yok(tmp_path):
    ayarlar, uyarilar = config.load(str(tmp_path / "yok.toml"))
    assert ayarlar == config.DEFAULTS
    assert uyarilar == []


def test_default_settings_derin_kopya_verir():
    birinci = config.default_settings()
    birinci["editor"]["font_size"] = 99
    assert config.default_settings()["editor"]["font_size"] == 15


def test_yalniz_verilen_anahtar_ezilir():
    ayarlar, uyarilar = config.parse('[editor]\nfont_size = 20\n')
    assert ayarlar["editor"]["font_size"] == 20
    assert ayarlar["editor"]["font_family"] == "Fira Code"   # dokunulmadı
    assert ayarlar["terminal"]["rows"] == 9
    assert uyarilar == []


def test_bozuk_toml_varsayilana_duser():
    ayarlar, uyarilar = config.parse("[editor\nfont_size = ")
    assert ayarlar == config.DEFAULTS
    assert len(uyarilar) == 1
    assert "okunamadı" in uyarilar[0]


def test_yanlis_tur_varsayilanda_birakir():
    ayarlar, uyarilar = config.parse('[editor]\nfont_size = "kocaman"\n')
    assert ayarlar["editor"]["font_size"] == 15
    assert any("font_size" in u for u in uyarilar)


def test_bool_font_boyutu_sayilmaz():
    """ Python'da bool, int'in alt sınıfı; isinstance(True, int) True döner.
    'font_size = true' geçerli sayılmamalı. """
    ayarlar, _u = config.parse("[editor]\nfont_size = true\n")
    assert ayarlar["editor"]["font_size"] == 15


def test_aralik_disi_deger_varsayilanda_birakir():
    ayarlar, uyarilar = config.parse("[editor]\nfont_size = 500\n")
    assert ayarlar["editor"]["font_size"] == 15
    assert any("6-72" in u for u in uyarilar)


def test_bos_font_ailesi_reddedilir():
    ayarlar, _u = config.parse('[editor]\nfont_family = "   "\n')
    assert ayarlar["editor"]["font_family"] == "Fira Code"


def test_bilinmeyen_anahtar_ve_bolum_uyarir():
    ayarlar, uyarilar = config.parse("[editor]\nzoom = 3\n\n[uzay]\nx = 1\n")
    assert ayarlar["editor"] == config.DEFAULTS["editor"]
    assert any("editor.zoom" in u for u in uyarilar)
    assert any("[uzay]" in u for u in uyarilar)


def test_renkler_hex_bicimini_zorunlu_kilar():
    ayarlar, uyarilar = config.parse(
        '[colors]\nbg = "#11111b"\nfg = "kirmizi"\nblue = "#abc"\n')
    assert ayarlar["colors"] == {"bg": "#11111b"}
    assert any("colors.fg" in u for u in uyarilar)
    assert any("colors.blue" in u for u in uyarilar)


def test_config_path_xdg_degiskenine_saygi_duyar(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/xdg")
    assert config.config_path() == "/tmp/xdg/decode/config.toml"


def test_config_path_xdg_yoksa_ev_dizinini_kullanir(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", "/home/deneme")
    assert config.config_path() == "/home/deneme/.config/decode/config.toml"


def test_sablon_varsayilanlarin_aynisini_uretir():
    """ Şablonu olduğu gibi geri okumak varsayılanları vermeli: kullanıcı
    hiçbir şeye dokunmadığında davranış değişmemeli. """
    ayarlar, uyarilar = config.parse(config.TEMPLATE)
    assert ayarlar == config.DEFAULTS
    assert uyarilar == []


def test_ensure_exists_yoksa_yazar_varsa_dokunmaz(tmp_path):
    yol = str(tmp_path / "alt" / "config.toml")
    assert config.ensure_exists(yol) is True
    assert config.ensure_exists(yol) is False

    with open(yol, "a", encoding="utf-8") as dosya:
        dosya.write("\n# kullanıcı notu\n")
    config.ensure_exists(yol)
    with open(yol, encoding="utf-8") as dosya:
        assert "# kullanıcı notu" in dosya.read()
