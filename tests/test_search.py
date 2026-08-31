""" Metin içi aramanın sözleşmesi: ileri/geri, sarma, harf duyarsızlığı. """
from core.search import find_all, find_next

METIN = "bir foo iki foo uc"
#        0123456789...        ilk 'foo' 4'te, ikinci 'foo' 12'de


def test_ileri_arar():
    assert find_next(METIN, "foo", 0) == 4


def test_imlecten_sonrakini_bulur():
    assert find_next(METIN, "foo", 5) == 12


def test_sona_gelince_basa_sarar():
    assert find_next(METIN, "foo", 13) == 4


def test_geri_arar():
    assert find_next(METIN, "foo", 12, backward=True) == 4


def test_geri_ararken_basa_gelince_sona_sarar():
    assert find_next(METIN, "foo", 0, backward=True) == 12


def test_buyuk_kucuk_harf_duyarsiz():
    assert find_next("Merhaba", "merhaba", 0) == 0
    assert find_next("Merhaba", "merhaba", 0, case_sensitive=True) is None


def test_bulunamazsa_none():
    assert find_next(METIN, "yok", 0) is None


def test_bos_desen_none():
    assert find_next(METIN, "", 0) is None


def test_find_all_tum_konumlari_verir():
    assert find_all(METIN, "foo") == [4, 12]


from core.search import parse_replace_args, replace_all


def test_parse_replace_args_iki_kelime():
    assert parse_replace_args("eski yeni") == ("eski", "yeni")


def test_parse_replace_args_tirnakli_argumani_bozmaz():
    assert parse_replace_args('"iki söz" yeni') == ("iki söz", "yeni")


def test_parse_replace_args_eksik_arguman_none():
    assert parse_replace_args("sadece") is None
    assert parse_replace_args("") is None


def test_parse_replace_args_kapanmamis_tirnak_none():
    assert parse_replace_args('"acik yeni') is None


def test_replace_all_sayiyi_dondurur():
    assert replace_all("foo bar foo", "foo", "baz") == ("baz bar baz", 2)


def test_replace_all_bos_eski_dokunmaz():
    assert replace_all("foo", "", "x") == ("foo", 0)
