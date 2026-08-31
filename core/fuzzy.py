""" Telescope paletinin bulanık (fuzzy) eşleştirmesi. Harici bağımlılık
kullanmıyoruz: sorgunun harfleri adayda sırayla geçiyorsa eşleşme sayılır,
puanı da 'ne kadar iyi geçtiği' belirler. """

# Yol ve isim sınırları: bunlardan hemen sonra gelen harf 'segment başı' sayılır.
SEPARATORS = "/\\_-. "

MATCH_SCORE = 1          # eşleşen her harf
CONSECUTIVE_BONUS = 5    # bir öncekiyle bitişik eşleşme ('window' içinde 'wi')
SEGMENT_START_BONUS = 8  # '/', '_', '.' sonrası ya da metnin başı


def score(query, text):
    """ 'query' harflerinin 'text' içinde (bitişik olmak zorunda olmadan)
    sırayla geçip geçmediğine bakar. Geçmiyorsa None döndürür; geçiyorsa
    puanı döndürür — ardışık harfler ve segment başları ödüllendirilir.

    Eşleştirme açgözlüdür: her harf için soldan ilk uygun konum seçilir. En
    iyi olası hizalamayı aramaz (o dinamik programlama ister); dosya yolları
    için pratikte yeterli sonuç veriyor. """
    if not query:
        return 0

    lowered_query = query.lower()
    lowered_text = text.lower()

    total = 0
    search_from = 0
    previous_index = -2  # ardışıklık kontrolü: -2, 'komşu değil' demek

    for character in lowered_query:
        index = lowered_text.find(character, search_from)
        if index == -1:
            return None

        total += MATCH_SCORE
        if index == previous_index + 1:
            total += CONSECUTIVE_BONUS
        if index == 0 or lowered_text[index - 1] in SEPARATORS:
            total += SEGMENT_START_BONUS

        previous_index = index
        search_from = index + 1

    return total


def rank(query, candidates, limit=None):
    """ Eşleşen adayları puana göre sıralar. Eşit puanda kısa olan, o da
    eşitse alfabetik olarak önce gelen kazanır (sıralama kararlı olsun diye). """
    scored = []
    for candidate in candidates:
        value = score(query, candidate)
        if value is not None:
            scored.append((value, candidate))

    scored.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    ordered = [candidate for _value, candidate in scored]
    return ordered[:limit] if limit is not None else ordered
