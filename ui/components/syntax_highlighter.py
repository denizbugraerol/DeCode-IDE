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