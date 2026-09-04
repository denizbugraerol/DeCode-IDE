# Değişiklik Günlüğü

## v0.2.0 — 04 Eyl 2026

### Eklendi
- **macOS (Apple Silicon) derlemesi.** Release'ler artık iki dosya içeriyor:
  `DeCode-*-linux-x86_64` ve `DeCode-*-macos-arm64`. Test süiti de her
  push'ta hem Linux hem macOS runner'ında koşuyor.

### Değişti
- Varlık adları platform taşıyor: `DeCode-v0.1.1-x86_64` →
  `DeCode-vX.Y.Z-linux-x86_64`. İki platform olunca kaçınılmazdı.
- `QT_QPA_PLATFORM` yalnız Linux'ta ve yalnız kullanıcı bir değer
  belirtmemişse ayarlanıyor. Eskiden koşulsuz `wayland;xcb` yazılıyordu;
  macOS'ta bu, olmayan plugin'lerin aranmasına yol açardı. Yan etkisi:
  artık `QT_QPA_PLATFORM=xcb ./DeCode` gerçekten X11 ile çalıştırıyor
  (eskiden sessizce eziliyordu).

## v0.1.1 — 04 Eyl 2026

### Eklendi
- `:pio init [kart]` — çalışma dizininde yeni PlatformIO projesi oluşturur.
  Diğer `:pio` komutlarının aksine var olan bir `platformio.ini` aramaz;
  onu oluşturan komut o. Kart argümanı opsiyonel: `:pio init` çıplak proje,
  `:pio init esp32dev` `[env:esp32dev]` bölümüyle birlikte kurar.

## v0.1.0 — 04 Eyl 2026

İlk halka açık sürüm. Tek dosya Linux çalıştırılabiliri olarak yayınlanıyor.

### Özellikler
- Modal editör (NORMAL / INSERT / COMMAND), çoklu sekme, satır numarası gutter'ı
- Gerçek `:` komut satırı: Tab tamamlama, kaydırılabilir öneri listesi
- Bulanık dosya arama (`:ts`), dosya içi arama/değiştirme (`:find`, `:replace`),
  sembol atlama (`:sym`), yol tamamlamalı `:openfile`
- Gömülü terminal: gerçek PTY, sekmeli, ANSI renkleri Tokyo Night'a eşlenmiş
- PlatformIO: `:pio build|upload|monitor|clean|env`, sekme başlığında `✓`/`✗`
- Ayar dosyası (`~/.config/decode/config.toml`): 17 renk tokeni, font, sekme
  genişliği, terminal satır sayısı; `:reload` ile kapatmadan uygulama
- C/C++ ve Python sözdizimi renklendirme

### Bilinen sınırlar
- Yalnız Linux x86_64 (glibc 2.35+). macOS ve Windows henüz yok.
- Vim düzenleme komutları (`dd`, `yy`, `x`, `o`/`O`) ve VISUAL mod yok
- Derleme hatasından koda atlama ve kendi seri monitörümüz yok
