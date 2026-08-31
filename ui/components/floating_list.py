from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QScrollArea,
                             QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt


class FloatingList(QWidget):
    """ Kaydırılabilir, gölgeli, yüzen liste kutusu. Satır sayısı arttıkça
    kutu ekranın dışına taşmasın diye satırlar kaydırılabilir bir panelin
    içinde durur: aynı anda en fazla MAX_VISIBLE_ROWS satır görünür,
    kalanlara fare tekerleğiyle ya da seçimi ilerleterek inilir.

    İki yerde kullanılıyor: komut önerileri (CommandSuggestions) ve telescope
    paleti (CommandPalette). """

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
        self.setObjectName("floatingList")
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
        self._scroll_area.setObjectName("floatingListScroll")
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

    def set_rows(self, labels, selected_index):
        """ Satırları baştan kurar; selected_index'teki satır vurgulanır.
        Satır metinlerinin biçimlenmesi çağırana ait. """
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                # Layout'tan çıkarılan satır, silinmesi (deleteLater) sıraya
                # girene kadar eski yerinde görünmesin diye ebeveyninden koparılır.
                item.widget().setParent(None)
                item.widget().deleteLater()

        self._rows = []
        self._selected_row = None

        for i, label in enumerate(labels):
            row = QLabel(label)
            row.setStyleSheet(self._SELECTED_ROW_STYLE if i == selected_index else self._ROW_STYLE)
            self._layout.addWidget(row)
            self._rows.append(row)
            if i == selected_index:
                self._selected_row = row

        # Liste küçülünce (ör. 9 satırdan 2'ye) Qt eski boyutu önbellekte
        # tutabiliyor; updateGeometry() olmadan fit_to() bunu görmüyor.
        self._layout.invalidate()
        self.updateGeometry()

    def has_rows(self):
        return bool(self._rows)

    def fit_to(self, width, available_height):
        """ Kutuyu verilen genişliğe getirir; yüksekliğini hem
        MAX_VISIBLE_ROWS satırla hem de kalan boşlukla sınırlar. Sığmayan
        satırlar kaydırılarak görülür. """
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
        """ Seçim ilerletildiğinde vurgulanan satır görünen alanın dışında
        kalıyorsa listeyi o satır görünecek kadar kaydırır. """
        if self._selected_row is None:
            return
        # ymargin olarak bir satır boyu veriyoruz: vurgulu satır kenara
        # yapışmasın, altında/üstünde bir satırlık bağlam kalsın.
        self._scroll_area.ensureWidgetVisible(self._selected_row, 0, self._selected_row.sizeHint().height())
