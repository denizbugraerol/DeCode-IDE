""" platformio.ini ayrıştırma ve proje kökü bulma. Saf katman: Qt yok,
PlatformIO kurulu olması gerekmiyor. """
from embedded import pio_project

BASIT_INI = """\
[platformio]
default_envs = esp32dev

[env:esp32dev]
platform = espressif32
board = esp32dev

[env:nanoatmega328]
platform = atmelavr
"""


def test_ortamlari_dosyadaki_sirayla_verir():
    bilgi, uyarilar = pio_project.parse_environments(BASIT_INI)
    assert bilgi["environments"] == ["esp32dev", "nanoatmega328"]
    assert uyarilar == []


def test_default_envs_okunur():
    bilgi, _ = pio_project.parse_environments(BASIT_INI)
    assert bilgi["default_envs"] == ["esp32dev"]


def test_default_envs_virgulle_ayrilir():
    bilgi, _ = pio_project.parse_environments(
        "[platformio]\ndefault_envs = bir, iki\n\n[env:bir]\n[env:iki]\n")
    assert bilgi["default_envs"] == ["bir", "iki"]


def test_default_envs_cok_satirli_olabilir():
    bilgi, _ = pio_project.parse_environments(
        "[platformio]\ndefault_envs =\n    bir\n    iki\n\n[env:bir]\n[env:iki]\n")
    assert bilgi["default_envs"] == ["bir", "iki"]


def test_platformio_bolumu_yoksa_default_envs_bos():
    bilgi, uyarilar = pio_project.parse_environments("[env:native]\nplatform = native\n")
    assert bilgi["default_envs"] == []
    assert bilgi["environments"] == ["native"]
    assert uyarilar == []


def test_yuzde_iceren_deger_cokertmez():
    """ interpolation=None regresyonu. ConfigParser interpolasyonu
    read_string'de değil get() çağrısında çalışır: okuduğumuz TEK değer
    default_envs olduğu için testin '%'yi oraya koyması şart — varsayılan
    parser bu değeri get() ederken InterpolationSyntaxError fırlatır.
    '${sysenv.HOME}' de PlatformIO ini'lerinde olağan; ham hâliyle geçmeli. """
    ini = (
        "[platformio]\n"
        "default_envs = yuzde%_env\n"
        "\n"
        "[env:yuzde%_env]\n"
        "build_flags = -I ${PROJECT_DIR}/inc\n"
    )
    bilgi, uyarilar = pio_project.parse_environments(ini)
    assert bilgi["environments"] == ["yuzde%_env"]
    assert bilgi["default_envs"] == ["yuzde%_env"]
    assert uyarilar == []


def test_tekrarlanan_anahtar_cokertmez():
    """ strict=False regresyonu: kopyala-yapıştır ini'lerde aynı anahtar iki
    kez yazılabiliyor; DuplicateOptionError ortam listesini komple yutmamalı. """
    bilgi, uyarilar = pio_project.parse_environments(
        "[env:bir]\nboard = a\nboard = b\n")
    assert bilgi["environments"] == ["bir"]
    assert uyarilar == []


def test_bozuk_ini_uyari_dondurur():
    bilgi, uyarilar = pio_project.parse_environments("bolumsuz = deger\n")
    assert bilgi == {"environments": [], "default_envs": []}
    assert len(uyarilar) == 1


def test_kok_alt_dizinden_yukari_bulunur(tmp_path):
    (tmp_path / "platformio.ini").write_text(BASIT_INI, encoding="utf-8")
    alt = tmp_path / "src" / "derin"
    alt.mkdir(parents=True)
    assert pio_project.find_project_root(str(alt)) == str(tmp_path)


def test_kok_yoksa_none(tmp_path):
    assert pio_project.find_project_root(str(tmp_path)) is None


def test_read_project_dosyayi_okur(tmp_path):
    (tmp_path / "platformio.ini").write_text(BASIT_INI, encoding="utf-8")
    bilgi, uyarilar = pio_project.read_project(str(tmp_path))
    assert bilgi["environments"] == ["esp32dev", "nanoatmega328"]
    assert uyarilar == []


def test_read_project_dosya_yoksa_uyari(tmp_path):
    bilgi, uyarilar = pio_project.read_project(str(tmp_path))
    assert bilgi["environments"] == []
    assert len(uyarilar) == 1
