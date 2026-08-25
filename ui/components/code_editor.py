from PyQt6.QtWidgets import QPlainTextEdit, QWidget
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QTextCursor, QPainter, QColor
from ui.components.syntax_highlighter import CppHighlighter
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
    quit_requested = pyqtSignal()
    mode_changed = pyqtSignal(str)
    command_line_changed = pyqtSignal(str)
    command_suggestions_changed = pyqtSignal(list, int)

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

        # --- Satır numarası gutter'ı (Vim/Neovim'deki 'number' gibi) ---
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self.line_number_area.update)
        self._update_line_number_area_width(0)

    def keyPressEvent(self, event):
        """
        Klavyeden basılan her tuş buraya düşer.
        Tuşları ekrana basmadan önce mod kontrolünden geçiririz.
        """
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
