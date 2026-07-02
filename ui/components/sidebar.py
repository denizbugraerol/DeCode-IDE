import os
from PyQt6.QtWidgets import QTreeView
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import QDir

class Sidebar(QTreeView):
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
        current_dir = os.getcwd()
        self.setRootIndex(self.file_system_model.index(current_dir))
        
        # Sadece dosya adını göster (Boyut ve Tarih sütunlarını gizle)
        for i in range(1, 4):
            self.hideColumn(i)
        self.setHeaderHidden(True)

    def get_file_path(self, index):
        """ Tıklanan öğenin tam dosya yolunu döndüren yardımcı fonksiyon """
        return self.file_system_model.filePath(index)