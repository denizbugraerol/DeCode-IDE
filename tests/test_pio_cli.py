""" pio çalıştırılabiliri ve argv üretimi. Saf katman: gerçek PlatformIO
kurulu olmasa da geçer. """
from embedded import pio_cli


def test_build_argv():
    assert pio_cli.build_argv("build", "/kurulum/pio") == ["/kurulum/pio", "run"]


def test_upload_argv():
    assert pio_cli.build_argv("upload", "/kurulum/pio") == [
        "/kurulum/pio", "run", "-t", "upload"]


def test_clean_argv():
    assert pio_cli.build_argv("clean", "/kurulum/pio") == [
        "/kurulum/pio", "run", "-t", "clean"]


def test_monitor_argv():
    assert pio_cli.build_argv("monitor", "/kurulum/pio") == [
        "/kurulum/pio", "device", "monitor"]


def test_ortam_verilince_e_bayragi_eklenir():
    assert pio_cli.build_argv("build", "/kurulum/pio", env="esp32dev") == [
        "/kurulum/pio", "run", "-e", "esp32dev"]


def test_ortam_yoksa_e_bayragi_hic_eklenmez():
    """ K5: ortam seçilmediyse kararı platformio.ini'nin default_envs'i verir;
    IDE '-e' ile ini'nin kararını ezmez. """
    for ortam in (None, ""):
        assert "-e" not in pio_cli.build_argv("upload", "/kurulum/pio", env=ortam)


def test_env_alt_komutu_surec_baslatmaz():
    assert pio_cli.build_argv("env", "/kurulum/pio") is None


def test_bilinmeyen_alt_komut_none():
    assert pio_cli.build_argv("derle", "/kurulum/pio") is None


def test_alt_komut_tablosu_tamamlamanin_kaynagi():
    assert set(pio_cli.PROCESS_SUBCOMMANDS) < set(pio_cli.SUBCOMMANDS)
    assert "env" in pio_cli.SUBCOMMANDS
    assert all(aciklama for aciklama in pio_cli.SUBCOMMANDS.values())


def test_find_executable_pathten_bulur(tmp_path, monkeypatch):
    sahte = tmp_path / "pio"
    sahte.write_text("#!/bin/sh\n", encoding="utf-8")
    sahte.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert pio_cli.find_executable() == str(sahte)


def test_find_executable_platformio_adini_da_dener(tmp_path, monkeypatch):
    sahte = tmp_path / "platformio"
    sahte.write_text("#!/bin/sh\n", encoding="utf-8")
    sahte.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert pio_cli.find_executable() == str(sahte)


def test_find_executable_penv_yedegi(tmp_path, monkeypatch):
    """ PlatformIO'nun kendi kurucusu pio'yu PATH'e koymayabiliyor. """
    penv = tmp_path / ".platformio" / "penv" / "bin"
    penv.mkdir(parents=True)
    sahte = penv / "pio"
    sahte.write_text("#!/bin/sh\n", encoding="utf-8")
    sahte.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path / "bos"))
    monkeypatch.setenv("HOME", str(tmp_path))
    assert pio_cli.find_executable() == str(sahte)


def test_find_executable_yoksa_none(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path / "bos"))
    monkeypatch.setenv("HOME", str(tmp_path))
    assert pio_cli.find_executable() is None


# --- ':pio init' (Sprint 11 sonrası) — projeyi OLUŞTURAN alt komut ---

def test_init_argv_kartsiz():
    assert pio_cli.build_argv("init", "/kurulum/pio") == [
        "/kurulum/pio", "project", "init"]


def test_init_argv_kartli():
    assert pio_cli.build_argv("init", "/kurulum/pio", board="esp32dev") == [
        "/kurulum/pio", "project", "init", "--board", "esp32dev"]


def test_inite_ortam_bayragi_eklenmez():
    """ 'pio project init -e esp32dev' anlamsız: seçili bir ortam varken bile
    '-e' eklenmemeli. """
    assert pio_cli.build_argv("init", "/kurulum/pio", env="esp32dev") == [
        "/kurulum/pio", "project", "init"]


def test_kart_yalniz_inite_eklenir():
    """ 'board' ötekilere sızmamalı; 'pio run --board' diye bir şey yok. """
    assert pio_cli.build_argv("build", "/kurulum/pio", board="esp32dev") == [
        "/kurulum/pio", "run"]
