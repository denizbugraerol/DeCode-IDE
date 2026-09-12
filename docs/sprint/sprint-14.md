# Sprint 14 — Windows portu ve dağıtımı
**Tarih:** 10 Eyl 2026 · **Durum:** Tamamlandı · **Commit(ler):** `207a2a7..010e55d`

## Hedef
DeCode IDE'yi Windows'ta çalışır hâle getirip tek dosya `.exe` olarak
yayınlamak — `:term` ve bütün `:pio` alt komutları dahil.

## Çıktılar
- [x] Testlerdeki POSIX'e sabit kabuk komutları platforma bağlandı — `tests/platform_commands.py`
- [x] `TerminalProcess` transport dikişine ayrıldı — `core/terminal_process.py`, `core/pty_posix.py`
- [x] ConPTY transport'u — `core/pty_windows.py`
- [x] `pywinpty` yokken editör çalışmaya devam ediyor — `_UnavailableTransport`
- [x] Ayar dosyası Windows'ta `%APPDATA%` — `core/config.py`
- [x] `pio` yedek yolu ve `isfile` kapısı — `embedded/pio_cli.py`
- [x] Kabuk adı transport'tan geliyor — `ui/components/terminal_panel.py`
- [x] Windows çıktı adı, `hide_console`, DLL toplama — `packaging/decode.spec`
- [x] `windows-latest` test ve release matrisinde — `.github/workflows/`
- [x] Yol ayracı her platformda normalize edildi (Task 4b, plan dışı) — core/file_index.py, core/state_machine.py

## Teknik notlar

**Transport dikişi.** Ortak olan her şey (`pyte` ekranı, çıkış kodu
semantiği, `child_environment`, `resize`'ın ölçüyü saklaması)
`TerminalProcess`'te tek yerde kaldı; platforma özgü dört iş ayrı modüllere
indi. İki ayrı tam sınıf yazmak bilinçli olarak elendi: o incelikler iki
yerde yaşasaydı zamanla ayrışırdı.

Sözleşmenin iki güvencesi var ve ikisi de bozulduğunda hata **sessiz**:
`on_data`/`on_eof` her zaman ana iş parçacığında çağrılır (yoksa
`pyte.Screen` iki thread'den güncellenir), ve `close()` ana iş parçacığında
süresiz bloklanmaz (macOS kapanış kilidinin genelleştirilmiş hâli).

**Neden Windows'ta thread var.** `QSocketNotifier` orada yalnız *socket*
tanıtıcılarıyla çalışıyor, ConPTY ise boru veriyor. Okuma bu yüzden
bloklayan bir `QThread`'de yapılıp kuyruklu bağlantıyla ana thread'e
taşınıyor — desen `core/file_index.py`'deki `FileIndexWorker`'ın aynısı.

**`pyte.ByteStream` kendi decoder'ını taşıyor.** İçinde
`codecs.getincrementaldecoder("utf-8")("replace")` var, yani çok baytlı bir
karakter iki `feed()` arasında bölünse bile doğru birleşiyor. Transport'ta
ikinci bir tampon kurmadık; tasarımın ilk hâli bunu öneriyordu ve gereksizdi.

**`platform.machine()` Windows'ta `AMD64` döner.** Normalleştirilmeseydi
çıktı `DeCode-v0.3.0-windows-AMD64` olur ve `release.yml`'deki ad kontrolü
release'i kırardı.

**`windows-latest`'te `run:` varsayılanı PowerShell.** Her iki workflow'daki
mevcut adımlar bash (`PIPESTATUS`, `tee`, `awk`); iş düzeyinde
`defaults: run: shell: bash` ile üçü de aynı betikleri koşuyor.

**CI'ın göremediği boşluk — bilinçli kabul.** `--version` `QApplication`'dan
önce dönüyor, yani ConPTY'ye hiç dokunmuyor: eksik bir `winpty` DLL'i duman
testinden görünmez geçer. `tests.yml` ConPTY'yi sınıyor ama kaynaktan,
donmuş binary'den değil. Boşluğu kapatmak `--selftest` bayrağı gerektirirdi;
uygulama yüzeyini büyütmek yerine güvence elle doğrulamadan alındı.

**Plan boşluğu.** Tasarımın §D'si taşınabilirlik düzeltmeleri olarak yalnız
üçünü (ayar yolu, `pio` yolu, kabuk adı) saymış, **yol ayracı sınıfını hiç
görmemişti**. `os.walk` ve `os.path.join` Windows'ta ters bölü üretiyor;
palet ve `:cd` tamamlaması orada öteki platformlardan farklı görünüyordu
(`klasor\alt/` gibi karışık ayraç dahil). Karar: uygulamanın içinde kanonik
yol biçimi POSIX tarzı (`/`) — Windows'ta Python ve Qt eğik çizgiyi kabul
ediyor, `core/fuzzy.py` de zaten iki ayracı da tanıyordu.

**Sprintin en öğretici bulgusu.** `pywinpty`'nin okuma tipini ölçmek için
Windows makinesi gerekmiyordu: `pip download pywinpty --no-deps
--no-binary :all:` ile sdist indirilip kaynak Linux'ta okunabiliyor. Bu iki
şeyi ortaya çıkardı — `read()`'in `str` döndürüp **kendi sınır tamamlama
döngüsünü** taşıdığı (yani UTF-8 sınır riski yok), ve tasarımın
`subprocess.list2cmdline(argv)` yönlendirmesinin **yanlış** olduğu
(pywinpty dizeye `shlex.split(posix=False)` uyguluyor, tırnaklar token
içinde kalıyor, boşluklu yollarda — varsayılan PowerShell 7 kurulumu dahil
— `:term` 127'ye düşüyordu). Ders: "bunu ancak o platformda ölçebiliriz"
varsayımı, bağımlılığın kaynağı okunabilirken yanlıştır.

## Devreden
- Kod imzalama ve notarization (Windows + macOS birlikte)
- Installer (Inno Setup / MSI) ve başlat menüsü girdisi
- Windows on ARM (`arm64`) — ayrı matris satırı
- Intel Mac (`macos-13`) — bu portla ilgisiz, hâlâ açık
- **Windows'ta elle doğrulama henüz yapılmadı** — tasarım dokümanının §Elle
  doğrulama listesindeki 13 madde release'in ön koşulu ve hiçbiri bu
  sprintte koşulmadı (projenin Windows makinesi var ama bu oturum Linux'ta
  yürütüldü). `core/pty_windows.py`'nin tek satırı bile gerçek bir ConPTY
  üzerinde çalıştırılmadı; güvence sdist kaynağının okunmasına ve statik
  sözleşme karşılaştırmasına dayanıyor.
