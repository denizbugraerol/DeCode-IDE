from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt


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
        self.position_label.setText(f"{line}:{col}")


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


class CommandSuggestions(QWidget):
    """ Komut kutusunun hemen altında beliren öneri listesi. Tab/Shift+Tab ile
    hangi komutun tamamlanacağı, o an vurgulu satırla gösterilir. """

    def __init__(self):
        super().__init__()
        self.setObjectName("commandSuggestions")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(0)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

    def set_suggestions(self, matches, selected_index):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, (command, description) in enumerate(matches):
            row = QLabel(f":{command}    {description}")
            if i == selected_index:
                row.setStyleSheet(
                    "background-color: #283457; color: #ffffff; "
                    "padding: 4px 12px; border-radius: 4px; "
                    "font-family: 'Fira Code', 'Consolas', monospace; font-size: 13px;"
                )
            else:
                row.setStyleSheet(
                    "color: #c0caf5; padding: 4px 12px; "
                    "font-family: 'Fira Code', 'Consolas', monospace; font-size: 13px;"
                )
            self._layout.addWidget(row)

        # Liste küçülünce (ör. 9 öneriden 2'ye) Qt eski boyutu önbellekte
        # tutabiliyor; updateGeometry() olmadan adjustSize() bunu görmüyor.
        self._layout.invalidate()
        self.updateGeometry()
