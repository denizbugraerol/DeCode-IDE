import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.main_window import IDEWindow

def main():
    # Wayland üzerinde sorunsuz çalışması için Qt'ye ipucu veriyoruz
    os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

    app = QApplication(sys.argv)
    
    # Ana penceremizi çağırıyoruz
    window = IDEWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()