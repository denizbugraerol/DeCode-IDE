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
    # '/bin/false' DEĞİL: macOS'ta o dosya /usr/bin'de, /bin'de yok. Orada
    # exec başarısız olur ve child 127 döner ('command not found'), yani test
    # ölçmek istediği şeyi değil, kendi taşınabilirsizliğini ölçer.
    # '/bin/sh' her iki sistemde de POSIX güvencesiyle var.
    surec, kodlar = _calistir(bekle, ["/bin/sh", "-c", "exit 1"])
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
    # argv hiç çalıştırılmıyor (süreç başlatılmıyor), ama macOS'ta var
    # olmayan bir yolu örnek bırakmayalım -- kopyalayan yanılır.
    surec = TerminalProcess(rows=6, cols=40, argv=["/bin/sh", "-c", "exit 0"])
    surec.resize(9, 120)
    assert (surec.rows, surec.cols) == (9, 120)


def test_close_toplanamayan_cocukta_asili_kalmaz(qapp, monkeypatch):
    """ close() hiçbir koşulda BLOKLAYAN waitpid çağırmamalı.

    macOS CI'da yaşanan kilit buydu: pty.fork() çok iş parçacıklı bir süreçten
    çağrıldığında çocuk, fork ile exec arasında sıkışıp yarım saniyede
    toplanabilir hâle gelmiyor. close() o zaman SIGKILL'in ardından zaman
    aşımsız bir os.waitpid(pid, 0)'a giriyor ve dönmüyor -- bu çağrı ANA İŞ
    PARÇACIĞINDA (IDEWindow.closeEvent) olduğu için uygulama kapanışta
    sonsuza kadar donuyor.

    Test gerçek bir öldürülemez süreç kuramaz; onun yerine değişmezi
    doğruluyor: çocuk hiç toplanmasa bile close() dönmeli ve her waitpid
    çağrısı WNOHANG taşımalı. """
    surec = TerminalProcess(rows=6, cols=40)
    surec._pid = 424242            # gerçek bir süreç değil; sistem çağrıları taklit
    surec._master_fd = None

    bayraklar = []

    def sahte_waitpid(pid, flags):
        bayraklar.append(flags)
        return (0, 0)              # "henüz toplanamadı" -- hiç toplanmayacak

    monkeypatch.setattr(os, "waitpid", sahte_waitpid)
    monkeypatch.setattr(os, "kill", lambda pid, sig: None)

    surec.close()

    assert bayraklar, "close() çocuğu hiç yoklamamış"
    assert all(f & os.WNOHANG for f in bayraklar), (
        f"close() bloklayan waitpid çağırdı (bayraklar={bayraklar})")
    assert surec._pid is None
