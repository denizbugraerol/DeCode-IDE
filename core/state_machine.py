from PyQt6.QtGui import QTextCursor

class StateMachine:
    def __init__(self, editor):
        self.editor = editor
        self.key_buffer = ""

    def process_key(self, text):
        self.key_buffer += text.lower()


        match self.key_buffer:
            case "i":
                self._enter_insert_mode()
                self.key_buffer = ""

            case "in":
                self._open_new_line()
                self.key_buffer = ""

            case "id":
                self._delete_current_line()

            #buffer dolduysa ya da uymuyosa sıfırla bufferı
            case _ if len(self.key_buffer) >= 2:
                    self.key_buffer = text.lower()

    # --- KOMUT FONKSİYONLARI ---

    def _enter_insert_mode(self):
        self.editor.current_mode = "INSERT"
        self.editor.setCursorWidth(self.editor.cursor_width_insert)
        print("MOD: INSERT")

    def _open_new_line(self):
        """ 'i ve n' tuşuna basıldığında bir alt satıra geçer ve Insert moduna girer """
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        cursor.insertText("\n")
        self.editor.setTextCursor(cursor)
        self._enter_insert_mode()

    def _delete_current_line(self):
        """ 'id' komutu için o anki satırı siler """
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.deleteChar()
        self.editor.setTextCursor(cursor)