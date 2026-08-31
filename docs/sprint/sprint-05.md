# Sprint 05 — Sekmeler, terminal ve kaydırılabilir öneriler
**Tarih:** 31 Ağu 2026 · **Durum:** Tamamlandı (henüz commit edilmedi, çalışma ağacında) · **Commit:** —

## Hedef
Tek dosyalık editörü çok sekmeli bir çalışma alanına çevirmek ve pencereden çıkmadan shell kullanılabilmesini sağlamak.

## Çıktılar
- [x] `EditorTabs`: her sekmenin kendi `ModalEditor`'ı (kendi modu, imleci, state machine'i); açık dosya tekrar açılınca o sekmeye geçiş, boş/adsız sekmenin yeniden kullanımı, başlıkta `●` kaydedilmemiş değişiklik göstergesi — `ui/components/editor_tabs.py`
- [x] Aktif sekme sinyal aktarımı (`_relay`): `IDEWindow` tek bir editörle konuşuyormuş gibi kalıyor, arka plan sekmelerinin sinyalleri yutuluyor
- [x] `TerminalProcess`: `pty.fork` + `QSocketNotifier` + `pyte` ekran arabelleği ile gerçek shell oturumu — `core/terminal_process.py`
- [x] `TerminalPanel` / `TerminalView`: editörün altında gerçek layout'ta yer kaplayan sekmeli terminal; ANSI renkleri Tokyo Night paletine eşlendi — `ui/components/terminal_panel.py`
- [x] Yeni komutlar: `:qa`, `:wqa`, `:term`, `:termnew`, `:tabnew`, `:tabclose`, `:tabnext`, `:tabprev` — `core/state_machine.py`
- [x] Alt+Shift kısayol ailesi: `T` odağı editör/terminal arasında taşır, `N` yeni terminal sekmesi, `W` kapatır, `Sağ`/`Sol` sekme değiştirir
- [x] Kaydırılabilir öneri paneli: `QScrollArea` içinde en fazla 8 satır, kalanı tekerlekle veya Tab ile kayıyor, ince Tokyo Night kaydırma çubuğu; pencere alçalsa bile kutu statusline'ın üstünde kalıyor — `ui/components/bottom_panel.py`, `ui/main_window.py`
- [x] `requirements.txt` (PyQt6 + pyte) ve `closeEvent`'te PTY/shell temizliği

## Teknik notlar
- Terminal, editörle aynı dikey layout'a kondu: panel açılınca editör gerçekten daralıyor, üstüne binmiyor (overlay değil).
- Terminal odaktayken çıplak Escape shell'e gidiyor (vim'in INSERT modundan çıkabilmesi için); panel işlemleri bu yüzden Alt+Shift ailesine alındı.
- `QScrollArea`'nın viewport'u ana penceredeki tema kurallarıyla (ve `autoFillBackground` / `WA_TranslucentBackground` ile) saydamlaşmıyor; saydamlık doğrudan viewport'un kendi stylesheet'ine yazıldı — gerekçe kodda yorum olarak duruyor.
- Doğrulama, `QT_QPA_PLATFORM=offscreen` ile çalıştırılan bir betikle yapıldı: 17 komut → 8 satırlık kutu + kaydırma, Tab ile vurgulu satıra otomatik kaydırma, 1200×300 pencerede taşma yok.

## Devreden
- Bu paketin commit'lenmesi ve `CLAUDE.md`'nin güncellenmesi — Sprint 06.
