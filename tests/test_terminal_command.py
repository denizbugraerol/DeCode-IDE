""" Terminal panelinde komut sekmesi: başlık, çıkış durumu, yeniden kullanım.
Gerçek PlatformIO gerekmiyor; /bin/echo ve /bin/false yetiyor. """
from PyQt6.QtGui import QShowEvent


def test_komut_sekmesi_baslik_ve_basarili_cikis(pencere, bekle):
    panel = pencere.terminal_panel
    view = panel.run_command(["/bin/echo", "merhaba"], "pio build")

    assert view.title() == "pio build"
    assert bekle(view.is_finished)
    assert view.title() == "pio build ✓"
    assert "merhaba" in "".join(view._process.screen.display)
    assert panel.tab_bar.tabText(0).endswith("pio build ✓")


def test_basarisiz_komut_sekmede_isaretlenir(pencere, bekle):
    # '/bin/false' macOS'ta yok (/usr/bin'de); orada exec 127 döndürür ve
    # test başlıktaki '✗ (1)' yerine '✗ (127)' görür.
    view = pencere.terminal_panel.run_command(["/bin/sh", "-c", "exit 1"], "pio upload")
    assert bekle(view.is_finished)
    assert view.title() == "pio upload ✗ (1)"


def test_ayni_komut_ayni_sekmeyi_kullanir(pencere, bekle):
    """ K4 regresyonu: ikinci çağrı bitmiş sekmeyi bulmalı. Eşleştirme
    süslenmiş başlığa ('pio build ✓') bakarsa burada kaçırır ve yeni sekme
    açar. """
    panel = pencere.terminal_panel
    ilk = panel.run_command(["/bin/echo", "bir"], "pio build")
    assert bekle(ilk.is_finished)
    sekme_sayisi = panel.stack.count()

    ikinci = panel.run_command(["/bin/echo", "iki"], "pio build")
    assert ikinci is ilk
    assert panel.stack.count() == sekme_sayisi
    assert bekle(ikinci.is_finished)
    assert "iki" in "".join(ikinci._process.screen.display)


def test_farkli_komut_yeni_sekme_acar(pencere, bekle):
    panel = pencere.terminal_panel
    panel.run_command(["/bin/echo", "bir"], "pio build")
    panel.run_command(["/bin/echo", "iki"], "pio upload")
    assert panel.stack.count() == 2


def test_biten_sekme_yeniden_gorununce_komutu_tekrarlamaz(pencere, bekle):
    """ En tehlikeli regresyon: showEvent'in 'koşmuyorsa başlat' kuralı,
    biten bir komut sekmesinde ':term' ile panel gizlenip açılınca komutu
    yeniden çalıştırır — 'pio upload' için bu gerçek donanıma yazmak demek. """
    view = pencere.terminal_panel.run_command(["/bin/echo", "bir"], "pio upload")
    assert bekle(view.is_finished)

    view.showEvent(QShowEvent())

    assert not view._process.is_running()
    assert view.title() == "pio upload ✓"


def test_shell_sekmesi_hala_kabuk_adini_gosterir(pencere):
    panel = pencere.terminal_panel
    panel.open_panel()
    assert panel.stack.widget(0).command_title is None
    assert panel.tab_bar.tabText(0).endswith(panel.stack.widget(0).shell_name())
