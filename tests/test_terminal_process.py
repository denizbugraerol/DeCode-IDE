""" PosixTransport.close()'un iç davranışı: WNOHANG-only reap, süresiz
waitpid asla çağrılmaz.

Argv/cwd/çıkış kodu gibi TerminalProcess sözleşmesinin geri kalanı artık
tests/test_pty_transport.py'de, AKTİF transport'a karşı (POSIX'te
PosixTransport, Windows'ta WindowsTransport) sınanıyor -- burada kalan tek
test PosixTransport'un iç durumuna (fake pid, monkeypatch'lenmiş os.waitpid)
bakıyor, bu yüzden POSIX'e özel ve Windows'ta import bile edilemez. """
import os
import sys

import pytest

POSIX_ONLY = pytest.mark.skipif(
    sys.platform == "win32",
    reason="PosixTransport'un iç davranışı; Windows'ta modül import edilemez")


@POSIX_ONLY
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
    çağrısı WNOHANG taşımalı.

    Transport'a DOĞRUDAN bakıyor: dikişten sonra süreç kimliği ve fd orada
    yaşıyor, TerminalProcess'te değil. """
    from core.pty_posix import PosixTransport

    transport = PosixTransport()
    transport._pid = 424242        # gerçek bir süreç değil; sistem çağrıları taklit
    transport._master_fd = None

    bayraklar = []

    def sahte_waitpid(pid, flags):
        bayraklar.append(flags)
        return (0, 0)              # "henüz toplanamadı" -- hiç toplanmayacak

    monkeypatch.setattr(os, "waitpid", sahte_waitpid)
    monkeypatch.setattr(os, "kill", lambda pid, sig: None)

    transport.close(timeout=0.05)

    assert bayraklar, "close() çocuğu hiç yoklamamış"
    assert all(f & os.WNOHANG for f in bayraklar), (
        f"close() bloklayan waitpid çağırdı (bayraklar={bayraklar})")
    assert transport._pid is None
