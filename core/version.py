""" Sürümün tek kaynağı. Saf Python, Qt yok — 'main.py --version' bunu
QApplication kurulmadan basabilsin diye (CI duman testi bu yoldan geçiyor).

Buradaki değer git tag'iyle aynı olmalı: tag 'vX.Y.Z' ise burası 'X.Y.Z'.
release.yml ikisini karşılaştırır ve uyuşmazsa release'i kırar. """

__version__ = "0.2.0"
