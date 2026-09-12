""" GEÇİCİ Windows teşhis betiği — kök neden bulunup düzeltilince SİLİNECEK.

Windows CI'da 11 test kırılıyor ve iki bilinmeyen var:

  1. `WindowsTransport` 'exited' sinyalini hiç yaymıyor (7 test:
     test_pty_transport'ta 3, test_terminal_command'da 4). Belirti her yerde
     aynı: `assert [] == [0]` — komut çalışıyor ama bitiş raporlanmıyor.
  2. `theme._first_monospace_family()` None döndürüyor (2 test). Veritabanı
     boş mu, yoksa dolu da ölçüm mü tutmuyor, bilmiyoruz.

Kaynak okumakla buraya kadar gelinebildi: pywinpty'nin iç okuma thread'i
(`ptyprocess._read_in_thread`) EOF'ta `client.close()` çağırıyor, bu da
bizim `recv()`'imizi boş döndürüp `PtyProcess.read()`'e `EOFError`
fırlattırmalı — yani `_ReaderThread.run()`'daki `except Exception: break`
tetiklenmeli ve `eof` yayılmalı. Olan bu değil, ama hangi katmanda koptuğu
kaynaktan görünmüyor. Bu betik her sınırda ne olduğunu basıyor.

Linux'ta koşulamaz (`winpty` orada yok); yalnız Windows runner'ında anlamlı. """
import os
import sys
import time

# DİKKAT: bu iki satır olmadan betik kendi İKİNCİ print()'inde ölüyordu.
# Windows'ta stdout bir BORUYA (CI, dosya yönlendirmesi) gittiğinde Python
# locale kodlamasını kullanıyor -- GitHub runner'ında cp1252 -- ve Türkçe
# 'ı' oraya sığmıyor: UnicodeEncodeError. İnteraktif konsolda sorun yok,
# çünkü Python 3.6+ orada WriteConsoleW ile UTF-16 yazıyor.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def baslik(metin):
    print(f"\n{'=' * 70}\n{metin}\n{'=' * 70}", flush=True)


# --- 0. Üretim print() yolu: Türkçe mesajlar boruya yazılabiliyor mu? ---
#
# Bu bölüm reconfigure'dan SONRA koşuyor, o yüzden kendi çıktısı güvenli.
# Ölçtüğü şey, uygulamanın reconfigure YAPMADAN kullandığı kodlama.

baslik("0. stdout kodlaması ve Türkçe mesajlar")

ham_kodlama = getattr(sys.stdout, "encoding", "?")
locale_kodlama = __import__("locale").getpreferredencoding(False)
print("reconfigure sonrası sys.stdout.encoding:", ham_kodlama, flush=True)
print("locale.getpreferredencoding():", locale_kodlama, flush=True)
print("sys.stdout bir tty mi:", sys.stdout.isatty(), flush=True)

# Uygulamanın gerçekten bastığı iki mesaj.
ORNEKLER = [
    "Ayar dosyası oluşturuldu: C:/x/config.toml",   # main.py
    "'pio' bulunamadı; PlatformIO kurulu mu?",       # IDEWindow._on_pio_requested
    "Sabit genişlikli 'Fira Code' fontu bulunamadı", # ui/theme.resolve_font_family
]
for ornek in ORNEKLER:
    try:
        ornek.encode(locale_kodlama)
        sonuc = "OK"
    except UnicodeEncodeError as hata:
        sonuc = f"KIRILIR -> {type(hata).__name__}: {hata.reason} ({hata.object[hata.start:hata.end]!r})"
    print(f"  {locale_kodlama} ile {ornek[:45]!r}: {sonuc}", flush=True)


# --- 1. pywinpty'nin çıplak davranışı (bizim kodumuz hiç devrede değil) ---

baslik("1. pywinpty HAM: cmd /c echo merhaba")

import winpty                                          # noqa: E402
from winpty import PtyProcess                          # noqa: E402

print("pywinpty:", getattr(winpty, "__version__", "?"), flush=True)
print("PYWINPTY_BLOCK:", os.environ.get("PYWINPTY_BLOCK", "(ayarlı değil)"), flush=True)

surec = PtyProcess.spawn(["cmd", "/c", "echo", "merhaba"])
print("spawn OK · pid:", surec.pid, "· isalive:", surec.isalive(), flush=True)

