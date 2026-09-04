""" Tema: adlandırılmış renk paleti + font durumu ve bunlardan üretilen Qt
stylesheet'i.

Renkler tek yerde durur. Bileşenler rengi BOYAMA ANINDA theme.color(...) ile
okur; böylece ':reload' paleti değiştirdiğinde yeniden çizilen her şey yeni
renklerle gelir ve paleti beş ayrı yapıcıya elden geçirmek gerekmez. Font
ailesi/boyutu da aynı ilkeyle module-level tutulur (font_family, font_size) —
QSS'in kendisi kullanmaz (o parametre alır, bkz. stylesheet()) ama QSS'in
DIŞINDA kalıp kendi stilini elle kuran bileşenler (FloatingList, StatusLine)
bunları okur.

Geçerli palet ve font süreç genelinde tektir — uygulamanın teması gerçekten
global bir şey. set_palette / set_font onları değiştiren TEK kapıdır:
set_palette verilen sözlüğü DEFAULT_PALETTE'in üstüne bindirir (kısmi bir
sözlük verilse bile _current eksiksiz kalır, aksi halde color() sonradan
boyama sırasında KeyError fırlatabilirdi). """
from string import Template

from PyQt6.QtGui import QFont, QFontDatabase, QFontInfo, QFontMetricsF

# Tokyo Night. Bugün altı dosyaya dağılmış 17 rengin tamamı.
DEFAULT_PALETTE = {
    "bg":        "#1a1b26",   # ana zemin, editör
    "bg_dark":   "#16161e",   # sidebar, gutter, terminal paneli, sekme çubuğu
    "panel":     "#1f2335",   # statusline, komut kutusu, öneri kutusu, hover
    "border":    "#414868",   # kenarlıklar, kaydırma tutamağı
    "fg":        "#c0caf5",   # ana metin
    "fg_dim":    "#565f89",   # sönük metin, yorumlar, pasif sekme
    "fg_bright": "#ffffff",   # seçili satır ve arama vurgusu metni
    "gutter":    "#3b4261",   # pasif satır numarası
    "selection": "#283457",   # seçili öneri satırı, ağaç seçimi
    "search":    "#3d59a1",   # arama eşleşmesi zemini
    "blue":      "#7aa2f7",   # NORMAL rozeti, seçili sekme, vurgu
    "green":     "#9ece6a",   # INSERT rozeti, dizeler
    "orange":    "#ff9e64",   # COMMAND rozeti, sayılar
    "yellow":    "#e0af68",   # dekoratörler
    "purple":    "#bb9af7",   # anahtar sözcükler
    "cyan":      "#7dcfff",   # Python builtin'leri
    "red":       "#f7768e",   # terminal kırmızısı
}

# Arayüz font boyutları editör boyutuna göre sapma olarak tutulur. Varsayılan
# 15 ile bugünkü değerleri birebir üretir: 16, 15, 14, 13, 12, 11, 28.
FONT_SIZE_OFFSETS = {
    "command_line": 1,
    "editor": 0,
    "sidebar": -1,
    "row": -2,
    "tab": -3,
    "status": -4,
    "welcome_title": 13,
}

_current = dict(DEFAULT_PALETTE)

# Font durumu palet gibi modül düzeyinde tek. Varsayılanlar
# core/config.DEFAULTS["editor"] ile birebir aynı olmalı: set_font hiç
# çağrılmadan (ör. IDEWindow dışında tek başına kurulan bir FloatingList/
# StatusLine testinde) üretilen stil de bugünkü sabit "13px/11px Fira Code"
# ile eşleşsin.
_current_font_family = "Fira Code"
_current_font_size = 15


def color(token):
    """ Geçerli paletten bir renk. Bileşenler bunu boyama anında çağırır. """
    return _current[token]


def palette():
    return dict(_current)


def set_palette(new_palette):
    """ Geçerli paleti değiştirir — set_font ile birlikte TEK kapı budur.
    new_palette DEFAULT_PALETTE'in üstüne bindirilir: kısmi bir sözlük
    (ör. yalnızca {'bg': ...}) verilse bile eksik tokenlar varsayılandan
    tamamlanır, aksi halde color() sonradan bir paintEvent içinden KeyError
    fırlatabilirdi. build_palette() zaten hep eksiksiz bir sözlük döndürür;
    bu tamamlama onun dışından çağıran biri için bir güvenlik ağıdır. """
    _current.clear()
    _current.update(DEFAULT_PALETTE)
    _current.update(new_palette)


# Fontun sabit genişlikli olup olmadığını ÖLÇEREK anlıyoruz; en dar ve en
# geniş ASCII glif. QFontInfo.fixedPitch()'e güvenilmiyor: gerçekten sabit
# genişlikli aileler için bile (ör. Noto Sans Mono) False dönebiliyor.
_MONO_PROBE = ("i", "M")


