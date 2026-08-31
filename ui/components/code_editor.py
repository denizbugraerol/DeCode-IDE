from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QPainter, QColor
from ui.components.syntax_highlighter import CppHighlighter, PythonHighlighter
from core.search import find_all, find_next, replace_all
from core.state_machine import StateMachine


class LineNumberArea(QWidget):
    """ ModalEditor'ın solunda satır numaralarını çizen ince yardımcı widget.
    Tüm gerçek iş (boyut/çizim) ModalEditor'a delege edilir — Qt'nin standart
    'Code Editor' örneğindeki desen. """

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class ModalEditor(QPlainTextEdit):
    save_requested = pyqtSignal()
    sidebar_toggle_requested = pyqtSignal()
    telescope_requested = pyqtSignal()
    open_path_requested = pyqtSignal(str)
    symbol_search_requested = pyqtSignal()
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

    def __init__(self):
        super().__init__()
        self.current_mode = "NORMAL"  # Uygulama başlarken Normal modda başlasın

        # Bu sekmenin hangi dosyayı gösterdiği (henüz kaydedilmemişse None).
        # Sekme başlığı, ':w' ve 'zaten açık mı' kontrolü bunu kullanır.
        self.file_path = None

        # ':find <desen>' ile aranan son desen; 'n'/'N' bunu kullanır.
        self.search_pattern = ""

        # İmleç genişliğini ayarlayarak modları görselleştiriyoruz
        self.cursor_width_insert = 1
        self.cursor_width_normal = 10
        self.setCursorWidth(self.cursor_width_normal)

        # Renklendirme motorunu editörün belgesine (document) bağlıyoruz
        self.highlighter = CppHighlighter(self.document())
        #state_machine yolla
        self.state_machine = StateMachine(self)

        # --- Satır numarası gutter'ı (Vim/Neovim'deki 'number' gibi) ---
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self.line_number_area.update)
        self._update_line_number_area_width(0)

    def set_highlighter_for_file(self, file_path):
        """ Dosya uzantısına göre uygun syntax highlighter'a geçer: '.py' için
        PythonHighlighter, diğer her şey için (varsayılan) CppHighlighter. """
        highlighter_cls = PythonHighlighter if file_path and file_path.lower().endswith(".py") else CppHighlighter
        if isinstance(self.highlighter, highlighter_cls):
            return
        self.highlighter.setDocument(None)
        self.highlighter = highlighter_cls(self.document())

    # Terminal panelindekiyle aynı aile: Alt+Shift tabanlı sekme/odak kısayolları
    _PANEL_MODIFIERS = Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier

    def keyPressEvent(self, event):
        """
        Klavyeden basılan her tuş buraya düşer.
        Tuşları ekrana basmadan önce mod kontrolünden geçiririz.
        """
        # Sekme geçişi ve terminale odaklanma her modda çalışır; bu yüzden
        # mod dağıtımından önce bakılır.
        if event.modifiers() == self._PANEL_MODIFIERS:
            if event.key() == Qt.Key.Key_Right:
                self.tab_next_requested.emit()
                return
            if event.key() == Qt.Key.Key_Left:
                self.tab_prev_requested.emit()
                return
            if event.key() == Qt.Key.Key_T:
                self.terminal_focus_requested.emit()
                return

        if self.current_mode == "NORMAL":
            self.handle_normal_mode(event)
        elif self.current_mode == "INSERT":
            self.handle_insert_mode(event)
        elif self.current_mode == "COMMAND":
            self.handle_command_mode(event)

    def handle_normal_mode(self, event):
            """ Normal moddayken tuşlar metin yazmaz. Tek çıplak komutlar var: 'i'
            Insert moduna, ':' gerçek komut satırına (COMMAND mod) geçirir. """
            nav_keys = [
                Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right,
                Qt.Key.Key_Home, Qt.Key.Key_End, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown
            ]

            if event.key() in nav_keys or event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                super().keyPressEvent(event)

            # Escape, text() olarak boş değil ('\x1b') döndüğü için aşağıdaki
            # 'yazılabilir tuş' dalından ÖNCE ele alınmalı.
            elif event.key() == Qt.Key.Key_Escape:
                self.clear_search()

            # 'i' ve ':' dahil, yazılabilir tuşları State Machine'e yönlendiriyoruz
            # (':' gibi Shift gerektiren tuşlar için Shift de kabul edilir)
            elif event.text() and event.modifiers() in (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.ShiftModifier):
                self.state_machine.handle_normal_key(event)

            else:
                event.ignore()

    def handle_command_mode(self, event):
        """ COMMAND modundayken (':' ile açılan gerçek komut satırı) tüm tuşlar
        State Machine'e gider; editörün metnine hiçbir şey yazılmaz. """
        self.state_machine.handle_command_key(event)

    def handle_insert_mode(self, event):
        """ Insert modundayken VS Code gibi davranır. Sadece Escape tuşunu dinleriz. """
        # Escape tuşuna basılırsa Normal moda dön
        if event.key() == Qt.Key.Key_Escape:
            self.current_mode = "NORMAL"
            self.setCursorWidth(self.cursor_width_normal)
            self.mode_changed.emit("NORMAL")
            print("NORMAL moda geçildi.")
        else:
            # Escape değilse, standart yazma işlemini yap (QPlainTextEdit'in kendi işlevi)
            super().keyPressEvent(event)

    # --- Dosya içi arama (':find', 'n', 'N') ---

    def search(self, pattern):
        """ ':find <desen>' — deseni saklar, tüm eşleşmeleri vurgular ve
        imleçten sonraki ilk eşleşmeye atlar. """
        self.search_pattern = pattern
        self._highlight_matches()
        return self.search_next()

    def search_next(self, backward=False):
        """ 'n' / 'N' — saklı desenin sonraki (ya da önceki) eşleşmesini seçer.
        Dosya sonuna gelince başa sarar. Desen yoksa ya da hiç eşleşme yoksa
        False döndürür. """
        if not self.search_pattern:
            return False

        cursor = self.textCursor()
        # Aramaya imlecin bir yanından başlıyoruz ki aynı eşleşmede takılı
        # kalmayalım (Vim'de de 'n' bulunduğun eşleşmeyi tekrar bulmaz).
        start = cursor.selectionStart() - 1 if backward else cursor.selectionStart() + 1

        index = find_next(self.toPlainText(), self.search_pattern, start, backward)
        if index is None:
            print(f"Desen bulunamadı: {self.search_pattern}")
            return False

        cursor.setPosition(index)
        cursor.setPosition(index + len(self.search_pattern), QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(cursor)
        return True

    def clear_search(self):
        """ NORMAL modda Escape — vurguyu temizler (Vim'deki ':nohlsearch').
        Desen saklı kalır, 'n' ile aramaya devam edilebilir. """
        self.setExtraSelections([])

    def _highlight_matches(self):
        """ Aranan desenin tüm geçişlerini Tokyo Night vurgusuyla boyar. """
        selections = []
        if self.search_pattern:
            highlight = QTextCharFormat()
            highlight.setBackground(QColor("#3d59a1"))
            highlight.setForeground(QColor("#ffffff"))

            for index in find_all(self.toPlainText(), self.search_pattern):
                cursor = QTextCursor(self.document())
                cursor.setPosition(index)
                cursor.setPosition(index + len(self.search_pattern), QTextCursor.MoveMode.KeepAnchor)
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format = highlight
                selections.append(selection)

        self.setExtraSelections(selections)

    def replace_all_text(self, old, new):
        """ ':replace eski yeni' — tüm eşleşmeleri değiştirir ve değiştirme
        sayısını döndürür. Tek bir geri-al adımı olsun diye belgenin tamamı
        beginEditBlock/endEditBlock arasında yeniden yazılır; imleç konumu
        elden geldiğince korunur. """
        new_text, count = replace_all(self.toPlainText(), old, new)
        if count == 0:
            return 0

        cursor = self.textCursor()
        position = cursor.position()

        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.insertText(new_text)
        cursor.endEditBlock()

        cursor.setPosition(min(position, len(new_text)))
        self.setTextCursor(cursor)
        self._highlight_matches()
        return count

    def goto_line(self, line_number):
        """ ':42' ve ':sym' ile seçilen sembol için: 1 tabanlı satıra atlar. """
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.Down,
                            QTextCursor.MoveMode.MoveAnchor, max(0, line_number - 1))
        self.setTextCursor(cursor)

    # --- Satır numarası gutter'ı: Qt'nin standart Code Editor deseni ---

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _new_block_count):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#16161e"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        current_line = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                color = QColor("#c0caf5") if block_number == current_line else QColor("#3b4261")
                painter.setPen(color)
                painter.drawText(
                    0, top, self.line_number_area.width() - 6, self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
