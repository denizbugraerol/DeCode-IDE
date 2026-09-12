""" GEÇİCİ teşhis testi — kök neden bulunup düzeltilince SİLİNECEK.

Neden var: `tools/teshis_windows.py` standalone betiği, kırılan testlerin tam
senaryosunu (`cmd /c echo merhaba` → `TerminalProcess` → Qt döngüsü) Windows
runner'ında çalıştırdı ve SORUNSUZ geçti — `exited(0)` yayıldı, ekranda
'merhaba' vardı. Yani `WindowsTransport` sağlam; kırılma pytest ortamına
özgü.

Kırık test deseni de bunu söylüyor: `test_pty_transport`'ta 12 testin yalnız
3'ü kırık ve hepsi süreç BİTİŞİNİ bekleyenler. Spawn etmeyen ya da bitişi
beklemeyen testler geçiyor.

Bu dosya adı 'aaa' ile başlıyor ki pytest onu İLK koşsun: ölçmek istediğimiz
şeylerden biri, ilk ConPTY spawn'ının soğuk maliyeti.

Ölçtüğü şey: `exited` sinyalinin gelmesi NE KADAR sürüyor. `bekle`
fixture'ının varsayılan zaman aşımı 5 saniye; eğer ilk spawn'lar bunu aşıyorsa
kök neden "transport bozuk" değil "zaman aşımı yetersiz" olur. """
import sys
import time

import pytest

from core.terminal_process import TerminalProcess
from tests.platform_commands import echo_argv, exit_argv

pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows'a özgü teşhis; Linux'ta ölçülecek bir şey yok")


def _sure_olc(qapp, argv, zaman_asimi=30.0):
    """ 'exited' gelene kadar geçen süreyi döndürür; gelmezse None. """
    surec = TerminalProcess(rows=6, cols=200, argv=argv)
    kodlar = []
    surec.exited.connect(kodlar.append)
    olaylar = []
    surec.output_ready.connect(lambda: olaylar.append(1))

    baslangic = time.monotonic()
    surec.start()
    tur = 0
    son = baslangic + zaman_asimi
    while time.monotonic() < son:
        tur += 1
        qapp.processEvents()
        if kodlar:
            break
        time.sleep(0.005)
    gecen = time.monotonic() - baslangic

    try:
        return {
            "gecen": round(gecen, 3),
            "tur": tur,
            "kodlar": list(kodlar),
            "output_ready": len(olaylar),
            "is_running": surec.is_running(),
            "ekran": "".join(surec.screen.display).strip()[:40],
        }
    finally:
        surec.close()


def test_teshis_ardisik_spawn_sureleri(qapp):
    """ Aynı komutu beş kez üst üste çalıştırıp her birinin süresini ölçer.
    İlki yavaş, sonrakiler hızlıysa kök neden soğuk başlatma maliyetidir.

    DİKKAT: sonuç pytest.fail ile raporlanıyor, print ile DEĞİL. pytest
    GEÇEN testlerin stdout'unu yutuyor ve ilk denemede ölçümler tam bu
    yüzden kayboldu. """
    satirlar = ["echo_argv, 5 ardışık spawn:"]
    for i in range(1, 6):
        satirlar.append(f"  {i}. spawn: {_sure_olc(qapp, echo_argv('merhaba'))}")
    satirlar.append("exit_argv(1), 3 ardışık spawn:")
    for i in range(1, 4):
        satirlar.append(f"  {i}. spawn: {_sure_olc(qapp, exit_argv(1))}")
    pytest.fail("TEŞHİS (hata değil):\n" + "\n".join(satirlar), pytrace=False)


def test_teshis_bekle_fixture_ile(qapp, bekle):
    """ Kırılan testlerin kullandığı 'bekle' fixture'ının tam kopyası.
    Burada da kırılıyorsa sorun fixture'ın 5 saniyelik zaman aşımında. """
    surec = TerminalProcess(rows=6, cols=200, argv=echo_argv("merhaba"))
    kodlar = []
    surec.exited.connect(kodlar.append)
    baslangic = time.monotonic()
    surec.start()
    sonuc = bekle(lambda: bool(kodlar))
    gecen = round(time.monotonic() - baslangic, 3)
    ekran = "".join(surec.screen.display).strip()[:40]
    surec.close()
    pytest.fail(f"TEŞHİS (hata değil): bekle() sonuc={sonuc} gecen={gecen}s "
                f"kodlar={kodlar} ekran={ekran!r}", pytrace=False)
