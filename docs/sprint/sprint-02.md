# Sprint 02 — Modal çekirdek ve kısayollar
**Tarih:** 06–11 Tem 2026 · **Durum:** Tamamlandı · **Commit'ler:** `e56191b` kısayol temelleri, `59b3a98` kısayol düzenlemeleri

## Hedef
Editörü sıradan bir yazı kutusu olmaktan çıkarıp modal bir editöre dönüştürmek.

## Çıktılar
- [x] NORMAL / INSERT modları; NORMAL'de tuşlar metne yazmıyor — `ui/components/code_editor.py`
- [x] Mod görselleştirmesi: imleç NORMAL'de kalın, INSERT'te ince
- [x] `StateMachine` tuş tamponu: tuşlar biriktirilip bilinen komutlarla eşleştiriliyor — `core/state_machine.py`
- [x] Komutlar: `i`, `:d`, `:w`, `:b`, `:ts`, `:wq`, `:q`
- [x] Komut → eylem bağlantısı sinyallerle (`save_requested`, `sidebar_toggle_requested`, …) `IDEWindow`'da kuruluyor
- [x] Sidebar'da Esc odağı editöre döndürüyor; sağ ok dosyayı açıyor, klasörde Qt'nin genişletme davranışına düşüyor

## Teknik notlar
- Komut yürütme editörün içine gömülmedi: `StateMachine` ya doğrudan `QTextCursor`'a dokunuyor ya da bir sinyal yayıyor. Yeni komut eklemek bu yüzden üç adım: komut listesi + `case` dalı + (gerekiyorsa) yeni sinyal.
- Navigasyon tuşları ve Ctrl'lü kombinasyonlar NORMAL modda da `QPlainTextEdit`'e geçiriliyor; sıfırdan hareket komutu yazma ihtiyacı ertelendi.

## Devreden
- Tuş tamponu gerçek bir Vim komut satırı gibi davranmıyor: yazılan komut ekranda görünmüyor, geri silme ve Enter yok — Sprint 03.
