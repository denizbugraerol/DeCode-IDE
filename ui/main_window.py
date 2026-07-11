import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QSplitter)
from PyQt6.QtCore import Qt

from ui.components.sidebar import Sidebar
from ui.components.code_editor import ModalEditor
from core.file_manager import FileManager


class IDEWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("DeCode IDE - v0.1")
        self.setGeometry(100, 100, 1200, 800)
        
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

        #Çift tıklama sinyalini dinle ve open_file fonksiyonuna yönlendir
        self.sidebar.doubleClicked.connect(self.open_file)

        # Komut satırı (':w', ':b', ':ts', ':qw') sinyallerini dinle
        self.editor.save_requested.connect(self.save_file)
        self.editor.sidebar_toggle_requested.connect(self.toggle_sidebar_focus)
        self.editor.telescope_requested.connect(self.open_telescope_search)
        self.editor.quit_requested.connect(self.close)

        # Sidebar'dayken Esc'e basılırsa odağı editöre geri ver
        self.sidebar.return_focus_requested.connect(self.editor.setFocus)

    def open_file(self, index):
        # Tıklanan öğenin dosya sistemindeki tam yolunu alıyoruz
        file_path = self.sidebar.get_file_path(index)
        
        try: 
            content = FileManager.read_file(file_path)
            self.editor.setPlainText(content)

            self.current_file_path = file_path
            self.current_file_name = os.path.basename(file_path)

            self.setWindowTitle(f"DeCode IDE - {self.current_file_name}")     
    
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
        """
        self.setStyleSheet(stylesheet)