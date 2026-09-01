# PlatformIO Çalıştırma Çekirdeği (Faz 4 / Sprint 10) — Uygulama Planı

> **Ajan işçiler için:** ZORUNLU ALT BECERİ: Bu planı görev görev uygulamak için
> `superpowers:subagent-driven-development` (önerilen) ya da
> `superpowers:executing-plans` kullanın. Adımlar takip için checkbox (`- [ ]`)
> sözdizimiyle yazılmıştır.

**Hedef:** `:pio build|upload|monitor|clean|env` komutlarını DeCode IDE'nin
içinden çalıştırmak: süreç gömülü terminal panelinde kendi PTY'sinde koşar,
`platformio.ini`'deki ortamlar okunup seçilebilir ve seçili ortam statusline'da
görünür.

**Mimari:** İki yeni saf modül (`embedded/pio_project.py` ini'yi okur,
`embedded/pio_cli.py` argv üretir — ikisi de Qt bilmez, doğrudan test edilir).
`core/terminal_process.py` artık login shell yerine verilen bir argv'yi de
çalıştırabiliyor ve çıkış kodunu yayıyor; `TerminalPanel` bunun üstüne "komut
sekmesi" kavramını koyuyor (başlık, `✓`/`✗`, aynı komut ikinci kez çalışınca
sekmeyi yeniden kullanma). `IDEWindow` her zamanki gibi tek orkestratör: kök bul
→ pio'yu bul → argv üret → sekmede çalıştır.

**Teknoloji:** Python 3.14 (`configparser`, `shutil.which`, `pty`), PyQt6, pyte.
**Yeni Python bağımlılığı yok** — PlatformIO harici bir araçtır, `requirements.txt`
değişmez.

**Spec:** [`docs/superpowers/specs/2026-09-01-pio-calistirma-cekirdegi-design.md`](../specs/2026-09-01-pio-calistirma-cekirdegi-design.md)

## Global Constraints

Her görevin gereksinimleri bu bölümü kapsar.

- **Dil:** Yorum, docstring, commit mesajı ve `docs/` **Türkçe** (depo geleneği).
  Kod tanımlayıcıları İngilizce, test fonksiyon adları Türkçe (mevcut testlerdeki
  gibi: `def test_pio_komutu_sinyal_yayar`).
- **Bağımlılık:** `requirements.txt` ve `requirements-dev.txt` değişmez.
  PlatformIO **kurulu olmadan** tüm testler geçmeli.
- **Katman:** `embedded/` saf Python — `PyQt6` ya da `ui` import etmez.
  `core/` `ui`'yi import etmez. `ui/` bu kuralın dışındaki tek katman.
- **Hata üslubu:** Kullanıcı hatası (proje yok, `pio` yok, bozuk ini) asla
  exception fırlatmaz; tek satır Türkçe mesaj `print` edilir — `:cd` / `:openfile`
  bugün nasıl davranıyorsa öyle. Saf modüller **yazdırmaz**: `core/config.parse`
  sözleşmesiyle aynı biçimde `(veri, uyarılar)` döner, yazdırmak çağıranın işi.
- **Renk:** Bu sprintte yeni renk **yok**. `tests/test_no_hardcoded_colors.py`
  `ui/` ve `core/` altında `#rrggbb` arıyor; statusline rozeti bilinçli olarak
  düz metin (stylesheet yok).
- **Ortam bayrağı:** Ortam seçilmemişse argv'ye `-e` **hiç** eklenmez (K5) —
  kararı `platformio.ini`'nin `default_envs`'i verir.
