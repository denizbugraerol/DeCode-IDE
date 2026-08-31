import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QStackedWidget, QTabBar, QVBoxLayout, QWidget

from core.terminal_process import TerminalProcess


class TerminalView(QWidget):
    """ Tek bir shell oturumunu (bir PTY + bir pyte ekranı) çizen ve klavye
    girdisini ona ileten widget. Yüksekliği 9 satıra sabitlenir. Panel
    içindeki her sekme bir TerminalView örneğidir. """

    return_focus_requested = pyqtSignal()   # Alt+Shift+T -> odak editöre
    new_tab_requested = pyqtSignal()        # Alt+Shift+N
    close_tab_requested = pyqtSignal()      # Alt+Shift+W
    next_tab_requested = pyqtSignal()       # Alt+Shift+Sağ
    prev_tab_requested = pyqtSignal()       # Alt+Shift+Sol

    ROWS = 9
    PADDING = 6

    # pyte'ın Char.fg / Char.bg alanlarında dönebilecek isimli renkler
    # (vt102 mirasından: "brown" aslında sarıdır) Tokyo Night paletine eşlenir.
    _ANSI_COLORS = {
        "black": "#1a1b26", "red": "#f7768e", "green": "#9ece6a", "brown": "#e0af68",
        "blue": "#7aa2f7", "magenta": "#bb9af7", "cyan": "#7dcfff", "white": "#c0caf5",
        "brightblack": "#414868", "brightred": "#f7768e", "brightgreen": "#9ece6a",
        "brightbrown": "#e0af68", "brightblue": "#7aa2f7", "brightmagenta": "#bb9af7",
        "brightcyan": "#7dcfff", "brightwhite": "#ffffff",
    }
    DEFAULT_FG = QColor("#c0caf5")
    DEFAULT_BG = QColor("#16161e")

    _PANEL_MODIFIERS = Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier

    _KEY_SEQUENCES = {
        Qt.Key.Key_Return: b"\r", Qt.Key.Key_Enter: b"\r",
        Qt.Key.Key_Backspace: b"\x7f", Qt.Key.Key_Tab: b"\t",
        Qt.Key.Key_Escape: b"\x1b",
        Qt.Key.Key_Up: b"\x1b[A", Qt.Key.Key_Down: b"\x1b[B",
        Qt.Key.Key_Right: b"\x1b[C", Qt.Key.Key_Left: b"\x1b[D",
        Qt.Key.Key_Home: b"\x1b[H", Qt.Key.Key_End: b"\x1b[F",
        Qt.Key.Key_PageUp: b"\x1b[5~", Qt.Key.Key_PageDown: b"\x1b[6~",
        Qt.Key.Key_Delete: b"\x1b[3~", Qt.Key.Key_Insert: b"\x1b[2~",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._process = TerminalProcess(rows=self.ROWS, cols=80, parent=self)
        self._process.output_ready.connect(self.update)
        self._process.finished.connect(self.update)

    # --- Boyut ---

    def apply_font(self, font):
        """ Panelden gelen (editörle aynı) fontu uygular ve yüksekliği tam
        9 satıra sabitler. """
        self.setFont(font)
        line_height = self.fontMetrics().lineSpacing()
        self.setFixedHeight(self.ROWS * line_height + 2 * self.PADDING)
        self._recompute_cols()

    def _recompute_cols(self):
        char_width = self.fontMetrics().horizontalAdvance("0")
        if char_width <= 0:
            return
        available = max(char_width, self.width() - 2 * self.PADDING)
        self._process.resize(self.ROWS, max(1, available // char_width))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._recompute_cols()

    def showEvent(self, event):
        super().showEvent(event)
        # Gizliyken layout resizeEvent üretmeyebilir; tekrar görünür olunca
        # savunmacı biçimde yeniden hesapla.
        self._recompute_cols()
        if not self._process.is_running():
            self._process.start()
        self.setFocus()

    # --- Oturum ---

    def shell_name(self):
        return os.path.basename(os.environ.get("SHELL", "/bin/bash"))

    def shutdown(self):
        self._process.close()

    # --- Klavye girdisi ---

    def focusNextPrevChild(self, _next):
        return False  # Tab odak değiştirmesin; shell'e gitsin

    def keyPressEvent(self, event):
        # Alt+Shift kısayolları terminale gönderilmez, panele iletilir.
        if event.modifiers() == self._PANEL_MODIFIERS:
            signal = {
                Qt.Key.Key_T: self.return_focus_requested,
                Qt.Key.Key_N: self.new_tab_requested,
                Qt.Key.Key_W: self.close_tab_requested,
                Qt.Key.Key_Right: self.next_tab_requested,
                Qt.Key.Key_Left: self.prev_tab_requested,
            }.get(event.key())
            if signal is not None:
                signal.emit()
                return

        data = self._translate_key(event)
        if data:
            self._process.write(data)

    def _translate_key(self, event):
        if event.key() in self._KEY_SEQUENCES:
            return self._KEY_SEQUENCES[event.key()]
        text = event.text()
        # Ctrl+C/Ctrl+D/Ctrl+A gibi kontrol kombinasyonları Linux'ta Qt
        # tarafından zaten kontrol byte'ı (\x03, \x04, \x01, ...) olarak
        # event.text()'e konur; ayrı bir eşleme gerekmiyor.
        return text.encode("utf-8", errors="ignore") if text else b""

    # --- Çizim: pyte'ın ekran arabelleğini karakter ızgarası olarak çizer ---

    def paintEvent(self, event):
        super().paintEvent(event)
        screen = self._process.screen
        if screen is None:
            return

        painter = QPainter(self)
        painter.setFont(self.font())
        metrics = self.fontMetrics()
        line_height = metrics.lineSpacing()
        char_width = metrics.horizontalAdvance("0")
        ascent = metrics.ascent()

        for y in range(screen.lines):
            row = screen.buffer[y]
            base_y = self.PADDING + y * line_height
            for x in range(screen.columns):
                cell = row[x]
                fg, bg = self._resolve_colors(cell)
                cx = self.PADDING + x * char_width
                if bg is not None:
                    painter.fillRect(cx, base_y, char_width, line_height, bg)
                if cell.data and cell.data != " ":
                    painter.setPen(fg)
                    painter.drawText(cx, base_y + ascent, cell.data)

        cursor = screen.cursor
        if not cursor.hidden and self.hasFocus():
            cx = self.PADDING + cursor.x * char_width
            cy = self.PADDING + cursor.y * line_height
            painter.fillRect(cx, cy, char_width, line_height, self.DEFAULT_FG)

    def _resolve_colors(self, cell):
        fg = self._resolve_one(cell.fg, self.DEFAULT_FG)
        bg = self._resolve_one(cell.bg, self.DEFAULT_BG)
        if cell.reverse:
            fg, bg = bg, fg
        return fg, (None if bg == self.DEFAULT_BG else bg)

    def _resolve_one(self, value, default):
        if value == "default":
            return default
        if value in self._ANSI_COLORS:
            return QColor(self._ANSI_COLORS[value])
        if len(value) == 6:
            return QColor(f"#{value}")
        return default


class TerminalPanel(QWidget):
    """ Editörün altına gerçek layout ile yerleşen terminal paneli. ':term'
    ile açılıp kapanır; birden fazla shell oturumunu sekmeler halinde tutar.

    Terminal odaktayken çıplak Escape shell'e (ör. vim'in INSERT modundan
    çıkması için) gider; panel işlemleri Alt+Shift ailesindedir:
    T odağı editöre döndürür, N yeni sekme, W sekmeyi kapatır,
    Sağ/Sol sekmeler arasında gezer. """

    return_focus_requested = pyqtSignal()

    TOP_BORDER = 2  # QSS'teki #terminalPanel border-top genişliğiyle senkron

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("terminalPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._font = None

        self.tab_bar = QTabBar()
        self.tab_bar.setObjectName("terminalTabBar")
        self.tab_bar.setDrawBase(False)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.stack = QStackedWidget()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.tab_bar, 0)
        layout.addWidget(self.stack, 1)

        self.tab_bar.currentChanged.connect(self.stack.setCurrentIndex)
        self.tab_bar.currentChanged.connect(self._focus_current_view)

    # --- Görünürlük ---

    def toggle(self):
        """ ':term' komutunun bağlandığı slot. """
        if self.isVisible():
            self.hide()
        else:
            self.open_panel()

    def open_panel(self):
        if self.stack.count() == 0:
            self.new_tab()
        self.show()
        self._focus_current_view()

    def open_new_tab(self):
        """ ':termnew' — panel kapalıysa açar, açıksa yeni bir oturum ekler. """
        if not self.isVisible():
            self.open_panel()
        else:
            self.new_tab()

    def focus_terminal(self):
        """ Editördeki Alt+Shift+T ile terminale odaklanmak için. """
        if self.isVisible():
            self._focus_current_view()

    # --- Sekmeler ---

    def new_tab(self):
        view = TerminalView()
        if self._font is not None:
            view.apply_font(self._font)

        view.return_focus_requested.connect(self.return_focus_requested)
        view.new_tab_requested.connect(self.new_tab)
        view.close_tab_requested.connect(self.close_current_tab)
        view.next_tab_requested.connect(lambda: self.switch_tab(1))
        view.prev_tab_requested.connect(lambda: self.switch_tab(-1))

        index = self.stack.addWidget(view)
        self.tab_bar.addTab("")
        self._relabel_tabs()
        self.tab_bar.setCurrentIndex(index)
        self._recompute_height()
        self._focus_current_view()
        return view

    def close_current_tab(self):
        index = self.tab_bar.currentIndex()
        if index < 0:
            return
        view = self.stack.widget(index)
        view.shutdown()
        self.stack.removeWidget(view)
        self.tab_bar.removeTab(index)
        view.setParent(None)
        view.deleteLater()
        self._relabel_tabs()

        if self.stack.count() == 0:
            # Son oturum da kapandı: panel kapanır, ':term' yeniden açar.
            self.hide()
        else:
            self._focus_current_view()

    def switch_tab(self, step):
        count = self.tab_bar.count()
        if count < 2:
            return
        self.tab_bar.setCurrentIndex((self.tab_bar.currentIndex() + step) % count)

    def _relabel_tabs(self):
        for i in range(self.tab_bar.count()):
            view = self.stack.widget(i)
            self.tab_bar.setTabText(i, f"{i + 1}: {view.shell_name()}")

    def _focus_current_view(self, *_args):
        view = self.stack.currentWidget()
        if view is not None and self.isVisible():
            view.setFocus()

    # --- Boyut / font ---

    def sync_font_with_editor(self, editor_widget):
        """ IDEWindow._apply_theme() içinde, setStyleSheet() çağrısından SONRA
        çağrılır. Panel fontunu editörünkiyle birebir eşitler ki '9 satır'
        editörün gerçek (QSS'ten gelen) satır yüksekliğiyle ölçülsün. """
        editor_widget.ensurePolished()
        self._font = editor_widget.font()
        for i in range(self.stack.count()):
            self.stack.widget(i).apply_font(self._font)
        self._recompute_height()

    def _recompute_height(self):
        """ Panel yüksekliği = sekme çubuğu + 9 satırlık terminal alanı.
        Terminalin kendisi her zaman tam 9 satır kalır. """
        view = self.stack.currentWidget()
        if view is None or self._font is None:
            return
        self.setFixedHeight(self.tab_bar.sizeHint().height() + view.height() + self.TOP_BORDER)

    # --- Kapanış ---

    def shutdown(self):
        """ IDEWindow.closeEvent tarafından çağrılır: tüm oturumları kapatır. """
        for i in range(self.stack.count()):
            self.stack.widget(i).shutdown()