def _probe_font(family, size):
    """ Ölçüm için, istenen aileden hiçbir ipucu eklenmemiş bir QFont. """
    font = QFont(family) if family else QFont()
    font.setPixelSize(size)
    return font


def _is_monospace(font):
    metrics = QFontMetricsF(font)
    return len({metrics.horizontalAdvance(ch) for ch in _MONO_PROBE}) == 1


def _first_monospace_family(size):
    """ Font veritabanındaki ilk GERÇEKTEN sabit genişlikli aile.

    styleHint(Monospace) başarısız olduğunda son çare. Ölçerek karar
    verdiğimiz için isim tahminine ("Mono geçen aileler") güvenmiyoruz. """
    for candidate in QFontDatabase.families():
        if _is_monospace(_probe_font(candidate, size)):
            return candidate
    return None


def resolve_font_family(family, size):
    """ İstenen aileyi gerçekten SABİT GENİŞLİKLİ, kurulu bir aileye çevirir.
    (aile, uyarılar) döndürür — build_palette ile aynı sözleşme; çağıran
    (IDEWindow.apply_settings) uyarıları basar, uygulama çalışmaya devam eder.

    Neden gerekli: terminal paneli pyte'ın ekranını sabit bir hücre ızgarası
    olarak çizer (hücre genişliği fontMetrics().horizontalAdvance("0") ile bir
    kez ölçülür, her karakter kendi hücresine çizilir). İstenen aile kurulu
    değilse Qt sessizce ORANTILI varsayılanına düşer ve o ızgara bozulur:
    'm' hücresinden taşıp komşusuna girer, 'i' ise hücresinin yarısını boş
    bırakır. Varsayılan "Fira Code" pek çok sistemde kurulu olmadığı için bu
    istisna değil, olağan durumdu.

    İki tuzak:
      * styleHint(Monospace) TEK BAŞINA yetmez — o yalnız aile BULUNAMAZSA
        devreye girer. Kurulu ama orantılı bir aile (ör. "Fira Sans")
        istendiğinde Qt onu memnuniyetle kullanır; bu yüzden geri düşülen
        font ailesiz kuruluyor.
      * Karar QFontInfo.fixedPitch() ile verilemez (bkz. _MONO_PROBE). """
    if _is_monospace(_probe_font(family, size)):
        return family, []

    fallback = _probe_font(None, size)
    fallback.setStyleHint(QFont.StyleHint.Monospace)
    fallback.setFixedPitch(True)
    resolved = QFontInfo(fallback).family()

    # ÜÇÜNCÜ tuzak: styleHint(Monospace) fontconfig'in "monospace" takma adına
    # güvenir. O takma ad tanımlı değilse (minimal sistemler, konteynerler, CI
    # runner'ları) Qt orantılı bir aile döndürür ve terminal ızgarası yine
    # bozulur -- düzeltmeye çalıştığımız hatanın tam kendisi. Bu yüzden yedeğe
    # de güvenmiyoruz: ÖLÇÜP doğruluyor, tutmazsa veritabanını tarıyoruz.
    if not _is_monospace(_probe_font(resolved, size)):
        scanned = _first_monospace_family(size)
        if scanned is not None:
            resolved = scanned

    return resolved, [
        f"Sabit genişlikli '{family}' fontu bulunamadı; '{resolved}' kullanılıyor."
    ]


def set_font(family, size):
    """ Geçerli font ailesini ve editör boyutunu değiştirir — set_palette'in
    font karşılığı; aynı yerden (IDEWindow.apply_settings) çağrılır. Rol
    bazlı boyutlar font_size(role) ile FONT_SIZE_OFFSETS'e göre türetilir. """
    global _current_font_family, _current_font_size
    _current_font_family = family
    _current_font_size = size


def font_family():
    """ Geçerli font ailesi. QSS'in dışında kalıp kendi stilini elle kuran
    bileşenler (FloatingList, StatusLine) bunu boyama/stil kurma anında
    çağırır — color() ile aynı ilke. """
    return _current_font_family


def font_size(role="editor"):
    """ Bir arayüz rolünün (FONT_SIZE_OFFSETS'teki adlardan biri) geçerli
    font boyutu: editör boyutu + o rolün sapması. Tanınmayan rol için sapma
    0 sayılır (editör boyutuyla aynı boyut döner). """
    return _current_font_size + FONT_SIZE_OFFSETS.get(role, 0)


def build_palette(overrides):
    """ Varsayılan paletin üstüne ayar dosyasındaki tokenları bindirir.
    (palet, uyarılar) döndürür; tanınmayan token adı yok sayılır. """
    result = dict(DEFAULT_PALETTE)
    warnings = []
    for name, value in (overrides or {}).items():
        if name in result:
            result[name] = value
        else:
            warnings.append(f"Bilinmeyen renk yok sayıldı: colors.{name}")
    return result, warnings


