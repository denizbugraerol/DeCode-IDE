""" Palet ve stylesheet üretecinin sözleşmesi. Qt gerektirmez. """
import ui.theme as theme


def test_varsayilan_palet_tokyo_night():
    assert theme.DEFAULT_PALETTE["bg"] == "#1a1b26"
    assert theme.DEFAULT_PALETTE["fg"] == "#c0caf5"
    assert len(theme.DEFAULT_PALETTE) == 17


def test_build_palette_yalniz_verileni_ezer():
    palet, uyarilar = theme.build_palette({"bg": "#11111b"})
    assert palet["bg"] == "#11111b"
    assert palet["fg"] == theme.DEFAULT_PALETTE["fg"]
    assert uyarilar == []


def test_build_palette_bilinmeyen_tokeni_uyarir():
    palet, uyarilar = theme.build_palette({"pembe": "#ff00ff"})
    assert "pembe" not in palet
    assert any("pembe" in u for u in uyarilar)


def test_build_palette_varsayilani_bozmaz():
    theme.build_palette({"bg": "#000000"})
    assert theme.DEFAULT_PALETTE["bg"] == "#1a1b26"


def test_set_palette_ve_color():
    try:
        theme.set_palette(theme.build_palette({"blue": "#89b4fa"})[0])
        assert theme.color("blue") == "#89b4fa"
    finally:
        theme.set_palette(dict(theme.DEFAULT_PALETTE))


def test_stylesheet_paletteki_rengi_kullanir():
    palet, _u = theme.build_palette({"bg": "#11111b"})
    qss = theme.stylesheet(palet, "Fira Code", 15)
    assert "#11111b" in qss
    assert "#1a1b26" not in qss          # eski zemin hiç kalmamalı


def test_stylesheet_font_ailesini_ve_boyutlarini_yerlestirir():
    qss = theme.stylesheet(dict(theme.DEFAULT_PALETTE), "JetBrains Mono", 15)
    assert "'JetBrains Mono'" in qss
    # Varsayılan 15 bugünkü boyutları birebir üretmeli
    for boyut in ("15px", "16px", "14px", "13px", "12px", "11px", "28px"):
        assert boyut in qss


def test_stylesheet_boyutlar_font_size_ile_kayar():
    qss = theme.stylesheet(dict(theme.DEFAULT_PALETTE), "Fira Code", 20)
    assert "font-size: 20px" in qss     # editör
    assert "font-size: 21px" in qss     # komut satırı (+1)
    assert "font-size: 16px" in qss     # statusline (-4)


def test_stylesheet_eksik_token_hata_verir():
    """ Şablonda kullanılıp palette olmayan bir token sessizce geçmemeli. """
    import pytest
    eksik = dict(theme.DEFAULT_PALETTE)
    del eksik["bg"]
    with pytest.raises(KeyError):
        theme.stylesheet(eksik, "Fira Code", 15)
