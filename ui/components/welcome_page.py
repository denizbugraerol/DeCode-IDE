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
from core import keymap
from ui import keys


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
    settings_reload_requested = pyqtSignal()  # ':reload'
    pio_requested = pyqtSignal(str)           # ':pio build|upload|monitor|clean|env'

    # Sekme (metin tamponu) yokken anlamlı olan komutlar. StateMachine öneri
    # listesini buna göre daraltıyor: çalışmayan komut önerilmesin.
    available_commands = ("b", "cd", "openfile", "pio", "qa", "reload",
                          "tabnew", "term", "termnew", "ts")

    # (tür, değer, açıklama). Tür 'command' ise değer olduğu gibi gösterilir;
    # 'action' ise geçerli tuş haritasından üretilir — kısayolunu değiştiren
    # kullanıcıya yalan söylemesin (bkz. apply_keymap).
    HINTS = [
        ("command", ":ts", "dosya bul"),
        ("command", ":openfile <yol>", "dosya aç"),
        ("command", ":tabnew", "yeni boş sekme"),
        ("action", "tab_new", "yeni boş sekme"),
        ("action", "terminal_focus", "terminale geç"),
        ("command", ":qa", "çıkış"),
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

        self._keymap = keymap.defaults()
        self._hints_label = QLabel()
        self._hints_label.setObjectName("welcomeHints")
        self._hints_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._refresh_hints()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(2)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(24)
        layout.addWidget(self._hints_label)
        layout.addStretch(3)

    # --- Klavye ---

    def focusNextPrevChild(self, _next):
        """ Tab odağı kaçırmasın; komut satırındaki tamamlamaya gitsin
        (CommandPalette/TerminalView'daki aynı gerekçe). """
        return False

    def apply_keymap(self, new_keymap):
        """ Haritayı saklar ve ipucu metnini yeniden kurar; ':reload' sonrası
        da doğru kalsın. """
        self._keymap = new_keymap
        self._refresh_hints()

    def _refresh_hints(self):
        self._hints_label.setText("\n".join(
            f"{self._hint_key(kind, value):<16}{description}"
            for kind, value, description in self.HINTS))

    def _hint_key(self, kind, value):
        return value if kind == "command" else self._keymap.label(value)

    def _panel_signal(self, action):
        """ ModalEditor ile aynı eylemler, aynı sinyal adları — IDEWindow
        ikisini de tek tablodan bağlıyor. """
        return {
            "terminal_focus": self.terminal_focus_requested,
            "tab_new": self.tab_new_requested,
            "tab_close": self.tab_close_requested,
            "tab_next": self.tab_next_requested,
            "tab_prev": self.tab_prev_requested,
        }[action]

    def keyPressEvent(self, event):
        action = keys.match(event, self._keymap, "panel")
        if action is not None:
            self._panel_signal(action).emit()
            return

        if self.current_mode == "COMMAND":
            self.state_machine.handle_command_key(event)
        elif keys.match(event, self._keymap, "normal") == "command_line":
            self.state_machine.start_command_line()
        else:
            # 'insert_mode', 'search_next' gibi tampon gerektiren eylemlerin
            # burada karşılığı yok.
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
