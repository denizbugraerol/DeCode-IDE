# Sprint 03 — Komut satırı ve durum çubuğu
**Tarih:** 25 Ağu 2026 · **Durum:** Tamamlandı · **Commit:** `fab43f0` komut paleti - durum çubuğu

## Hedef
Tuş tamponunu, Vim'deki gibi yazılıp Enter'la çalıştırılan gerçek bir `:` komut satırıyla değiştirmek.

## Çıktılar
- [x] COMMAND modu: `:` ile giriliyor; Escape ya da komut metnini tamamen silmek NORMAL moda döndürüyor — `core/state_machine.py`
- [x] `CommandLine`: bir bara bağlı olmayan, ekranın ortasında beliren gölgeli/yuvarlatılmış yüzen kutu — `ui/components/bottom_panel.py`
- [x] `StatusLine`: renkli mod rozeti (NORMAL mavi, INSERT yeşil, COMMAND turuncu), dosya adı ve satır:sütun
- [x] Komut metni Enter'a kadar serbestçe yazılıp düzeltilebiliyor; sayısal komut (`:42`) o satıra atlıyor
- [x] Yüzen kutuların konumu `IDEWindow.resizeEvent` ile pencereyle birlikte güncelleniyor

## Teknik notlar
- `StatusLine` layout'ta duran kalıcı bir bar; `CommandLine` ise `central_widget`'a parent'lanmış, mutlak konumlanan ve `raise_()` ile öne alınan yüzen bir çocuk. İkisi aynı dosyada ama sorumlulukları ayrı.
- Mod değişimi tek bir kaynaktan (`mode_changed` sinyali) besleniyor: statusline, komut kutusu ve öneri listesi hep aynı olaydan güncelleniyor.

## Devreden
- Komut adını hatırlamak hâlâ tamamen kullanıcıda: öneri ve tamamlama yok — Sprint 04.
