""" Telescope paletinin dosya kaynağı: çalışma dizinini tarayıp göreli yol
listesi üretir. Tarama saf bir fonksiyon (scan_files) olarak yazıldı; Qt
tarafı onu arka planda çalıştıran ince bir sarmalayıcıdan ibaret. """
import os

from PyQt6.QtCore import QThread, pyqtSignal

# Kod deposunda arama sonucunda görmek istemediğimiz dizinler.
IGNORED_DIRS = frozenset({
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "build", "dist", ".idea", ".vscode",
})

# Dev depolarda tarama sonsuza kadar sürmesin; palet zaten bu kadarını
# anlamlı biçimde gösteremez.
MAX_FILES = 20000


def scan_files(root, ignored_dirs=IGNORED_DIRS, max_files=MAX_FILES):
    """ 'root' altındaki dosyaları köke göreli yollar olarak döndürür.
    IGNORED_DIRS ve nokta ile başlayan dizin/dosyalar atlanır; max_files
    sınırına gelince tarama olduğu yerde biter. Kök okunamıyorsa boş liste. """
    paths = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Yerinde değiştirmek (dirnames[:] = ...) os.walk'a 'bu dizinlere hiç
        # inme' demenin tek yolu. Sıralama, sonucun deterministik olması için.
        dirnames[:] = sorted(
            name for name in dirnames
            if name not in ignored_dirs and not name.startswith(".")
        )

        for name in sorted(filenames):
            if name.startswith("."):
                continue
            paths.append(os.path.relpath(os.path.join(dirpath, name), root))
            if len(paths) >= max_files:
                return paths

    return paths


class FileIndexWorker(QThread):
    """ scan_files'ı arka planda çalıştırır: büyük depolarda tarama arayüzü
    kilitlemesin. Bittiğinde 'ready' sinyaliyle yol listesini yayar. """

    ready = pyqtSignal(list)

    def __init__(self, root, parent=None):
        super().__init__(parent)
        self._root = root

    def run(self):
        self.ready.emit(scan_files(self._root))
