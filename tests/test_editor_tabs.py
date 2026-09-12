""" IDEWindow._open_path'in yol kanonikleştirmesi (bkz. ui/main_window.py).

Sidebar, telescope paleti (':ts') ve ':openfile' aynı dosyayı Windows'ta üç
farklı dize ile _open_path'e verebiliyor (bkz. modüldeki yorum). Linux'ta bu
farkı normpath'siz eşdeğer İKİ göreli yol biçimiyle üretiyoruz: './x.py' ile
'x.py' aynı dosyayı gösterir ama normpath olmadan birebir dize karşılaştırması
(EditorTabs.open_file) onları farklı sanır. """


def test_esdeger_yol_bicimleriyle_acmak_tek_sekme_uretir(pencere, tmp_path, monkeypatch):
    (tmp_path / "dosya.py").write_text("icerik")
    monkeypatch.chdir(tmp_path)

    onceki_sekme = pencere.editor_tabs.count()

    # İlk çağrı: pencere açılışındaki boş/adsız sekmeyi doldurur (sekme
    # sayısı değişmez). İkinci çağrı, normpath doğru çalışıyorsa AYNI
    # sekmeye geçer -- yeni bir sekme AÇMAMALI.
    pencere._open_path("./dosya.py")
    pencere._open_path("dosya.py")

    assert pencere.editor_tabs.count() == onceki_sekme
    # Ve sekmedeki yol da kanonik biçimde saklanmış olmalı.
    assert pencere.editor.file_path == "dosya.py"
