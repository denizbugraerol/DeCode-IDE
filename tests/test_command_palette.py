""" Paletin klavye sözleşmesi: yaz-filtrele, gez, seç, iptal et. """
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from ui.components.command_palette import CommandPalette

OGELER = [
    ("main.py", "main.py"),
    ("ui/main_window.py", "ui/main_window.py"),
    ("core/state_machine.py", "core/state_machine.py"),
]


def _palet(qapp):
    palet = CommandPalette()
    palet.open_with("Dosya ara", OGELER, mode="file")
    return palet


def test_yazinca_bulanik_filtreler(qapp):
    palet = _palet(qapp)
    QTest.keyClicks(palet, "mwpy")
    assert palet.current_payload() == "ui/main_window.py"


def test_asagi_yukari_secimi_gezdirir(qapp):
    palet = _palet(qapp)
    ilk = palet.current_payload()
    QTest.keyClick(palet, Qt.Key.Key_Down)
    assert palet.current_payload() != ilk
    QTest.keyClick(palet, Qt.Key.Key_Up)
    assert palet.current_payload() == ilk


def test_enter_accepted_yayinlar(qapp):
    palet = _palet(qapp)
    secilenler = []
    palet.accepted.connect(secilenler.append)

    QTest.keyClicks(palet, "state")
    QTest.keyClick(palet, Qt.Key.Key_Return)

    assert secilenler == ["core/state_machine.py"]


def test_escape_cancelled_yayinlar(qapp):
    palet = _palet(qapp)
    iptaller = []
    palet.cancelled.connect(lambda: iptaller.append(True))

    QTest.keyClick(palet, Qt.Key.Key_Escape)
    assert iptaller == [True]


def test_backspace_sorguyu_kisaltir(qapp):
    palet = _palet(qapp)
    QTest.keyClicks(palet, "mwpy")
    QTest.keyClick(palet, Qt.Key.Key_Backspace)
    assert palet.query == "mwp"


def test_eslesme_yoksa_payload_none(qapp):
    palet = _palet(qapp)
    QTest.keyClicks(palet, "zzzz")
    assert palet.current_payload() is None