son = time.monotonic() + 10.0
tur = 0
bos_tur = 0
while time.monotonic() < son:
    tur += 1
    try:
        veri = surec.read(65536)
    except EOFError as hata:
        print(f"tur {tur}: EOFError -> {hata!r}  <-- beklediğimiz çıkış", flush=True)
        break
    except Exception as hata:
        print(f"tur {tur}: {type(hata).__name__} -> {hata!r}", flush=True)
        break
    if veri:
        print(f"tur {tur}: tip={type(veri).__name__} len={len(veri)} "
              f"repr={veri[:60]!r} isalive={surec.isalive()}", flush=True)
    else:
        bos_tur += 1
        if bos_tur <= 3 or bos_tur % 2000 == 0:
            print(f"tur {tur}: BOŞ ('' sentinel) · bos_tur={bos_tur} "
                  f"isalive={surec.isalive()}", flush=True)
    if tur > 30000:
        print("!!! tur sınırı aşıldı — read() sonsuza kadar '' döndürüyor, "
              "EOFError hiç gelmiyor", flush=True)
        break

print(f"döngü sonu · tur={tur} bos_tur={bos_tur} isalive={surec.isalive()} "
      f"exitstatus={surec.exitstatus}", flush=True)

# EOF'tan sonra exitstatus ne zaman okunabilir hale geliyor?
for bekleme in (0.0, 0.1, 0.5):
    time.sleep(bekleme)
    print(f"  +{bekleme}s sonra: isalive={surec.isalive()} "
          f"exitstatus={surec.exitstatus}", flush=True)


# --- 2. Bizim katmanımız: WindowsTransport + TerminalProcess + Qt döngüsü ---

baslik("2. TerminalProcess (bizim dikişimiz)")

from PyQt6.QtWidgets import QApplication                # noqa: E402

app = QApplication([])

import core.terminal_process as tp                      # noqa: E402

print("seçilen transport:", tp._Transport.__name__, flush=True)

islem = tp.TerminalProcess(rows=6, cols=200, argv=["cmd", "/c", "echo", "merhaba"])
olaylar = []
islem.output_ready.connect(lambda: olaylar.append("output_ready"))
islem.finished.connect(lambda: olaylar.append("finished"))
islem.exited.connect(lambda kod: olaylar.append(f"exited({kod})"))
islem.start()

print("start() döndü · is_running:", islem.is_running(), flush=True)
transport = islem._transport
print("transport._pty:", transport._pty is not None,
      "· reader:", transport._reader is not None,
      "· reader.isRunning():",
      transport._reader.isRunning() if transport._reader else "(yok)", flush=True)

son = time.monotonic() + 10.0
while time.monotonic() < son:
    app.processEvents()
    if any(o.startswith("exited") for o in olaylar):
        break
    time.sleep(0.005)

print("olaylar (ilk 8):", olaylar[:8], "· toplam:", len(olaylar), flush=True)
print("is_running:", islem.is_running(), "· exit_code:", islem.exit_code, flush=True)
print("transport._exit_code:", transport._exit_code, flush=True)
print("reader.isRunning():",
      transport._reader.isRunning() if transport._reader else "(yok)", flush=True)
print("ekran:", repr("".join(islem.screen.display).strip())[:200], flush=True)
islem.close()
print("close() döndü", flush=True)


# --- 3. Qt font veritabanı ---

baslik("3. Qt font veritabanı (offscreen platformda)")

from PyQt6.QtGui import QFontDatabase                   # noqa: E402
import ui.theme as theme                                # noqa: E402

aileler = list(QFontDatabase.families())
print("aile sayısı:", len(aileler), flush=True)
print("ilk 20:", aileler[:20], flush=True)
print("_first_monospace_family(15):", theme._first_monospace_family(15), flush=True)

for ad in ("Consolas", "Courier New", "Cascadia Mono", "Lucida Console", "Fira Code"):
    font = theme._probe_font(ad, 15)
    print(f"  {ad!r}: veritabanında={ad in aileler} "
          f"monospace={theme._is_monospace(font)}", flush=True)

print("resolve_font_family('Fira Code', 15):",
      theme.resolve_font_family("Fira Code", 15), flush=True)
