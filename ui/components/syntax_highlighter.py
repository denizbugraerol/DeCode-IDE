import keyword

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

class CppHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # --- 1. Yorum Satırları (Soluk ve İtalik) ---
        # Tokyo Night'ın soluk gri-mavi yorum rengi: #565f89
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#565f89"))
        comment_format.setFontItalic(True)
        # '//' ile başlayıp satır sonuna kadar giden her şeyi yakalar
        self.highlighting_rules.append((QRegularExpression("//[^\n]*"), comment_format))

        # --- 2. Anahtar Kelimeler (Mor) ---
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#bb9af7")) # Tokyo Night Moru
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        keywords = [
            "\\bint\\b", "\\bchar\\b", "\\bvoid\\b", "\\bif\\b", "\\belse\\b",
            "\\bwhile\\b", "\\bfor\\b", "\\breturn\\b", "\\bstruct\\b", "\\binclude\\b"
        ]
        for word in keywords:
            pattern = QRegularExpression(word)
            self.highlighting_rules.append((pattern, keyword_format))

        # --- 3. String İfadeler (Yeşil) ---
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#9ece6a")) # Tokyo Night Yeşili
        self.highlighting_rules.append((QRegularExpression("\".*\""), string_format))

        # --- 4. Rakamlar (Turuncu) ---
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#ff9e64")) # Tokyo Night Turuncusu
        self.highlighting_rules.append((QRegularExpression("\\b[0-9]+\\b"), number_format))

    def highlightBlock(self, text):
        """
        Bu fonksiyon, editördeki metin değiştikçe PyQt tarafından otomatik çağrılır.
        Yazdığımız kuralları (Regex) metin üzerinde tarar ve boyar.
        """
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class PythonHighlighter(QSyntaxHighlighter):
    """ Python (.py) dosyaları için regex tabanlı syntax highlighter. CppHighlighter
    ile aynı desende çalışır (kural listesi + highlightBlock döngüsü); ek olarak
    üç tırnaklı (docstring) string'lerin birden çok satıra yayılabilmesi için
    blok durumu (block state) takip eder. """

    # Üç tırnaklı string'lerin satırlar arası takibi için blok durumu kodları
    _TRIPLE_DOUBLE = 1
    _TRIPLE_SINGLE = 2

    BUILTINS = [
        "self", "cls", "print", "len", "range", "str", "int", "float", "bool",
        "list", "dict", "set", "tuple", "object", "super", "isinstance",
        "type", "open", "enumerate", "zip", "map", "filter", "input",
        "sorted", "sum", "min", "max", "abs", "round",
    ]

    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # --- 1. Yorum Satırları (Soluk ve İtalik) ---
        # Tokyo Night'ın soluk gri-mavi yorum rengi: #565f89
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#565f89"))
        comment_format.setFontItalic(True)
        # '#' ile başlayıp satır sonuna kadar giden her şeyi yakalar
        self.highlighting_rules.append((QRegularExpression("#[^\n]*"), comment_format))

        # --- 2. Anahtar Kelimeler (Mor) ---
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#bb9af7")) # Tokyo Night Moru
        keyword_format.setFontWeight(QFont.Weight.Bold)
        # Elle liste tutmak yerine stdlib'in kendi anahtar kelime listesini kullanıyoruz
        # (True/False/None de Python 3'te birer keyword olduğu için buraya dahil)
        for word in keyword.kwlist:
            self.highlighting_rules.append((QRegularExpression(f"\\b{word}\\b"), keyword_format))

        # --- 3. Built-in Fonksiyon/Tipler (Camgöbeği) ---
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#7dcfff")) # Tokyo Night Camgöbeği
        for word in self.BUILTINS:
            self.highlighting_rules.append((QRegularExpression(f"\\b{word}\\b"), builtin_format))

        # --- 4. Decorator'lar (Sarı) ---
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor("#e0af68")) # Tokyo Night Sarısı
        self.highlighting_rules.append((QRegularExpression(r"@[A-Za-z_][A-Za-z0-9_.]*"), decorator_format))

        # --- 5. Tek Satırlık String İfadeler (Yeşil) ---
        # Tek ve çift tırnağı, kaçış karakterlerini (\" , \') hesaba katarak yakalar
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#9ece6a")) # Tokyo Night Yeşili
        self.highlighting_rules.append((QRegularExpression(r'"(?:\\.|[^"\\\n])*"'), self.string_format))
        self.highlighting_rules.append((QRegularExpression(r"'(?:\\.|[^'\\\n])*'"), self.string_format))

        # --- 6. Rakamlar (Turuncu) ---
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#ff9e64")) # Tokyo Night Turuncusu
        self.highlighting_rules.append((QRegularExpression(r"\b[0-9]+(\.[0-9]+)?\b"), number_format))

    def highlightBlock(self, text):
        """
        Önce tek satırlık kuralları (yorum/keyword/builtin/decorator/string/sayı)
        tarar, ardından üç tırnaklı string'ler için satırlar arası takip yapar.
        """
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

        self._highlight_triple_quoted_strings(text)

    def _highlight_triple_quoted_strings(self, text):
        """ ''' veya \"\"\" ile açılan string'leri (docstring'ler dahil), birden
        çok satıra yayılabilecek şekilde boyar. Her blok, bir önceki bloğun
        'içinde miyiz' durumunu (previousBlockState) okuyup kendi durumunu
        (setCurrentBlockState) bir sonrakine devrederek satırlar arası takibi
        sağlar — Qt'nin resmi çok-satırlı yorum örneğindeki teknikle aynı. """
        delimiters = {self._TRIPLE_DOUBLE: '"""', self._TRIPLE_SINGLE: "'''"}
        state = self.previousBlockState()
        if state not in delimiters:
            state = 0

        pos = 0
        while True:
            if state == 0:
                idx_double = text.find('"""', pos)
                idx_single = text.find("'''", pos)
                if idx_double == -1 and idx_single == -1:
                    self.setCurrentBlockState(0)
                    return
                if idx_single == -1 or (idx_double != -1 and idx_double < idx_single):
                    start, state = idx_double, self._TRIPLE_DOUBLE
                else:
                    start, state = idx_single, self._TRIPLE_SINGLE
            else:
                start = 0

            delimiter = delimiters[state]
            end = text.find(delimiter, start + 3)
            if end == -1:
                # Bu satırda kapanmıyor: satır sonuna kadar boya, durumu bir sonraki bloğa devret
                self.setFormat(start, len(text) - start, self.string_format)
                self.setCurrentBlockState(state)
                return

            self.setFormat(start, end + 3 - start, self.string_format)
            pos = end + 3
            state = 0