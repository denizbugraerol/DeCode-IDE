# Değişiklik Günlüğü

## Yayınlanmamış

Sürüm numarası ve tarih, `core/version.py` yükseltilip `v*` tag'i atılırken
doldurulacak.

### Eklendi
- Windows desteği: `:term` ve bütün `:pio` alt komutları için ConPTY yolu
  eklendi; tek dosya `.exe` GitHub Releases'te. (Windows derlemesi elle
  denenmedi, bkz. "Bilinen sınırlar".)

### Değişti
- `TerminalProcess` bir transport dikişine ayrıldı (`core/pty_posix.py`,
  `core/pty_windows.py`). POSIX davranışı değişmedi.
- Ayar dosyası Windows'ta `%APPDATA%\decode\config.toml`.

### Bilinen sınırlar
- Windows on ARM ve Intel Mac (x86_64) için hazır dosya yok.
- `.exe` imzasız: SmartScreen ilk açılışta uyarı gösteriyor.
- Windows derlemesi elle denenmedi; ConPTY yolu yalnız otomatik testler ve
  statik doğrulamayla güvence altında.

## v0.3.0 — 10 Eyl 2026

### Eklendi
- **Yapılandırılabilir kısayollar.** Ayar dosyasına `[shortcuts]` bölümü
  geldi: 10 eylemin tuşu buradan değiştirilebiliyor ve `:reload` ile
  uygulama kapatılmadan uygulanıyor. Panel eylemleri `terminal_focus`,
  `tab_new`, `tab_close`, `tab_next`, `tab_prev`; NORMAL mod eylemleri
  `insert_mode`, `command_line`, `search_next`, `search_prev`,
  `clear_search`.
- İki grubun kuralları bilinçli olarak farklı: panel kısayolları her modda
  ve mod dağıtımından ÖNCE okunduğu için `ctrl`, `alt` ya da `meta`
  içermek ZORUNDA (yoksa o harf INSERT modunda yazılamaz hale gelirdi),
  NORMAL mod kısayolları ise tek karakter ya da `escape` ve hiçbir
  değiştirici öneki almaz — büyük/küçük harf ayrımı korunur (`n` ≠ `N`).
- İki eylem aynı tuşa düşerse önce tanımlı olan kazanır ve kaybeden için
  açılışta bir uyarı basılır. Geçersiz bir bağlama yalnız o satırı
  varsayılanına düşürür, uygulamayı kırmaz — `[colors]` ile aynı davranış.

### Değişti
- Karşılama sayfasındaki kısayol ipuçları artık sabit metin değil, tuş
  haritasından üretiliyor: kendi tuşunu atadığında ipucu da onu gösterir.

### Düzeltildi
- **macOS'ta uygulama kapanışta donabiliyordu.** `TerminalProcess.close()`
  terminal sürecini SIGKILL ile temizledikten sonra zaman aşımsız bir
  `os.waitpid(pid, 0)` ile bekliyordu. macOS'ta `pty.fork()` çok iş
  parçacıklı bir süreçten çağrıldığında çocuk fork ile exec arasında
  sıkışabiliyor ve toplanabilir hâle gelmiyor; o çağrının dönüşü olmadığı
  ve ana iş parçacığında (`IDEWindow.closeEvent`) çalıştığı için arayüz
  sonsuza kadar donuyordu. Bekleme artık her koşulda sınırlı: yalnız
  `WNOHANG` ile yokluyor, süre dolarsa çocuğu bırakıyor.
- CI artık asılı kalan bir koşuyu 6 saat beklemiyor: `faulthandler_timeout`
  eşiği aşılınca tüm iş parçacıklarının yığın izi basılıyor ve çıktı `tee`
  ile canlı akıyor, yani nerede kilitlendiği loga düşüyor.

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
