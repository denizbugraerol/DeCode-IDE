# Sprint 07 — Dosya içi arama, değiştirme ve sembol atlama
**Tarih:** 31 Ağu 2026 · **Durum:** Tamamlandı · **Commit(ler):** `81d3c7f` `:find` + `n`/`N`, `b597c18` `:replace`, `f664996` `:openfile`, `4d9c159` `:sym`

## Hedef
Faz 2'yi kapatmak: dosya içinde arama/değiştirme, `:openfile` ile dosya açma ve sembol paleti.

## Çıktılar
- [x] `core/search.py`: sarma destekli ileri/geri arama (`find_next`), tüm eşleşmeler (`find_all`), değiştirme (`replace_all`) ve argüman ayrıştırma (`parse_replace_args`) — hepsi Qt'siz, doğrudan test edilebilir
- [x] `:find <desen>` + çıplak `n` / `N`; tüm eşleşmeler `#3d59a1` ile vurgulanıyor, NORMAL modda Escape vurguyu temizliyor (`:nohlsearch` karşılığı). Argümansız `:find` son deseni tekrarlıyor
- [x] `:replace eski yeni` — `shlex` ile tırnaklı argüman, tek geri-al adımı
- [x] `:openfile <yol>` + `:cd`/`:openfile` ortak yol tamamlaması (`_path_matches_for` artık komut adını ve `include_files` bayrağını alıyor)
- [x] `core/symbols.py` + `:sym` sembol paleti — telescope kutusu sembol kaynağıyla yeniden kullanıldı
- [x] `ModalEditor.goto_line` çıkarıldı: `:42` ve `:sym` aynı yeri kullanıyor
- [x] 60 test — `tests/`

## Teknik notlar
- `handle_normal_key` artık `event.text().lower()` kullanmıyor: `n` ile `N` farklı komut olduğu için harf durumu korunmalı. **Yan etki:** Shift+i artık INSERT'e sokmuyor (Vim'de de `I` ayrı bir komut).
- Escape'in `event.text()` değeri boş değil (`\x1b`). Tuş dağıtımında "yazılabilir tuş" dalından **önce** ele alınmazsa `clear_search` hiç çalışmıyor — bu tam olarak ilk denemede olan hataydı; `tests/test_editor_search.py` regresyon testiyle sabitlendi.
- `:replace` belgenin tamamını tek `beginEditBlock` içinde yeniden yazıyor: satır bazlı düzenleme granülerliğini kaybediyoruz ama Ctrl+Z tek adımda hepsini geri alıyor.
- `FileManager.read_file`, olmayan yol ya da dizin için `FileNotFoundError` değil `ValueError` fırlatıyor; `_open_path` bunu yakalayıp anlaşılır mesaj basıyor.
- Sembol çıkarma bir ayrıştırıcı değil, satır bazlı regex sezgiseli. Python tarafı güvenilir; C/C++'ta çok satıra yayılan imzalar ve makro yoğun kod kaçabilir. `if (...) {` gibi kontrol yapıları anahtar sözcük listesiyle eleniyor.

## Devreden
- Yok. Faz 2 kapandı; sıradaki [Faz 3](../Roadmap.md) — Vim hareketleri, VISUAL mod ve ayar dosyası.
