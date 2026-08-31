""" Bulanık skorlayıcının davranış sözleşmesi. Qt gerektirmez. """
from core.fuzzy import rank, score


def test_bos_sorgu_her_seyle_eslesir():
    assert score("", "ui/main_window.py") == 0


def test_alt_dizi_eslesir_sirasiz_eslesmez():
    assert score("abc", "axbxc") is not None
    assert score("cba", "abc") is None


def test_buyuk_kucuk_harf_onemsiz():
    assert score("MW", "main_window") == score("mw", "main_window")


def test_ardisik_harfler_daha_yuksek_puan_alir():
    assert score("ab", "ab") > score("ab", "axxxb")


def test_segment_basi_odullendirilir():
    # 'w' alt çizgiden sonra geliyor: bu bir segment başı.
    assert score("mw", "main_window") > score("mw", "mainwindow")


def test_rank_en_iyi_eslesmeyi_basa_koyar():
    adaylar = [
        "ui/components/command_palette.py",
        "ui/main_window.py",
        "core/state_machine.py",
    ]
    assert rank("mwpy", adaylar) == ["ui/main_window.py"]


def test_rank_esitlikte_kisa_olani_tercih_eder():
    assert rank("mp", ["mp.py", "map_parser.py"])[0] == "mp.py"


def test_rank_limit_uygular():
    assert len(rank("a", ["a1", "a2", "a3"], limit=2)) == 2
