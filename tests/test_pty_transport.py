""" Transport sözleşmesinin testleri.

DİKKAT: bunlar AKTİF transport'a karşı koşar -- Linux/macOS'ta
PosixTransport, Windows runner'ında WindowsTransport. Yani tek dosya iki
uygulamayı da sınıyor ve sözleşme ihlali hangi platformda olursa olsun
burada yakalanıyor. Bu yüzden skipif YOK -- POSIX'e özel iki test bunun
istisnası, aşağıda ayrıca işaretli (bkz. POSIX_ONLY).

Sözleşme TerminalProcess üzerinden sınanıyor, transport sınıfı doğrudan
kurulmuyor: dışarıya verilen davranış bu ve iki katmanın birlikte doğru
çalışması asıl mesele. """
import os
import sys
import threading
import time

import pytest

from core.terminal_process import TerminalProcess
from tests.platform_commands import echo_argv, exit_argv, missing_argv, pwd_argv

POSIX_ONLY = pytest.mark.skipif(
    sys.platform == "win32",
    reason="PosixTransport'un iç durumuna (master fd) bakıyor; Windows'ta "
           "modül import edilemez")


def _calistir(bekle, argv, cwd=None, cols=200):
    surec = TerminalProcess(rows=6, cols=cols, argv=argv, cwd=cwd)
    kodlar = []
    surec.exited.connect(kodlar.append)
    surec.start()
    bekle(lambda: bool(kodlar))
    return surec, kodlar


def test_sozlesme_cikti_okunuyor(qapp, bekle):
    surec, kodlar = _calistir(bekle, echo_argv("merhaba"))
    try:
        assert kodlar == [0]
        assert "merhaba" in "".join(surec.screen.display)
    finally:
        surec.close()


def test_sozlesme_turkce_karakter_bozulmuyor(qapp, bekle):
    """ UTF-8 sınır riski: çok baytlı bir karakter iki okuma arasında
    bölünebilir. pyte.ByteStream artık tutan bir decoder taşıdığı için
    doğru birleşmeli -- bu test onu her iki transport'ta da doğruluyor. """
    metin = "ığüşöçİĞÜŞÖÇ" * 20
    surec, kodlar = _calistir(bekle, echo_argv(metin))
    try:
        assert kodlar == [0]
        ekran = "".join(surec.screen.display)
        assert "ığüşöçİĞÜŞÖÇ" in ekran
        assert "\ufffd" not in ekran, "UTF-8 çözümü bozuldu (replacement char)"
    finally:
        surec.close()


def test_sozlesme_cikis_kodu(qapp, bekle):
    surec, kodlar = _calistir(bekle, exit_argv(1))
    try:
        assert kodlar == [1]
        assert surec.exit_code == 1
    finally:
        surec.close()


def test_sozlesme_olmayan_komut_127(qapp, bekle):
    """ 'Komut bulunamadı' = 127, iki platformda da aynı anlam: sekme
    başlığında '✗ (127)' olarak görünüyor. """
    surec, kodlar = _calistir(bekle, missing_argv())
    try:
        assert kodlar == [127]
    finally:
        surec.close()


def test_sozlesme_cwd_uygulanir(qapp, bekle, tmp_path):
    hedef = os.path.realpath(str(tmp_path))
    surec, _kodlar = _calistir(bekle, pwd_argv(), cwd=hedef)
    try:
        assert os.path.basename(hedef) in "".join(surec.screen.display)
    finally:
        surec.close()


def test_sozlesme_close_donuyor_ve_is_running_dusuyor(qapp):
    """ Güvence 2: close() ana iş parçacığında SÜRESİZ bloklanmaz. Süre
    sınırı olmadan bu test yalnız "close() sonunda is_running() düşer" der;
    close() gerçekten asılırsa test FAIL etmez, ASILIR. Üst sınır (5 sn) bu
    riski gerçek bir başarısızlığa çevirir. """
    surec = TerminalProcess(rows=6, cols=40)
    surec.start()
    assert surec.is_running()

    baslangic = time.monotonic()
    surec.close()
    sure = time.monotonic() - baslangic

    assert not surec.is_running()
    assert sure < 5.0, f"close() {sure:.2f}s sürdü -- süresiz bloklanma riski"


def test_sozlesme_close_sonrasi_gec_veri_sinyal_yaymiyor(qapp, bekle):
    """ Kapanıştan sonra gelen veri output_ready yaymamalı: Windows'ta
    reader thread bırakılabildiği için bu gerçek bir risk, POSIX'te de
    notifier kapatılmış olmalı. """
    surec = TerminalProcess(rows=6, cols=40, argv=echo_argv("bir"))
    surec.start()
    surec.close()

    sayac = []
    surec.output_ready.connect(lambda: sayac.append(1))
    bekle(lambda: False, zaman_asimi=0.3)   # olay döngüsünü bir süre döndür
    assert sayac == []


