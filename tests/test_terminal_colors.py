""" TerminalView'ın hücre renk çözümlemesi. Kod incelemesi Bulgu 3: paintEvent
artık paleti KAREye bir kez çözüp bir QColor sözlüğü olarak resolver'lara
veriyor (bkz. ui/components/terminal_panel.py). Bu testler hem eski
sözleşmenin (adlı ANSI rengi -> palet tokeni, truecolor kendi rengini korur,
reverse fg/bg'yi takas eder, varsayılan zemin fillRect'i atlasın diye None
döner) bozulmadığını, hem de önbelleğin KARELER ARASI sızmadığını (bir palet
değişikliği bir sonraki paintEvent'te hemen görünür) doğrular. """
from PyQt6.QtGui import QColor
from pyte.screens import Char

import ui.theme as theme
from ui.components.terminal_panel import TerminalView


def _palette_colors():
    """ paintEvent'in her karede kurduğu önbelleğin testteki karşılığı. """
    return {token: QColor(hex_value) for token, hex_value in theme.palette().items()}


def test_varsayilan_hucre_arka_plani_none_doner(qapp):
    """ bg 'default' (bg_dark ile aynı) ise paintEvent fillRect'i atlayabilsin
    diye None dönmeli -- boş terminal alanının çoğunluğu budur. """
    view = TerminalView()
    cell = Char(data="a", fg="default", bg="default")

    fg, bg = view._resolve_colors(cell, _palette_colors())

    assert bg is None
    assert fg == QColor(theme.color("fg"))


def test_adli_ansi_rengi_paletten_gelir(qapp):
    view = TerminalView()
    cell = Char(data="a", fg="red", bg="default")

    fg, _bg = view._resolve_colors(cell, _palette_colors())

    assert fg == QColor(theme.color("red"))


def test_truecolor_hucre_palet_disinda_kendi_rengini_korur(qapp):
    """ pyte 256-renk/truecolor SGR kodlarını 6 haneli hex string olarak
    verir; bunlar palet tokeni değildir, olduğu gibi çizilmeli. """
    view = TerminalView()
    cell = Char(data="a", fg="ff6432", bg="default")

    fg, _bg = view._resolve_colors(cell, _palette_colors())

    assert fg == QColor("#ff6432")


def test_reverse_hucrede_fg_bg_yer_degistirir(qapp):
    view = TerminalView()
    cell = Char(data="a", fg="red", bg="default", reverse=True)

    fg, bg = view._resolve_colors(cell, _palette_colors())

    assert fg == QColor(theme.color("bg_dark"))
    assert bg == QColor(theme.color("red"))


def test_palet_degisikligi_bir_sonraki_karede_hemen_gorunur(qapp):
    """ Bulgu 3'ün 'kareler arası önbelleklenmez' koşulu: paintEvent'in her
    çağrısı kendi palette_colors sözlüğünü taze kurar (burada olduğu gibi);
    bir ':reload' bu yüzden BİR SONRAKİ paint'te hemen görünür, eski bir
    çerçevenin rengi asla sızmaz. """
    view = TerminalView()
    cell = Char(data="a", fg="red", bg="default")

    onceki_kare = _palette_colors()
    fg1, _bg = view._resolve_colors(cell, onceki_kare)
    assert fg1 == QColor("#f7768e")   # varsayılan Tokyo Night kırmızısı

    try:
        theme.set_palette(theme.build_palette({"red": "#00ff00"})[0])
        yeni_kare = _palette_colors()     # paintEvent'in HER çağrıda kurduğu taze sözlük
        fg2, _bg = view._resolve_colors(cell, yeni_kare)
        assert fg2 == QColor("#00ff00")
    finally:
        theme.set_palette(dict(theme.DEFAULT_PALETTE))


def test_paint_event_palette_colors_parametresini_kullanir(qapp):
    """ Regresyon: _resolve_colors artık palette_colors parametresi bekliyor
    (bkz. paintEvent) -- imza eskisi gibi tek argümanlıya geri dönerse bu
    test TypeError ile kırılır. """
    import inspect
    params = inspect.signature(TerminalView._resolve_colors).parameters
    assert "palette_colors" in params
