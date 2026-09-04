""" Sürümün tek kaynağı. Saf Python, Qt yok — 'main.py --version' bunu
QApplication kurulmadan basabilsin diye (CI duman testi bu yoldan geçiyor).

Buradaki değer git tag'iyle aynı olmalı: tag 'v0.1.0' ise burası '0.1.0'.
release.yml ikisini karşılaştırır ve uyuşmazsa release'i kırar. """

__version__ = "0.1.0"
