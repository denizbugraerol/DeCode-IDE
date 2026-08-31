""" Telescope tarzı yüzen seçici: üstte yazdıkça daralan sorgu satırı, altında
bulanık eşleşmelerin listesi. ':ts' (dosya) ve ':sym' (sembol) aynı bileşeni
farklı öğe kaynağıyla kullanır.

Komut satırının aksine palet odağı KENDİ alır (terminal panelindeki desen):
tuşlar editöre değil buraya düşer, Escape odağı editöre geri verir. """
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QLabel, QVBoxLayout, QWidget

from core.fuzzy import rank
from ui.components.floating_list import FloatingList


class CommandPalette(QWidget):

    accepted = pyqtSignal(object)   # seçilen öğenin payload'ı
    cancelled = pyqtSignal()

    WIDTH = 520
    MAX_RESULTS = 200

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("commandPalette")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedWidth(self.WIDTH)

        self.mode = None        # "file" | "symbol" — IDEWindow seçimi buna göre yorumlar
        self.query = ""
        self._title = ""
        self._items = []        # (görünen metin, payload)
        self._results = []      # filtrelenmiş (görünen metin, payload)
        self._selected = 0

        self._prompt = QLabel()
        self._prompt.setObjectName("palettePrompt")
        self._list = FloatingList()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._prompt)
        layout.addWidget(self._list)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

    # --- Açma / öğe kaynağı ---

    def open_with(self, title, items, mode):
        """ Paleti sıfırdan açar. 'items' henüz hazır değilse boş verilebilir;
        tarama bitince set_items ile doldurulur. """
        self.mode = mode
        self._title = title
        self.query = ""
        self.set_items(items)

    def set_items(self, items):
        """ Öğe kaynağını değiştirir (arka plan taraması bitince çağrılır) ve
        o anki sorguyla yeniden filtreler. """
        self._items = list(items)
        self._refilter()

    # --- Sorgu / filtre ---

    def _refilter(self):
        """ Bulanık skorlayıcıyla filtreler. rank() düz metin listesiyle
        çalıştığı için görünen metinden payload'a geri eşleme yapıyoruz. """
        if self.query:
            by_label = {label: payload for label, payload in self._items}
            ordered = rank(self.query, list(by_label), limit=self.MAX_RESULTS)
            self._results = [(label, by_label[label]) for label in ordered]
        else:
            self._results = self._items[:self.MAX_RESULTS]

        self._selected = 0
        self._render()

    def _render(self):
        counter = f"{len(self._results)}/{len(self._items)}"
        self._prompt.setText(f"{self._title}  ❯ {self.query}    {counter}")
        self._list.set_rows([label for label, _payload in self._results], self._selected)
        # Palet ekranın üst üçte birinde durduğu için kutuya bol yer var;
        # yüksekliği MAX_VISIBLE_ROWS zaten sınırlıyor.
        self._list.fit_to(self.WIDTH, 9999)
        self._list.scroll_to_selected()

    def current_payload(self):
        if not self._results:
            return None
        return self._results[self._selected][1]

    def _move_selection(self, step):
        if not self._results:
            return
        self._selected = (self._selected + step) % len(self._results)
        self._render()

    # --- Klavye ---

    def focusNextPrevChild(self, _next):
        """ Tab'ın odağı başka widget'a kaçırmasını engeller; Tab da bize
        keyPressEvent olarak gelsin (TerminalView'daki aynı gerekçe). """
        return False

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key.Key_Escape:
            self.cancelled.emit()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            payload = self.current_payload()
            if payload is not None:
                self.accepted.emit(payload)
        elif key in (Qt.Key.Key_Down, Qt.Key.Key_Tab):
            self._move_selection(1)
        elif key in (Qt.Key.Key_Up, Qt.Key.Key_Backtab):
            self._move_selection(-1)
        elif key == Qt.Key.Key_Backspace:
            self.query = self.query[:-1]
            self._refilter()
        elif event.text() and event.text().isprintable():
            self.query += event.text()
            self._refilter()
        else:
            super().keyPressEvent(event)
