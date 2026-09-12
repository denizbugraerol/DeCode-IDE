import sys
import os
from PyQt6.QtWidgets import QApplication

from core import config
from core.version import __version__
from ui.main_window import IDEWindow


def utf8_cikti_zorla(stream):
    """ Verilen akışı UTF-8'e çevirir; başarılıysa True döner.

    Neden gerekli: Windows'ta sys.stdout bir BORUYA ya da dosyaya gittiğinde
    Python locale kodlamasını kullanıyor -- Türkçe bir Windows'ta cp1254,
    İngilizce bir Windows'ta (ve GitHub runner'ında) cp1252. Bu uygulama
    baştan sona Türkçe mesaj basıyor ve 'ı' ile 'ş' o kod sayfalarının
    birinde ya da ötekinde yok:

        DeCode.exe > log.txt
        -> UnicodeEncodeError: 'charmap' codec can't encode character '\u0131'

    Yani ilk açılışta basılan "Ayar dosyası oluşturuldu: ..." satırı
    uygulamayı çökertiyordu. CI'da ölçüldü: cp1252 ile bu mesajın da,
    "'pio' bulunamadı..." mesajının da, "Sabit genişlikli ... bulunamadı"
    mesajının da kodlanması başarısız.

    İnteraktif konsol ETKİLENMİYOR: Python 3.6+ orada WriteConsoleW ile
    UTF-16 yazıyor. Hata yalnız çıktı yönlendirildiğinde görünüyor, bu yüzden
    release duman testi de yakalamıyor ('--version' çıktısı saf ASCII).

    errors="replace": bir mesaj yine de kodlanamazsa uygulama ÇÖKMEMELİ --
    bozuk bir karakter, kaybolmuş bir uygulamadan iyidir.

    Satır sonu davranışına DOKUNULMUYOR (newline= verilmiyor): Windows'ta
    '\n' -> '\r\n' çevirisi sürüyor. Release duman testi bu yüzden hâlâ
    'tr -d' ile '\r' temizliyor; ikisi bilinçli olarak ayrı tutuluyor.

    stream parametre olarak alınıyor ki bu yol testten sınanabilsin
    (_qt_platform_hint ile aynı desen). """
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is None:
        return False          # pytest'in yakalama nesnesi gibi sarmalayıcılar
    try:
        reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, OSError):
        return False          # kapatılmış ya da yeniden kurulamayan akış
    return True


def _qt_platform_hint(platform_name, current):
    """ QT_QPA_PLATFORM'a yazılacak değer; None ise ortama DOKUNULMAZ.

    'wayland;xcb' yalnız Linux'ta anlamlı. macOS ('darwin') ve Windows'ta Qt
    kendi plugin'ini ('cocoa' / 'windows') seçmeli; oraya bu değeri yazmak
    olmayan plugin'leri aratır ve uygulama hiç açılmaz.

    Kullanıcının açıkça verdiği değer EZİLMEZ. Eskiden koşulsuz atanıyordu ve
    bu sessiz bir tuzaktı: 'QT_QPA_PLATFORM=xcb ./DeCode' ile yapılan bir
    doğrulama aslında yine 'wayland;xcb' çalıştırıyordu, yani X11 hiç
    sınanmamış oluyordu. """
    if current:
        return None
    if platform_name.startswith("linux"):
        return "wayland;xcb"
    return None


def main(argv=None):
    """ Çıkış kodunu DÖNDÜRÜR (sys.exit çağırmaz) ki '--version' yolu testten
    çağrılabilsin. """
    argv = sys.argv[1:] if argv is None else argv

    # HER print'ten ÖNCE: Türkçe mesajlar Windows'ta boruya yazılamıyordu
    # (bkz. utf8_cikti_zorla). stdout ve stderr ayrı ayrı, çünkü uyarılar
    # ikisine de düşebiliyor.
    utf8_cikti_zorla(sys.stdout)
    utf8_cikti_zorla(sys.stderr)

    # DİKKAT: bu dal QApplication'dan ve ensure_exists'ten ÖNCE olmalı.
    # CI, binary'yi ekransız runner'da '--version' ile duman testinden
    # geçiriyor: Qt platform plugin'i aranmamalı ve ev dizinine ayar dosyası
    # yazılmamalı.
    if "--version" in argv:
        print(f"DeCode IDE {__version__}")
        return 0

    # Wayland üzerinde sorunsuz çalışması için Qt'ye ipucu veriyoruz
    # (yalnız Linux'ta ve yalnız kullanıcı bir şey belirtmemişse).
    hint = _qt_platform_hint(sys.platform, os.environ.get("QT_QPA_PLATFORM"))
    if hint:
        os.environ["QT_QPA_PLATFORM"] = hint

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
