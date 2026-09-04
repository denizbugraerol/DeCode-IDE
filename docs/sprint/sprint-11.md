# Sprint 11 — Linux tek dosya dağıtımı
**Tarih:** 04 Eyl 2026 · **Durum:** Tamamlandı · **Commit(ler):** `db952d6` lisans/hijyen, `457f13e` sürüm, `d6d10d5` donmuş ortam, `012df0c` PyInstaller, `c01b583` monospace yedeği

## Hedef
DeCode IDE'yi indirilip çalıştırılabilen tek bir Linux dosyası olarak
yayınlamak (v0.1.0) ve bunu her tag'de tekrarlayan bir CI hattına bağlamak.

## Çıktılar
- [x] `.gitignore` takibe alındı, GPL-3.0 lisansı eklendi — `LICENSE`
- [x] Sürümün tek kaynağı ve `--version` bayrağı — `core/version.py`, `main.py`
- [x] PyInstaller ortam izlerinin PTY çocuğuna sızmasını önleme — `core/terminal_process.py`
- [x] Tek dosya PyInstaller yapılandırması — `packaging/decode.spec`
- [x] Monospace yedeğinin ölçülerek doğrulanması — `ui/theme.py`
- [x] Her push'ta pytest — `.github/workflows/tests.yml`
- [x] `v*` tag'inde build + duman testi + Release — `.github/workflows/release.yml`
- [x] README, CHANGELOG, Roadmap güncellemesi
- [x] `main`'e merge, `v0.1.0` tag'i, yayın — https://github.com/denizbugraerol/DeCode-IDE/releases/tag/v0.1.0

## Teknik notlar

**Build neden CI'da, geliştirici makinesinde değil.** Binary, üzerinde
derlendiği glibc'yi taban alır. Geliştirme makinesi CachyOS (glibc 2.44);
burada derlenen dosya Ubuntu 22.04 (2.35) ya da Debian 12 (2.36) üzerinde
açılmaz. `ubuntu-22.04` runner'ında derlemek tabanı düşürüyor ve aynı matris
ileride `macos-latest` satırıyla genişleyebiliyor.

**Donmuş ortamın kabuğa sızması.** PyInstaller bootloader'ı
`LD_LIBRARY_PATH`'i paketin açıldığı geçici dizine çevirir; `pty.fork()` ile
doğan kabuk bunu miras alır ve içeriden çalıştırılan `pio`/`git`/`gcc`
paketlenmiş kütüphanelerle çakışabilir. `child_environment()` saf tutuldu ki
donmadan test edilebilsin. Dondurulmuş bir tanı aracıyla ölçüldü:
`LD_LIBRARY_PATH` gerçekten `/tmp/_MEI...`'e çevriliyor ve temizlik çalışıyor.
Pakette `libstdc++.so.6`, `libgcc_s.so.1`, `libssl.so.3` dahil 19 çakışma
adayı var; kırılma bu makinede yeniden üretilmedi (paket ve sistem sürümleri
aynı, çünkü binary burada derlendi) ama başka bir dağıtımda somut risk.

**`--version` neden `QApplication`'dan önce.** CI, ürettiği binary'yi ekransız
runner'da `--version` ile duman testinden geçiriyor: Qt platform plugin'i
aranmamalı ve ev dizinine ayar dosyası yazılmamalı. `main()` artık çıkış
kodunu döndürüyor, `sys.exit` çağırmıyor — bayrak testten çağrılabilsin diye.

**Monospace yedeğine güvenilemez.** `setStyleHint(QFont.StyleHint.Monospace)`
fontconfig'in `monospace` takma adına güvenir. Takma ad tanımlı değilse
(minimal sistemler, konteynerler, CI runner'ları) Qt orantılı bir aile
döndürür ve terminal ızgarası bozulur — Sprint'in başında düzeltilen hatanın
tam kendisi. Yedek artık ölçülüyor, tutmazsa font veritabanı taranıyor.
CI'ın ilk iki koşusu tam olarak bu yüzden kırıldı.

**Yerel taklit yanıltabilir.** İlk denemede fontsuz/DejaVu'lu bir
`fonts.conf` kurup testleri geçirdim; ama o dosyaya `monospace` takma adını
elle yazmıştım, yani runner'da olmayan şeyi taklide hediye etmiştim. Takma
adsız taklit gerçeği gösterdi. Ortam taklit edilirken taklidin neyi *fazladan*
sağladığı, neyi eksik bıraktığı kadar önemli.

**Duman testi kapısı `set -e`'ye güvenmemeli.** İlk yazımda sürüm
karşılaştırması `test A = B` ile yapılıyor ve ardından `ls -lh` geliyordu;
betiğin çıkış kodunu son komut belirlediği için yanlış sürümlü ve hiç
açılmayan binary'ler kapıdan GEÇİYORDU. Üç durumla (doğru sürüm / yanlış
sürüm / çöken binary) yerelde sınandı ve açık `exit 1`'lere çevrildi. Bozuk
binary'nin yayınlanmasını engelleyen tek mekanizma bu adım olduğu için
kabuk davranışına bağlı kalamaz.

**CI log'ları okunamıyor, annotation'lar okunabiliyor.** İş log'ları GitHub
API'sinden kimlik doğrulaması ister; annotation'lar public depolarda
doğrulamasız okunur. `tests.yml` kırılan test adlarını `::error::` ile
yayınlıyor, böylece bir koşunun neden kırıldığı `gh` kurulu olmayan bir
makineden de görülebiliyor.

**glibc tabanı ölçüldü, varsayılmadı.** Yayınlanan binary indirilip paketin
açıldığı dizindeki 45 kütüphane tarandı: en yüksek gereksinim `GLIBC_2.35`
(`libpython3.12.so.1.0`, `libgcc_s.so.1`, `libcairo.so.2`). README'nin
"glibc 2.35+ / Ubuntu 22.04+" iddiası bununla örtüşüyor. Bootloader ELF'ine
bakmak yanıltıcı olurdu: o yalnız `GLIBC_2.14` istiyor, asıl taban paketin
içindeki kütüphanelerde.

**`main` doğrusal değil.** Depoya Faz 3 ve Faz 4 GitHub PR'larıyla merge
edilmiş; yerel `main` bayat olduğu için ilk `--ff-only` denemesi yerelde
geçip push'ta reddedildi. Zorlanmadı: `origin/main`'e hizalanıp `--no-ff`
merge ile deponun kendi PR-merge topolojisine uyuldu.

## Devreden
- AppImage, `.desktop` girdisi ve uygulama ikonu (Faz 5'in kalanı)
- `pyproject.toml` + `decode` konsol komutu
- macOS alt projesi: `main.py`'deki `QT_QPA_PLATFORM` ataması Linux'a
  koşullanmalı, `macos-latest` matris satırı
- Windows alt projesi: `TerminalProcess`'in ConPTY (`pywinpty`) portu