- **Test komutu:** `.venv/bin/python -m pytest -q` (konsol script'lerinin
  shebang'i bayat, `-m` ile çağrılır).
- **Commit:** Her görevin sonunda bir commit. Mesaj biçimi depo geleneği:
  `feat: ...`, `test: ...`, `refactor: ...`, `docs: ...` + Türkçe özet.

## Dosya haritası

| Dosya | Durum | Sorumluluk |
|---|---|---|
| `embedded/pio_project.py` | **Yeni** | `platformio.ini`: proje kökü + ortam listesi (saf) |
| `embedded/pio_cli.py` | **Yeni** | `pio` çalıştırılabiliri + alt komut tablosu + argv (saf) |
| `core/terminal_process.py` | Değişiyor | PTY: `argv`/`cwd` parametreleri, `exited(int)` sinyali |
| `ui/components/terminal_panel.py` | Değişiyor | Komut sekmesi: başlık, `✓`/`✗`, yeniden kullanım |
| `core/state_machine.py` | Değişiyor | `:pio` komutu ve `:pio ` tamamlaması |
| `ui/components/code_editor.py` | Değişiyor | `pio_requested = pyqtSignal(str)` |
| `ui/components/welcome_page.py` | Değişiyor | Aynı sinyal + `available_commands`'a `pio` |
| `ui/components/editor_tabs.py` | Değişiyor | Sinyalin aktif sekmeden dışa aktarımı |
| `ui/components/bottom_panel.py` | Değişiyor | Statusline'da ortam etiketi |
| `ui/main_window.py` | Değişiyor | Orkestrasyon: kök → pio → argv → sekme; ortam paleti; rozet |
| `tests/conftest.py` | Değişiyor | PTY testleri için `bekle` fixture'ı |
| `tests/test_pio_project.py` | **Yeni** | ini ayrıştırma + kök bulma |
| `tests/test_pio_cli.py` | **Yeni** | argv üretimi + `find_executable` |
| `tests/test_terminal_process.py` | **Yeni** | PTY'de argv/cwd/çıkış kodu |
| `tests/test_terminal_command.py` | **Yeni** | Komut sekmesi davranışı |
| `tests/test_pio_window.py` | **Yeni** | `:pio` akışı uçtan uca |
| `tests/test_state_machine.py` | Değişiyor | `:pio` ayrıştırma/tamamlama testleri |
| `docs/` + `CLAUDE.md` | Değişiyor | Sprint 10 kaydı, Roadmap, mimari notlar |

---

## Task 1: `embedded/pio_project.py` — platformio.ini

**Files:**
- Create: `embedded/pio_project.py`
- Test: `tests/test_pio_project.py`

**Interfaces:**
- Consumes: yok (ilk görev).
- Produces:
  - `find_project_root(start_dir: str) -> str | None`
  - `parse_environments(ini_text: str) -> tuple[dict, list[str]]`
  - `read_project(root: str) -> tuple[dict, list[str]]`
  - Sözlük biçimi: `{"environments": list[str], "default_envs": list[str]}`
  - Modül sabiti: `INI_NAME = "platformio.ini"`

- [ ] **Step 1: Testleri yaz (hepsi başarısız olacak)**

`tests/test_pio_project.py`:

```python
""" platformio.ini ayrıştırma ve proje kökü bulma. Saf katman: Qt yok,
PlatformIO kurulu olması gerekmiyor. """
import os

from embedded import pio_project

BASIT_INI = """\
[platformio]
default_envs = esp32dev

[env:esp32dev]
platform = espressif32
board = esp32dev

[env:nanoatmega328]
platform = atmelavr
"""


def test_ortamlari_dosyadaki_sirayla_verir():
    bilgi, uyarilar = pio_project.parse_environments(BASIT_INI)
    assert bilgi["environments"] == ["esp32dev", "nanoatmega328"]
    assert uyarilar == []


def test_default_envs_okunur():
    bilgi, _ = pio_project.parse_environments(BASIT_INI)
    assert bilgi["default_envs"] == ["esp32dev"]


def test_default_envs_virgulle_ayrilir():
    bilgi, _ = pio_project.parse_environments(
        "[platformio]\ndefault_envs = bir, iki\n\n[env:bir]\n[env:iki]\n")
    assert bilgi["default_envs"] == ["bir", "iki"]


def test_default_envs_cok_satirli_olabilir():
    bilgi, _ = pio_project.parse_environments(
        "[platformio]\ndefault_envs =\n    bir\n    iki\n\n[env:bir]\n[env:iki]\n")
    assert bilgi["default_envs"] == ["bir", "iki"]


def test_platformio_bolumu_yoksa_default_envs_bos():
    bilgi, uyarilar = pio_project.parse_environments("[env:native]\nplatform = native\n")
    assert bilgi["default_envs"] == []
    assert bilgi["environments"] == ["native"]
    assert uyarilar == []


def test_yuzde_iceren_deger_cokertmez():
    """ interpolation=None regresyonu. ConfigParser interpolasyonu
    read_string'de değil get() çağrısında çalışır: okuduğumuz TEK değer
    default_envs olduğu için testin '%'yi oraya koyması şart — varsayılan
    parser bu değeri get() ederken InterpolationSyntaxError fırlatır.
    '${sysenv.HOME}' de PlatformIO ini'lerinde olağan; ham hâliyle geçmeli. """
    ini = (
        "[platformio]\n"
        "default_envs = yuzde%_env\n"
        "\n"
        "[env:yuzde%_env]\n"
        "build_flags = -I ${PROJECT_DIR}/inc\n"
    )
    bilgi, uyarilar = pio_project.parse_environments(ini)
    assert bilgi["environments"] == ["yuzde%_env"]
    assert bilgi["default_envs"] == ["yuzde%_env"]
    assert uyarilar == []


def test_tekrarlanan_anahtar_cokertmez():
    """ strict=False regresyonu: kopyala-yapıştır ini'lerde aynı anahtar iki
    kez yazılabiliyor; DuplicateOptionError ortam listesini komple yutmamalı. """
    bilgi, uyarilar = pio_project.parse_environments(
        "[env:bir]\nboard = a\nboard = b\n")
    assert bilgi["environments"] == ["bir"]
    assert uyarilar == []


def test_bozuk_ini_uyari_dondurur():
    bilgi, uyarilar = pio_project.parse_environments("bolumsuz = deger\n")
    assert bilgi == {"environments": [], "default_envs": []}
    assert len(uyarilar) == 1


def test_kok_alt_dizinden_yukari_bulunur(tmp_path):
    (tmp_path / "platformio.ini").write_text(BASIT_INI, encoding="utf-8")
    alt = tmp_path / "src" / "derin"
    alt.mkdir(parents=True)
    assert pio_project.find_project_root(str(alt)) == str(tmp_path)


def test_kok_yoksa_none(tmp_path):
    assert pio_project.find_project_root(str(tmp_path)) is None


def test_read_project_dosyayi_okur(tmp_path):
    (tmp_path / "platformio.ini").write_text(BASIT_INI, encoding="utf-8")
    bilgi, uyarilar = pio_project.read_project(str(tmp_path))
    assert bilgi["environments"] == ["esp32dev", "nanoatmega328"]
    assert uyarilar == []


def test_read_project_dosya_yoksa_uyari(tmp_path):
    bilgi, uyarilar = pio_project.read_project(str(tmp_path))
    assert bilgi["environments"] == []
    assert len(uyarilar) == 1
```

- [ ] **Step 2: Testlerin başarısız olduğunu gör**

Çalıştır: `.venv/bin/python -m pytest tests/test_pio_project.py -q`
Beklenen: toplama hatası — `ModuleNotFoundError: No module named 'embedded.pio_project'`
(dosya var ama boş olduğu için `AttributeError` da olabilir; ikisi de kabul).

- [ ] **Step 3: Modülü yaz**

`embedded/pio_project.py` (bugün boş olan dosyanın içeriği):

```python
""" platformio.ini okuma: proje kökünü bulma ve ortam (env) listesi çıkarma.

Saf Python — Qt import etmez. core/config.py ile aynı sözleşme: modül
yazdırmaz, (veri, uyarılar) ikilisi döner; yazdırmak çağıranın işidir. """
import configparser
import os

INI_NAME = "platformio.ini"


def _bos_bilgi():
    return {"environments": [], "default_envs": []}


def find_project_root(start_dir):
    """ start_dir'den başlayıp yukarı doğru platformio.ini arar; bulduğu
    dizini, dosya sisteminin köküne kadar bulamazsa None döner. """
    current = os.path.abspath(start_dir)
    while True:
        if os.path.isfile(os.path.join(current, INI_NAME)):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def parse_environments(ini_text):
    """ platformio.ini metnini ayrıştırır: [env:<ad>] bölümlerinden ortam
    adları (dosyadaki sırayla) ve [platformio] default_envs.

    DİKKAT — iki ConfigParser ayarı bilinçli:

    * interpolation=None: interpolasyon read_string'de değil get() çağrısında
      çalışır; okuduğumuz default_envs değeri '%' içeriyorsa varsayılan parser
      InterpolationSyntaxError fırlatır. PlatformIO ini'lerinde '-D FMT="%d"'
      ve '${sysenv.HOME}' olağan; ikisini de ham hâliyle istiyoruz, zaten
      çözmüyoruz.
    * strict=False: kopyala-yapıştır ini'lerde aynı anahtar iki kez yazılmış
      olabiliyor; DuplicateOptionError yüzünden tüm ortam listesini kaybetmek
      istemiyoruz. """
    info = _bos_bilgi()
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        parser.read_string(ini_text)
    except configparser.Error as hata:
        return info, [f"platformio.ini ayrıştırılamadı: {hata}"]

    for section in parser.sections():
        if section.startswith("env:") and section[4:]:
            info["environments"].append(section[4:])

    if parser.has_option("platformio", "default_envs"):
        info["default_envs"] = _split_list(parser.get("platformio", "default_envs"))
    return info, []


def _split_list(value):
    """ default_envs hem virgülle ('bir, iki') hem satır satır yazılabiliyor;
    ikisini de tek listeye indirger. """
    parts = [part.strip() for part in value.replace(",", "\n").splitlines()]
    return [part for part in parts if part]


def read_project(root):
    """ Kökteki platformio.ini'yi okuyup parse_environments'a verir. Dosya
    okunamıyorsa boş bilgi + tek uyarı döner; asla exception sızdırmaz. """
    path = os.path.join(root, INI_NAME)
    try:
        with open(path, "r", encoding="utf-8") as dosya:
            text = dosya.read()
    except OSError as hata:
        return _bos_bilgi(), [f"{path} okunamadı: {hata}"]
    return parse_environments(text)
```

- [ ] **Step 4: Testlerin geçtiğini gör**

Çalıştır: `.venv/bin/python -m pytest tests/test_pio_project.py -q`
Beklenen: 12 passed.

- [ ] **Step 5: Commit**

```bash
git add embedded/pio_project.py tests/test_pio_project.py
git commit -m "feat: platformio.ini ayrıştırma ve proje kökü bulma"
```

---

## Task 2: `embedded/pio_cli.py` — çalıştırılabilir ve argv

**Files:**
- Create: `embedded/pio_cli.py`
- Test: `tests/test_pio_cli.py`

**Interfaces:**
- Consumes: yok (Task 1'den bağımsız).
- Produces:
  - `SUBCOMMANDS: dict[str, str]` — `{alt_komut: açıklama}`, **tamamlama
    listesinin tek kaynağı**; sırası: `build`, `upload`, `monitor`, `clean`, `env`
  - `PROCESS_SUBCOMMANDS: tuple[str, ...]` — süreç başlatanlar (`env` hariç)
  - `find_executable() -> str | None`
  - `build_argv(subcommand: str, executable: str, env: str | None = None) -> list[str] | None`

- [ ] **Step 1: Testleri yaz**

`tests/test_pio_cli.py`:

```python
""" pio çalıştırılabiliri ve argv üretimi. Saf katman: gerçek PlatformIO
kurulu olmasa da geçer. """
from embedded import pio_cli


def test_build_argv():
    assert pio_cli.build_argv("build", "/kurulum/pio") == ["/kurulum/pio", "run"]


def test_upload_argv():
    assert pio_cli.build_argv("upload", "/kurulum/pio") == [
        "/kurulum/pio", "run", "-t", "upload"]


def test_clean_argv():
    assert pio_cli.build_argv("clean", "/kurulum/pio") == [
        "/kurulum/pio", "run", "-t", "clean"]


def test_monitor_argv():
    assert pio_cli.build_argv("monitor", "/kurulum/pio") == [
        "/kurulum/pio", "device", "monitor"]


def test_ortam_verilince_e_bayragi_eklenir():
    assert pio_cli.build_argv("build", "/kurulum/pio", env="esp32dev") == [
        "/kurulum/pio", "run", "-e", "esp32dev"]


def test_ortam_yoksa_e_bayragi_hic_eklenmez():
    """ K5: ortam seçilmediyse kararı platformio.ini'nin default_envs'i verir;
    IDE '-e' ile ini'nin kararını ezmez. """
    for ortam in (None, ""):
        assert "-e" not in pio_cli.build_argv("upload", "/kurulum/pio", env=ortam)


def test_env_alt_komutu_surec_baslatmaz():
    assert pio_cli.build_argv("env", "/kurulum/pio") is None


def test_bilinmeyen_alt_komut_none():
    assert pio_cli.build_argv("derle", "/kurulum/pio") is None


def test_alt_komut_tablosu_tamamlamanin_kaynagi():
    assert set(pio_cli.PROCESS_SUBCOMMANDS) < set(pio_cli.SUBCOMMANDS)
    assert "env" in pio_cli.SUBCOMMANDS
    assert all(aciklama for aciklama in pio_cli.SUBCOMMANDS.values())


def test_find_executable_pathten_bulur(tmp_path, monkeypatch):
    sahte = tmp_path / "pio"
    sahte.write_text("#!/bin/sh\n", encoding="utf-8")
    sahte.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert pio_cli.find_executable() == str(sahte)


def test_find_executable_platformio_adini_da_dener(tmp_path, monkeypatch):
    sahte = tmp_path / "platformio"
    sahte.write_text("#!/bin/sh\n", encoding="utf-8")
    sahte.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert pio_cli.find_executable() == str(sahte)


def test_find_executable_penv_yedegi(tmp_path, monkeypatch):
    """ PlatformIO'nun kendi kurucusu pio'yu PATH'e koymayabiliyor. """
    penv = tmp_path / ".platformio" / "penv" / "bin"
    penv.mkdir(parents=True)
    sahte = penv / "pio"
    sahte.write_text("#!/bin/sh\n", encoding="utf-8")
    sahte.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path / "bos"))
    monkeypatch.setenv("HOME", str(tmp_path))
    assert pio_cli.find_executable() == str(sahte)


def test_find_executable_yoksa_none(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path / "bos"))
    monkeypatch.setenv("HOME", str(tmp_path))
    assert pio_cli.find_executable() is None
```

- [ ] **Step 2: Testlerin başarısız olduğunu gör**

Çalıştır: `.venv/bin/python -m pytest tests/test_pio_cli.py -q`
Beklenen: `AttributeError: module 'embedded.pio_cli' has no attribute 'build_argv'`

- [ ] **Step 3: Modülü yaz**

`embedded/pio_cli.py`:

```python
""" PlatformIO CLI sarmalayıcısı: çalıştırılabiliri bulur ve alt komutlar için
argv üretir. Süreci başlatmak bu modülün işi DEĞİL — argv'yi terminal paneline
IDEWindow veriyor (bkz. ui/main_window.py). Saf Python, Qt yok. """
import os
import shutil

# Öneri listesinin ve ':pio ' tamamlamasının TEK kaynağı. 'env' süreç
# başlatmaz (paleti açar), o yüzden PROCESS_SUBCOMMANDS'ta yoktur.
SUBCOMMANDS = {
    "build": "projeyi derle",
    "upload": "karta yükle",
    "monitor": "seri monitörü aç",
    "clean": "derleme çıktılarını sil",
    "env": "ortam seç",
}

_ARGUMENTS = {
    "build": ["run"],
    "upload": ["run", "-t", "upload"],
    "clean": ["run", "-t", "clean"],
    # '-e' ile koşunca monitor_speed / monitor_port da platformio.ini'den
    # okunur; baud'u IDE'nin sorması gerekmiyor.
    "monitor": ["device", "monitor"],
}

PROCESS_SUBCOMMANDS = tuple(_ARGUMENTS)


def find_executable():
    """ 'pio' ya da 'platformio'yu PATH'te arar; bulamazsa PlatformIO'nun
    kendi kurucusunun kullandığı ~/.platformio/penv/bin/pio yolunu dener.
    Hiçbiri yoksa None — çağıran kullanıcıya kurulum ipucu verir. """
    for name in ("pio", "platformio"):
        path = shutil.which(name)
        if path:
            return path

    fallback = os.path.join(os.path.expanduser("~"), ".platformio", "penv", "bin", "pio")
    return fallback if os.access(fallback, os.X_OK) else None


def build_argv(subcommand, executable, env=None):
    """ Alt komut için tam argv listesi. Süreç başlatmayan ('env') ve
    bilinmeyen alt komutlarda None döner.

    Ortam verilmemişse '-e' HİÇ eklenmez: kararı platformio.ini'deki
    default_envs verir, IDE onu ezmez. """
    arguments = _ARGUMENTS.get(subcommand)
    if arguments is None:
        return None

    argv = [executable] + list(arguments)
    if env:
        argv += ["-e", env]
    return argv
```

- [ ] **Step 4: Testlerin geçtiğini gör**

Çalıştır: `.venv/bin/python -m pytest tests/test_pio_cli.py -q`
Beklenen: 13 passed.

- [ ] **Step 5: Commit**

```bash
git add embedded/pio_cli.py tests/test_pio_cli.py
git commit -m "feat: pio çalıştırılabiliri ve alt komut argv üretimi"
```

---

## Task 3: `core/terminal_process.py` — argv, cwd, çıkış kodu

**Files:**
- Modify: `core/terminal_process.py` (sinyaller, `__init__`, `start`, `resize`, `_handle_child_exit`)
- Modify: `tests/conftest.py` (yeni `bekle` fixture'ı)
- Test: `tests/test_terminal_process.py`

**Interfaces:**
- Consumes: yok.
- Produces:
  - `TerminalProcess(rows=9, cols=80, argv=None, cwd=None, parent=None)`
  - `exited = pyqtSignal(int)` — çıkış kodu (sinyalle ölen süreçte negatif)
  - `self.exit_code: int | None`
  - `finished = pyqtSignal()` **argümansız kalır**
  - `bekle(kosul, zaman_asimi=5.0) -> bool` fixture'ı (Task 4 de kullanır)

- [ ] **Step 1: `bekle` fixture'ını ekle**

`tests/conftest.py` — dosyanın en üstündeki import'lara `import time` ekle,
sonuna bu fixture'ı ekle:

```python
@pytest.fixture
def bekle(qapp):
    """ PTY testleri için: koşul sağlanana kadar Qt olay döngüsünü döndürür.
    QSocketNotifier yalnız olay döngüsü dönerken tetiklenir — süreç çıktısını
    düz bir 'sleep' ile beklemek işe yaramaz, hiçbir zaman gelmez. """
    def _bekle(kosul, zaman_asimi=5.0):
        son = time.monotonic() + zaman_asimi
        while time.monotonic() < son:
            qapp.processEvents()
            if kosul():
                return True
            time.sleep(0.005)
        return bool(kosul())
    return _bekle
```

- [ ] **Step 2: Testleri yaz**

`tests/test_terminal_process.py`:

```python
""" PTY üzerinde komut çalıştırma: argv, cwd ve çıkış kodu.

Gerçek süreç başlatılır (pty.fork), ama yalnız /bin altındaki minik
araçlarla — PlatformIO kurulu olması gerekmez. """
import os

from core.terminal_process import TerminalProcess


def _calistir(bekle, argv, cwd=None, cols=200):
    surec = TerminalProcess(rows=6, cols=cols, argv=argv, cwd=cwd)
    kodlar = []
    surec.exited.connect(kodlar.append)
    surec.start()
    bekle(lambda: bool(kodlar))
    return surec, kodlar


def test_argv_ile_komut_calisir_ve_ciktisi_ekranda(qapp, bekle):
    surec, kodlar = _calistir(bekle, ["/bin/echo", "merhaba"])
    try:
        assert kodlar == [0]
        assert "merhaba" in "".join(surec.screen.display)
    finally:
        surec.close()


def test_basarisiz_komutun_cikis_kodu(qapp, bekle):
    surec, kodlar = _calistir(bekle, ["/bin/false"])
    try:
        assert kodlar == [1]
        assert surec.exit_code == 1
    finally:
        surec.close()


def test_olmayan_komut_127_dondurur(qapp, bekle):
    """ exec başarısız olunca child 127 ile çıkar (kabuk geleneği:
    'command not found'). Sekme başlığında '✗ (127)' olarak görünür. """
    surec, kodlar = _calistir(bekle, ["/olmayan/komut"])
    try:
        assert kodlar == [127]
    finally:
        surec.close()


def test_cwd_uygulanir(qapp, bekle, tmp_path):
    hedef = os.path.realpath(str(tmp_path))
    surec, _kodlar = _calistir(bekle, ["/bin/pwd"], cwd=hedef)
    try:
        assert os.path.basename(hedef) in "".join(surec.screen.display)
    finally:
        surec.close()


def test_argv_verilmezse_shell_baslar(qapp):
    """ Varsayılan davranış (':term') değişmedi: argv yoksa login shell. """
    surec = TerminalProcess(rows=6, cols=40)
    surec.start()
    try:
        assert surec.is_running()
    finally:
        surec.close()


def test_baslamamis_surecte_olcu_saklanir(qapp):
    """ PTY boyutu start() sırasında kuruluyor; 'önce ölç, sonra başlat'
    sırası çalışsın diye resize() koşmayan süreçte de rows/cols'u güncellemeli
    (yoksa komut sekmesi 80 sütunla başlar ve çıktı yanlış sarmalanır). """
    surec = TerminalProcess(rows=6, cols=40, argv=["/bin/true"])
    surec.resize(9, 120)
    assert (surec.rows, surec.cols) == (9, 120)
```

- [ ] **Step 3: Testlerin başarısız olduğunu gör**

Çalıştır: `.venv/bin/python -m pytest tests/test_terminal_process.py -q`
Beklenen: `TypeError: TerminalProcess(...) got an unexpected keyword argument 'argv'`

- [ ] **Step 4: Sinyalleri ve `__init__`'i güncelle**

`core/terminal_process.py` içinde `TerminalProcess` sınıfının başı:

```python
    output_ready = pyqtSignal()   # pyte ekranı güncellendi -> panel repaint etsin
    finished = pyqtSignal()       # child süreç sona erdi
    exited = pyqtSignal(int)      # child sürecin çıkış kodu

    # DİKKAT: 'finished' ARGÜMANSIZ kalmalı. TerminalView onu doğrudan
    # QWidget.update'e bağlıyor; sinyale int eklenirse Qt update(int)
    # overload'ı arar ve bağlantı sessizce kopar (terminal çizmeyi bırakır).
    # Çıkış kodu bu yüzden ayrı 'exited' sinyaliyle taşınıyor.

    def __init__(self, rows=9, cols=80, argv=None, cwd=None, parent=None):
        super().__init__(parent)
        self.rows, self.cols = rows, cols
        self.argv = argv        # None -> kullanıcının login shell'i (':term')
        self.cwd = cwd          # None -> sürecin mevcut çalışma dizini
        self.exit_code = None
        self._pid = None
        self._master_fd = None
        self._notifier = None
        self.screen = None
        self._stream = None
```

- [ ] **Step 5: `start`'ı argv/cwd alacak şekilde güncelle**

Aynı dosyada `start()`'ın baştan `# --- Parent süreç devam ediyor ---`
satırına kadar olan kısmı bununla değiştir:

```python
    def start(self):
        """ pty.fork() ile gerçek bir sözde-terminal (pseudo-terminal) üzerinde
        bir süreç başlatır: argv verilmemişse kullanıcının kendi shell'ini
        (SHELL ortam değişkeni, yoksa /bin/bash) login shell olarak, verilmişse
        doğrudan o komutu (':pio build' gibi). """
        if self.is_running():
            return
        env = dict(os.environ)
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"

        if self.argv is None:
            shell = os.environ.get("SHELL", "/bin/bash")
            argv = [shell, "-l"]
        else:
            argv = list(self.argv)

        self.exit_code = None
        pid, master_fd = pty.fork()
        if pid == 0:
            # Child süreç: pty.fork() setsid + TIOCSCTTY + 0/1/2 dup işini
            # zaten kendi içinde halletti. Burada tek iş exec etmek.
            try:
                if self.cwd:
                    os.chdir(self.cwd)
                os.execvpe(argv[0], argv, env)
            except Exception:
                # 127: kabuk geleneğinde "komut bulunamadı"; sekme başlığında
                # '✗ (127)' olarak görünsün diye 1 değil bu.
                os._exit(127)
```

- [ ] **Step 6: `resize`'ı koşmayan süreçte de ölçüyü saklayacak şekilde güncelle**

```python
    def resize(self, rows, cols):
        """ Ölçüyü her hâlükârda saklar. PTY boyutu start() sırasında
        kurulduğu için, süreç henüz başlamamışken gelen ölçü ATILIRSA komut
        sekmesi 80 sütunla başlar ve 'pio'nun ilk çıktısı yanlış sarmalanır;
        bu yüzden erken dönüş yalnız ioctl/screen kısmını atlıyor. """
        if rows == self.rows and cols == self.cols:
            return
        self.rows, self.cols = rows, cols
        if not self.is_running():
            return
        # DİKKAT: Screen() constructor'ı (columns, lines) sırasında ama
        # resize() metodu (lines, columns) sırasında bekliyor.
        self.screen.resize(lines=rows, columns=cols)
        self._apply_winsize()
```

- [ ] **Step 7: `_handle_child_exit`'i çıkış kodunu okuyacak şekilde güncelle**

```python
    def _handle_child_exit(self):
        if self._pid is None:
            return          # close() zaten temizlemiş
        if self._notifier:
            self._notifier.setEnabled(False)
        try:
            # WNOHANG DEĞİL: PTY'de EOF ile çocuğun reap edilebilir hâle
            # gelmesi arasında yarış var, WNOHANG (0, 0) dönüp çıkış kodunu
            # kaçırabiliyor. EOF geldiyse çocuk zaten ölmek üzere olduğundan
            # bloklayan bekleme pratikte anında dönüyor.
            _pid, status = os.waitpid(self._pid, 0)
            # Sinyalle ölen süreçte (ör. Ctrl+C -> SIGINT) negatif değer döner.
            self.exit_code = os.waitstatus_to_exitcode(status)
        except (ChildProcessError, OSError):
            self.exit_code = -1
        self.finished.emit()
        self.exited.emit(self.exit_code)
```

- [ ] **Step 8: Testlerin geçtiğini gör**

Çalıştır: `.venv/bin/python -m pytest tests/test_terminal_process.py tests/test_terminal_colors.py -q`
Beklenen: 6 + mevcut terminal renk testleri, hepsi passed.

- [ ] **Step 9: Tüm paketi çalıştır (regresyon)**

Çalıştır: `.venv/bin/python -m pytest -q`
Beklenen: mevcut 112 test + bu ana kadarki 31 yeni test (12 + 13 + 6), hepsi passed.

- [ ] **Step 10: Commit**

```bash
git add core/terminal_process.py tests/conftest.py tests/test_terminal_process.py
git commit -m "feat: PTY'de verilen komutu çalıştırma ve çıkış kodu"
```

---

## Task 4: `ui/components/terminal_panel.py` — komut sekmesi

**Files:**
- Modify: `ui/components/terminal_panel.py` (`TerminalView.__init__`, `showEvent`,
  yeni `title`/`start_now`/`restart`/`is_finished`; `TerminalPanel.new_tab` bölünüyor,
  yeni `run_command`/`_find_command_tab`/`_add_view`/`_activate_layout`)
- Test: `tests/test_terminal_command.py`

**Interfaces:**
- Consumes: Task 3'ten `TerminalProcess(argv=..., cwd=...)`, `exited(int)`, `exit_code`.
- Produces:
  - `TerminalView(rows=ROWS, argv=None, title=None, cwd=None, parent=None)`
  - `TerminalView.command_title: str | None` (süslenmemiş başlık; eşleştirme buna bakar)
  - `TerminalView.title() -> str`, `TerminalView.is_finished() -> bool`
  - `TerminalView.command_finished = pyqtSignal()`
  - `TerminalPanel.run_command(argv, title, cwd=None) -> TerminalView`

- [ ] **Step 1: Testleri yaz**

`tests/test_terminal_command.py`:

```python
""" Terminal panelinde komut sekmesi: başlık, çıkış durumu, yeniden kullanım.
Gerçek PlatformIO gerekmiyor; /bin/echo ve /bin/false yetiyor. """
from PyQt6.QtGui import QShowEvent


def test_komut_sekmesi_baslik_ve_basarili_cikis(pencere, bekle):
    panel = pencere.terminal_panel
    view = panel.run_command(["/bin/echo", "merhaba"], "pio build")

    assert view.title() == "pio build"
    assert bekle(view.is_finished)
    assert view.title() == "pio build ✓"
    assert "merhaba" in "".join(view._process.screen.display)
    assert panel.tab_bar.tabText(0).endswith("pio build ✓")


def test_basarisiz_komut_sekmede_isaretlenir(pencere, bekle):
    view = pencere.terminal_panel.run_command(["/bin/false"], "pio upload")
    assert bekle(view.is_finished)
    assert view.title() == "pio upload ✗ (1)"


def test_ayni_komut_ayni_sekmeyi_kullanir(pencere, bekle):
    """ K4 regresyonu: ikinci çağrı bitmiş sekmeyi bulmalı. Eşleştirme
    süslenmiş başlığa ('pio build ✓') bakarsa burada kaçırır ve yeni sekme
    açar. """
    panel = pencere.terminal_panel
    ilk = panel.run_command(["/bin/echo", "bir"], "pio build")
    assert bekle(ilk.is_finished)
    sekme_sayisi = panel.stack.count()

    ikinci = panel.run_command(["/bin/echo", "iki"], "pio build")
    assert ikinci is ilk
    assert panel.stack.count() == sekme_sayisi
    assert bekle(ikinci.is_finished)
    assert "iki" in "".join(ikinci._process.screen.display)


def test_farkli_komut_yeni_sekme_acar(pencere, bekle):
    panel = pencere.terminal_panel
    panel.run_command(["/bin/echo", "bir"], "pio build")
    panel.run_command(["/bin/echo", "iki"], "pio upload")
    assert panel.stack.count() == 2


def test_biten_sekme_yeniden_gorununce_komutu_tekrarlamaz(pencere, bekle):
    """ En tehlikeli regresyon: showEvent'in 'koşmuyorsa başlat' kuralı,
    biten bir komut sekmesinde ':term' ile panel gizlenip açılınca komutu
    yeniden çalıştırır — 'pio upload' için bu gerçek donanıma yazmak demek. """
    view = pencere.terminal_panel.run_command(["/bin/echo", "bir"], "pio upload")
    assert bekle(view.is_finished)

    view.showEvent(QShowEvent())

    assert not view._process.is_running()
    assert view.title() == "pio upload ✓"


def test_shell_sekmesi_hala_kabuk_adini_gosterir(pencere):
    panel = pencere.terminal_panel
    panel.open_panel()
    assert panel.stack.widget(0).command_title is None
    assert panel.tab_bar.tabText(0).endswith(panel.stack.widget(0).shell_name())
```

- [ ] **Step 2: Testlerin başarısız olduğunu gör**

Çalıştır: `.venv/bin/python -m pytest tests/test_terminal_command.py -q`
Beklenen: `AttributeError: 'TerminalPanel' object has no attribute 'run_command'`

- [ ] **Step 3: `TerminalView`'u komut sekmesi bilecek hâle getir**

`ui/components/terminal_panel.py` — `TerminalView`'un sinyal listesine bir satır
ekle ve `__init__`'i değiştir:

```python
    return_focus_requested = pyqtSignal()   # Alt+Shift+T -> odak editöre
    new_tab_requested = pyqtSignal()        # Alt+Shift+N
    close_tab_requested = pyqtSignal()      # Alt+Shift+W
    next_tab_requested = pyqtSignal()       # Alt+Shift+Sağ
    prev_tab_requested = pyqtSignal()       # Alt+Shift+Sol
    command_finished = pyqtSignal()         # komut bitti -> panel başlığı tazelesin

    def __init__(self, rows=ROWS, argv=None, title=None, cwd=None, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.command_title = title   # None -> shell sekmesi
        self.exit_code = None
        self._finished = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._process = TerminalProcess(rows=self.rows, cols=80, argv=argv,
                                        cwd=cwd, parent=self)
        self._process.output_ready.connect(self.update)
        self._process.finished.connect(self.update)
        self._process.exited.connect(self._on_exited)
```

- [ ] **Step 4: Başlık ve yaşam döngüsü metotlarını ekle**

`TerminalView`'daki `shell_name` metodunun yanına (`# --- Oturum ---` bölümü):

```python
    def _on_exited(self, exit_code):
        self._finished = True
        self.exit_code = exit_code
        self.update()
        self.command_finished.emit()

    def is_finished(self):
        return self._finished

    def title(self):
        """ Sekme etiketi: shell sekmesinde kabuğun adı, komut sekmesinde
        verilen başlık ve süreç bitince sonucu.

        DİKKAT: sekme eşleştirmesi (TerminalPanel._find_command_tab) bu SÜSLÜ
        metne değil command_title'a bakar; yoksa 'pio build ✓' ile 'pio build'
        eşleşmez ve her derleme yeni sekme açar. """
        if self.command_title is None:
            return self.shell_name()
        if not self._finished:
            return self.command_title
        return (f"{self.command_title} ✓" if self.exit_code == 0
                else f"{self.command_title} ✗ ({self.exit_code})")

    def start_now(self):
        """ Sekmenin görünür olmasını beklemeden süreci başlatır (komut
        sekmeleri). Ölçü ÖNCE alınır: PTY boyutu start() sırasında kurulur,
        sonra hesaplamak ilk çıktıyı yanlış genişlikte sarmalar. """
        self._recompute_cols()
        if not self._process.is_running():
            self._process.start()

    def restart(self, argv, cwd=None):
        """ Aynı sekmede yeni bir süreç (K4: ':pio build' ikinci kez). Eski
        süreç TerminalProcess.close() ile (SIGHUP, gerekirse SIGKILL)
        kapatılır; pyte ekranı start() içinde sıfırdan kurulur. """
        self._process.close()
        self._process.argv = argv
        self._process.cwd = cwd
        self._finished = False
        self.exit_code = None
        self.start_now()
        self.command_finished.emit()   # başlıktaki ✓/✗ eki temizlensin
```

- [ ] **Step 5: `showEvent`'e biten-komut korumasını koy**

```python
    def showEvent(self, event):
        super().showEvent(event)
        # Gizliyken layout resizeEvent üretmeyebilir; tekrar görünür olunca
        # savunmacı biçimde yeniden hesapla.
        self._recompute_cols()
        # DİKKAT: '_finished' koşulu olmadan, biten bir komut sekmesi panel
        # ':term' ile gizlenip yeniden açıldığında komutu KENDİLİĞİNDEN
        # tekrar çalıştırır — 'pio upload' için bu, gerçek karta yeniden
        # yazmak demek.
        if not self._process.is_running() and not self._finished:
            self._process.start()
        self.setFocus()
```

- [ ] **Step 6: `TerminalPanel`'de sekme kurulumunu ayır ve `run_command`'ı ekle**

`new_tab`'ın gövdesini `_add_view`'a taşı, üstüne iki yeni metot koy:

```python
    def new_tab(self):
        """ ':termnew' / Alt+Shift+N — her zaman yeni bir SHELL sekmesi. """
        return self._add_view(TerminalView(rows=self._rows))

    def run_command(self, argv, title, cwd=None):
        """ Bir komutu kendi sekmesinde çalıştırır (':pio build'). Aynı
        başlıkla açık bir komut sekmesi varsa yeni sekme açılmaz, o sekme
        yeniden kullanılır (K4). """
        index = self._find_command_tab(title)
        if index is None:
            view = self._add_view(
                TerminalView(rows=self._rows, argv=argv, title=title, cwd=cwd))
            self.show()
            self._activate_layout()
            view.start_now()
        else:
            view = self.stack.widget(index)
            self.tab_bar.setCurrentIndex(index)
            self.show()
            self._activate_layout()
            view.restart(argv, cwd)

        self._relabel_tabs()
        self._focus_current_view()
        return view

    def _find_command_tab(self, title):
        """ Süslenmemiş başlığa göre arar (bkz. TerminalView.title). """
        for i in range(self.stack.count()):
            if self.stack.widget(i).command_title == title:
                return i
        return None

    def _activate_layout(self):
        """ Yeni eklenen sekmenin geometrisi henüz hesaplanmamış olabilir;
        süreci başlatmadan önce layout'u zorlayarak sütun sayısını doğru
        ölçüyoruz (PTY boyutu start()'ta kuruluyor). """
        self.layout().activate()

    def _add_view(self, view):
        """ Sekme kurulumunun ortak yolu: shell sekmesi de komut sekmesi de
        buradan geçer. """
        if self._font is not None:
            view.apply_font(self._font)

        view.return_focus_requested.connect(self.return_focus_requested)
        view.new_tab_requested.connect(self.new_tab)
        view.close_tab_requested.connect(self.close_current_tab)
        view.next_tab_requested.connect(lambda: self.switch_tab(1))
        view.prev_tab_requested.connect(lambda: self.switch_tab(-1))
        view.command_finished.connect(self._relabel_tabs)

        index = self.stack.addWidget(view)
        self.tab_bar.addTab("")
        self._relabel_tabs()
        self.tab_bar.setCurrentIndex(index)
        self._recompute_height()
        self._focus_current_view()
        return view
```

- [ ] **Step 7: Sekme etiketini `title()`'a çevir**

```python
    def _relabel_tabs(self):
        for i in range(self.tab_bar.count()):
            view = self.stack.widget(i)
            self.tab_bar.setTabText(i, f"{i + 1}: {view.title()}")
```

- [ ] **Step 8: Testlerin geçtiğini gör**

Çalıştır: `.venv/bin/python -m pytest tests/test_terminal_command.py -q`
Beklenen: 6 passed.

- [ ] **Step 9: Tüm paketi çalıştır**

Çalıştır: `.venv/bin/python -m pytest -q`
Beklenen: hepsi passed (özellikle `tests/test_terminal_colors.py` ve
`tests/test_settings_reload.py` — sekme etiketi ve font yolu değişti).

- [ ] **Step 10: Commit**

```bash
git add ui/components/terminal_panel.py tests/test_terminal_command.py
git commit -m "feat: terminal panelinde komut sekmesi (başlık, çıkış durumu, yeniden kullanım)"
```

---

## Task 5: `:pio` komutu ve sinyal boru hattı

**Files:**
- Modify: `core/state_machine.py` (`KNOWN_COMMANDS`, `COMMAND_DESCRIPTIONS`,
  `_matches_for`, `_execute_command_line`, yeni `_pio_matches_for` / `_run_pio`)
- Modify: `ui/components/code_editor.py` (yeni sinyal)
- Modify: `ui/components/welcome_page.py` (yeni sinyal + `available_commands`)
- Modify: `ui/components/editor_tabs.py` (sinyal + `_wire` aktarımı)
- Test: `tests/test_state_machine.py` (ekleme), `tests/test_welcome_page.py` (ekleme)

**Interfaces:**
- Consumes: Task 2'den `pio_cli.SUBCOMMANDS`.
- Produces: `pio_requested = pyqtSignal(str)` — `ModalEditor`, `WelcomePage` ve
  `EditorTabs` üzerinde aynı adla; taşıdığı değer alt komut adı (`"build"`).

- [ ] **Step 1: Testleri yaz**

`tests/test_state_machine.py` sonuna ekle:

```python
def test_pio_komutu_alt_komutu_sinyalle_yayar(qapp):
    editor = _editor(qapp)
    gelen = []
    editor.pio_requested.connect(gelen.append)
    QTest.keyClicks(editor, ":pio build")
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert gelen == ["build"]


def test_pio_bilinmeyen_alt_komut_sinyal_yaymaz(qapp):
    editor = _editor(qapp)
    gelen = []
    editor.pio_requested.connect(gelen.append)
    QTest.keyClicks(editor, ":pio derle")
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert gelen == []


def test_pio_argumansiz_sinyal_yaymaz(qapp):
    editor = _editor(qapp)
    gelen = []
    editor.pio_requested.connect(gelen.append)
    QTest.keyClicks(editor, ":pio")
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert gelen == []


def test_pio_tamamlamasi_alt_komutlari_listeler(qapp):
    editor = _editor(qapp)
    adlar = [ad for ad, _aciklama in editor.state_machine._matches_for("pio ")]
    assert adlar == ["pio build", "pio clean", "pio env", "pio monitor", "pio upload"]


def test_pio_tamamlamasi_oneke_gore_daralir(qapp):
    editor = _editor(qapp)
    adlar = [ad for ad, _aciklama in editor.state_machine._matches_for("pio u")]
    assert adlar == ["pio upload"]


def test_pio_ana_oneri_listesinde(qapp):
    editor = _editor(qapp)
    assert any(ad == "pio" for ad, _aciklama in editor.state_machine._matches_for("pi"))
```

`tests/test_welcome_page.py` sonuna ekle:

```python
def test_karsilama_sayfasinda_pio_kullanilabilir(qapp):
    """ ':pio build' metin tamponu gerektirmiyor; son sekme kapandığında da
    çalışmalı. """
    from ui.components.welcome_page import WelcomePage
    assert "pio" in WelcomePage.available_commands
```

- [ ] **Step 2: Testlerin başarısız olduğunu gör**

Çalıştır: `.venv/bin/python -m pytest tests/test_state_machine.py -q -k pio`
Beklenen: `AttributeError: 'ModalEditor' object has no attribute 'pio_requested'`

- [ ] **Step 3: Sinyali üç bileşene ekle**

`ui/components/code_editor.py` — `settings_reload_requested` satırının altına:

```python
    pio_requested = pyqtSignal(str)           # ':pio build|upload|monitor|clean|env'
```

`ui/components/welcome_page.py` — aynı satırı sinyal listesine ekle ve
`available_commands`'a `"pio"`yu (alfabetik yerine) yerleştir:

```python
    available_commands = ("b", "cd", "openfile", "pio", "qa", "reload",
                          "tabnew", "term", "termnew", "ts")
```

`ui/components/editor_tabs.py` — sinyal listesine ekle:

```python
    pio_requested = pyqtSignal(str)           # ':pio <alt-komut>'
```

ve `_wire` içine, `settings_reload_requested` aktarımının hemen altına:

```python
        editor.pio_requested.connect(
            lambda subcommand, e=editor: self._relay(e, self.pio_requested, subcommand))
```

- [ ] **Step 4: `StateMachine`'e komutu tanıt**

`core/state_machine.py` — en üste import ekle:

```python
from core.search import parse_replace_args
from embedded import pio_cli
```

`KNOWN_COMMANDS`'ın sonuna `"pio"` ekle:

```python
    KNOWN_COMMANDS = (
        "d", "w", "b", "y", "p", "wq", "q", "qa", "wqa", "ts", "cd",
        "term", "termnew", "tabnew", "tabclose", "tabnext", "tabprev",
        "find", "replace", "openfile", "sym", "reload", "pio",
    )
```

`COMMAND_DESCRIPTIONS`'a satır ekle:

```python
        "pio": "PlatformIO (:pio build|upload|monitor|clean|env)",
```

- [ ] **Step 5: Tamamlamayı ekle**

`_matches_for` içinde, `openfile` dalının hemen altına:

```python
        if prefix.startswith("pio "):
            return self._pio_matches_for(prefix[4:])
```

ve `_path_matches_for`'un altına yeni metot:

```python
    def _pio_matches_for(self, fragment):
        """ ':pio <alt-komut>' tamamlaması. Alt komut listesinin tek kaynağı
        embedded/pio_cli.SUBCOMMANDS — komut satırı ile gerçekten çalışan
        komutlar ayrışmasın diye. """
        fragment = fragment.strip()
        return [(f"pio {ad}", aciklama)
                for ad, aciklama in sorted(pio_cli.SUBCOMMANDS.items())
                if ad.startswith(fragment)]
```

- [ ] **Step 6: Komutu çalıştır**

`_execute_command_line` içinde, `openfile` dalının altına:

```python
        elif text == "pio" or text.startswith("pio "):
            self._run_pio(text[3:].strip())
```

ve `_delete_current_line`'ın yanına (KOMUT FONKSİYONLARI bölümü):

```python
    def _run_pio(self, subcommand):
        """ ':pio <alt-komut>' — asıl iş IDEWindow'da (proje kökü, pio'nun
        yeri, terminal sekmesi); burada yalnız alt komut doğrulanıp sinyal
        yayılıyor. """
        if subcommand in pio_cli.SUBCOMMANDS:
            self.editor.pio_requested.emit(subcommand)
        else:
            print(f"Kullanım: :pio {'|'.join(pio_cli.SUBCOMMANDS)}")
```

- [ ] **Step 7: Testlerin geçtiğini gör**

Çalıştır: `.venv/bin/python -m pytest tests/test_state_machine.py tests/test_welcome_page.py -q`
Beklenen: hepsi passed (6 yeni + 1 yeni + mevcutlar).

- [ ] **Step 8: Commit**

```bash
git add core/state_machine.py ui/components/code_editor.py \
        ui/components/welcome_page.py ui/components/editor_tabs.py \
        tests/test_state_machine.py tests/test_welcome_page.py
git commit -m "feat: ':pio <alt-komut>' komutu ve tamamlaması"
```

---

## Task 6: `IDEWindow` orkestrasyonu, ortam paleti ve statusline rozeti

**Files:**
- Modify: `ui/components/bottom_panel.py` (`StatusLine`: `env_label`, `set_env`)
- Modify: `ui/main_window.py` (import, `__init__`, `_connect_modal_host`,
  `_setup_ui` sonu, `_on_palette_accepted`, `_change_directory`, üç yeni metot)
- Test: `tests/test_pio_window.py`

**Interfaces:**
- Consumes: Task 1 (`pio_project.find_project_root`, `read_project`),
  Task 2 (`pio_cli.find_executable`, `build_argv`, `SUBCOMMANDS`),
  Task 4 (`terminal_panel.run_command`), Task 5 (`pio_requested`).
- Produces:
  - `IDEWindow.pio_env: str | None`
  - `IDEWindow._on_pio_requested(subcommand: str)`
  - `IDEWindow._refresh_pio_badge()`
  - `StatusLine.set_env(text: str | None)` ve `StatusLine.env_label`
  - Palet için yeni `mode="env"`; payload = ortam adı (str)

- [ ] **Step 1: Testleri yaz**

`tests/test_pio_window.py`:

```python
""" ':pio ...' akışı uçtan uca: proje kökü, argv, ortam seçimi ve statusline
rozeti. Gerçek 'pio' süreci başlatılmaz — run_command yakalanır. """
import os

import pytest

from embedded import pio_cli

INI = """\
[platformio]
default_envs = esp32dev

[env:esp32dev]
platform = espressif32

[env:native]
platform = native
"""


@pytest.fixture
def proje(tmp_path, monkeypatch):
    """ Geçici bir PlatformIO projesi ve içine geçmiş bir çalışma dizini.
    'pencere' fixture'ından ÖNCE istenmeli: IDEWindow açılışta rozeti
    kuruyor. """
    (tmp_path / "platformio.ini").write_text(INI, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def kayit(pencere, monkeypatch):
    """ Terminal panelinin run_command'ını yakalar. """
    cagrilar = []
    monkeypatch.setattr(
        pencere.terminal_panel, "run_command",
        lambda argv, title, cwd=None: cagrilar.append((argv, title, cwd)))
    return cagrilar


@pytest.fixture
def sahte_pio(monkeypatch):
    monkeypatch.setattr(pio_cli, "find_executable", lambda: "/kurulum/pio")


def test_proje_yoksa_sekme_acilmaz(tmp_path, monkeypatch, pencere, kayit, sahte_pio):
    monkeypatch.chdir(tmp_path)          # platformio.ini yok
    pencere._on_pio_requested("build")
    assert kayit == []


def test_build_argv_ve_calisma_dizini(proje, pencere, kayit, sahte_pio):
    pencere._on_pio_requested("build")
    argv, baslik, cwd = kayit[0]
    assert argv == ["/kurulum/pio", "run"]
    assert baslik == "pio build"
    assert os.path.realpath(cwd) == os.path.realpath(str(proje))


def test_pio_kurulu_degilse_sekme_acilmaz(proje, pencere, kayit, monkeypatch):
    monkeypatch.setattr(pio_cli, "find_executable", lambda: None)
    pencere._on_pio_requested("upload")
    assert kayit == []


def test_secili_ortam_argva_gecer(proje, pencere, kayit, sahte_pio):
    pencere.pio_env = "native"
    pencere._on_pio_requested("upload")
    argv, _baslik, _cwd = kayit[0]
    assert argv == ["/kurulum/pio", "run", "-t", "upload", "-e", "native"]


def test_editorden_gelen_sinyal_pencereye_ulasir(proje, pencere, kayit, sahte_pio):
    """ ModalEditor -> EditorTabs._relay -> IDEWindow boru hattı. """
    pencere.editor.pio_requested.emit("clean")
    argv, baslik, _cwd = kayit[0]
    assert argv == ["/kurulum/pio", "run", "-t", "clean"]
    assert baslik == "pio clean"


def test_env_paleti_ortamlari_listeler_ve_secimi_uygular(proje, pencere, kayit, sahte_pio):
    pencere._on_pio_requested("env")
    assert pencere.command_palette.mode == "env"
    assert kayit == []                      # 'env' süreç başlatmaz

    pencere._on_palette_accepted("native")
    assert pencere.pio_env == "native"
    assert pencere.status_line.env_label.text() == "native"


def test_rozet_secim_yokken_ini_varsayilanini_parantezle_gosterir(proje, pencere):
    assert pencere.status_line.env_label.text() == "(esp32dev)"


def test_rozet_proje_yokken_bos(pencere):
    """ Depo kökünde platformio.ini yok. """
    assert pencere.status_line.env_label.text() == ""


def test_cd_secili_ortami_sifirlar(proje, pencere, tmp_path):
    pencere.pio_env = "native"
    baska = tmp_path / "alt"
    baska.mkdir()
    pencere._change_directory(str(baska))
    assert pencere.pio_env is None
```

- [ ] **Step 2: Testlerin başarısız olduğunu gör**

Çalıştır: `.venv/bin/python -m pytest tests/test_pio_window.py -q`
Beklenen: `AttributeError: 'IDEWindow' object has no attribute '_on_pio_requested'`

- [ ] **Step 3: Statusline'a ortam etiketini ekle**

`ui/components/bottom_panel.py` — `StatusLine.__init__` içinde etiketi kur ve
layout'a **dosya ile konum arasına** yerleştir:

```python
        self.mode_label = QLabel()
        self.mode_label.setObjectName("statusMode")
        self.file_label = QLabel()
        self.env_label = QLabel()
        self.position_label = QLabel()

        layout.addWidget(self.mode_label)
        layout.addWidget(self.file_label, 1)
        layout.addWidget(self.env_label)
        layout.addWidget(self.position_label)

        self.set_mode("NORMAL")
        self.set_file("[No Name]")
        self.set_env(None)
        self.set_position(1, 1)
```

ve `set_file`'ın altına:

```python
    def set_env(self, text):
        """ PlatformIO ortamı. Parantezli metin ('(esp32dev)') 'ben seçmedim,
        pio'nun kendi varsayılanı' demek; None etiketi boşaltır.

        Bilinçli olarak setStyleSheet YOK: rengi/fontu stylesheet'e kopyalayan
        her çağrı ':reload'da elle tazelenmek zorunda kalıyor (bkz. set_mode ve
        IDEWindow.apply_settings). Düz metin bu tuzağı hiç doğurmuyor. """
        self.env_label.setText(text or "")
```

- [ ] **Step 4: `IDEWindow`'a durumu ve bağlantıyı ekle**

`ui/main_window.py` — import bloğuna:

```python
from embedded import pio_cli, pio_project
```

`__init__` içinde, `self._setup_ui()` çağrısından **önce**:

```python
        # ':pio env' ile seçilen ortam; ':cd' başka projeye geçince sıfırlanır.
        # _setup_ui rozeti kurduğu için bu satır ondan önce gelmeli.
        self.pio_env = None
```

`_connect_modal_host` tablosuna satır:

```python
            "pio_requested": self._on_pio_requested,
```

`_setup_ui`'nin en sonuna (sidebar bağlantısının altına):

```python
        # PlatformIO rozeti açılışta da doğru olsun (CWD zaten bir proje
        # olabilir).
        self._refresh_pio_badge()
```

- [ ] **Step 5: `:pio` işleyicisini yaz**

`open_symbol_search`'ün altına üç metot:

```python
    def _on_pio_requested(self, subcommand):
        """ ':pio <alt-komut>' — proje kökünü ve pio'yu bulup komutu terminal
        panelinde kendi sekmesinde çalıştırır. Hatalar konsola tek satır
        yazılır; hiçbiri sekme açmaz. """
        root = pio_project.find_project_root(os.getcwd())
        if root is None:
            print("PlatformIO projesi bulunamadı (platformio.ini yok).")
            return

        if subcommand == "env":
            self._open_env_palette(root)
            return

        executable = pio_cli.find_executable()
        if executable is None:
            print("PlatformIO bulunamadı (kurulum: pip install platformio).")
            return

        argv = pio_cli.build_argv(subcommand, executable, env=self.pio_env)
        if argv is None:
            print(f"Bilinmeyen PlatformIO alt komutu: {subcommand}")
            return

        self.terminal_panel.run_command(argv, f"pio {subcommand}", cwd=root)

    def _open_env_palette(self, root):
        """ ':pio env' — platformio.ini'deki ortamları telescope paletinde
        listeler; seçim self.pio_env olur (bkz. _on_palette_accepted). """
        info, warnings = pio_project.read_project(root)
        for warning in warnings:
            print(warning)

        environments = info["environments"]
        if not environments:
            print("Bu projede tanımlı ortam yok (platformio.ini'de [env:...] yok).")
            return

        self.command_palette.open_with(
            f"Ortam seç ({os.path.basename(root)})",
            [(name, name) for name in environments], mode="env")
        self._show_palette()

    def _refresh_pio_badge(self):
        """ Statusline'daki ortam etiketi. Seçim yoksa pio'nun kendi
        varsayılanı parantez içinde gösterilir (K5: o durumda argv'ye '-e'
        eklenmiyor, kararı ini veriyor); proje yoksa etiket boşalır. """
        root = pio_project.find_project_root(os.getcwd())
        if root is None:
            self.status_line.set_env(None)
            return
        if self.pio_env:
            self.status_line.set_env(self.pio_env)
            return

        info, warnings = pio_project.read_project(root)
        for warning in warnings:
            print(warning)
        defaults = info["default_envs"]
        self.status_line.set_env(f"({defaults[0]})" if defaults else "(—)")
```

- [ ] **Step 6: Palet seçimini ve `:cd`'yi bağla**

`_on_palette_accepted` içindeki `elif mode == "symbol":` dalının altına:

```python
        elif mode == "env":
            self.pio_env = payload
            self._refresh_pio_badge()
            print(f"PlatformIO ortamı: {payload}")
```

`_change_directory`'nin sonuna (`print(f"Çalışma dizini değiştirildi: ...")`
satırının altına):

```python
        # Başka bir projeye geçmiş olabiliriz: seçili ortam artık geçerli değil.
        self.pio_env = None
        self._refresh_pio_badge()
```

- [ ] **Step 7: Testlerin geçtiğini gör**

Çalıştır: `.venv/bin/python -m pytest tests/test_pio_window.py -q`
Beklenen: 9 passed.

- [ ] **Step 8: Tüm paketi çalıştır**

Çalıştır: `.venv/bin/python -m pytest -q`
Beklenen: hepsi passed. Özellikle `tests/test_bottom_panel.py` (statusline
düzeni değişti) ve `tests/test_settings_reload.py` yeşil kalmalı.

- [ ] **Step 9: Commit**

```bash
git add ui/main_window.py ui/components/bottom_panel.py tests/test_pio_window.py
git commit -m "feat: ':pio' akışı, ortam paleti ve statusline ortam rozeti"
```

---

## Task 7: Belgeler

**Files:**
- Create: `docs/sprint/sprint-10.md`
- Modify: `docs/sprint/README.md`, `docs/Roadmap.md`, `CLAUDE.md`

**Interfaces:**
- Consumes: Task 1-6'nın tamamı.
- Produces: belge; kod arayüzü yok.

- [ ] **Step 1: Sprint kaydını yaz**

`docs/sprint/sprint-10.md`:

```markdown
# Sprint 10 — PlatformIO çalıştırma çekirdeği
**Tarih:** 01 Eyl 2026 · **Durum:** Tamamlandı · **Commit(ler):** bu sprintin
commit'lerinin kısa hash'leri (`git log --oneline` çıktısından, belge commit'i
atılırken doldurulur)

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

## Teknik notlar
- **`finished` sinyaline argüman eklenmedi.** `TerminalView` onu doğrudan
  `QWidget.update`'e bağlıyor; `int` eklenseydi Qt `update(int)` overload'ı arar
  ve terminal çizmeyi sessizce bırakırdı. Çıkış kodu ayrı `exited(int)` ile.
- **`showEvent`'in "koşmuyorsa başlat" kuralı komut sekmesinde tehlikeli.**
  `_finished` bayrağı olmadan, biten bir `pio upload` sekmesi panel `:term` ile
  gizlenip açıldığında komutu tekrar çalıştırır — gerçek karta yeniden yazar.
- **Sekme eşleştirmesi süslenmemiş başlığa bakar.** `title()` bitmiş sekmede
  `pio build ✓` döndüğü için, eşleştirme `command_title`'a bakmasa her derleme
  yeni sekme açardı.
- **`ConfigParser(interpolation=None, strict=False)`.** İnterpolasyon
  `read_string`'de değil `get()`'te çalışıyor; okuduğumuz tek değer olan
  `default_envs` `%` içeriyorsa varsayılan parser çöker.
- **PTY ölçüsü `start()`'ta kuruluyor**, bu yüzden `resize()` süreç
  koşmuyorken de `rows`/`cols`'u saklıyor ve komut sekmesi `start_now()` içinde
  önce ölçüp sonra başlıyor — yoksa `pio`'nun ilk çıktısı yanlış genişlikte
  sarmalanıyor.
- Ortam seçilmemişse argv'ye `-e` eklenmiyor: kararı `platformio.ini`'nin
  `default_envs`'i veriyor, IDE onu ezmiyor.

## Devreden
- Derleme hatasından koda atlama (Faz 4/E) — Sprint 11.
- Kendi seri monitörümüz (`embedded/serial_reader.py`, Faz 4/D) — Sprint 12.
  Bu sprintte `:pio monitor` PlatformIO'nun kendi monitörünü çalıştırıyor.
```

- [ ] **Step 2: Sprint dizinini güncelle**

`docs/sprint/README.md` — "Aktif sprint" satırını ve tabloyu güncelle:

```markdown
**Aktif sprint:** yok — son iş [Sprint 10](sprint-10.md).
```

tabloya son satır:

```markdown
| [10](sprint-10.md) | 01 Eyl 2026 | PlatformIO çalıştırma çekirdeği | Tamamlandı |
```

- [ ] **Step 3: Roadmap'i güncelle**

`docs/Roadmap.md`:

1. "Bugünkü durum" listesine yeni madde (terminal maddesinin altına):

```markdown
- **PlatformIO** — `:pio build|upload|monitor|clean` komutları gömülü
  terminalde kendi sekmesinde çalışıyor (renkli çıktı, gerçek Ctrl+C, sekme
  başlığında `✓`/`✗`); `:pio env` ile `platformio.ini`'deki ortam seçiliyor ve
  statusline'da görünüyor ([Sprint 10](sprint/sprint-10.md))
```

2. "Henüz yok" paragrafındaki `PlatformIO/seri monitör entegrasyonu` ifadesini
   şununla değiştir:

```markdown
kendi seri monitörümüz, derleme hatasından koda atlama
```

3. "Faz 4 — Gömülü hedef (PlatformIO)" bölümünde ilk üç maddeyi tamamlandı
   olarak işaretle, ikisini açık bırak:

```markdown
- **`embedded/pio_cli.py` + `embedded/pio_project.py`** — **tamamlandı**
  ([Sprint 10](sprint/sprint-10.md)): `build`, `upload`, `clean`, `monitor`
  argv'leri ve `platformio.ini` ayrıştırma. Çıktı `TerminalPanel`'de yeni bir
  sekmeye akıyor; ayrı çıktı penceresi yazılmadı.
- **Komutlar** — **tamamlandı**: `:pio build|upload|monitor|clean|env`,
  öneri listesi ve `:pio ` tamamlamasıyla.
- **Kart ve port seçimi** — **tamamlandı**: `platformio.ini` okunup ortamlar
  `:pio env` paletinde listeleniyor, seçim statusline rozetinde.
- **`embedded/serial_reader.py`** — açık (Sprint 12): kendi seri monitörümüz
  (port/baud seçimi, yeniden bağlanma). Bugün `:pio monitor` PlatformIO'nun
  monitörünü çalıştırıyor.
- **Derleme hatasından koda atlama** — açık (Sprint 11): çıktıdaki
  `dosya:satır` eşleşmelerini yakalayıp ilgili sekmede o satıra gitme.
```

4. Teknik borç tablosundaki "Boş yer tutucular" satırını değiştir:

```markdown
| Boş yer tutucular | `pio_cli.py` yazıldı ([Sprint 10](sprint/sprint-10.md)); `serial_reader.py` duruyor | Sprint 12 |
```

- [ ] **Step 4: `CLAUDE.md`'yi güncelle**

1. "Architecture" listesindeki `embedded/` maddesini değiştir:

```markdown
- **`embedded/pio_cli.py`** — pure PlatformIO CLI helpers: `find_executable()`
  (PATH, then `~/.platformio/penv/bin/pio`), the `SUBCOMMANDS` table that is the
  single source for `:pio ` completion, and `build_argv()`. It builds argv only —
  starting the process is `IDEWindow`'s job.
- **`embedded/pio_project.py`** — pure `platformio.ini` reader:
  `find_project_root()` walks up for the file, `parse_environments()` returns
  `{"environments": [...], "default_envs": [...]}`. Uses
  `ConfigParser(interpolation=None, strict=False)` — interpolation runs at
  `get()` time and a `%` in `default_envs` would otherwise raise, and real-world
  ini files repeat keys. Same contract as `core/config.py`: returns
  `(data, warnings)`, never prints, never raises.
- **`embedded/serial_reader.py`** — still an empty placeholder (Sprint 12);
  `:pio monitor` currently runs PlatformIO's own monitor in a command tab.
```

2. `core/terminal_process.py` / `terminal_panel.py` maddesine ekle:

```markdown
  `TerminalProcess` also runs a given `argv` (with an optional `cwd`) instead of
  the login shell, and reports the child's exit status on a separate
  `exited(int)` signal — deliberately separate, because `finished` is wired
  straight to `QWidget.update` and adding an argument would silently break that
  connection. `TerminalPanel.run_command(argv, title, cwd)` opens (or reuses)
  a *command tab*: `:pio build` twice refreshes one tab instead of piling up
  new ones, and a finished tab must not restart itself when the panel is
  re-shown (`_finished` guard) — for `pio upload` that would write to the board
  again.
```

3. Komut listesine (`Commands` bölümü) `:pio` ekle:

```markdown
`:pio build|upload|monitor|clean|env` (PlatformIO; output goes to a command tab
in the terminal panel, `:pio env` picks the `platformio.ini` environment shown
in the status line)
```

- [ ] **Step 5: Tüm paketi son kez çalıştır**

Çalıştır: `.venv/bin/python -m pytest -q`
Beklenen: hepsi passed.

- [ ] **Step 6: Commit**

```bash
git add docs/ CLAUDE.md
git commit -m "docs: Sprint 10 kaydı, Roadmap Faz 4 ilerlemesi ve mimari notlar"
```

---

## Bitiş kontrolü

- [ ] `.venv/bin/python -m pytest -q` — tamamı yeşil
- [ ] `python3 main.py` açılıyor, `:term` hâlâ shell açıyor, Alt+Shift ailesi çalışıyor
- [ ] Spec'teki "Elle doğrulama (gerçek kart)" listesindeki 10 madde gerçek bir
      PlatformIO projesinde tek tek deneniyor
