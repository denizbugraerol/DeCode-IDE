import keyword

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

from ui import theme

class CppHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rebuild()

    def rebuild(self):
        """ Kuralları geçerli paletle YERİNDE yeniden kurar (highlighter
        nesnesi atılmaz). ModalEditor.refresh_theme bunu çağırır -- açılışta
        ve ':reload'da, ikisi de artık IDEWindow.apply_settings üzerinden
        aynı yoldan geçiyor; renkler QTextCharFormat içine kopyalandığı için
        palet değişince kendiliğinden güncellenmiyorlar. """
        self.highlighting_rules = []

        # --- 1. Yorum Satırları (Soluk ve İtalik) ---
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(theme.color("fg_dim")))
        comment_format.setFontItalic(True)
        # '//' ile başlayıp satır sonuna kadar giden her şeyi yakalar
        self.highlighting_rules.append((QRegularExpression("//[^\n]*"), comment_format))

        # --- 2. Anahtar Kelimeler (Mor) ---
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(theme.color("purple")))
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
        string_format.setForeground(QColor(theme.color("green")))
        self.highlighting_rules.append((QRegularExpression("\".*\""), string_format))

        # --- 4. Rakamlar (Turuncu) ---
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(theme.color("orange")))
        self.highlighting_rules.append((QRegularExpression("\\b[0-9]+\\b"), number_format))

        self.rehighlight()

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
        self.rebuild()

    def rebuild(self):
        """ Kuralları geçerli paletle YERİNDE yeniden kurar (highlighter
        nesnesi atılmaz). ModalEditor.refresh_theme bunu çağırır -- açılışta
        ve ':reload'da, ikisi de artık IDEWindow.apply_settings üzerinden
        aynı yoldan geçiyor; renkler QTextCharFormat içine kopyalandığı için
        palet değişince kendiliğinden güncellenmiyorlar. """
        self.highlighting_rules = []

        # --- 1. Yorum Satırları (Soluk ve İtalik) ---
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(theme.color("fg_dim")))
        comment_format.setFontItalic(True)
        # '#' ile başlayıp satır sonuna kadar giden her şeyi yakalar
        self.highlighting_rules.append((QRegularExpression("#[^\n]*"), comment_format))

        # --- 2. Anahtar Kelimeler (Mor) ---
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(theme.color("purple")))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        # Elle liste tutmak yerine stdlib'in kendi anahtar kelime listesini kullanıyoruz
        # (True/False/None de Python 3'te birer keyword olduğu için buraya dahil)
        for word in keyword.kwlist:
            self.highlighting_rules.append((QRegularExpression(f"\\b{word}\\b"), keyword_format))

        # --- 3. Built-in Fonksiyon/Tipler (Camgöbeği) ---
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor(theme.color("cyan")))
        for word in self.BUILTINS:
            self.highlighting_rules.append((QRegularExpression(f"\\b{word}\\b"), builtin_format))

        # --- 4. Decorator'lar (Sarı) ---
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor(theme.color("yellow")))
        self.highlighting_rules.append((QRegularExpression(r"@[A-Za-z_][A-Za-z0-9_.]*"), decorator_format))

        # --- 5. Tek Satırlık String İfadeler (Yeşil) ---
        # Tek ve çift tırnağı, kaçış karakterlerini (\" , \') hesaba katarak yakalar
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor(theme.color("green")))
        self.highlighting_rules.append((QRegularExpression(r'"(?:\\.|[^"\\\n])*"'), self.string_format))
        self.highlighting_rules.append((QRegularExpression(r"'(?:\\.|[^'\\\n])*'"), self.string_format))

        # --- 6. Rakamlar (Turuncu) ---
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(theme.color("orange")))
        self.highlighting_rules.append((QRegularExpression(r"\b[0-9]+(\.[0-9]+)?\b"), number_format))

        self.rehighlight()

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
