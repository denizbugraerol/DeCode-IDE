""" PyInstaller ile dondurulmuş binary'de PTY çocuğuna verilen ortam.

Bootloader LD_LIBRARY_PATH'i paketin açıldığı dizine çevirir ve orijinali
'<AD>_ORIG' altında saklar. Bu ortam kabuğa miras kalırsa içeriden
çalıştırılan sistem binary'leri (pio, git, ls) paketlenmiş kütüphanelerle
çakışır. child_environment saf tutuluyor ki bu yol DONMADAN test edilebilsin
— aksi halde yalnız yayınlanmış binary'de sınanabilirdi. """
from core.terminal_process import child_environment


def test_donmus_ortamda_ld_library_path_geri_alinir():
    ortam = {
        "PATH": "/usr/bin",
        "LD_LIBRARY_PATH": "/tmp/_MEI123456",
        "LD_LIBRARY_PATH_ORIG": "/usr/local/lib",
    }

    sonuc = child_environment(ortam, frozen=True)

    assert sonuc["LD_LIBRARY_PATH"] == "/usr/local/lib"
    assert "LD_LIBRARY_PATH_ORIG" not in sonuc


def test_donmus_ortamda_orig_yoksa_degisken_silinir():
    """ Kullanıcının LD_LIBRARY_PATH'i hiç yoktuysa bootloader _ORIG yazmaz;
    o zaman değişken tamamen kaldırılmalı, bootloader değeri sızmamalı. """
    ortam = {"PATH": "/usr/bin", "LD_LIBRARY_PATH": "/tmp/_MEI123456"}

    sonuc = child_environment(ortam, frozen=True)

    assert "LD_LIBRARY_PATH" not in sonuc


def test_donmamis_ortam_degismeden_gecer():
    """ Geliştirme ortamında (python3 main.py) davranış bugünküyle birebir
    aynı kalmalı. """
    ortam = {"PATH": "/usr/bin", "LD_LIBRARY_PATH": "/opt/kendi/lib"}

    sonuc = child_environment(ortam, frozen=False)

    assert sonuc == ortam


def test_ld_preload_da_geri_alinir():
    ortam = {"LD_PRELOAD": "/tmp/_MEI123456/libz.so", "LD_PRELOAD_ORIG": "/lib/libx.so"}

    sonuc = child_environment(ortam, frozen=True)

    assert sonuc["LD_PRELOAD"] == "/lib/libx.so"
    assert "LD_PRELOAD_ORIG" not in sonuc


def test_ilgisiz_degiskenler_korunur():
    ortam = {"PATH": "/usr/bin", "HOME": "/home/deniz", "SHELL": "/usr/bin/fish"}

    sonuc = child_environment(ortam, frozen=True)

    assert sonuc == ortam


def test_kaynak_sozluk_degistirilmez():
    """ Kopya döndürülmeli; çağıranın os.environ'ı bozulmamalı. """
    ortam = {"LD_LIBRARY_PATH": "/tmp/_MEI1", "LD_LIBRARY_PATH_ORIG": "/usr/lib"}

    child_environment(ortam, frozen=True)

    assert ortam["LD_LIBRARY_PATH"] == "/tmp/_MEI1"
