""" Son sekme kapandığında editörün yerini alan karşılama sayfası.

Uygulama artık son ':q' ile kapanmıyor; sekmesiz bir sayfada bekliyor. Bu
sayfanın kendi StateMachine'i var, yani ':' komut satırı burada da çalışıyor —
ama yalnızca bir metin tamponu gerektirmeyen komutlar için (':ts', ':openfile',
':cd', ':tabnew', ':term', ':qa'). Aksi halde sekme yokken ne dosya bulunabilir
ne de klavyeyle çıkılabilirdi.

ModalEditor ile aynı sinyal adlarını yayar; IDEWindow ikisini de aynı tablodan
bağlıyor (bkz. IDEWindow._connect_modal_host). """
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.state_machine import StateMachine


class WelcomePage(QWidget):

    # --- ModalEditor ile aynı sinyaller (IDEWindow tek tabloyla bağlıyor) ---
    save_requested = pyqtSignal()
    sidebar_toggle_requested = pyqtSignal()
    telescope_requested = pyqtSignal()
    symbol_search_requested = pyqtSignal()
    open_path_requested = pyqtSignal(str)
    change_directory_requested = pyqtSignal(str)
    quit_requested = pyqtSignal()
    terminal_toggle_requested = pyqtSignal()
    terminal_new_requested = pyqtSignal()
    terminal_focus_requested = pyqtSignal()
    tab_new_requested = pyqtSignal()
    tab_close_requested = pyqtSignal()
    tab_next_requested = pyqtSignal()
    tab_prev_requested = pyqtSignal()
    mode_changed = pyqtSignal(str)
    command_line_changed = pyqtSignal(str)
    command_suggestions_changed = pyqtSignal(list, int)

    # Sekme (metin tamponu) yokken anlamlı olan komutlar. StateMachine öneri
    # listesini buna göre daraltıyor: çalışmayan komut önerilmesin.
    available_commands = ("b", "cd", "openfile", "qa", "tabnew", "term", "termnew", "ts")

    # Terminal ve editördekiyle aynı aile
    _PANEL_MODIFIERS = Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier

    HINTS = [
        (":ts", "dosya bul"),
        (":openfile <yol>", "dosya aç"),
        (":tabnew", "yeni boş sekme"),
        ("Alt+Shift+N", "yeni boş sekme"),
        ("Alt+Shift+T", "terminale geç"),
        (":qa", "çıkış"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("welcomePage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.current_mode = "NORMAL"
        self.state_machine = StateMachine(self)

        title = QLabel("DeCode IDE")
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Açık sekme yok")
        subtitle.setObjectName("welcomeSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hints = QLabel("\n".join(f"{key:<16}{description}" for key, description in self.HINTS))
        hints.setObjectName("welcomeHints")
        hints.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(2)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(24)
        layout.addWidget(hints)
        layout.addStretch(3)

    # --- Klavye ---

    def focusNextPrevChild(self, _next):
        """ Tab odağı kaçırmasın; komut satırındaki tamamlamaya gitsin
        (CommandPalette/TerminalView'daki aynı gerekçe). """
        return False

    def keyPressEvent(self, event):
        if event.modifiers() == self._PANEL_MODIFIERS:
            signal = {
                Qt.Key.Key_T: self.terminal_focus_requested,
                Qt.Key.Key_N: self.tab_new_requested,
                Qt.Key.Key_W: self.tab_close_requested,
                Qt.Key.Key_Right: self.tab_next_requested,
                Qt.Key.Key_Left: self.tab_prev_requested,
            }.get(event.key())
            if signal is not None:
                signal.emit()
                return

        if self.current_mode == "COMMAND":
            self.state_machine.handle_command_key(event)
        elif event.text() == ":":
            self.state_machine.start_command_line()
        else:
            # 'i', 'n', 'N' gibi tampon gerektiren çıplak tuşların burada
            # karşılığı yok.
            event.ignore()

    # --- StateMachine'in editörde beklediği işlemler ---
    # Sekme yokken üzerinde çalışılacak metin olmadığı için hepsi sessiz.
    # (Bu komutlar available_commands'ta olmadığından öneri listesinde de
    # görünmüyor; yine de elle yazılabilirler.)

    def copy(self):
        pass

    def paste(self):
        pass

    def delete_current_line(self):
        pass

    def goto_line(self, line_number):
        pass

    def search(self, pattern):
        return False

    def search_next(self, backward=False):
        return False

    def replace_all_text(self, old, new):
        return 0
