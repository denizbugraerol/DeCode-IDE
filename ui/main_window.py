import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QSplitter)
from PyQt6.QtCore import Qt, QTimer

from ui.components.sidebar import Sidebar
from ui.components.code_editor import ModalEditor
from ui.components.bottom_panel import StatusLine, CommandLine, CommandSuggestions
from core.file_manager import FileManager


class IDEWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("DeCode IDE - v0.1")
        self.setGeometry(100, 100, 1200, 800)

        # Henüz bir dosya açılmadıysa statusline ve save_file bunu güvenle bilsin
        self.current_file_path = None
        self.current_file_name = "[No Name]"

        # Merkez widget ve ana layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Ekranı böleceğimiz ana splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        #Sol panel - Dosya Sistemi
        self.sidebar = Sidebar()

        # --- Sağ Panel: Kod Editörü ---
        self.editor = ModalEditor()
        self.editor.setPlaceholderText("Normal Mod: Yazmak için 'i', komut için ':' tuşuna basın. Çıkmak için 'Esc'.")

        # Bileşenleri Splitter'a ekliyoruz
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.editor)
        self.splitter.setSizes([300, 900])

        # --- Alt Panel: ince statusline (her zaman altta) ---
        self.status_line = StatusLine()
        self.main_layout.addWidget(self.status_line)

        # --- Komut satırı: bir bara bağlı değil, ekranın ortasında beliren
        # yüzen bir kutu (VSCode komut paleti gibi). Sadece COMMAND moddayken görünür. ---
        self.command_line = CommandLine()
        self.command_line.setParent(self.central_widget)
        self.command_line.hide()

        # --- Komut önerileri: komut kutusunun altında, Tab/Shift+Tab ile
        # gezinilip tamamlanabilen öneri listesi. ---
        self.command_suggestions = CommandSuggestions()
        self.command_suggestions.setParent(self.central_widget)
        self.command_suggestions.hide()

        #Çift tıklama sinyalini dinle ve open_file fonksiyonuna yönlendir
        self.sidebar.doubleClicked.connect(self.open_file)

        # Komut satırı (':w', ':b', ':ts', ':qw') sinyallerini dinle
        self.editor.save_requested.connect(self.save_file)
        self.editor.sidebar_toggle_requested.connect(self.toggle_sidebar_focus)
        self.editor.telescope_requested.connect(self.open_telescope_search)
        self.editor.quit_requested.connect(self.close)

        # Mod, komut satırı ve imleç konumu değiştikçe alt panelleri güncelle
        self.editor.mode_changed.connect(self._on_mode_changed)
        self.editor.command_line_changed.connect(self.command_line.set_text)
        self.editor.command_suggestions_changed.connect(self._on_suggestions_changed)
        self.editor.cursorPositionChanged.connect(self._update_cursor_position)

        # Alt panellerin başlangıç durumunu editörle senkronla
        self._on_mode_changed(self.editor.current_mode)
        self.status_line.set_file(self.current_file_name)
        self._update_cursor_position()

        # Sidebar'dayken Esc'e basılırsa odağı editöre geri ver
        self.sidebar.return_focus_requested.connect(self.editor.setFocus)

    def _on_mode_changed(self, mode):
        """ Statusline'ı günceller; komut satırı kutusunu (ve açıksa öneri
        listesini) sadece COMMAND moddayken ekranın ortasında gösterir. """
        self.status_line.set_mode(mode)

        if mode == "COMMAND":
            self._position_command_line()
            self.command_line.show()
            self.command_line.raise_()
        else:
            self.command_line.hide()
            self.command_suggestions.hide()

    def _on_suggestions_changed(self, matches, selected_index):
        """ Komut satırındaki metne uyan öneriler değiştikçe (yazarken ya da
        Tab/Shift+Tab ile gezinirken) öneri kutusunu günceller. """
        self.command_suggestions.set_suggestions(matches, selected_index)

        if matches and self.editor.current_mode == "COMMAND":
            # Liste boyutu (ör. 9 satırdan 2'ye) küçüldüğünde Qt'nin layout
            # önbelleği aynı olay döngüsü turunda doğru boyutu vermiyor;
            # boyutlandırmayı bir sonraki tur'a erteliyoruz.
            QTimer.singleShot(0, self._show_command_suggestions)
        else:
            self.command_suggestions.hide()

    def _show_command_suggestions(self):
        if self.editor.current_mode != "COMMAND" or not self.command_suggestions._layout.count():
            return
        self.command_suggestions.setFixedWidth(self.command_line.width())
        self.command_suggestions.adjustSize()
        self._position_command_suggestions()
        self.command_suggestions.show()
        self.command_suggestions.raise_()

    def _position_command_line(self):
        """ Komut satırı kutusunu merkez widget'ın tam ortasına yerleştirir. """
        area = self.central_widget.rect()
        x = (area.width() - self.command_line.width()) // 2
        y = (area.height() - self.command_line.height()) // 2
        self.command_line.move(x, y)

    def _position_command_suggestions(self):
        """ Öneri kutusunu komut satırının hemen altına yerleştirir. """
        command_line_geometry = self.command_line.geometry()
        self.command_suggestions.move(command_line_geometry.x(), command_line_geometry.bottom() + 6)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.command_line.isVisible():
            self._position_command_line()
        if self.command_suggestions.isVisible():
            self._position_command_suggestions()

    def _update_cursor_position(self):
        """ İmleç her hareket ettiğinde statusline'daki satır:sütun bilgisini günceller. """
        cursor = self.editor.textCursor()
        self.status_line.set_position(cursor.blockNumber() + 1, cursor.columnNumber() + 1)

    def open_file(self, index):
        # Tıklanan öğenin dosya sistemindeki tam yolunu alıyoruz
        file_path = self.sidebar.get_file_path(index)
        
        try: 
            content = FileManager.read_file(file_path)
            self.editor.setPlainText(content)

            self.current_file_path = file_path
            self.current_file_name = os.path.basename(file_path)

            self.setWindowTitle(f"DeCode IDE - {self.current_file_name}")
            self.status_line.set_file(self.current_file_name)
    
        except UnicodeDecodeError:
            self.editor.setPlainText("HATA: Bu dosya metin formatında değil (Örn: Resim veya derlenmiş dosya).")
        except Exception as e:
            self.editor.setPlainText(f"Dosya okunurken bir hata oluştu: {str(e)}")
    
    def save_file(self):
        if self.current_file_path:
            try:
                content = self.editor.toPlainText()
                FileManager.save_file(self.current_file_path, content)
                
                file_name = os.path.basename(self.current_file_path)
                self.windowTitle(f"DeCode IDE - {file_name} kaydedildi.")

            except Exception as e:
                self.editor.setPlainText(f"Dosya kaydedilirken bir hata oluştu: {str(e)}")

    def toggle_sidebar_focus(self):
            """ ':b' komutuyla odak Sidebar ile Editor arasında gidip gelir. """
            if self.sidebar.hasFocus():
                self.editor.setFocus()
            else:
                self.sidebar.setFocus()

    def open_telescope_search(self):
        """ ':ts' komutuyla tetiklenir — LazyVim'deki Telescope'a benzer bulanık arama modunun temeli.
        Henüz gerçek bir arama arayüzü yok; Faz 2/3'te ui/components/command_palette.py üzerinden uygulanacak. """
        print("Telescope arama modu tetiklendi (henüz uygulanmadı).")


    def _apply_theme(self):
        # Tokyo Night esintili arayüz renkleri
        stylesheet = """
            QMainWindow { background-color: #1a1b26; }
            QTreeView {
                background-color: #16161e;
                color: #c0caf5;
                border: none;
                font-size: 14px;
                outline: none;
            }
            QTreeView::item:selected { background-color: #283457; color: #ffffff; }
            QTreeView::item:hover { background-color: #1f2335; }
            QPlainTextEdit {
                background-color: #1a1b26;
                color: #c0caf5;
                border: none;
                font-family: 'Fira Code', 'Consolas', monospace;
                font-size: 15px;
                padding: 10px;
            }
            QSplitter::handle { background-color: #1f2335; width: 2px; }
            QWidget#statusLine {
                background-color: #1f2335;
            }
            QWidget#statusLine QLabel {
                color: #c0caf5;
                font-family: 'Fira Code', 'Consolas', monospace;
                font-size: 11px;
            }
            QLabel#commandLine {
                background-color: #1f2335;
                color: #c0caf5;
                border: 1px solid #414868;
                border-radius: 8px;
                padding: 4px 12px;
                font-family: 'Fira Code', 'Consolas', monospace;
                font-size: 16px;
            }
            QWidget#commandSuggestions {
                background-color: #1f2335;
                border: 1px solid #414868;
                border-radius: 8px;
            }
        """
        self.setStyleSheet(stylesheet)