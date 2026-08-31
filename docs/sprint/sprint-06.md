# Sprint 06 — Telescope ve depo hijyeni
**Tarih:** 31 Ağu 2026 – … · **Durum:** Aktif · **Commit:** —

## Hedef
Sprint 05 paketini depoya almak ve `:ts`'yi (telescope) gerçek bir bulanık dosya arama paletine dönüştürmek.

## Çıktılar
- [ ] Sprint 05 çalışma ağacını commit'le: sekmeler, terminal, öneri paneli, `requirements.txt`
- [ ] `.gitignore`'a `__pycache__/` ve `*.pyc` ekle; takip edilen 11 `.pyc` dosyasını `git rm --cached` ile takipten çıkar
- [ ] `docs/` paketi: [Roadmap](../Roadmap.md) + sprint günlüğü (bu belge)
- [ ] `ui/components/command_palette.py`: bulanık dosya arama paleti — bugün dosya boş, `IDEWindow.open_telescope_search` yalnızca `print` ediyor
- [ ] `CLAUDE.md`'yi güncelle: tuş tamponu yerine `:` komut satırı modeli, sekmeler (`EditorTabs`) ve terminal paneli

## Teknik notlar
- Palet için `CommandSuggestions`'daki desen (yüzen kutu + kaydırılabilir liste + Tab ile gezinme) yeniden kullanılabilir; ortak bir "yüzen liste" bileşenine çıkarmak değerlendirilecek.
- Dosya listesi kaynağı: `Sidebar`'ın `QFileSystemModel`'i yerine çalışma dizinini tarayan ayrı bir arama daha uygun olabilir; büyük dizinlerde tarama arayüzü kilitlememeli.

## Devreden
- (sprint kapanırken doldurulacak)
