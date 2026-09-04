""" ':pio ...' akışı uçtan uca: proje kökü, argv, ortam seçimi ve statusline
rozeti. Gerçek 'pio' süreci başlatılmaz — run_command yakalanır. """
import os

import pytest

from embedded import pio_cli

INI = """\
[platformio]
default_envs = esp32dev

[env:esp32dev]
platform = espressif32

[env:native]
platform = native
"""


@pytest.fixture
def proje(tmp_path, monkeypatch):
    """ Geçici bir PlatformIO projesi ve içine geçmiş bir çalışma dizini.
    'pencere' fixture'ından ÖNCE istenmeli: IDEWindow açılışta rozeti
    kuruyor. """
    (tmp_path / "platformio.ini").write_text(INI, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def kayit(pencere, monkeypatch):
    """ Terminal panelinin run_command'ını yakalar. """
    cagrilar = []
    monkeypatch.setattr(
        pencere.terminal_panel, "run_command",
        lambda argv, title, cwd=None: cagrilar.append((argv, title, cwd)))
    return cagrilar


@pytest.fixture
def sahte_pio(monkeypatch):
    monkeypatch.setattr(pio_cli, "find_executable", lambda: "/kurulum/pio")


def test_proje_yoksa_sekme_acilmaz(tmp_path, monkeypatch, pencere, kayit, sahte_pio):
    monkeypatch.chdir(tmp_path)          # platformio.ini yok
    pencere._on_pio_requested("build")
    assert kayit == []


def test_build_argv_ve_calisma_dizini(proje, pencere, kayit, sahte_pio):
    pencere._on_pio_requested("build")
    argv, baslik, cwd = kayit[0]
    assert argv == ["/kurulum/pio", "run"]
    assert baslik == "pio build"
    assert os.path.realpath(cwd) == os.path.realpath(str(proje))


def test_pio_kurulu_degilse_sekme_acilmaz(proje, pencere, kayit, monkeypatch):
    monkeypatch.setattr(pio_cli, "find_executable", lambda: None)
    pencere._on_pio_requested("upload")
    assert kayit == []


def test_secili_ortam_argva_gecer(proje, pencere, kayit, sahte_pio):
    pencere.pio_env = "native"
    pencere._on_pio_requested("upload")
    argv, _baslik, _cwd = kayit[0]
    assert argv == ["/kurulum/pio", "run", "-t", "upload", "-e", "native"]


def test_editorden_gelen_sinyal_pencereye_ulasir(proje, pencere, kayit, sahte_pio):
    """ ModalEditor -> EditorTabs._relay -> IDEWindow boru hattı. """
    pencere.editor.pio_requested.emit("clean")
    argv, baslik, _cwd = kayit[0]
    assert argv == ["/kurulum/pio", "run", "-t", "clean"]
    assert baslik == "pio clean"


def test_env_paleti_ortamlari_listeler_ve_secimi_uygular(proje, pencere, kayit, sahte_pio):
    pencere._on_pio_requested("env")
    assert pencere.command_palette.mode == "env"
    assert kayit == []                      # 'env' süreç başlatmaz

    pencere._on_palette_accepted("native")
    assert pencere.pio_env == "native"
    assert pencere.status_line.env_label.text() == "native"


def test_rozet_secim_yokken_ini_varsayilanini_parantezle_gosterir(proje, pencere):
    assert pencere.status_line.env_label.text() == "(esp32dev)"


def test_rozet_proje_yokken_bos(pencere):
    """ Depo kökünde platformio.ini yok. """
    assert pencere.status_line.env_label.text() == ""


def test_cd_secili_ortami_sifirlar(proje, pencere, tmp_path):
    pencere.pio_env = "native"
    baska = tmp_path / "alt"
    baska.mkdir()
    pencere._change_directory(str(baska))
    assert pencere.pio_env is None


# --- ':pio init' — ters ön koşul ---

def test_init_proje_yokken_de_sekme_acar(tmp_path, monkeypatch, pencere, kayit, sahte_pio):
    """ 'init' ötekilerin TERSİ: platformio.ini YOKKEN çalışmalı, çünkü onu
    oluşturan komut o. Diğer alt komutlar aynı durumda sekme açmıyor
    (bkz. test_proje_yoksa_sekme_acilmaz) -- asıl regresyon riski burada. """
    monkeypatch.chdir(tmp_path)
    pencere._on_pio_requested("init")
    argv, baslik, cwd = kayit[0]
    assert argv == ["/kurulum/pio", "project", "init"]
    assert baslik == "pio init"
    assert os.path.realpath(cwd) == os.path.realpath(str(tmp_path))


def test_init_kart_argumani_argva_gecer(tmp_path, monkeypatch, pencere, kayit, sahte_pio):
    monkeypatch.chdir(tmp_path)
    pencere._on_pio_requested("init esp32dev")
    argv, baslik, _cwd = kayit[0]
    assert argv == ["/kurulum/pio", "project", "init", "--board", "esp32dev"]
    assert baslik == "pio init"


def test_init_secili_ortami_sifirlar(proje, pencere, kayit, sahte_pio):
    """ init'ten sonra platformio.ini'deki ortam listesi değişebilir; rozet
    olmayan bir ortamı göstermeye devam etmesin (':cd' ile aynı gerekçe). """
    pencere.pio_env = "esp32dev"
    pencere._on_pio_requested("init")
    assert pencere.pio_env is None


def test_init_argumani_editor_sinyalinden_gecer(proje, pencere, kayit, sahte_pio):
    """ ModalEditor -> EditorTabs._relay -> IDEWindow boru hattı, argümanlı. """
    pencere.editor.pio_requested.emit("init nanoatmega328")
    argv, _baslik, _cwd = kayit[0]
    assert argv == ["/kurulum/pio", "project", "init", "--board", "nanoatmega328"]
