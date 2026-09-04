""" Sürüm tek kaynağı ve '--version' bayrağı.

CI, ürettiği binary'yi 'QT_QPA_PLATFORM=offscreen ./DeCode --version' ile
duman testinden geçirir. Bu yüzden bayrağın iki sözleşmesi var: sürümü tam
olarak beklenen biçimde basmak ve GUI/ev dizini yan etkisi üretmemek. """
import re

import main
from core import config
from core.version import __version__


def test_surum_semver_bicimli():
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)


def test_version_bayragi_surumu_basip_sifir_doner(capsys):
    kod = main.main(["--version"])
    assert kod == 0
    assert capsys.readouterr().out.strip() == f"DeCode IDE {__version__}"


def test_version_bayragi_ayar_dosyasi_yazmaz(monkeypatch, capsys):
    """ ensure_exists ev dizinine yazan TEK yer; --version onu çağırmamalı,
    yoksa CI runner'ında (ve sürümü soran her kullanıcıda) dosya yaratır. """
    cagrildi = []
    monkeypatch.setattr(config, "ensure_exists", lambda *a, **k: cagrildi.append(a))

    main.main(["--version"])

    assert cagrildi == []
    capsys.readouterr()