def test_sozlesme_set_size_kosarken_ve_kosmazken(qapp):
    """ PTY boyutu spawn sırasında kuruluyor; süreç yokken gelen ölçü
    ATILIRSA komut sekmesi 80 sütunla başlar ve ilk çıktı yanlış sarmalanır. """
    surec = TerminalProcess(rows=6, cols=40, argv=exit_argv(0))
    surec.resize(9, 120)
    assert (surec.rows, surec.cols) == (9, 120)

    surec.start()
    try:
        surec.resize(10, 100)
        assert (surec.rows, surec.cols) == (10, 100)
        assert surec.screen.columns == 100
    finally:
        surec.close()


def test_sozlesme_resize_transport_set_size_cagirir(qapp):
    """ Yukarıdaki test yalnız TerminalProcess.rows/cols ve screen.columns'u
    ölçüyor -- ikisi de dikişin ÜSTÜNDE, transport'a hiç uğramadan
    kurulabilir. set_size'ı no-op yapan ya da rows/cols'u ters geçiren bir
    transport önceki testten geçer. Bu test dikişin KENDİSİNİ ölçüyor:
    resize()'ın transport.set_size'a doğru argümanlarla, doğru sırada
    uğradığını doğruluyor. """
    surec = TerminalProcess(rows=6, cols=40)
    surec.start()
    try:
        cagrilar = []
        gercek_set_size = surec._transport.set_size

        def casus(rows, cols):
            cagrilar.append((rows, cols))
            return gercek_set_size(rows, cols)

        surec._transport.set_size = casus
        surec.resize(10, 100)

        assert cagrilar == [(10, 100)]
    finally:
        surec.close()


@POSIX_ONLY
def test_sozlesme_set_size_gercek_pty_geometrisini_uygular(qapp):
    """ Yukarıdaki casus testi yalnız "transport.set_size çağrıldı mı"nı
    ölçüyor, transport'un o çağrıyı gerçekten çekirdeğe doğru uyguladığını
    değil. Burada master fd'den TIOCGWINSZ ile geri okuyarak PTY'nin GERÇEK
    geometrisini doğruluyoruz -- 3. task'ın belgelenmiş tuzağı (satır/sütun
    sırasının bir katmanda ters geçmesi) tam burada yakalanır. Windows'ta
    gerçek geometri doğrulaması elle doğrulama listesine bırakıldı. """
    import fcntl
    import struct
    import termios

    surec = TerminalProcess(rows=6, cols=40, argv=exit_argv(0))
    surec.start()
    try:
        surec.resize(10, 100)
        paket = fcntl.ioctl(surec._transport._master_fd, termios.TIOCGWINSZ,
                             struct.pack("HHHH", 0, 0, 0, 0))
        satir, sutun, _xpiksel, _ypiksel = struct.unpack("HHHH", paket)
        assert (satir, sutun) == (10, 100)
    finally:
        surec.close()


def test_sozlesme_callback_ana_ip_parciginda_calisir(qapp, bekle):
    """ Güvence 1: on_data/on_eof (ve dolayısıyla output_ready) HER ZAMAN ana
    iş parçacığında tetiklenir -- pyte.Screen ve TerminalPanel bu güvenceye
    dayanarak tek iş parçacıklı kalıyor. Bugün POSIX'te bedava doğru
    (QSocketNotifier zaten ana döngüde); asıl değeri Windows'ta reader
    thread geldiğinde (3. task) ortaya çıkacak. """
    ana_iplikte = []
    surec = TerminalProcess(rows=6, cols=40, argv=echo_argv("bir"))
    surec.output_ready.connect(
        lambda: ana_iplikte.append(threading.current_thread() is threading.main_thread()))
    surec.start()
    try:
        bekle(lambda: bool(ana_iplikte))
        assert ana_iplikte and all(ana_iplikte)
    finally:
        surec.close()


def test_terminal_destegi_yoksa_uygulama_cokmez(qapp):
    """ pywinpty kurulu değilse uygulama AÇILMAMALI değil -- yalnız terminal
    çalışmamalı. Bu dal her platformda sınanabiliyor çünkü yedek transport
    import dalından bağımsız bir sınıf. """
    from core import terminal_process as tp

    # Asıl çökme yolu import dalı + seçim satırıdır (sys.platform ==
    # "win32" ise pywinpty yok -> _Transport None kalır -> _UnavailableTransport
    # devreye girer); bu dal hiçbir platformda (Linux'ta hiç, Windows'ta
    # pywinpty kuruluyken) koşulmuyor. Burada en azından modülün gerçek
    # seçimi None BIRAKMADIĞINI iddia ediyoruz -- bu makinede
    # PosixTransport'a, pywinpty'siz Windows'ta _UnavailableTransport'a
    # çözülür, ikisinde de None olmamalı.
    assert tp._Transport is not None

    surec = tp.TerminalProcess(rows=6, cols=40, argv=["olsun"])
    surec._transport = tp._UnavailableTransport()
    kodlar = []
    surec.exited.connect(kodlar.append)
    surec.start()

    assert kodlar == [127]
    assert not surec.is_running()
    assert surec.shell_name() == "yok"
