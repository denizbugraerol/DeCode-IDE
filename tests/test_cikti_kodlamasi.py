""" Türkçe mesajların çıktıya yazılabilmesi.

Windows'ta sys.stdout bir BORUYA ya da dosyaya gittiğinde Python locale
kodlamasını kullanıyor (GitHub runner'ında cp1252, Türkçe bir Windows'ta
cp1254) ve 'ı' ile 'ş' o kod sayfalarının birinde ya da ötekinde yok. Bu
uygulama baştan sona Türkçe mesaj bastığı için ilk açılıştaki "Ayar dosyası
oluşturuldu: ..." satırı `DeCode.exe > log.txt` çağrısını çökertiyordu.

Testler mekanizmayı GERÇEK bir cp1252 akışı kurarak her platformda üretiyor;
Windows gerektirmiyorlar. Bu bilinçli: hata yalnız Windows'ta görünüyor ama
sebebi taşınabilir (kodlama seçimi), o yüzden bekçisi de taşınabilir olmalı. """
import io

import main

# Uygulamanın gerçekten bastığı mesajlar. Kaynakları:
#   main.py                       -> "Ayar dosyası oluşturuldu: ..."
#   ui/main_window.py             -> "'pio' bulunamadı; ..."
#   ui/theme.resolve_font_family  -> "Sabit genişlikli ... bulunamadı"
GERCEK_MESAJLAR = (
    "Ayar dosyası oluşturuldu: C:/x/config.toml",
    "'pio' bulunamadı; PlatformIO kurulu mu?",
    "Sabit genişlikli 'Fira Code' fontu bulunamadı",
)


def _cp1252_akis():
    """ Windows'ta yönlendirilmiş bir stdout'un birebir karşılığı. """
    return io.TextIOWrapper(io.BytesIO(), encoding="cp1252", newline="")


def test_cp1252_akis_turkce_mesajlari_gercekten_reddediyor():
    """ Önce hatanın var olduğunu göster: bu test geçmezse geri kalanı
    boşluğa karşı koruma yapıyor demektir. """
    akis = _cp1252_akis()
    for mesaj in GERCEK_MESAJLAR:
        try:
            akis.write(mesaj)
            akis.flush()
        except UnicodeEncodeError:
            continue
        raise AssertionError(
            f"cp1252 bu mesajı kabul etti, oysa etmemeliydi: {mesaj!r}")


def test_utf8_zorlandiktan_sonra_turkce_mesajlar_yazilabiliyor():
    akis = _cp1252_akis()
    assert main.utf8_cikti_zorla(akis) is True
    assert akis.encoding.lower().replace("-", "") == "utf8"

    for mesaj in GERCEK_MESAJLAR:
        akis.write(mesaj + "\n")
    akis.flush()

    yazilan = akis.buffer.getvalue().decode("utf-8")
    for mesaj in GERCEK_MESAJLAR:
        assert mesaj in yazilan


def test_reconfigure_olmayan_akis_sessizce_atlaniyor():
    """ pytest'in yakalama nesnesi gibi sarmalayıcılarda reconfigure yok.
    Uygulama bu yüzden açılmamamalı. """
    class Sarmalayici:
        def write(self, _veri):
            return 0

    assert main.utf8_cikti_zorla(Sarmalayici()) is False


def test_kapatilmis_akis_cokertmiyor():
    """ Kapatılmış bir akışta reconfigure ValueError fırlatıyor; yakalanmalı
    çünkü bu yol uygulamanın ilk satırlarında koşuyor. """
    akis = _cp1252_akis()
    akis.close()
    assert main.utf8_cikti_zorla(akis) is False


def test_satir_sonu_cevirisine_dokunulmuyor():
    """ newline= verilmiyor: Windows'ta '\\n' -> '\\r\\n' çevirisi sürüyor ve
    release duman testi bu yüzden hâlâ 'tr -d' ile '\\r' temizliyor. İkisi
    bilinçli olarak ayrı tutuluyor; burada değiştirilirse o temizlik
    gereksizleşir ve biri onu silmeye kalkar. """
    akis = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", newline="\r\n")
    assert main.utf8_cikti_zorla(akis) is True
    akis.write("bir\n")
    akis.flush()
    assert akis.buffer.getvalue() == b"bir\r\n"
