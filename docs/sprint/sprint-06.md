# Sprint 06 — Telescope ve depo hijyeni
**Tarih:** 31 Ağu 2026 · **Durum:** Tamamlandı · **Commit(ler):** `3d741ee` test altyapısı + hijyen, `276274c` fuzzy, `aff94a6` file_index, `0b4cfe0` FloatingList, `de5a06f` `:ts`

## Hedef
Sprint 05 paketini depoya almak ve `:ts`'yi (telescope) gerçek bir bulanık dosya arama paletine dönüştürmek.

## Çıktılar
- [x] Sprint 05 çalışma ağacı commit'lendi: sekmeler, terminal, öneri paneli, `requirements.txt` — `56b3a59`
- [x] `.gitignore`'a `__pycache__/`, `*.pyc` ve `.pytest_cache/` eklendi; takip edilen 14 `.pyc` dosyası `git rm --cached` ile takipten çıkarıldı
- [x] `docs/` paketi: [Roadmap](../Roadmap.md) + sprint günlüğü (bu belge)
- [x] pytest altyapısı: `pytest.ini`, `requirements-dev.txt`, `tests/conftest.py` — Qt `QT_QPA_PLATFORM=offscreen` ile ekransız çalışıyor
- [x] `core/fuzzy.py`: alt dizi skorlaması; ardışık harf ve segment başı (`/`, `_`, `.`) bonusları — harici bağımlılık yok
- [x] `core/file_index.py`: çalışma dizini taraması (gürültülü dizinler atlanır, 20.000 dosya sınırı) + `FileIndexWorker(QThread)`
- [x] `ui/components/floating_list.py`: kaydırılabilir yüzen kutu ortak bileşene çıkarıldı; `CommandSuggestions` onun ince adaptörü oldu
- [x] `ui/components/command_palette.py`: bulanık dosya arama paleti — `IDEWindow.open_telescope_search` artık gerçek iş yapıyor
- [x] `IDEWindow.open_file`, `_open_path` olarak bölündü: sidebar, palet ve (Sprint 07) `:openfile` aynı yoldan geçiyor

## Teknik notlar
- Palet, öneri kutusunun kutu mantığını (kaydırma + boyutlandırma + gölge) `FloatingList`'ten miras alıyor; ikisi arasında kopya kod kalmadı. Stylesheet seçicileri bu yüzden `commandSuggestions` → `floatingList` olarak yeniden adlandırıldı.
- Palet, komut satırının aksine **odağı kendisi alıyor** (terminal panelindeki desen): tuşlar editöre değil palete düşüyor, Escape odağı editöre geri veriyor. Böylece palet mantığı `StateMachine`'i şişirmedi.
- Dosya listesi `Sidebar`'ın `QFileSystemModel`'inden değil, ayrı bir `os.walk` taramasından geliyor ve tarama arka plan iş parçacığında yapılıyor — büyük dizinlerde arayüz kilitlenmiyor. Palet tarama bitmeden de açılıyor, sonuç gelince kendiliğinden doluyor.
- Her `:ts` yeniden tarıyor: önbellek yok, dolayısıyla bayatlama da yok.

## Devreden
- Yok. Faz 2'nin kalan maddeleri (dosya içi arama/değiştirme, `:openfile`, `:sym`) [Sprint 07](sprint-07.md)'de.
