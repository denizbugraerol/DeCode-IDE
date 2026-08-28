import os
from PyQt6.QtWidgets import QTreeView
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import QDir, Qt, pyqtSignal

class Sidebar(QTreeView):
    return_focus_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._setup_model()

    def _setup_model(self):
        # Dosya sistemi modelini oluştur
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setRootPath(QDir.rootPath())
        
        # Modeli ağaca bağla
        self.setModel(self.file_system_model)
        
        # Varsayılan olarak projenin bulunduğu klasörü aç
        self.set_root_path(os.getcwd())

        # Sadece dosya adını göster (Boyut ve Tarih sütunlarını gizle)
        for i in range(1, 4):
            self.hideColumn(i)
        self.setHeaderHidden(True)

    def set_root_path(self, path):
        """ Sidebar'ın kök dizinini değiştirir (':cd <yol>' komutuyla tetiklenir). """
        self.setRootIndex(self.file_system_model.index(path))

    def get_file_path(self, index):
        """ Tıklanan öğenin tam dosya yolunu döndüren yardımcı fonksiyon """
        return self.file_system_model.filePath(index)

    def keyPressEvent(self, event):
        """ Esc tuşuna basılırsa odağı editöre geri verir, böylece komut girmeye kaldığın yerden devam edebilirsin.
        Sağ ok bir dosyanın üzerindeyse (klasör değilse) dosyayı açar; klasördeyse Qt'nin
        varsayılan genişletme davranışına düşer. Enter/Return için ekstra koda gerek yok:
        Qt zaten 'activated' sinyalini kendiliğinden yayınlıyor (bkz. main_window._setup_ui). """
        if event.key() == Qt.Key.Key_Escape:
            self.return_focus_requested.emit()
        elif event.key() == Qt.Key.Key_Right:
            index = self.currentIndex()
            if index.isValid() and not self.file_system_model.isDir(index):
                self.activated.emit(index)
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)