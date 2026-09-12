""" Testler için ortak kurulum. Qt'yi başsız (offscreen) çalıştırır: CI'da ya
da SSH oturumunda ekran olmadan da testler geçmeli. """
import os
import sys
import time

# QApplication oluşturulmadan ÖNCE ayarlanmalı; bu yüzden import'ların en
# üstünde duruyor (main.py'deki wayland;xcb ipucunun test karşılığı).
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(autouse=True)
def tema_durumunu_koru():
    """ ui.theme'in paleti ve fontu SÜREÇ GENELİNDE tektir (bilinçli bir
    tasarım: bkz. ui/theme.py). Bir IDEWindow kuran her test apply_settings
    üzerinden set_palette/set_font çağırır, yani durumu bir sonraki teste
    sızdırır. Varsayılanı doğrulayan testler (ör. test_theme.
    test_font_family_varsayilani_fira_code) o yüzden çalışma SIRASINA bağlı
    kalıyordu; burada her testten sonra durum geri alınıyor. """
    import ui.theme as theme

    onceki_palet = theme.palette()
    onceki_aile = theme.font_family()
    onceki_boyut = theme.font_size("editor")
    yield
    theme.set_palette(onceki_palet)
    theme.set_font(onceki_aile, onceki_boyut)


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
    sırasında (QObjectPrivate::deleteChildren) çakılıyor.

    settings açıkça config.default_settings() ile veriliyor: aksi halde
    IDEWindow ayar dosyası yokken bile config.load() çağırır ve testler
    geliştiricinin gerçek ~/.config/decode/config.toml dosyasına bağımlı
    kalır. """
    from core import config
    from ui.main_window import IDEWindow

    window = IDEWindow(settings=config.default_settings())
    yield window

    window.terminal_panel.shutdown()
    window.close()
    window.deleteLater()
    qapp.processEvents()


# Windows'ta süreç bitişi ConPTY katmanında ~5 saniye gecikiyor. CI'da
# ölçüldü: sekiz ardışık spawn'ın hepsi 5.031–5.062 saniye sürdü, oysa süreç
# başarıyla bitiyor ve çıkış kodu ile ekran içeriği doğru geliyor. Eski
# varsayılan olan 5.0 saniye tam o sınırda olduğu için bitişi bekleyen her
# test yarışı milisaniyeyle kaybediyordu (11 test kırıktı).
#
# Gecikme pywinpty'nin Rust katmanında — ptyprocess.py'de 5 saniyelik bir
# sabit yok (delayafterterminate 0.1, PTY timeout'u 30000ms), yani bloklayan
# read()'i tutan şey iseof()'un geç True dönmesi olmalı. Python'dan
# kaldırılamıyor; bilinçli olarak kabul edildi, bkz. docs/Roadmap.md teknik
# borç tablosu.
_ZAMAN_ASIMI = 20.0 if sys.platform == "win32" else 5.0


@pytest.fixture
def bekle(qapp):
    """ PTY testleri için: koşul sağlanana kadar Qt olay döngüsünü döndürür.
    QSocketNotifier yalnız olay döngüsü dönerken tetiklenir — süreç çıktısını
    düz bir 'sleep' ile beklemek işe yaramaz, hiçbir zaman gelmez.

    Varsayılan zaman aşımı platforma göre: Windows'ta 20 saniye (bkz.
    _ZAMAN_ASIMI'nin üstündeki not), başka yerde 5. """
    def _bekle(kosul, zaman_asimi=_ZAMAN_ASIMI):
        son = time.monotonic() + zaman_asimi
        while time.monotonic() < son:
            qapp.processEvents()
            if kosul():
                return True
            time.sleep(0.005)
        return bool(kosul())
    return _bekle
