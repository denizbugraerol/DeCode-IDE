from PyQt6.QtGui import QTextCursor

class StateMachine:
    # Tüm geçerli komutlar (tek karakterli NORMAL komutları + ':' önekli komutlar)
    KNOWN_COMMANDS = ("i", ":n", ":d", ":w", ":b", ":c", ":v", ":qw", ":ts")

    def __init__(self, editor):
        self.editor = editor
        self.key_buffer = ""

    def process_key(self, text):
        self.key_buffer += text.lower()


        match self.key_buffer:
            case "i":
                self._enter_insert_mode()
                self.key_buffer = ""

            case ":n":
                self._open_new_line()
                self.key_buffer = ""

            case ":d":
                self._delete_current_line()
                self.key_buffer = ""

            case ":w":
                self.editor.save_requested.emit()
                self.key_buffer = ""

            case ":b":
                self.editor.sidebar_toggle_requested.emit()
                self.key_buffer = ""

            case ":c":
                self.editor.copy()
                self.key_buffer = ""

            case ":v":
                self.editor.paste()
                self.key_buffer = ""

            case ":qw":
                self.editor.save_requested.emit()
                self.editor.quit_requested.emit()
                self.key_buffer = ""
            case ":q":
                self.editor.quit_requested.emit()

            case ":ts":
                self.editor.telescope_requested.emit()
                self.key_buffer = ""

            #buffer bilinen bir komutun başlangıcı değilse sıfırla, öyleyse daha fazla tuş bekle
            case _ if not self._is_known_prefix(self.key_buffer):
                self.key_buffer = text.lower()

    def reset_buffer(self):
        """ Escape tuşuna basıldığında bekleyen tuş/komut dizisini iptal eder """
        self.key_buffer = ""

    def _is_known_prefix(self, buffer):
        """ Buffer, KNOWN_COMMANDS'daki komutlardan en az birinin başlangıcı mı kontrol eder """
        return any(command.startswith(buffer) for command in self.KNOWN_COMMANDS)

    # --- KOMUT FONKSİYONLARI ---

    def _enter_insert_mode(self):
        self.editor.current_mode = "INSERT"
        self.editor.setCursorWidth(self.editor.cursor_width_insert)
        print("MOD: INSERT")

    def _open_new_line(self):
        """ ':n' komutuyla bir alt satıra geçer ve Insert moduna girer """
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        cursor.insertText("\n")
        self.editor.setTextCursor(cursor)
        self._enter_insert_mode()

    def _delete_current_line(self):
        """ ':d' komutu için o anki satırı siler """
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.deleteChar()
        self.editor.setTextCursor(cursor)