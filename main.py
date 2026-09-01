import sys
import os
from PyQt6.QtWidgets import QApplication

from core import config
from ui.main_window import IDEWindow


def main():
    # Wayland üzerinde sorunsuz çalışması için Qt'ye ipucu veriyoruz
    os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

    # Ayar dosyası yoksa yorumlu şablonu yaz; ardından oku. Ev dizinine yazan
    # tek yer burası (IDEWindow oluşturmak dosya yaratmaz).
    path = config.config_path()
    if config.ensure_exists(path):
        print(f"Ayar dosyası oluşturuldu: {path}")

    settings, warnings = config.load(path)
    for warning in warnings:
        print(warning)

    app = QApplication(sys.argv)

    window = IDEWindow(settings=settings)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
