# Sprint 01 — Temeller: iskelet, editör, sidebar
**Tarih:** 02 Tem 2026 · **Durum:** Tamamlandı · **Commit'ler:** `029861e` First commit, `7efc1a8` Sidebar Eklendi, `d502fce` Save shortcut eklendi

## Hedef
PyQt6 üzerinde açılan, dosya gezinip okuyabilen ve kaydedebilen bir editör iskeleti çıkarmak.

## Çıktılar
- [x] Proje iskeleti ve sorumluluk ayrımı: `main.py`, `core/`, `ui/`, `ui/components/`, `embedded/`
- [x] `IDEWindow`: `QSplitter` ile solda dosya ağacı, sağda editör — `ui/main_window.py`
- [x] `ModalEditor` (`QPlainTextEdit` türevi) ve `StateMachine` iskeleti — `ui/components/code_editor.py`, `core/state_machine.py`
- [x] `CppHighlighter`: yorum / anahtar kelime / string / rakam kuralları — `ui/components/syntax_highlighter.py`
- [x] `Sidebar`: `QFileSystemModel` üzerinde tek sütunlu `QTreeView`, çalışma dizinine köklenmiş — `ui/components/sidebar.py`
- [x] `FileManager`: statik oku/yaz yardımcıları — `core/file_manager.py`
- [x] Tokyo Night stylesheet'i tek yerde toplandı (`IDEWindow._apply_theme`)
- [x] İlk kaydetme kısayolu

## Teknik notlar
- `main.py`, `QApplication`'dan önce `QT_QPA_PLATFORM=wayland;xcb` ayarlıyor; aynı kod hem Wayland hem X11'de açılıyor.
- `embedded/pio_cli.py` ve `embedded/serial_reader.py` bilinçli olarak boş bırakıldı: gömülü hedef en baştan mimaride yer tuttu (bkz. [Roadmap · Faz 4](../Roadmap.md#faz-4--gömülü-hedef-platformio)).
- Tek harici bağımlılık PyQt6; kurulum dosyası ya da paketleme yok.

## Devreden
- Kalıcı bir modal (Vim benzeri) giriş modeli — Sprint 02.
