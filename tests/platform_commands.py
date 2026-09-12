""" Testlerdeki kabuk komutlarını platforma göre çözen yardımcı.

Testler eskiden '/bin/echo', '/bin/sh -c exit 1' gibi POSIX'e sabit yollar
kullanıyordu; Windows'ta bunların hiçbiri yok ve testler orada import bile
edilemeden anlamsızlaşıyordu.

'/bin/false' bilinçli olarak KULLANILMIYOR: macOS'ta o dosya /usr/bin'de,
/bin'de değil -- orada exec 127 ile başarısız olur ve test ölçmek istediği
şeyi değil kendi taşınabilirsizliğini ölçer. '/bin/sh' POSIX güvencesiyle
her iki sistemde de var. """
import sys

WINDOWS = sys.platform == "win32"


def echo_argv(metin):
    """ Verilen metni basıp 0 ile çıkan komut.

    UYARI (davranış değiştirilmedi, yalnız not): Windows'ta 'cmd /c echo'
    çıktısı konsol kod sayfasından geçer ve GitHub Actions runner'ının
    varsayılan OEM kod sayfası 437'dir -- bu kod sayfasında 'ı ğ ş İ Ğ Ş'
    yoktur. ConPTY'nin ekran tamponu UTF-16 tuttuğu için Türkçe karakter
    içeren testin (tests/test_pty_transport.py) yine de sağ kalması
    beklenir, ama bu HİÇ Windows runner'ında koşulmadı. O test Windows'ta
    kırılırsa ilk şüpheli 'core/pty_windows.py' transport'u değil, BU
    yardımcı olmalı: 'chcp 65001' önekiyle ya da PowerShell tabanlı bir
    argv karşılığıyla çözülür. """
    if WINDOWS:
        return ["cmd", "/c", "echo", metin]
    return ["/bin/echo", metin]


def exit_argv(kod):
    """ Hiçbir şey basmadan verilen kodla çıkan komut. """
    if WINDOWS:
        return ["cmd", "/c", f"exit {kod}"]
    return ["/bin/sh", "-c", f"exit {kod}"]


def pwd_argv():
    """ Çalışma dizinini basan komut ('cwd uygulanıyor mu' testi için).
    Windows'ta argümansız 'cd' bunu yapar. """
    if WINDOWS:
        return ["cmd", "/c", "cd"]
    return ["/bin/pwd"]


def missing_argv():
    """ Var olmayan komut: spawn/exec başarısız olmalı, çıkış kodu 127. """
    if WINDOWS:
        return ["decode-testi-olmayan-komut"]
    return ["/olmayan/komut"]


def exe_name(taban):
    """ Sahte çalıştırılabilir dosya adı. Windows'ta shutil.which yalnız
    PATHEXT uzantılı dosyaları bulur, yani 'pio' değil 'pio.exe' aranır. """
    return f"{taban}.exe" if WINDOWS else taban
