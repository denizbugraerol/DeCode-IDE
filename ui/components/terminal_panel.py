import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QStackedWidget, QTabBar, QVBoxLayout, QWidget

from core.terminal_process import TerminalProcess
from ui import theme


class TerminalView(QWidget):
    """ Tek bir shell oturumunu (bir PTY + bir pyte ekranı) çizen ve klavye
    girdisini ona ileten widget. Yüksekliği ayar dosyasındaki [terminal] rows
    değerine göre belirlenir (varsayılan 9). Panel içindeki her sekme bir
    TerminalView örneğidir. """

    return_focus_requested = pyqtSignal()   # Alt+Shift+T -> odak editöre
    new_tab_requested = pyqtSignal()        # Alt+Shift+N
    close_tab_requested = pyqtSignal()      # Alt+Shift+W
    next_tab_requested = pyqtSignal()       # Alt+Shift+Sağ
    prev_tab_requested = pyqtSignal()       # Alt+Shift+Sol
    command_finished = pyqtSignal()         # komut bitti -> panel başlığı tazelesin

    ROWS = 9
    PADDING = 6

    # pyte'ın Char.fg / Char.bg alanlarında dönebilecek isimli renkler
    # (vt102 mirasından: "brown" aslında sarıdır) palet tokenlarına eşlenir.
    _ANSI_TOKENS = {
        "black": "bg", "red": "red", "green": "green", "brown": "yellow",
        "blue": "blue", "magenta": "purple", "cyan": "cyan", "white": "fg",
        "brightblack": "border", "brightred": "red", "brightgreen": "green",
        "brightbrown": "yellow", "brightblue": "blue", "brightmagenta": "purple",
        "brightcyan": "cyan", "brightwhite": "fg_bright",
    }

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

    def __init__(self, rows=ROWS, argv=None, title=None, cwd=None, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.command_title = title   # None -> shell sekmesi
        self.exit_code = None
        self._finished = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._process = TerminalProcess(rows=self.rows, cols=80, argv=argv,
                                        cwd=cwd, parent=self)
        self._process.output_ready.connect(self.update)
        self._process.finished.connect(self.update)
        self._process.exited.connect(self._on_exited)

    # --- Boyut ---

    def set_rows(self, rows):
        """ Satır sayısını değiştirir. Yüksekliği ve PTY boyutunu yeniden
        ölçmek panelin işi: apply_font'u o çağırıyor (bkz.
        TerminalPanel.apply_settings). """
        self.rows = rows

    def apply_font(self, font):
        """ Panelden gelen (editörle aynı) fontu uygular ve yüksekliği tam
        satır sayısına sabitler. """
        self.setFont(font)
        line_height = self.fontMetrics().lineSpacing()
        self.setFixedHeight(self.rows * line_height + 2 * self.PADDING)
        self._recompute_cols()

    def _recompute_cols(self):
        char_width = self.fontMetrics().horizontalAdvance("0")
        if char_width <= 0:
            return
        available = max(char_width, self.width() - 2 * self.PADDING)
        self._process.resize(self.rows, max(1, available // char_width))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._recompute_cols()

    def showEvent(self, event):
        super().showEvent(event)
        # Gizliyken layout resizeEvent üretmeyebilir; tekrar görünür olunca
        # savunmacı biçimde yeniden hesapla.
        self._recompute_cols()
        # DİKKAT: '_finished' koşulu olmadan, biten bir komut sekmesi panel
        # ':term' ile gizlenip yeniden açıldığında komutu KENDİLİĞİNDEN
        # tekrar çalıştırır — 'pio upload' için bu, gerçek karta yeniden
        # yazmak demek.
        if not self._process.is_running() and not self._finished:
            self._process.start()
        self.setFocus()

    # --- Oturum ---

    def shell_name(self):
        return os.path.basename(os.environ.get("SHELL", "/bin/bash"))

    def _on_exited(self, exit_code):
        self._finished = True
        self.exit_code = exit_code
        self.update()
        self.command_finished.emit()

    def is_finished(self):
        return self._finished

    def title(self):
        """ Sekme etiketi: shell sekmesinde kabuğun adı, komut sekmesinde
        verilen başlık ve süreç bitince sonucu.

        DİKKAT: sekme eşleştirmesi (TerminalPanel._find_command_tab) bu SÜSLÜ
        metne değil command_title'a bakar; yoksa 'pio build ✓' ile 'pio build'
        eşleşmez ve her derleme yeni sekme açar. """
        if self.command_title is None:
            return self.shell_name()
        if not self._finished:
            return self.command_title
        return (f"{self.command_title} ✓" if self.exit_code == 0
                else f"{self.command_title} ✗ ({self.exit_code})")

    def start_now(self):
        """ Sekmenin görünür olmasını beklemeden süreci başlatır (komut
        sekmeleri). Ölçü ÖNCE alınır: PTY boyutu start() sırasında kurulur,
        sonra hesaplamak ilk çıktıyı yanlış genişlikte sarmalar. """
        self._recompute_cols()
        if not self._process.is_running():
            self._process.start()

    def restart(self, argv, cwd=None):
        """ Aynı sekmede yeni bir süreç (K4: ':pio build' ikinci kez). Eski
        süreç TerminalProcess.close() ile (SIGHUP, gerekirse SIGKILL)
        kapatılır; pyte ekranı start() içinde sıfırdan kurulur. """
        self._process.close()
        self._process.argv = argv
        self._process.cwd = cwd
        self._finished = False
        self.exit_code = None
        self.start_now()
        self.command_finished.emit()   # başlıktaki ✓/✗ eki temizlensin

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

        # Paletteki 17 tokenin QColor'ını bu KAREDE bir kez kuruyoruz.
        # Eskiden her hücre kendi _resolve_one çağrısında theme.color(...) +
        # QColor(hex) ayrıştırması yapıyordu (80x9'luk varsayılan ekranda bile
        # hücre başına iki, üstelik _resolve_colors karşılaştırma için ÜÇÜNCÜ
        # bir QColor daha kuruyordu) -- kod incelemesi Bulgu 3, ~7.6x'lik
        # yavaşlama. Kareler arası ÖNBELLEKLEMİYORUZ: bu sözlük her
        # paintEvent'te yeniden kuruluyor ki bir palet değişikliği (':reload')
        # bir SONRAKİ karede hemen görünsün.
        palette_colors = {token: QColor(hex_value) for token, hex_value in theme.palette().items()}

        for y in range(screen.lines):
            row = screen.buffer[y]
            base_y = self.PADDING + y * line_height
            for x in range(screen.columns):
                cell = row[x]
                fg, bg = self._resolve_colors(cell, palette_colors)
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
            painter.fillRect(cx, cy, char_width, line_height, palette_colors["fg"])

    def _ansi_color(self, name, default_token, palette_colors):
        """ pyte'ın verdiği renk adını (ya da 'default'ı) geçerli paletteki
        tokene çevirir. palette_colors bu KAREnin başında paintEvent
        tarafından kurulan QColor önbelleği — böylece ':reload' bir sonraki
        paintEvent'te yine güncel çıkar, ama hücre başına yeniden
        theme.color(...) + QColor(hex) ayrıştırması gerekmez. """
        token = self._ANSI_TOKENS.get(name)
        return palette_colors[token if token else default_token]

    def _resolve_colors(self, cell, palette_colors):
        fg = self._resolve_one(cell.fg, "fg", palette_colors)
        bg = self._resolve_one(cell.bg, "bg_dark", palette_colors)
        if cell.reverse:
            fg, bg = bg, fg
        return fg, (None if bg == palette_colors["bg_dark"] else bg)

    def _resolve_one(self, value, default_token, palette_colors):
        # pyte, 256-renk/truecolor SGR kodlarını (ör. "\x1b[38;2;r;g;bm")
        # 6 haneli hex string olarak verir; bu, hiçbir isimli ANSI rengiyle
        # (en kısası 3 harf, ama hiçbiri 6 harf değil) çakışmaz, palet
        # tokenlarının dışında kalır ve olduğu gibi çizilir. Bunlar palet
        # önbelleğinde YOK (keyfi/sonsuz değer uzayı); yalnız bunlar için
        # hücre başına bir QColor kurulmaya devam eder.
        if len(value) == 6:
            return QColor(f"#{value}")
        return self._ansi_color(value, default_token, palette_colors)


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
        self._rows = TerminalView.ROWS

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
        """ ':termnew' / Alt+Shift+N — her zaman yeni bir SHELL sekmesi. """
        return self._add_view(TerminalView(rows=self._rows))

    def run_command(self, argv, title, cwd=None):
        """ Bir komutu kendi sekmesinde çalıştırır (':pio build'). Aynı
        başlıkla açık bir komut sekmesi varsa yeni sekme açılmaz, o sekme
        yeniden kullanılır (K4). """
        index = self._find_command_tab(title)
        if index is None:
            view = self._add_view(
                TerminalView(rows=self._rows, argv=argv, title=title, cwd=cwd))
            self.show()
            self._activate_layout()
            view.start_now()
        else:
            view = self.stack.widget(index)
            self.tab_bar.setCurrentIndex(index)
            self.show()
            self._activate_layout()
            view.restart(argv, cwd)

        self._relabel_tabs()
        self._focus_current_view()
        return view

    def _find_command_tab(self, title):
        """ Süslenmemiş başlığa göre arar (bkz. TerminalView.title). """
        for i in range(self.stack.count()):
            if self.stack.widget(i).command_title == title:
                return i
        return None

    def _activate_layout(self):
        """ Yeni eklenen sekmenin geometrisi henüz hesaplanmamış olabilir;
        süreci başlatmadan önce layout'u zorlayarak sütun sayısını doğru
        ölçüyoruz (PTY boyutu start()'ta kuruluyor). """
        self.layout().activate()

    def _add_view(self, view):
        """ Sekme kurulumunun ortak yolu: shell sekmesi de komut sekmesi de
        buradan geçer. """
        if self._font is not None:
            view.apply_font(self._font)

        view.return_focus_requested.connect(self.return_focus_requested)
        view.new_tab_requested.connect(self.new_tab)
        view.close_tab_requested.connect(self.close_current_tab)
        view.next_tab_requested.connect(lambda: self.switch_tab(1))
        view.prev_tab_requested.connect(lambda: self.switch_tab(-1))
        view.command_finished.connect(self._relabel_tabs)

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
            self.tab_bar.setTabText(i, f"{i + 1}: {view.title()}")

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

    def apply_settings(self, terminal_settings):
        """ Ayar dosyasındaki [terminal] bölümü. Açık oturumlar kapanmadan
        yeniden boyutlanır. """
        self._rows = terminal_settings["rows"]
        for i in range(self.stack.count()):
            view = self.stack.widget(i)
            view.set_rows(self._rows)
            if self._font is not None:
                # Yükseklik ve PTY satır sayısı fontla birlikte ölçülüyor.
                view.apply_font(self._font)
        self._recompute_height()

    def _recompute_height(self):
        """ Panel yüksekliği = sekme çubuğu + terminal alanı. Terminalin
        kendi satır sayısı ayar dosyasındaki [terminal] rows değerini takip
        eder (varsayılan 9). """
        view = self.stack.currentWidget()
        if view is None or self._font is None:
            return
        self.setFixedHeight(self.tab_bar.sizeHint().height() + view.height() + self.TOP_BORDER)

    # --- Kapanış ---

    def shutdown(self):
        """ IDEWindow.closeEvent tarafından çağrılır: tüm oturumları kapatır. """
        for i in range(self.stack.count()):
            self.stack.widget(i).shutdown()
