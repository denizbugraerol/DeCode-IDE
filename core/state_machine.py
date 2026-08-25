from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor

class StateMachine:
    """ NORMAL moddaki çıplak tuşları (i, :) ve COMMAND moddaki gerçek
    ':' komut satırını (Enter'a basılana kadar serbestçe yazılıp sonra
    çalıştırılan) yönetir. """

    # Bilinen komutlar ve öneri listesinde gösterilecek açıklamaları.
    # Yeni bir komut eklerken burayı ve _execute_command_line'daki match'i
    # birlikte güncelleyin.
    KNOWN_COMMANDS = ("n", "d", "w", "b", "c", "v", "qw", "q", "ts")
    COMMAND_DESCRIPTIONS = {
        "n": "yeni satır aç ve Insert moduna gir",
        "d": "geçerli satırı sil",
        "w": "dosyayı kaydet",
        "b": "sidebar/editör arasında odak değiştir",
        "c": "kopyala",
        "v": "yapıştır",
        "qw": "kaydet ve çık",
        "q": "çık",
        "ts": "telescope arama (yakında)",
    }

    def __init__(self, editor):
        self.editor = editor
        self.command_text = ""
        self._reset_completion_state()

    # --- NORMAL MOD ---

    def handle_normal_key(self, event):
        """ NORMAL moddayken tek bir çıplak tuşa karşılık gelir: 'i' Insert moduna,
        ':' ise gerçek komut satırına geçirir. Başka hiçbir çıplak tuş yok. """
        text = event.text().lower()
        if text == "i":
            self._enter_insert_mode()
        elif text == ":":
            self.start_command_line()

    # --- COMMAND MOD (gerçek ':' komut satırı) ---

    def start_command_line(self):
        """ ':' tuşuna basılınca COMMAND moduna geçer ve boş bir komut satırı açar. """
        self.editor.current_mode = "COMMAND"
        self.command_text = ""
        self.editor.mode_changed.emit("COMMAND")
        self.editor.command_line_changed.emit(":")
        self._refresh_suggestions()

    def handle_command_key(self, event):
        """ COMMAND moddayken her tuş komut metnine eklenir; komut ancak Enter'a
        basılınca çalıştırılır (gerçek Vim komut satırı gibi). Tab/Shift+Tab ise
        öneriler arasında gezinip yazılanı tamamlar. """
        if event.key() == Qt.Key.Key_Escape:
            self._exit_command_line()

        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._execute_command_line()

        elif event.key() == Qt.Key.Key_Tab:
            self._cycle_completion(reverse=event.modifiers() == Qt.KeyboardModifier.ShiftModifier)

        elif event.key() == Qt.Key.Key_Backspace:
            if self.command_text:
                self.command_text = self.command_text[:-1]
                self.editor.command_line_changed.emit(":" + self.command_text)
                self._refresh_suggestions()
            else:
                # ':' de silinirse (Vim'deki gibi) komut satırından tamamen çık
                self._exit_command_line()

        elif event.text():
            self.command_text += event.text()
            self.editor.command_line_changed.emit(":" + self.command_text)
            self._refresh_suggestions()

    def _matches_for(self, prefix):
        """ Verilen önekle başlayan bilinen komutları (ad, açıklama) çiftleri
        olarak, alfabetik sırayla döndürür. Önek boşsa hepsini döndürür. """
        names = [c for c in self.KNOWN_COMMANDS if c.startswith(prefix)] if prefix else list(self.KNOWN_COMMANDS)
        names.sort()
        return [(name, self.COMMAND_DESCRIPTIONS.get(name, "")) for name in names]

    def _refresh_suggestions(self):
        """ Yazma/silme sonrası (Tab dışı her değişiklikte) tamamlama döngüsünü
        sıfırlar ve o anki metne göre öneri listesini yeniden hesaplayıp yayınlar. """
        self._reset_completion_state()
        matches = self._matches_for(self.command_text)
        self.editor.command_suggestions_changed.emit(matches, 0 if matches else -1)

    def _cycle_completion(self, reverse):
        """ Tab/Shift+Tab: ilk basışta o anki metne göre öneri listesini sabitler,
        sonraki basışlarda aynı liste içinde ileri/geri gezinir. """
        if self._completion_prefix is None:
            matches = self._matches_for(self.command_text)
            if not matches:
                return
            self._completion_prefix = self.command_text
            self._completion_matches = matches
            self._completion_index = 0
        else:
            step = -1 if reverse else 1
            self._completion_index = (self._completion_index + step) % len(self._completion_matches)

        self.command_text = self._completion_matches[self._completion_index][0]
        self.editor.command_line_changed.emit(":" + self.command_text)
        self.editor.command_suggestions_changed.emit(self._completion_matches, self._completion_index)

    def _reset_completion_state(self):
        self._completion_prefix = None
        self._completion_matches = []
        self._completion_index = -1

    def _execute_command_line(self):
        """ Enter'a basılınca komut metnini yorumlar. Sayısal bir metin ise ilgili
        satıra atlar (Vim'deki ':42' gibi); değilse bilinen komutlarla eşleştirir. """
        text = self.command_text

        if text.isdigit():
            self._goto_line(int(text))
        else:
            match text:
                case "n":
                    self._open_new_line()
                case "d":
                    self._delete_current_line()
                case "w":
                    self.editor.save_requested.emit()
                case "b":
                    self.editor.sidebar_toggle_requested.emit()
                case "c":
                    self.editor.copy()
                case "v":
                    self.editor.paste()
                case "qw":
                    self.editor.save_requested.emit()
                    self.editor.quit_requested.emit()
                case "q":
                    self.editor.quit_requested.emit()
                case "ts":
                    self.editor.telescope_requested.emit()
                # bilinmeyen komut: sessizce yok sayılır

        self._exit_command_line()

    def _exit_command_line(self):
        """ Komut çalıştıktan sonra ya da Escape/':' silinince NORMAL moda döner. """
        self.command_text = ""
        self._reset_completion_state()
        self.editor.current_mode = "NORMAL"
        self.editor.mode_changed.emit("NORMAL")
        self.editor.command_line_changed.emit("")
        self.editor.command_suggestions_changed.emit([], -1)

    def _goto_line(self, line_number):
        """ ':42' gibi sayısal komutlarla belirtilen satıra imleci taşır. """
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, line_number - 1)
        self.editor.setTextCursor(cursor)

    # --- KOMUT FONKSİYONLARI ---

    def _enter_insert_mode(self):
        self.editor.current_mode = "INSERT"
        self.editor.setCursorWidth(self.editor.cursor_width_insert)
        self.editor.mode_changed.emit("INSERT")
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
