from PyQt6.QtWidgets import (QWidget, QLabel, QHBoxLayout,
                             QGraphicsDropShadowEffect)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from ui.components.floating_list import FloatingList


class StatusLine(QWidget):
    """ Vim/Neovim'deki statusline'a benzer, her zaman görünen üst bar.
    O anki modu (renkli rozet olarak), açık dosyanın adını ve imlecin
    satır:sütun konumunu gösterir. """

    MODE_COLORS = {
        "NORMAL": "#7aa2f7",   # Tokyo Night mavisi
        "INSERT": "#9ece6a",   # Tokyo Night yeşili
        "COMMAND": "#ff9e64",  # Tokyo Night turuncusu
    }

    def __init__(self):
        super().__init__()
        self.setObjectName("statusLine")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(20)  # ince, tek satırlık bir bar

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)

        self.mode_label = QLabel()
        self.mode_label.setObjectName("statusMode")
        self.file_label = QLabel()
        self.position_label = QLabel()

        layout.addWidget(self.mode_label)
        layout.addWidget(self.file_label, 1)
        layout.addWidget(self.position_label)

        self.set_mode("NORMAL")
        self.set_file("[No Name]")
        self.set_position(1, 1)

    def set_mode(self, mode):
        self.mode_label.setText(f" {mode} ")
        color = self.MODE_COLORS.get(mode, self.MODE_COLORS["NORMAL"])
        self.mode_label.setStyleSheet(
            f"background-color: {color}; color: #1a1b26; font-weight: bold; padding: 0 6px; font-size: 11px;"
        )

    def set_file(self, name):
        self.file_label.setText(name or "[No Name]")

    def set_position(self, line, col):
        """ Satır/sütun; sekme yokken (karşılama sayfası) None verilip boş
        bırakılır. """
        self.position_label.setText(f"{line}:{col}" if line is not None else "")


class CommandLine(QLabel):
    """ ':' ile açılan komut satırı. Sabit bir barda değil, komut palet'i gibi
    ekranın ortasında beliren, kenarlıklı/gölgeli yüzen bir kutu olarak durur.
    Sadece COMMAND moddayken (IDEWindow tarafından) gösterilir. """

    def __init__(self):
        super().__init__()
        self.setObjectName("commandLine")
        self.setFixedSize(480, 40)
        self.setText("")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

    def set_text(self, text):
        self.setText(text)


class CommandSuggestions(FloatingList):
    """ Komut kutusunun hemen altında beliren öneri listesi. Tab/Shift+Tab ile
    hangi komutun tamamlanacağı, o an vurgulu satırla gösterilir.

    Kutunun kendisi (kaydırma, boyutlandırma, gölge) FloatingList'te; burada
    sadece (komut, açıklama) çiftleri satır metnine çevriliyor. """

    def set_suggestions(self, matches, selected_index):
        self.set_rows([f":{command}    {description}" for command, description in matches],
                      selected_index)

    def has_suggestions(self):
        return self.has_rows()
