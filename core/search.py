""" Dosya içi arama ve değiştirmenin saf (Qt'siz) çekirdeği. Editör tarafı
sadece burayı çağırıp imleci taşır — böylece sarma/sınır davranışı doğrudan
test edilebiliyor. """
import shlex


def _prepare(text, pattern, case_sensitive):
    if case_sensitive:
        return text, pattern
    return text.lower(), pattern.lower()


def find_next(text, pattern, start, backward=False, case_sensitive=False):
    """ 'pattern'ı 'start' konumundan itibaren arar ve eşleşmenin başlangıç
    indeksini döndürür. Dosya sonuna gelince başa (geri aramada sona) sarar.
    Desen boşsa ya da hiç geçmiyorsa None. """
    if not pattern:
        return None

    haystack, needle = _prepare(text, pattern, case_sensitive)

    if backward:
        index = haystack.rfind(needle, 0, max(0, start))
        if index == -1:
            index = haystack.rfind(needle)      # başa sarma: sondan devam et
    else:
        index = haystack.find(needle, max(0, start))
        if index == -1:
            index = haystack.find(needle)       # sona sarma: baştan devam et

    return index if index != -1 else None


def find_all(text, pattern, case_sensitive=False):
    """ Tüm eşleşmelerin başlangıç indeksleri — hepsini vurgulamak için. """
    if not pattern:
        return []

    haystack, needle = _prepare(text, pattern, case_sensitive)

    positions = []
    index = haystack.find(needle)
    while index != -1:
        positions.append(index)
        index = haystack.find(needle, index + len(needle))
    return positions
