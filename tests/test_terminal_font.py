""" Terminal ızgarası ile fontun uyumu.

TerminalView, pyte'ın ekran arabelleğini SABİT genişlikli bir hücre ızgarası
olarak çizer: hücre genişliği fontMetrics().horizontalAdvance("0") ile bir kez
ölçülür, her karakter kendi hücresinin sol üst köşesine çizilir. Bu, fontun
gerçekten sabit genişlikli (monospace) olmasını şart koşar.

Ayar dosyasındaki font (varsayılan "Fira Code") kurulu değilse Qt sessizce
ORANTILI bir aileye düşer; o zaman 'm' hücresinden taşıp komşusuna girer, 'i'
ise hücresinin yarısını boş bırakır -- kullanıcının gördüğü "harfler bazen iç
içe giriyor, bazılarının arası fazla" hatası tam olarak budur. Aşağıdaki
testler o düşüşü yakalar. """
from PyQt6.QtGui import QFontMetricsF

import ui.theme as theme

# Terminalde gerçekten çizilen karakter kümesinin uçları: en dar ve en geniş
# glifler orantılı bir fontta birbirinden ayrışır, monospace'te ayrışmaz.
UC_KARAKTERLER = "iml.WM@0 "

# QFontMetrics font veritabanına bakar: qapp olmadan Qt süreci abort eder,
# bu yüzden font ölçen her test qapp fixture'ını ister.


def _genislikler(font):
    metrics = QFontMetricsF(font)
    return [metrics.horizontalAdvance(ch) for ch in UC_KARAKTERLER]


def test_cozulmeyen_font_sabit_genislikli_aileye_duser(qapp):
    """ Kurulu olmayan bir aile istendiğinde orantılı varsayılana değil,
    sistemin monospace fontuna düşülmeli ve bu bir uyarıyla söylenmeli. """
    aile, uyarilar = theme.resolve_font_family("Kesinlikle Kurulu Olmayan Font", 15)

    from PyQt6.QtGui import QFont
    font = QFont(aile)
    font.setPixelSize(15)
    assert len(set(_genislikler(font))) == 1
    assert any("Kesinlikle Kurulu Olmayan Font" in u for u in uyarilar)


def test_kurulu_mono_font_dokunulmadan_gecer(qapp):
    """ İstenen aile zaten sabit genişlikliyse olduğu gibi kullanılmalı --
    fallback yalnızca gerçekten gerektiğinde devreye girsin. """
    mono, _ = theme.resolve_font_family("Kesinlikle Kurulu Olmayan Font", 15)

    aile, uyarilar = theme.resolve_font_family(mono, 15)
    assert aile == mono
    assert uyarilar == []


def test_terminal_fontu_sabit_genislikli(pencere):
    """ Asıl regresyon: panelin gerçekte kullandığı font (QSS'ten gelip
    sync_font_with_editor ile kopyalanan) sabit genişlikli olmalı. """
    view = pencere.terminal_panel.new_tab()

    genislikler = set(_genislikler(view.font()))
    assert len(genislikler) == 1, (
        f"terminal fontu orantılı: {view.font().family()} -> {sorted(genislikler)}")


def test_terminal_hucre_genisligi_glifle_ortusur(pencere):
    """ Çizim ızgarası ile fontun gerçek ilerlemesi yarım pikselden fazla
    ayrışmamalı: hücre dardan hesaplanırsa harfler bindirir, genişten
    hesaplanırsa aralarında boşluk kalır. """
    view = pencere.terminal_panel.new_tab()

    hucre = view.fontMetrics().horizontalAdvance("0")   # paintEvent'in kullandığı
    for karakter, genislik in zip(UC_KARAKTERLER, _genislikler(view.font())):
        assert abs(genislik - hucre) <= 0.5, (
            f"{karakter!r} {genislik:.2f}px, hücre {hucre}px")


def test_editor_fontu_da_sabit_genislikli(pencere):
    """ Terminal fontunu editörden kopyalıyor; kaynak da monospace olmalı --
    zaten bir kod editöründe hizalama buna bağlı. """
    genislikler = set(_genislikler(pencere.editor.font()))
    assert len(genislikler) == 1
