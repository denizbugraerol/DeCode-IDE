from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor
from ui.components.syntax_highlighter import CppHighlighter
from core.state_machine import StateMachine

class ModalEditor(QPlainTextEdit):
    save_requested = pyqtSignal()
    sidebar_toggle_requested = pyqtSignal()
    telescope_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_mode = "NORMAL"  # Uygulama başlarken Normal modda başlasın
        
        # İmleç genişliğini ayarlayarak modları görselleştiriyoruz
        self.cursor_width_insert = 1
        self.cursor_width_normal = 10
        self.setCursorWidth(self.cursor_width_normal)

        # Renklendirme motorunu editörün belgesine (document) bağlıyoruz
        self.highlighter = CppHighlighter(self.document())
        #state_machine yolla
        self.state_machine = StateMachine(self)
    def keyPressEvent(self, event):
        """
        Klavyeden basılan her tuş buraya düşer.
        Tuşları ekrana basmadan önce mod kontrolünden geçiririz.
        """
        if self.current_mode == "NORMAL":
            self.handle_normal_mode(event)
        elif self.current_mode == "INSERT":
            self.handle_insert_mode(event)

    def handle_normal_mode(self, event):
            """ Normal moddayken tuşlar metin yazmaz, State Machine'e gönderilir. ':' ile başlayan komutlar (':w', ':b' vb.) da aynı yoldan, ayrı bir moda geçmeden işlenir. """
            nav_keys = [
                Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right,
                Qt.Key.Key_Home, Qt.Key.Key_End, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown
            ]

            if event.key() == Qt.Key.Key_Escape:
                # Bekleyen tuş/komut dizisini iptal eder (NORMAL mod zaten komut modudur)
                self.state_machine.reset_buffer()

            elif event.key() in nav_keys or event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                super().keyPressEvent(event)

            # Geri kalan normal harfleri State Machine'e gönderiyoruz (':' gibi Shift gerektiren tuşlar için Shift de kabul edilir)
            elif event.text() and event.modifiers() in (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.ShiftModifier):
                self.state_machine.process_key(event.text())

            else:
                event.ignore()


    def handle_insert_mode(self, event):
        """ Insert modundayken VS Code gibi davranır. Sadece Escape tuşunu dinleriz. """
        # Escape tuşuna basılırsa Normal moda dön
        if event.key() == Qt.Key.Key_Escape:
            self.current_mode = "NORMAL"
            self.setCursorWidth(self.cursor_width_normal)
            print("NORMAL moda geçildi.")
        else:
            # Escape değilse, standart yazma işlemini yap (QPlainTextEdit'in kendi işlevi)
            super().keyPressEvent(event)