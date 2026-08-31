""" Tema: adlandırılmış renk paleti ve ondan üretilen Qt stylesheet'i.

Renkler tek yerde durur. Bileşenler rengi BOYAMA ANINDA theme.color(...) ile
okur; böylece ':reload' paleti değiştirdiğinde yeniden çizilen her şey yeni
renklerle gelir ve paleti beş ayrı yapıcıya elden geçirmek gerekmez.

Geçerli palet süreç genelinde tektir — uygulamanın teması gerçekten global bir
şey. set_palette onu değiştiren tek kapıdır. """
from string import Template

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


def color(token):
    """ Geçerli paletten bir renk. Bileşenler bunu boyama anında çağırır. """
    return _current[token]


def palette():
    return dict(_current)


def set_palette(new_palette):
    _current.clear()
    _current.update(new_palette)


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
