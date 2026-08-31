""" Sembol çıkarma sezgiselinin sınırları: neyi yakalar, neyi yakalamaz. """
from core.symbols import extract_symbols

PYTHON_KAYNAK = '''\
import os


class IDEWindow:
    def __init__(self):
        pass

    async def yukle(self):
        pass


def yardimci(x):
    return x
'''

CPP_KAYNAK = '''\
#include <Arduino.h>

class Motor {
};

void setup() {
    if (x) {
        digitalWrite(1);
    }
}

int loop(int a) {
}
'''


def test_python_def_ve_class_bulunur():
    semboller = extract_symbols(PYTHON_KAYNAK, "ui/main_window.py")
    adlar = [ad for _tur, ad, _satir in semboller]
    assert adlar == ["IDEWindow", "__init__", "yukle", "yardimci"]


def test_satir_numaralari_bir_tabanli():
    semboller = extract_symbols(PYTHON_KAYNAK, "x.py")
    assert semboller[0] == ("class", "IDEWindow", 4)


def test_cpp_fonksiyon_ve_tip_bulunur():
    adlar = [ad for _t, ad, _s in extract_symbols(CPP_KAYNAK, "src/main.cpp")]
    assert "Motor" in adlar
    assert "setup" in adlar
    assert "loop" in adlar


def test_cpp_kontrol_yapilari_ve_cagrilar_sembol_sayilmaz():
    adlar = [ad for _t, ad, _s in extract_symbols(CPP_KAYNAK, "src/main.cpp")]
    assert "if" not in adlar
    assert "digitalWrite" not in adlar


def test_bos_metin_bos_liste():
    assert extract_symbols("", "x.py") == []
