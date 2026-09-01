""" Dosya taramasının neyi dahil edip neyi atladığı. """
from core.file_index import scan_files


def _hazirla(root):
    """ Küçük bir örnek ağaç kurar: iki gerçek dosya, bir gizli dosya, bir
    gizli dizin, bir de __pycache__. """
    (root / "main.py").write_text("x")
    (root / "ui").mkdir()
    (root / "ui" / "main_window.py").write_text("x")
    (root / ".env").write_text("gizli")
    (root / ".git").mkdir()
    (root / ".git" / "config").write_text("x")
    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "main.pyc").write_text("x")


def test_gercek_dosyalari_goreli_yolla_dondurur(tmp_path):
    _hazirla(tmp_path)
    sonuc = scan_files(str(tmp_path))
    assert "main.py" in sonuc
    assert "ui/main_window.py" in sonuc


def test_gurultulu_dizinleri_ve_gizli_dosyalari_atlar(tmp_path):
    _hazirla(tmp_path)
    sonuc = scan_files(str(tmp_path))
    assert not any(yol.startswith(".git") for yol in sonuc)
    assert not any("__pycache__" in yol for yol in sonuc)
    assert ".env" not in sonuc


def test_max_files_sinirinda_durur(tmp_path):
    for i in range(20):
        (tmp_path / f"f{i:02d}.txt").write_text("x")
    assert len(scan_files(str(tmp_path), max_files=5)) == 5


def test_okunamayan_kok_bos_liste_dondurur(tmp_path):
    assert scan_files(str(tmp_path / "yok")) == []
