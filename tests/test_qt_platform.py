""" QT_QPA_PLATFORM ipucunun platforma göre seçilmesi.

'wayland;xcb' yalnız Linux'ta anlamlı: macOS'ta Qt'ye olmayan plugin'leri
aratır ve uygulama hiç açılmaz. Ayrıca kullanıcının açıkça verdiği değer
EZİLMEMELİ -- eskiden koşulsuz atanıyordu, bu yüzden
'QT_QPA_PLATFORM=xcb ./DeCode' ile yapılan bir doğrulama aslında yine
'wayland;xcb' çalıştırıyordu. """
import main


def test_linuxta_wayland_xcb_ipucu_verilir():
    assert main._qt_platform_hint("linux", None) == "wayland;xcb"


def test_macoste_ipucu_verilmez():
    """ macOS'ta Qt kendi 'cocoa' plugin'ini seçmeli. """
    assert main._qt_platform_hint("darwin", None) is None


def test_windowsta_ipucu_verilmez():
    assert main._qt_platform_hint("win32", None) is None


def test_kullanicinin_secimi_ezilmez():
    """ Linux'ta bile: açıkça verilmiş bir değer korunur, yoksa belirli bir
    platform plugin'iyle test etmek imkânsız hale gelir. """
    assert main._qt_platform_hint("linux", "xcb") is None
    assert main._qt_platform_hint("linux", "offscreen") is None


def test_bos_dize_verilmemis_sayilir():
    assert main._qt_platform_hint("linux", "") == "wayland;xcb"
