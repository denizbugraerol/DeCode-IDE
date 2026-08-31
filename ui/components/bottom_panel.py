from PyQt6.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout, QScrollArea,
                             QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt


class StatusLine(QWidget):
    """ Vim/Neovim'deki statusline'a benzer, her zaman görünen üst bar.
    O anki modu (renkli rozet olarak), açık dosyanın adını ve imlecin
    satır:sütun konumunu gösterir. """

    MODE_COLORS = {
        "NORMAL": "#7aa2f7",   # Tokyo Night mavisi
        "INSERT": "#9ece6a",   # Tokyo Night yeşili
        "COMMAND": "#ff9e64",  # Tokyo Night turuncusu
    }

    def __init__(self):
        super().__init__()
        self.setObjectName("statusLine")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(20)  # ince, tek satırlık bir bar

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)

        self.mode_label = QLabel()
        self.mode_label.setObjectName("statusMode")
        self.file_label = QLabel()
        self.position_label = QLabel()

        layout.addWidget(self.mode_label)
        layout.addWidget(self.file_label, 1)
        layout.addWidget(self.position_label)

        self.set_mode("NORMAL")
        self.set_file("[No Name]")
        self.set_position(1, 1)

    def set_mode(self, mode):
        self.mode_label.setText(f" {mode} ")
        color = self.MODE_COLORS.get(mode, self.MODE_COLORS["NORMAL"])
        self.mode_label.setStyleSheet(
            f"background-color: {color}; color: #1a1b26; font-weight: bold; padding: 0 6px; font-size: 11px;"
        )

    def set_file(self, name):
        self.file_label.setText(name or "[No Name]")

    def set_position(self, line, col):
        self.position_label.setText(f"{line}:{col}")


class CommandLine(QLabel):
    """ ':' ile açılan komut satırı. Sabit bir barda değil, komut palet'i gibi
    ekranın ortasında beliren, kenarlıklı/gölgeli yüzen bir kutu olarak durur.
    Sadece COMMAND moddayken (IDEWindow tarafından) gösterilir. """

    def __init__(self):
        super().__init__()
        self.setObjectName("commandLine")
        self.setFixedSize(480, 40)
        self.setText("")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

    def set_text(self, text):
        self.setText(text)


class CommandSuggestions(QWidget):
    """ Komut kutusunun hemen altında beliren öneri listesi. Tab/Shift+Tab ile
    hangi komutun tamamlanacağı, o an vurgulu satırla gösterilir.

    Komut sayısı arttıkça kutu ekranın dışına taşmasın diye satırlar
    kaydırılabilir bir panelin içinde durur: aynı anda en fazla
    MAX_VISIBLE_ROWS satır görünür, kalanlara fare tekerleğiyle ya da Tab ile
    gezinerek inilir. """

    MAX_VISIBLE_ROWS = 8   # kutu bu satır sayısından daha fazla uzamaz
    PADDING = 4            # kutunun kenarı ile satırlar arasındaki boşluk

    _ROW_STYLE = (
        "color: #c0caf5; padding: 4px 12px; "
        "font-family: 'Fira Code', 'Consolas', monospace; font-size: 13px;"
    )
    _SELECTED_ROW_STYLE = (
        "background-color: #283457; color: #ffffff; "
        "padding: 4px 12px; border-radius: 4px; "
        "font-family: 'Fira Code', 'Consolas', monospace; font-size: 13px;"
    )

    def __init__(self):
        super().__init__()
        self.setObjectName("commandSuggestions")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Satırlar doğrudan bu kutuya değil, kaydırılabilir alanın içindeki
        # kaba ekleniyor; kutunun kendi yüksekliğini fit_to() sınırlıyor.
        self._rows_container = QWidget()
        self._layout = QVBoxLayout(self._rows_container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._rows = []
        self._selected_row = None

        self._scroll_area = QScrollArea()
        self._scroll_area.setObjectName("commandSuggestionsScroll")
        self._scroll_area.setWidget(self._rows_container)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Viewport'un varsayılan (beyaz) zemini, kutunun koyu zeminini örter.
        # Ana penceredeki tema kuralları (ve autoFillBackground/translucent
        # denemeleri) viewport'a ulaşmıyor; saydamlığı doğrudan onun kendi
        # stylesheet'ine yazmak gerekiyor. Kaydırma çubukları viewport'un değil
        # QScrollArea'nın çocuğu olduğu için bundan etkilenmez.
        self._scroll_area.viewport().setStyleSheet("background: transparent;")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(self.PADDING, self.PADDING, self.PADDING, self.PADDING)
        outer_layout.setSpacing(0)
        outer_layout.addWidget(self._scroll_area)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

    def set_suggestions(self, matches, selected_index):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                # Layout'tan çıkarılan satır, silinmesi (deleteLater) sıraya
                # girene kadar eski yerinde görünmesin diye ebeveyninden koparılır.
                item.widget().setParent(None)
                item.widget().deleteLater()

        self._rows = []
        self._selected_row = None

        for i, (command, description) in enumerate(matches):
            row = QLabel(f":{command}    {description}")
            row.setStyleSheet(self._SELECTED_ROW_STYLE if i == selected_index else self._ROW_STYLE)
            self._layout.addWidget(row)
            self._rows.append(row)
            if i == selected_index:
                self._selected_row = row

        # Liste küçülünce (ör. 9 öneriden 2'ye) Qt eski boyutu önbellekte
        # tutabiliyor; updateGeometry() olmadan fit_to() bunu görmüyor.
        self._layout.invalidate()
        self.updateGeometry()

    def has_suggestions(self):
        return bool(self._rows)

    def fit_to(self, width, available_height):
        """ Kutuyu komut satırıyla aynı genişliğe getirir; yüksekliğini hem
        MAX_VISIBLE_ROWS satırla hem de komut kutusunun altında kalan boşlukla
        sınırlar. Sığmayan satırlar kaydırılarak görülür. """
        if not self._rows:
            return

        row_height = max(row.sizeHint().height() for row in self._rows)
        chrome = 2 * self.PADDING
        visible_rows = min(len(self._rows), self.MAX_VISIBLE_ROWS)

        height = visible_rows * row_height + chrome
        # Pencere alçaldığında bile en az bir satır görünsün; gerisi kayar.
        height = min(height, max(row_height + chrome, available_height))

        self.setFixedWidth(width)
        self.setFixedHeight(height)

    def scroll_to_selected(self):
        """ Tab/Shift+Tab ile vurgulanan satır görünen alanın dışında kalıyorsa
        listeyi o satır görünecek kadar kaydırır. """
        if self._selected_row is None:
            return
        # ymargin olarak bir satır boyu veriyoruz: vurgulu satır kenara
        # yapışmasın, altında/üstünde bir satırlık bağlam kalsın.
        self._scroll_area.ensureWidgetVisible(self._selected_row, 0, self._selected_row.sizeHint().height())