def stylesheet(palette_map, font_family, font_size):
    """ Ana pencerenin QSS'ini üretir. string.Template kullanıyoruz çünkü QSS
    süslü parantez dolu; str.format orada boğulur. Şablonda geçip palette
    olmayan bir token KeyError verir — yazım hatası sessizce geçmesin. """
    sizes = {f"size_{name}": font_size + offset for name, offset in FONT_SIZE_OFFSETS.items()}
    return Template(_QSS).substitute(font_family=font_family, **sizes, **palette_map)


_QSS = """
    QMainWindow { background-color: $bg; }
    QTreeView {
        background-color: $bg_dark;
        color: $fg;
        border: none;
        font-size: ${size_sidebar}px;
        outline: none;
    }
    QTreeView::item:selected { background-color: $selection; color: $fg_bright; }
    QTreeView::item:hover { background-color: $panel; }
    QPlainTextEdit {
        background-color: $bg;
        color: $fg;
        border: none;
        font-family: '$font_family', 'Consolas', monospace;
        font-size: ${size_editor}px;
        padding: 10px;
    }
    QSplitter::handle { background-color: $panel; width: 2px; }
    QWidget#statusLine {
        background-color: $panel;
    }
    QWidget#statusLine QLabel {
        color: $fg;
        font-family: '$font_family', 'Consolas', monospace;
        font-size: ${size_status}px;
    }
    QLabel#commandLine {
        background-color: $panel;
        color: $fg;
        border: 1px solid $border;
        border-radius: 8px;
        padding: 4px 12px;
        font-family: '$font_family', 'Consolas', monospace;
        font-size: ${size_command_line}px;
    }
    QWidget#floatingList {
        background-color: $panel;
        border: 1px solid $border;
        border-radius: 8px;
    }
    QWidget#welcomePage { background-color: $bg; }
    QLabel#welcomeTitle {
        color: $blue;
        font-family: '$font_family', 'Consolas', monospace;
        font-size: ${size_welcome_title}px;
        font-weight: bold;
    }
    QLabel#welcomeSubtitle {
        color: $fg_dim;
        font-family: '$font_family', 'Consolas', monospace;
        font-size: ${size_row}px;
    }
    QLabel#welcomeHints {
        color: $fg;
        font-family: '$font_family', 'Consolas', monospace;
        font-size: ${size_row}px;
        line-height: 150%;
    }
    QWidget#commandPalette { background-color: transparent; }
    QLabel#palettePrompt {
        background-color: $panel;
        color: $fg;
        border: 1px solid $border;
        border-radius: 8px;
        padding: 8px 12px;
        font-family: '$font_family', 'Consolas', monospace;
        font-size: ${size_editor}px;
    }
    QScrollArea#floatingListScroll {
        background: transparent;
        border: none;
    }
    QScrollArea#floatingListScroll QScrollBar:vertical {
        background: transparent;
        width: 6px;
        margin: 0;
    }
    QScrollArea#floatingListScroll QScrollBar::handle:vertical {
        background-color: $border;
        border-radius: 3px;
        min-height: 24px;
    }
    QScrollArea#floatingListScroll QScrollBar::handle:vertical:hover {
        background-color: $fg_dim;
    }
    QScrollArea#floatingListScroll QScrollBar::add-line:vertical,
    QScrollArea#floatingListScroll QScrollBar::sub-line:vertical {
        height: 0;
    }
    QScrollArea#floatingListScroll QScrollBar::add-page:vertical,
    QScrollArea#floatingListScroll QScrollBar::sub-page:vertical {
        background: transparent;
    }
    QWidget#terminalPanel {
        background-color: $bg_dark;
        border-top: 2px solid $border;
    }

    /* --- Sekmeler: editör (üstte) ve terminal (panel içinde) --- */
    QTabWidget#editorTabs::pane {
        border: none;
        background-color: $bg;
    }
    QTabWidget#editorTabs > QTabBar,
    QTabBar#terminalTabBar {
        background-color: $bg_dark;
        qproperty-drawBase: 0;
    }
    QTabWidget#editorTabs > QTabBar::tab,
    QTabBar#terminalTabBar::tab {
        background-color: $bg_dark;
        color: $fg_dim;
        border: none;
        border-right: 1px solid $bg;
        border-bottom: 2px solid transparent;
        padding: 5px 14px;
        font-family: '$font_family', 'Consolas', monospace;
        font-size: ${size_tab}px;
    }
    QTabWidget#editorTabs > QTabBar::tab:hover,
    QTabBar#terminalTabBar::tab:hover {
        background-color: $panel;
        color: $fg;
    }
    QTabWidget#editorTabs > QTabBar::tab:selected,
    QTabBar#terminalTabBar::tab:selected {
        background-color: $bg;
        color: $blue;
        border-bottom: 2px solid $blue;
    }
    QTabBar#terminalTabBar::tab {
        font-size: ${size_status}px;
        padding: 3px 12px;
    }
"""
