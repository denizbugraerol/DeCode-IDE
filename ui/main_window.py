import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QSplitter, 
                             QTreeView, QPlainTextEdit)
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import Qt, QDir

from ui.components.code_editor import ModalEditor

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
        # --- Sol Panel: Dosya Ağacı (Sidebar) ---
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setRootPath(QDir.rootPath())
        
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_system_model)
        self.tree_view.setRootIndex(self.file_system_model.index(os.getcwd()))
        
        for i in range(1, 4):
            self.tree_view.hideColumn(i)
        self.tree_view.setHeaderHidden(True)

        # --- Sağ Panel: Kod Editörü ---
        # Standart editör yerine kendi ModalEditor'ümüzü çağırıyoruz
        self.editor = ModalEditor()
        self.editor.setPlaceholderText("Normal Mod: Yazmak için 'i' tuşuna basın. Çıkmak için 'Esc'.")

        # Bileşenleri Splitter'a ekliyoruz
        self.splitter.addWidget(self.tree_view)
        self.splitter.addWidget(self.editor)
        self.splitter.setSizes([300, 900])

        #Çift tıklama sinyalini dinle ve open_file fonksiyonuna yönlendir
        self.tree_view.doubleClicked.connect(self.open_file)

    def open_file(self, index):
        # Tıklanan öğenin dosya sistemindeki tam yolunu alıyoruz
        file_path = self.file_system_model.filePath(index)
        
        # Eğer tıklanan şey bir klasör değil de dosyaysa işlemi başlat
        if os.path.isfile(file_path):
            try:
                # Dosyayı UTF-8 formatında oku
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # İçeriği sağ taraftaki kendi ModalEditor'ümüze bas
                self.editor.setPlainText(content)
                
                # Pencere başlığını açılan dosyanın adıyla güncelle
                file_name = os.path.basename(file_path)
                self.setWindowTitle(f"DeCode IDE - {file_name}")
                
            except UnicodeDecodeError:
                self.editor.setPlainText("HATA: Bu dosya metin formatında değil (Örn: Resim veya derlenmiş dosya).")
            except Exception as e:
                self.editor.setPlainText(f"Dosya okunurken bir hata oluştu: {str(e)}")


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