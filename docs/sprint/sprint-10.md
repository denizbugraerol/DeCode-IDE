# Sprint 10 — PlatformIO çalıştırma çekirdeği
**Tarih:** 01 Eyl 2026 · **Durum:** Tamamlandı · **Commit(ler):** `3bdd95a` tasarım+plan,
`944e11e` pio_project, `7a791c5` pio_cli, `42307d6` PTY komut çalıştırma,
`cc56cee` komut sekmesi, `a61e093` `:pio` komutu, `f4032ec` pencere akışı

## Hedef
`:pio build|upload|monitor|clean|env` komutlarını IDE'nin içinden, gömülü
terminalde gerçek bir PTY üzerinde çalıştırmak.

## Çıktılar
- [x] `platformio.ini` ayrıştırma ve proje kökü bulma — `embedded/pio_project.py`
- [x] `pio` çalıştırılabiliri ve argv üretimi — `embedded/pio_cli.py`
- [x] PTY'de verilen komutu çalıştırma, `cwd`, çıkış kodu — `core/terminal_process.py`
- [x] Komut sekmesi: başlık, `✓`/`✗`, aynı komutta sekme yeniden kullanımı — `ui/components/terminal_panel.py`
- [x] `:pio <alt-komut>` ve tamamlaması — `core/state_machine.py`
- [x] Ortam paleti (`:pio env`) ve statusline ortam rozeti — `ui/main_window.py`, `ui/components/bottom_panel.py`
- [x] 40 yeni test (toplam 183), PlatformIO kurulu olmadan geçiyor

## Teknik notlar
- **`finished` sinyaline argüman eklenmedi.** `TerminalView` onu doğrudan
  `QWidget.update`'e bağlıyor; sinyale `int` eklenseydi Qt `update(int)`
  overload'ı arar ve bağlantı sessizce kopardı — terminal çizmeyi bırakırdı.
  Çıkış kodu ayrı `exited(int)` sinyaliyle taşınıyor.
- **`_handle_child_exit` artık reap ettiği pid'i temizliyor.** Eskiden `_pid`
  ölü süreçte de dolu kalıyordu, yani `is_running()` yalan söylüyordu. Bu, "biten
  komut sekmesi yeniden görününce çalışmasın" korumasını farkında olmadan bayat
  pid'in üstlenmesine yol açıyordu; asıl koruma (`_finished`) ölü kod gibi
  duruyordu. Test bunu yakaladı.
- **`showEvent`'in "koşmuyorsa başlat" kuralı komut sekmesinde tehlikeli.**
  `_finished` bayrağı olmadan, biten bir `pio upload` sekmesi panel `:term` ile
  gizlenip açıldığında komutu tekrar çalıştırır — gerçek karta yeniden yazar.
- **Sekme eşleştirmesi süslenmemiş başlığa bakar.** `title()` bitmiş sekmede
  `pio build ✓` döndüğü için, `_find_command_tab` `command_title`'a bakmasa her
  derleme yeni sekme açardı.
- **`ConfigParser(interpolation=None, strict=False)`.** İnterpolasyon
  `read_string`'de değil `get()`'te çalışıyor; okuduğumuz tek değer olan
  `default_envs` `%` içeriyorsa varsayılan parser çöker. `strict=False` de
  tekrarlanan anahtarlı ini'ler için.
- **PTY ölçüsü `start()`'ta kuruluyor**, bu yüzden `resize()` süreç
  koşmuyorken de `rows`/`cols`'u saklıyor ve komut sekmesi `start_now()` içinde
  önce ölçüp sonra başlıyor — yoksa `pio`'nun ilk çıktısı yanlış genişlikte
  sarmalanıyor.
- Ortam seçilmemişse argv'ye `-e` eklenmiyor: kararı `platformio.ini`'nin
  `default_envs`'i veriyor, IDE onu ezmiyor. Rozet o durumda parantezle
  (`(esp32dev)`) gösteriyor.
- Statusline'daki ortam etiketi bilinçli olarak `setStyleSheet` kullanmıyor:
  renk/font kopyalayan her çağrı `apply_settings`'te elle tazelenmek zorunda
  (Sprint 09, Bulgu 1/4). Düz metin bu tuzağı hiç doğurmuyor.

## Devreden
- Derleme hatasından koda atlama (Faz 4/E) — Sprint 11. `_drain_master`'daki tek
  `feed()` noktası ham byte'ları dışarı vermeye hazır; ekran 9 satır ve `pyte`
  kaydırma tamponu tutmadığı için ayrıştırma ekranı kazıyarak yapılamaz.
- Kendi seri monitörümüz (`embedded/serial_reader.py`, Faz 4/D) — Sprint 12.
  Bu sprintte `:pio monitor` PlatformIO'nun kendi monitörünü çalıştırıyor.
