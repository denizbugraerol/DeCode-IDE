from PyQt6.QtWidgets import (QWidget, QLabel, QHBoxLayout,
                             QGraphicsDropShadowEffect)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from ui import theme
from ui.components.floating_list import FloatingList


class StatusLine(QWidget):
    """ Vim/Neovim'deki statusline'a benzer, her zaman görünen üst bar.
    O anki modu (renkli rozet olarak), açık dosyanın adını ve imlecin
    satır:sütun konumunu gösterir. """

    # Mod -> palet tokeni. Gerçek renk set_mode'da okunuyor ki ':reload'
    # paleti değiştirdiğinde rozet de değişsin.
    MODE_TOKENS = {
        "NORMAL": "blue",
        "INSERT": "green",
        "COMMAND": "orange",
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
        self.env_label = QLabel()
        self.position_label = QLabel()

        layout.addWidget(self.mode_label)
        layout.addWidget(self.file_label, 1)
        layout.addWidget(self.env_label)
        layout.addWidget(self.position_label)

        self.set_mode("NORMAL")
        self.set_file("[No Name]")
        self.set_env(None)
        self.set_position(1, 1)

    def set_mode(self, mode):
        """ Rozetin metnini ve rengini yeniden kurar. Renk VE font, rengi/
        boyutu setStyleSheet içine KOPYALAYAN bir çağrı olduğu için palet ya
        da font_size değiştiğinde kendiliğinden güncellenmez — IDEWindow.
        apply_settings bu yüzden mod değişmese bile bunu açılışta ve
        ':reload'da yeniden çağırır (bkz. kod incelemesi Bulgu 1 ve 4).
        'status' rolü FONT_SIZE_OFFSETS'te editöre göre -4: varsayılan
        font_size=15 ile bugünkü sabit 11px'i birebir üretir. """
        self.mode_label.setText(f" {mode} ")
        color = theme.color(self.MODE_TOKENS.get(mode, "blue"))
        self.mode_label.setStyleSheet(
            f"background-color: {color}; color: {theme.color('bg')}; "
            f"font-weight: bold; padding: 0 6px; "
            f"font-family: '{theme.font_family()}', 'Consolas', monospace; "
            f"font-size: {theme.font_size('status')}px;"
        )

    def set_file(self, name):
        self.file_label.setText(name or "[No Name]")

    def set_env(self, text):
        """ PlatformIO ortamı. Parantezli metin ('(esp32dev)') 'ben seçmedim,
        pio'nun kendi varsayılanı' demek; None etiketi boşaltır.

        Bilinçli olarak setStyleSheet YOK: rengi/fontu stylesheet'e kopyalayan
        her çağrı ':reload'da elle tazelenmek zorunda kalıyor (bkz. set_mode ve
        IDEWindow.apply_settings). Düz metin bu tuzağı hiç doğurmuyor. """
        self.env_label.setText(text or "")

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
