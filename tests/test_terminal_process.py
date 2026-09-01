""" PTY üzerinde komut çalıştırma: argv, cwd ve çıkış kodu.

Gerçek süreç başlatılır (pty.fork), ama yalnız /bin altındaki minik
araçlarla — PlatformIO kurulu olması gerekmez. """
import os

from core.terminal_process import TerminalProcess


def _calistir(bekle, argv, cwd=None, cols=200):
    surec = TerminalProcess(rows=6, cols=cols, argv=argv, cwd=cwd)
    kodlar = []
    surec.exited.connect(kodlar.append)
    surec.start()
    bekle(lambda: bool(kodlar))
    return surec, kodlar


def test_argv_ile_komut_calisir_ve_ciktisi_ekranda(qapp, bekle):
    surec, kodlar = _calistir(bekle, ["/bin/echo", "merhaba"])
    try:
        assert kodlar == [0]
        assert "merhaba" in "".join(surec.screen.display)
    finally:
        surec.close()


def test_basarisiz_komutun_cikis_kodu(qapp, bekle):
    surec, kodlar = _calistir(bekle, ["/bin/false"])
    try:
        assert kodlar == [1]
        assert surec.exit_code == 1
    finally:
        surec.close()


def test_olmayan_komut_127_dondurur(qapp, bekle):
    """ exec başarısız olunca child 127 ile çıkar (kabuk geleneği:
    'command not found'). Sekme başlığında '✗ (127)' olarak görünür. """
    surec, kodlar = _calistir(bekle, ["/olmayan/komut"])
    try:
        assert kodlar == [127]
    finally:
        surec.close()


def test_cwd_uygulanir(qapp, bekle, tmp_path):
    hedef = os.path.realpath(str(tmp_path))
    surec, _kodlar = _calistir(bekle, ["/bin/pwd"], cwd=hedef)
    try:
        assert os.path.basename(hedef) in "".join(surec.screen.display)
    finally:
        surec.close()


def test_argv_verilmezse_shell_baslar(qapp):
    """ Varsayılan davranış (':term') değişmedi: argv yoksa login shell. """
    surec = TerminalProcess(rows=6, cols=40)
    surec.start()
    try:
        assert surec.is_running()
    finally:
        surec.close()


def test_baslamamis_surecte_olcu_saklanir(qapp):
    """ PTY boyutu start() sırasında kuruluyor; 'önce ölç, sonra başlat'
    sırası çalışsın diye resize() koşmayan süreçte de rows/cols'u güncellemeli
    (yoksa komut sekmesi 80 sütunla başlar ve çıktı yanlış sarmalanır). """
    surec = TerminalProcess(rows=6, cols=40, argv=["/bin/true"])
    surec.resize(9, 120)
    assert (surec.rows, surec.cols) == (9, 120)
