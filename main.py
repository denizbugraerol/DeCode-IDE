import sys
import os
from PyQt6.QtWidgets import QApplication

from core import config
from core.version import __version__
from ui.main_window import IDEWindow


def main(argv=None):
    """ Çıkış kodunu DÖNDÜRÜR (sys.exit çağırmaz) ki '--version' yolu testten
    çağrılabilsin. """
    argv = sys.argv[1:] if argv is None else argv

    # DİKKAT: bu dal QApplication'dan ve ensure_exists'ten ÖNCE olmalı.
    # CI, binary'yi ekransız runner'da '--version' ile duman testinden
    # geçiriyor: Qt platform plugin'i aranmamalı ve ev dizinine ayar dosyası
    # yazılmamalı.
    if "--version" in argv:
        print(f"DeCode IDE {__version__}")
        return 0

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

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
