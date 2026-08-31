""" Testler için ortak kurulum. Qt'yi başsız (offscreen) çalıştırır: CI'da ya
da SSH oturumunda ekran olmadan da testler geçmeli. """
import os

# QApplication oluşturulmadan ÖNCE ayarlanmalı; bu yüzden import'ların en
# üstünde duruyor (main.py'deki wayland;xcb ipucunun test karşılığı).
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """ Tüm test oturumu için tek bir QApplication. Qt aynı süreçte ikinci bir
    örneğe izin vermediği için oturum kapsamlı. """
    return QApplication.instance() or QApplication([])


@pytest.fixture
def pencere(qapp):
    """ Kendi kendini toplayan bir IDEWindow.

    Terminal PTY'si kapatılıp widget ağacı olay döngüsü içinde siliniyor:
    aynı oturumda birden fazla pencere çöp toplayıcıya kalırsa Qt yıkım
    sırasında (QObjectPrivate::deleteChildren) çakılıyor. """
    from ui.main_window import IDEWindow

    window = IDEWindow()
    yield window

    window.terminal_panel.shutdown()
    window.close()
    window.deleteLater()
    qapp.processEvents()
