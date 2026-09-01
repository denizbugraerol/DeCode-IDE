""" Açık dosyadaki tanımları (':sym' paleti için) satır numaralarıyla çıkarır.

Gerçek bir ayrıştırıcı değil, satır bazlı sezgisel bir regex taraması: dil
seçimi CppHighlighter/PythonHighlighter'daki kuralla aynı — '.py' Python,
gerisi C/C++. """
import re

_PYTHON_DEF = re.compile(r"^\s*(?:async\s+)?(def|class)\s+(\w+)")

_CPP_TYPE = re.compile(r"^\s*(class|struct|enum|namespace)\s+(\w+)")
# 'tür ad(...) {' kalıbı. Satır ';' ile bitiyorsa (bildirim ya da çağrı)
# eşleşmez; bu yüzden parantez içi [^;{]* ve satır sonu '{?' ile bağlanıyor.
_CPP_FUNC = re.compile(r"^[A-Za-z_][\w\s\*&:<>,~]*?(\w+)\s*\([^;{]*\)\s*(?:const\s*)?\{?\s*$")

# Fonksiyon gibi görünen kontrol yapıları sembol sayılmamalı.
_CPP_KEYWORDS = frozenset({
    "if", "for", "while", "switch", "catch", "return", "sizeof", "else", "do",
})


def extract_symbols(text, file_path=None):
    """ (tür, ad, satır) üçlülerini kaynaktaki sırayla döndürür. Satır
    numaraları 1 tabanlıdır (editörün goto_line'ıyla aynı sözleşme). """
    is_python = bool(file_path) and file_path.lower().endswith(".py")
    symbols = []

    for number, line in enumerate(text.splitlines(), start=1):
        if is_python:
            match = _PYTHON_DEF.match(line)
            if match:
                symbols.append((match.group(1), match.group(2), number))
            continue

        match = _CPP_TYPE.match(line)
        if match:
            symbols.append((match.group(1), match.group(2), number))
            continue

        match = _CPP_FUNC.match(line)
        if match and match.group(1) not in _CPP_KEYWORDS:
            symbols.append(("func", match.group(1), number))

    return symbols
