""" Transport sözleşmesinin testleri.

DİKKAT: bunlar AKTİF transport'a karşı koşar -- Linux/macOS'ta
PosixTransport, Windows runner'ında WindowsTransport. Yani tek dosya iki
uygulamayı da sınıyor ve sözleşme ihlali hangi platformda olursa olsun
burada yakalanıyor. Bu yüzden skipif YOK.

Sözleşme TerminalProcess üzerinden sınanıyor, transport sınıfı doğrudan
kurulmuyor: dışarıya verilen davranış bu ve iki katmanın birlikte doğru
çalışması asıl mesele. """
import os

from core.terminal_process import TerminalProcess
from tests.platform_commands import echo_argv, exit_argv, missing_argv, pwd_argv


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
        assert "�" not in ekran, "UTF-8 çözümü bozuldu (replacement char)"
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
    surec = TerminalProcess(rows=6, cols=40)
    surec.start()
    assert surec.is_running()
    surec.close()
    assert not surec.is_running()


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
