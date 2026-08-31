""" Renkler tek yerde dursun: ui/theme.py dışında hex renk kalmamalı.
Bu bir regresyon bekçisi — yeni bir bileşen eklerken rengi gömmek kolay. """
import pathlib
import re

HEX = re.compile(r"#[0-9a-fA-F]{6}")
KOK = pathlib.Path(__file__).resolve().parent.parent

# Paletin kendisi ve şablonu doğal olarak hex içerir.
MUAF = {"ui/theme.py", "core/config.py"}


def test_hex_renkler_yalniz_temada():
    suclular = {}
    # İkisi de recursive taranıyor: core/*.py düz taraması bir alt paket
    # (ör. core/embedded/) eklense hex sızıntısını görmezden gelirdi (kod
    # incelemesi Bulgu 11).
    for yol in list(KOK.glob("ui/**/*.py")) + list(KOK.glob("core/**/*.py")):
        goreli = yol.relative_to(KOK).as_posix()
        if goreli in MUAF:
            continue
        satirlar = [
            f"{goreli}:{no}"
            for no, satir in enumerate(yol.read_text(encoding="utf-8").splitlines(), 1)
            if HEX.search(satir) and not satir.lstrip().startswith("#")
        ]
        if satirlar:
            suclular[goreli] = satirlar

    assert not suclular, f"{sorted(MUAF)} dışında hex renk kaldı: {suclular}"
