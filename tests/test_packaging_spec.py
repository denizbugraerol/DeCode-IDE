""" packaging/decode.spec'in ad üretimi.

Spec dosyası PyInstaller tarafından enjekte edilen SPECPATH'e dayandığı için
doğrudan import edilemiyor; normalleştirme tablosu buradan sınanıyor. Tablo
spec'te de aynen duruyor ve bu test ikisinin ayrışmasını yakalıyor. """
import re

SPEC = "packaging/decode.spec"


def _tablo():
    """ Spec'teki _ARCH_ADLARI sözlüğünü metinden okur. """
    metin = open(SPEC, encoding="utf-8").read()
    govde = re.search(r"_ARCH_ADLARI\s*=\s*\{(.*?)\}", metin, re.S).group(1)
    return dict(re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', govde))


def test_windows_amd64_x86_64_olur():
    """ platform.machine() Windows'ta 'AMD64' döner. Normalleştirilmezse
    çıktı 'DeCode-v0.3.0-windows-AMD64' olur ve release.yml'deki ad
    kontrolü release'i kırar. """
    assert _tablo()["amd64"] == "x86_64"


def test_mevcut_platform_adlari_degismedi():
    """ Linux ve macOS çıktı adları bugünküyle aynı kalmalı; yoksa
    yayınlanmış sürümlerle tutarsız adlar üretiriz. """
    tablo = _tablo()
    assert tablo["x86_64"] == "x86_64"
    assert tablo["arm64"] == "arm64"
    assert tablo["aarch64"] == "arm64"
