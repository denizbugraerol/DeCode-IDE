# Ayar Dosyası (Faz 3) — Uygulama Planı

> **Ajan işçiler için:** ZORUNLU ALT BECERİ: Bu planı görev görev uygulamak için
> `superpowers:subagent-driven-development` (önerilen) ya da
> `superpowers:executing-plans` kullanın. Adımlar takip için checkbox (`- [ ]`)
> sözdizimiyle yazılmıştır.

**Hedef:** Bugün koda gömülü olan tema, font, sekme genişliği, satır numarası ve
terminal yüksekliğini `~/.config/decode/config.toml`'dan okunabilir hale
getirmek; `:reload` ile uygulamayı kapatmadan uygulamak.

**Mimari:** İki yeni modül. `core/config.py` TOML'u okur, varsayılanların üstüne
bindirir ve doğrular — Qt'ye hiç dokunmaz, doğrudan test edilir. `ui/theme.py`
adlandırılmış bir renk paleti tutar ve Qt stylesheet'ini ondan üretir; bugün altı
dosyaya dağılmış 17 renk (79 kullanım) oraya çekilir. Bileşenler rengi **boyama
anında** `theme.color(...)` ile okur, böylece `:reload` sonrası yeniden çizilen
her şey yeni paletle gelir. `IDEWindow` ayarları okuyup `apply_settings()` ile
dağıtan tek yer olarak kalır.

**Teknoloji:** Python 3.14 (`tomllib` standart kütüphanede, salt okunur — tam
ihtiyacımız kadar), PyQt6, pyte. **Yeni bağımlılık yok.**

**Spec:** `docs/Roadmap.md` → "Faz 3 — Editör olgunluğu", *Ayar dosyası* maddesi:
"`~/.config/decode/config.toml` gibi: tema, font, sekme genişliği, satır numarası
açık/kapalı — bugün hepsi kodda sabit."

---

## Context — bu iş neden yapılıyor

Roadmap'in teknik borç tablosunda "Tema kodda sabit — renkler
`IDEWindow._apply_theme` içinde string olarak" satırı Faz 3'ten beri duruyor.
Bugünkü durum tablodakinden de kötü: renkler yalnız `_apply_theme`'de değil, altı
dosyaya dağılmış durumda — sözdizimi renklendiricisinde, gutter'da, statusline
rozetlerinde, öneri kutusunda ve terminalin ANSI eşlemesinde. Tek bir rengi
değiştirmek altı dosyaya dokunmak demek.

Font ailesi ve boyutu stylesheet'e gömülü; sekme genişliği hiç ayarlanmamış
(Qt'nin 80 piksellik varsayılanı yürürlükte); satır numarası kapatılamıyor;
terminal paneli 9 satıra sabit.

Bu plan bitince kullanıcı kendi paletini, fontunu ve editör davranışını bir
dosyadan yönetebilir; `:reload` ile de değişikliği açık sekmeleri ve terminal
oturumunu kaybetmeden görebilir.

**Bu plan Faz 3'ün yalnızca bu maddesini kapsar.** Vim hareket/düzenleme
komutları, VISUAL mod ve oturum geri yükleme kapsam dışı.

---

## Global Constraints

Her görevin gereksinimleri bu bölümü kapsar.

- **Bağımlılık:** `requirements.txt` değişmez (PyQt6 + pyte). TOML için
  `tomllib` (standart kütüphane, Python 3.11+).
- **Dil:** Yorum, docstring, commit mesajı ve `docs/` Türkçe (depo geleneği).
- **Katman:** `core/` Qt'ye ve `ui/`'ye bağımlı olmaz. `core/config.py` renk
  *token adlarını* bilmez; hangi tokenların var olduğu `ui/theme.py`'nin
  bilgisidir. `config` yalnız `#rrggbb` biçimini doğrular.
- **Varsayılanlar bugünkü görünümü birebir korur.** Ayar dosyası yokken
  uygulama şu ana kadarki hâliyle açılmalı: aynı renkler, aynı font boyutları
  (15/16/14/13/12/11/28), 9 satırlık terminal. Tek bilinçli değişiklik: sekme
  genişliği artık 4 karakter (bugün Qt'nin 80 piksellik varsayılanı).
- **Ev dizinine yazma yalnız `main.py`'den.** `IDEWindow` oluşturmak asla dosya
  yaratmaz ve **kullanıcının gerçek ayar dosyasını okumaz** — aksi halde testler
  geliştiricinin kendi yapılandırmasına bağımlı olur. `IDEWindow(settings=...)`
  parametresi bunun içindir.
- **Kısayol kararı (kullanıcı, bu turda):** Navigasyon Vim'den ayrılıp **ok
  tuşlarında kalır.** `h/j/k/l`, `w/b`, `gg`/`G` gibi harf tabanlı hareket
  komutları **uygulanmayacak**; Roadmap'in Faz 3 maddesi buna göre düzeltilecek
  (Görev 8). Bugünkü davranış zaten budur ve doğrudur — `handle_normal_mode`
  içindeki `nav_keys` denetimi değiştiriciden bağımsız olarak önce baktığı için
  Ok, Home/End, PageUp/Down çalışır, Shift+Ok seçer, Ctrl+Ok kelime atlar.
  **Bu karar için kod değişikliği yoktur**, yalnız belge.
- **Ayar dosyası bozuksa uygulama açılır.** Her hatalı/bilinmeyen anahtar bir
  uyarı metnine dönüşür, ilgili ayar varsayılanda kalır; uyarılar konsola
  basılır (deponun mevcut hata bildirme biçimi).
- **Renk sözleşmesi:** yalnız `#rrggbb`. Kısa biçim, isimli renk, alfa yok.

---

## Ayar dosyasının şekli

`~/.config/decode/config.toml` (`$XDG_CONFIG_HOME` varsa ona saygı duyulur).
Dosya yoksa `main.py` ilk açılışta bu şablonu yazar.

```toml
# DeCode IDE ayarları
# Silinen ya da yorumlanan satırlar varsayılana döner.

[editor]
font_family  = "Fira Code"
font_size    = 15      # editör ve terminal; arayüz boyutları buna göre kayar
tab_width    = 4       # karakter
expand_tabs  = false   # true ise Tab tuşu boşluk yazar
line_numbers = true

[terminal]
rows = 9               # panelin yüksekliği (satır)

[colors]
# Tokyo Night. Yalnız değiştirmek istediğin tokeni yaz.
# bg = "#1a1b26"        bg_dark = "#16161e"     panel = "#1f2335"
# border = "#414868"    fg = "#c0caf5"          fg_dim = "#565f89"
# fg_bright = "#ffffff" gutter = "#3b4261"      selection = "#283457"
# search = "#3d59a1"    blue = "#7aa2f7"        green = "#9ece6a"
# orange = "#ff9e64"    yellow = "#e0af68"      purple = "#bb9af7"
# cyan = "#7dcfff"      red = "#f7768e"
```

---

## Dosya yapısı

**Yeni:**

| Dosya | Sorumluluk |
|---|---|
| `core/config.py` | TOML okuma, varsayılanlarla birleştirme, doğrulama, şablon, XDG yolu. Qt yok. |
| `ui/theme.py` | 17 tokenlık palet, palet ezme, stylesheet üreteci, font boyutu sapmaları |

**Değişecek:**

| Dosya | Ne olacak |
|---|---|
| `ui/main_window.py` | `_apply_theme`'deki QSS `ui/theme.py`'ye taşınır; `settings` parametresi, `apply_settings()`, `reload_settings()` |
| `ui/components/syntax_highlighter.py` | 6 renk temadan; `:reload` için kurallar yeniden kurulabilir olacak |
| `ui/components/code_editor.py` | Gutter/arama renkleri temadan; font, `tab_width`, `expand_tabs`, `line_numbers` |
| `ui/components/bottom_panel.py` | `MODE_COLORS` temadan okunacak |
| `ui/components/floating_list.py` | Satır stilleri temadan okunacak |
| `ui/components/terminal_panel.py` | ANSI eşlemesi temadan; `ROWS` sabiti ayardan gelen örnek alanına dönüşecek |
| `core/state_machine.py` | `:reload` komutu |
| `ui/components/welcome_page.py` | `:reload` sinyali + `available_commands` |
| `ui/components/editor_tabs.py` | `:reload` sinyalinin aktarımı |
| `main.py` | Açılışta ayar dosyasını oluştur, oku, `IDEWindow`'a ver |
| `tests/conftest.py` | `pencere` fixture'ı varsayılan ayarları verir (ev dizini okunmasın) |

**Test:** `tests/test_config.py`, `tests/test_theme.py`,
`tests/test_no_hardcoded_colors.py`, `tests/test_editor_settings.py`,
`tests/test_settings_reload.py`.

---

## Görev 1: `core/config.py` — ayar yükleyici

**Files:**
- Create: `core/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces:
  - `DEFAULTS: dict` ve `default_settings() -> dict` (derin kopya)
  - `config_path() -> str`
  - `parse(text: str) -> tuple[dict, list[str]]` — (ayarlar, uyarılar)
  - `load(path: str | None = None) -> tuple[dict, list[str]]`
  - `ensure_exists(path: str | None = None) -> bool` — yazdıysa True
  - `TEMPLATE: str`

- [ ] **Adım 1: Düşen testleri yaz**

`tests/test_config.py`:

```python
""" Ayar yükleyicinin sözleşmesi: varsayılanlar, birleştirme, doğrulama.
Qt gerektirmez. """
import core.config as config


def test_dosya_yoksa_varsayilanlar_ve_uyari_yok(tmp_path):
    ayarlar, uyarilar = config.load(str(tmp_path / "yok.toml"))
    assert ayarlar == config.DEFAULTS
    assert uyarilar == []


def test_default_settings_derin_kopya_verir():
    birinci = config.default_settings()
    birinci["editor"]["font_size"] = 99
    assert config.default_settings()["editor"]["font_size"] == 15


def test_yalniz_verilen_anahtar_ezilir():
    ayarlar, uyarilar = config.parse('[editor]\nfont_size = 20\n')
    assert ayarlar["editor"]["font_size"] == 20
    assert ayarlar["editor"]["font_family"] == "Fira Code"   # dokunulmadı
    assert ayarlar["terminal"]["rows"] == 9
    assert uyarilar == []


def test_bozuk_toml_varsayilana_duser():
    ayarlar, uyarilar = config.parse("[editor\nfont_size = ")
    assert ayarlar == config.DEFAULTS
    assert len(uyarilar) == 1
    assert "okunamadı" in uyarilar[0]


def test_yanlis_tur_varsayilanda_birakir():
    ayarlar, uyarilar = config.parse('[editor]\nfont_size = "kocaman"\n')
    assert ayarlar["editor"]["font_size"] == 15
    assert any("font_size" in u for u in uyarilar)


def test_bool_font_boyutu_sayilmaz():
    """ Python'da bool, int'in alt sınıfı; isinstance(True, int) True döner.
    'font_size = true' geçerli sayılmamalı. """
    ayarlar, _u = config.parse("[editor]\nfont_size = true\n")
    assert ayarlar["editor"]["font_size"] == 15


def test_aralik_disi_deger_varsayilanda_birakir():
    ayarlar, uyarilar = config.parse("[editor]\nfont_size = 500\n")
    assert ayarlar["editor"]["font_size"] == 15
    assert any("6-72" in u for u in uyarilar)


def test_bos_font_ailesi_reddedilir():
    ayarlar, _u = config.parse('[editor]\nfont_family = "   "\n')
    assert ayarlar["editor"]["font_family"] == "Fira Code"


def test_bilinmeyen_anahtar_ve_bolum_uyarir():
    ayarlar, uyarilar = config.parse("[editor]\nzoom = 3\n\n[uzay]\nx = 1\n")
    assert ayarlar["editor"] == config.DEFAULTS["editor"]
    assert any("editor.zoom" in u for u in uyarilar)
    assert any("[uzay]" in u for u in uyarilar)


def test_renkler_hex_bicimini_zorunlu_kilar():
    ayarlar, uyarilar = config.parse(
        '[colors]\nbg = "#11111b"\nfg = "kirmizi"\nblue = "#abc"\n')
    assert ayarlar["colors"] == {"bg": "#11111b"}
    assert any("colors.fg" in u for u in uyarilar)
    assert any("colors.blue" in u for u in uyarilar)


def test_config_path_xdg_degiskenine_saygi_duyar(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/xdg")
    assert config.config_path() == "/tmp/xdg/decode/config.toml"


def test_config_path_xdg_yoksa_ev_dizinini_kullanir(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", "/home/deneme")
    assert config.config_path() == "/home/deneme/.config/decode/config.toml"


def test_sablon_varsayilanlarin_aynisini_uretir():
    """ Şablonu olduğu gibi geri okumak varsayılanları vermeli: kullanıcı
    hiçbir şeye dokunmadığında davranış değişmemeli. """
    ayarlar, uyarilar = config.parse(config.TEMPLATE)
    assert ayarlar == config.DEFAULTS
    assert uyarilar == []


def test_ensure_exists_yoksa_yazar_varsa_dokunmaz(tmp_path):
    yol = str(tmp_path / "alt" / "config.toml")
    assert config.ensure_exists(yol) is True
    assert config.ensure_exists(yol) is False

    with open(yol, "a", encoding="utf-8") as dosya:
        dosya.write("\n# kullanıcı notu\n")
    config.ensure_exists(yol)
    with open(yol, encoding="utf-8") as dosya:
        assert "# kullanıcı notu" in dosya.read()
```

- [ ] **Adım 2: Çalıştır — düşmeli**

```bash
.venv/bin/python -m pytest tests/test_config.py -q
```

Beklenen: `ModuleNotFoundError: No module named 'core.config'`.

- [ ] **Adım 3: Uygula**

`core/config.py`:

```python
""" Ayar dosyası: ~/.config/decode/config.toml okunur, varsayılanların üstüne
bindirilir ve doğrulanır.

Qt'ye bağımlı değil — tamamen saf, doğrudan test edilebilir. Bozuk ya da
tanınmayan anahtarlar sessizce yutulmuyor: her biri bir uyarı metnine dönüşüyor
ve ilgili ayar varsayılanda kalıyor. Renk *token adlarının* geçerliliğine burada
bakılmaz (o temanın bilgisi, bkz. ui/theme.build_palette); burada yalnız
'#rrggbb' biçimi denetlenir. """
import copy
import os
import re
import tomllib

APP_NAME = "decode"
FILE_NAME = "config.toml"

DEFAULTS = {
    "editor": {
        "font_family": "Fira Code",
        "font_size": 15,
        "tab_width": 4,
        "expand_tabs": False,
        "line_numbers": True,
    },
    "terminal": {
        "rows": 9,
    },
    # ui/theme.DEFAULT_PALETTE üzerine bindirilecek tokenlar; boş = varsayılan tema
    "colors": {},
}

# (bölüm, anahtar) -> (en az, en çok). Yalnız sayısal alanlar için.
_LIMITS = {
    ("editor", "font_size"): (6, 72),
    ("editor", "tab_width"): (1, 16),
    ("terminal", "rows"): (1, 50),
}

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

TEMPLATE = '''\
# DeCode IDE ayarları
# Silinen ya da yorumlanan satırlar varsayılana döner.

[editor]
font_family  = "Fira Code"
font_size    = 15      # editör ve terminal; arayüz boyutları buna göre kayar
tab_width    = 4       # karakter
expand_tabs  = false   # true ise Tab tuşu boşluk yazar
line_numbers = true

[terminal]
rows = 9               # panelin yüksekliği (satır)

[colors]
# Tokyo Night. Yalnız değiştirmek istediğin tokeni yaz.
# bg = "#1a1b26"        bg_dark = "#16161e"     panel = "#1f2335"
# border = "#414868"    fg = "#c0caf5"          fg_dim = "#565f89"
# fg_bright = "#ffffff" gutter = "#3b4261"      selection = "#283457"
# search = "#3d59a1"    blue = "#7aa2f7"        green = "#9ece6a"
# orange = "#ff9e64"    yellow = "#e0af68"      purple = "#bb9af7"
# cyan = "#7dcfff"      red = "#f7768e"
'''


def default_settings():
    """ Varsayılanların derin kopyası — çağıran üstünde oynayabilsin. """
    return copy.deepcopy(DEFAULTS)


def config_path():
    """ XDG'ye saygılı ayar dosyası yolu. """
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, APP_NAME, FILE_NAME)


def parse(text):
    """ TOML metnini ayrıştırıp varsayılanlarla birleştirir ve doğrular.
    (ayarlar, uyarılar) döndürür. Ayrıştırma hatası tüm dosyayı düşürür —
    yarım uygulanmış bir ayar dosyasından kötüsü yok. """
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        return default_settings(), [f"Ayar dosyası okunamadı, varsayılanlar kullanılıyor: {error}"]
    return _merge_and_validate(raw)


def load(path=None):
    """ Dosyadan okur. Dosya yoksa varsayılanlar döner ve bu bir hata değildir
    (uyarı üretilmez). """
    path = path or config_path()
    try:
        with open(path, "r", encoding="utf-8") as file:
            text = file.read()
    except FileNotFoundError:
        return default_settings(), []
    except OSError as error:
        return default_settings(), [f"Ayar dosyası açılamadı: {error}"]
    return parse(text)


def ensure_exists(path=None):
    """ Dosya yoksa yorumlu şablonu yazar; yazdıysa True döner. Var olan dosyaya
    asla dokunmaz.

    Yalnızca main.py çağırır: bir IDEWindow oluşturmak kullanıcının ev dizinine
    dosya yazmamalı (testler de öyle). """
    path = path or config_path()
    if os.path.exists(path):
        return False

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            file.write(TEMPLATE)
    except OSError as error:
        print(f"Ayar dosyası oluşturulamadı: {error}")
        return False
    return True


# --- İç işler ---

def _merge_and_validate(raw):
    settings = default_settings()
    warnings = []

    for section, values in raw.items():
        if section not in settings:
            warnings.append(f"Bilinmeyen ayar bölümü yok sayıldı: [{section}]")
            continue
        if not isinstance(values, dict):
            warnings.append(f"[{section}] bir tablo olmalı; yok sayıldı.")
            continue

        if section == "colors":
            settings["colors"], color_warnings = _validated_colors(values)
            warnings.extend(color_warnings)
            continue

        for key, value in values.items():
            if key not in settings[section]:
                warnings.append(f"Bilinmeyen ayar yok sayıldı: {section}.{key}")
                continue
            clean, warning = _validated(section, key, value, settings[section][key])
            settings[section][key] = clean
            if warning:
                warnings.append(warning)

    return settings, warnings


def _validated(section, key, value, default):
    """ Türü ve (varsa) aralığı denetler; uymuyorsa varsayılanı ve bir uyarı
    döndürür.

    bool'un int alt sınıfı olduğuna dikkat: 'font_size = true' isinstance
    denetimini geçer, o yüzden ayrıca eleniyor. """
    expected = type(default)

    if expected is bool:
        if not isinstance(value, bool):
            return default, f"{section}.{key} true/false olmalı; varsayılan kullanıldı ({default})."
        return value, None

    if isinstance(value, bool) or not isinstance(value, expected):
        return default, f"{section}.{key} {expected.__name__} olmalı; varsayılan kullanıldı ({default})."

    if expected is str and not value.strip():
        return default, f"{section}.{key} boş olamaz; varsayılan kullanıldı ({default})."

    limits = _LIMITS.get((section, key))
    if limits is not None:
        low, high = limits
        if not low <= value <= high:
            return default, f"{section}.{key} {low}-{high} arasında olmalı; varsayılan kullanıldı ({default})."

    return value, None


def _validated_colors(values):
    """ Renk değerlerinin '#rrggbb' biçiminde olduğunu doğrular. Token adının
    geçerliliğine ui/theme.build_palette bakar: hangi tokenların var olduğu
    temanın bilgisi, ayar dosyasının değil. """
    colors = {}
    warnings = []
    for name, value in values.items():
        if isinstance(value, str) and _HEX.match(value):
            colors[name] = value
        else:
            warnings.append(f"colors.{name} '#rrggbb' biçiminde olmalı; yok sayıldı.")
    return colors, warnings
```

- [ ] **Adım 4: Çalıştır — geçmeli**

```bash
.venv/bin/python -m pytest tests/test_config.py -q
```

- [ ] **Adım 5: Commit**

```bash
git add core/config.py tests/test_config.py
git commit -m "feat: ayar dosyası yükleyicisi (core/config)"
```

---

## Görev 2: `ui/theme.py` — palet ve stylesheet üreteci

Bu görevde yalnız `IDEWindow._apply_theme`'deki QSS taşınır ve parametrik hale
gelir. Diğer bileşenlerdeki renkler Görev 3'te gelecek.

**Files:**
- Create: `ui/theme.py`
- Modify: `ui/main_window.py:417-557` (`_apply_theme`)
- Test: `tests/test_theme.py`

**Interfaces:**
- Consumes: `core.config` (yalnız çağıran taraf; theme config'i import etmez)
- Produces:
  - `DEFAULT_PALETTE: dict[str, str]` — 17 token
  - `FONT_SIZE_OFFSETS: dict[str, int]`
  - `build_palette(overrides: dict) -> tuple[dict, list[str]]`
  - `color(token: str) -> str`, `palette() -> dict`, `set_palette(dict) -> None`
  - `stylesheet(palette_map: dict, font_family: str, font_size: int) -> str`

- [ ] **Adım 1: Düşen testleri yaz**

`tests/test_theme.py`:

```python
""" Palet ve stylesheet üretecinin sözleşmesi. Qt gerektirmez. """
import ui.theme as theme


def test_varsayilan_palet_tokyo_night():
    assert theme.DEFAULT_PALETTE["bg"] == "#1a1b26"
    assert theme.DEFAULT_PALETTE["fg"] == "#c0caf5"
    assert len(theme.DEFAULT_PALETTE) == 17


def test_build_palette_yalniz_verileni_ezer():
    palet, uyarilar = theme.build_palette({"bg": "#11111b"})
    assert palet["bg"] == "#11111b"
    assert palet["fg"] == theme.DEFAULT_PALETTE["fg"]
    assert uyarilar == []


def test_build_palette_bilinmeyen_tokeni_uyarir():
    palet, uyarilar = theme.build_palette({"pembe": "#ff00ff"})
    assert "pembe" not in palet
    assert any("pembe" in u for u in uyarilar)


def test_build_palette_varsayilani_bozmaz():
    theme.build_palette({"bg": "#000000"})
    assert theme.DEFAULT_PALETTE["bg"] == "#1a1b26"


def test_set_palette_ve_color():
    try:
        theme.set_palette(theme.build_palette({"blue": "#89b4fa"})[0])
        assert theme.color("blue") == "#89b4fa"
    finally:
        theme.set_palette(dict(theme.DEFAULT_PALETTE))


def test_stylesheet_paletteki_rengi_kullanir():
    palet, _u = theme.build_palette({"bg": "#11111b"})
    qss = theme.stylesheet(palet, "Fira Code", 15)
    assert "#11111b" in qss
    assert "#1a1b26" not in qss          # eski zemin hiç kalmamalı


def test_stylesheet_font_ailesini_ve_boyutlarini_yerlestirir():
    qss = theme.stylesheet(dict(theme.DEFAULT_PALETTE), "JetBrains Mono", 15)
    assert "'JetBrains Mono'" in qss
    # Varsayılan 15 bugünkü boyutları birebir üretmeli
    for boyut in ("15px", "16px", "14px", "13px", "12px", "11px", "28px"):
        assert boyut in qss


def test_stylesheet_boyutlar_font_size_ile_kayar():
    qss = theme.stylesheet(dict(theme.DEFAULT_PALETTE), "Fira Code", 20)
    assert "font-size: 20px" in qss     # editör
    assert "font-size: 21px" in qss     # komut satırı (+1)
    assert "font-size: 16px" in qss     # statusline (-4)


def test_stylesheet_eksik_token_hata_verir():
    """ Şablonda kullanılıp palette olmayan bir token sessizce geçmemeli. """
    import pytest
    eksik = dict(theme.DEFAULT_PALETTE)
    del eksik["bg"]
    with pytest.raises(KeyError):
        theme.stylesheet(eksik, "Fira Code", 15)
```

- [ ] **Adım 2: Çalıştır — düşmeli**

```bash
.venv/bin/python -m pytest tests/test_theme.py -q
```

- [ ] **Adım 3: `ui/theme.py`'yi yaz**

```python
""" Tema: adlandırılmış renk paleti ve ondan üretilen Qt stylesheet'i.

Renkler tek yerde durur. Bileşenler rengi BOYAMA ANINDA theme.color(...) ile
okur; böylece ':reload' paleti değiştirdiğinde yeniden çizilen her şey yeni
renklerle gelir ve paleti beş ayrı yapıcıya elden geçirmek gerekmez.

Geçerli palet süreç genelinde tektir — uygulamanın teması gerçekten global bir
şey. set_palette onu değiştiren tek kapıdır. """
from string import Template

# Tokyo Night. Bugün altı dosyaya dağılmış 17 rengin tamamı.
DEFAULT_PALETTE = {
    "bg":        "#1a1b26",   # ana zemin, editör
    "bg_dark":   "#16161e",   # sidebar, gutter, terminal paneli, sekme çubuğu
    "panel":     "#1f2335",   # statusline, komut kutusu, öneri kutusu, hover
    "border":    "#414868",   # kenarlıklar, kaydırma tutamağı
    "fg":        "#c0caf5",   # ana metin
    "fg_dim":    "#565f89",   # sönük metin, yorumlar, pasif sekme
    "fg_bright": "#ffffff",   # seçili satır ve arama vurgusu metni
    "gutter":    "#3b4261",   # pasif satır numarası
    "selection": "#283457",   # seçili öneri satırı, ağaç seçimi
    "search":    "#3d59a1",   # arama eşleşmesi zemini
    "blue":      "#7aa2f7",   # NORMAL rozeti, seçili sekme, vurgu
    "green":     "#9ece6a",   # INSERT rozeti, dizeler
    "orange":    "#ff9e64",   # COMMAND rozeti, sayılar
    "yellow":    "#e0af68",   # dekoratörler
    "purple":    "#bb9af7",   # anahtar sözcükler
    "cyan":      "#7dcfff",   # Python builtin'leri
    "red":       "#f7768e",   # terminal kırmızısı
}

# Arayüz font boyutları editör boyutuna göre sapma olarak tutulur. Varsayılan
# 15 ile bugünkü değerleri birebir üretir: 16, 15, 14, 13, 12, 11, 28.
FONT_SIZE_OFFSETS = {
    "command_line": 1,
    "editor": 0,
    "sidebar": -1,
    "row": -2,
    "tab": -3,
    "status": -4,
    "welcome_title": 13,
}

_current = dict(DEFAULT_PALETTE)


def color(token):
    """ Geçerli paletten bir renk. Bileşenler bunu boyama anında çağırır. """
    return _current[token]


def palette():
    return dict(_current)


def set_palette(new_palette):
    _current.clear()
    _current.update(new_palette)


def build_palette(overrides):
    """ Varsayılan paletin üstüne ayar dosyasındaki tokenları bindirir.
    (palet, uyarılar) döndürür; tanınmayan token adı yok sayılır. """
    result = dict(DEFAULT_PALETTE)
    warnings = []
    for name, value in (overrides or {}).items():
        if name in result:
            result[name] = value
        else:
            warnings.append(f"Bilinmeyen renk yok sayıldı: colors.{name}")
    return result, warnings


def stylesheet(palette_map, font_family, font_size):
    """ Ana pencerenin QSS'ini üretir. string.Template kullanıyoruz çünkü QSS
    süslü parantez dolu; str.format orada boğulur. Şablonda geçip palette
    olmayan bir token KeyError verir — yazım hatası sessizce geçmesin. """
    sizes = {f"size_{name}": font_size + offset for name, offset in FONT_SIZE_OFFSETS.items()}
    return Template(_QSS).substitute(font_family=font_family, **sizes, **palette_map)


_QSS = """
    QMainWindow { background-color: $bg; }
    QTreeView {
        background-color: $bg_dark;
        color: $fg;
        border: none;
        font-size: ${size_sidebar}px;
        outline: none;
    }
    QTreeView::item:selected { background-color: $selection; color: $fg_bright; }
    QTreeView::item:hover { background-color: $panel; }
    QPlainTextEdit {
        background-color: $bg;
        color: $fg;
        border: none;
        font-family: '$font_family', 'Consolas', monospace;
        font-size: ${size_editor}px;
        padding: 10px;
    }
    /* --- buradan sonrası mevcut stylesheet'in geri kalanının aynısı:
       QSplitter, statusLine, commandLine, floatingList, floatingListScroll
       (kaydırma çubuğu kuralları dahil), commandPalette, palettePrompt,
       welcomePage/Title/Subtitle/Hints, terminalPanel, editorTabs ve
       terminalTabBar blokları — yalnız hex ve font değerleri aşağıdaki
       tabloya göre token'a çevrilir. --- */
"""
```

`_QSS`'in tamamı `ui/main_window.py:419-555` arasındaki mevcut stylesheet
metnidir; taşırken uygulanacak kural mekanik:

| Bugünkü değer | Şablonda |
|---|---|
| `#1a1b26` | `$bg` |
| `#16161e` | `$bg_dark` |
| `#1f2335` | `$panel` |
| `#414868` | `$border` |
| `#c0caf5` | `$fg` |
| `#565f89` | `$fg_dim` |
| `#ffffff` | `$fg_bright` |
| `#283457` | `$selection` |
| `#7aa2f7` | `$blue` |
| `font-family: 'Fira Code', 'Consolas', monospace` | `font-family: '$font_family', 'Consolas', monospace` |
| `font-size: 15px` (QPlainTextEdit) | `font-size: ${size_editor}px` |
| `font-size: 16px` (commandLine) | `${size_command_line}px` |
| `font-size: 15px` (palettePrompt) | `${size_editor}px` |
| `font-size: 14px` (QTreeView) | `${size_sidebar}px` |
| `font-size: 13px` (welcomeSubtitle, welcomeHints) | `${size_row}px` |
| `font-size: 12px` (editorTabs::tab) | `${size_tab}px` |
| `font-size: 11px` (statusLine, terminalTabBar::tab) | `${size_status}px` |
| `font-size: 28px` (welcomeTitle) | `${size_welcome_title}px` |

- [ ] **Adım 4: `_apply_theme`'i ince çağrıya indir**

`ui/main_window.py` — import'a `from ui import theme`, sonra:

```python
    def _apply_theme(self):
        """ Geçerli paleti ve fontu pencereye uygular. Palet ui/theme'de;
        burada yalnız üretilen QSS takılıyor. """
        editor_settings = self.settings["editor"]
        self.setStyleSheet(theme.stylesheet(
            theme.palette(), editor_settings["font_family"], editor_settings["font_size"]))

        # Terminal '9 satır' yüksekliğini editörün QSS'ten gelen gerçek satır
        # yüksekliğiyle ölçüyor; sekme yoksa ölçecek editör de yok.
        if self.editor is not None:
            self.terminal_panel.sync_font_with_editor(self.editor)
```

> `self.settings` Görev 4'te geliyor. Bu görevde `_apply_theme` geçici olarak
> `theme.stylesheet(theme.palette(), "Fira Code", 15)` çağırsın; Görev 4 onu
> ayarlara bağlayacak.

- [ ] **Adım 5: Çalıştır**

```bash
.venv/bin/python -m pytest -q
QT_QPA_PLATFORM=offscreen python3 -c "
from PyQt6.QtWidgets import QApplication
from ui.main_window import IDEWindow
app = QApplication([]); w = IDEWindow(); w.show()
print('QSS uzunluğu:', len(w.styleSheet()))
w.terminal_panel.shutdown()"
```

Beklenen: tüm testler geçer; pencere eskisiyle aynı görünür.

- [ ] **Adım 6: Commit**

```bash
git add ui/theme.py ui/main_window.py tests/test_theme.py
git commit -m "refactor: stylesheet'i ui/theme'deki paletten üret"
```

---

## Görev 3: Renkleri bileşenlerden temaya taşı

Beş dosyada kalan 43 renk kullanımı temaya bağlanır. Kural: renk **boyama /
biçim kurma anında** okunur, modül yüklenirken sabitlenmez — yoksa `:reload`
onları değiştiremez.

**Files:**
- Modify: `ui/components/syntax_highlighter.py`, `ui/components/code_editor.py:190-196,265-285`,
  `ui/components/bottom_panel.py:14-46`, `ui/components/floating_list.py:18-26`,
  `ui/components/terminal_panel.py:25-34`
- Test: `tests/test_no_hardcoded_colors.py`

**Interfaces:**
- Consumes: `ui.theme.color(token)`
- Produces: `CppHighlighter.rebuild()` / `PythonHighlighter.rebuild()` — kuralları
  geçerli paletle yeniden kurar (Görev 7 `:reload`'da çağırır);
  `ModalEditor.set_highlighter_for_file(file_path, force=False)`

- [ ] **Adım 1: Düşen testi yaz**

`tests/test_no_hardcoded_colors.py`:

```python
""" Renkler tek yerde dursun: ui/theme.py dışında hex renk kalmamalı.
Bu bir regresyon bekçisi — yeni bir bileşen eklerken rengi gömmek kolay. """
import pathlib
import re

HEX = re.compile(r"#[0-9a-fA-F]{6}")
KOK = pathlib.Path(__file__).resolve().parent.parent

# Paletin kendisi ve şablonu doğal olarak hex içerir.
MUAF = {"ui/theme.py", "core/config.py"}


def test_hex_renkler_yalniz_temada():
    suclular = {}
    for yol in list(KOK.glob("ui/**/*.py")) + list(KOK.glob("core/*.py")):
        goreli = yol.relative_to(KOK).as_posix()
        if goreli in MUAF:
            continue
        satirlar = [
            f"{goreli}:{no}"
            for no, satir in enumerate(yol.read_text(encoding="utf-8").splitlines(), 1)
            if HEX.search(satir) and not satir.lstrip().startswith("#")
        ]
        if satirlar:
            suclular[goreli] = satirlar

    assert not suclular, f"ui/theme.py dışında hex renk kaldı: {suclular}"
```

- [ ] **Adım 2: Çalıştır — düşmeli**

```bash
.venv/bin/python -m pytest tests/test_no_hardcoded_colors.py -q
```

Beklenen: FAIL, beş dosyayı listeler.

- [ ] **Adım 3: `syntax_highlighter.py`**

Her iki sınıfta da kural kurulumunu `rebuild()` metoduna al; `__init__` onu
çağırsın. Renkler:

| Bugün | Token |
|---|---|
| `#565f89` (yorum) | `fg_dim` |
| `#bb9af7` (anahtar sözcük) | `purple` |
| `#9ece6a` (dize) | `green` |
| `#ff9e64` (sayı) | `orange` |
| `#7dcfff` (builtin) | `cyan` |
| `#e0af68` (dekoratör) | `yellow` |

```python
from ui import theme


class CppHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rebuild()

    def rebuild(self):
        """ Kuralları geçerli paletle yeniden kurar. ':reload' bunu çağırır;
        renkler QTextCharFormat içine kopyalandığı için palet değişince
        kendiliğinden güncellenmiyorlar. """
        self.highlighting_rules = []

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(theme.color("fg_dim")))
        comment_format.setFontItalic(True)
        # ... (mevcut kuralların gövdesi aynen; yalnız QColor("#...") çağrıları
        #      yukarıdaki tabloya göre theme.color(...) olur)

        self.rehighlight()
```

- [ ] **Adım 4: `code_editor.py`**

```python
from ui import theme
```

`_highlight_matches` içinde:

```python
            highlight.setBackground(QColor(theme.color("search")))
            highlight.setForeground(QColor(theme.color("fg_bright")))
```

`line_number_area_paint_event` içinde (boyama anında okunuyor, `:reload`
sonrası ilk çizimde yeni renk gelir):

```python
        painter.fillRect(event.rect(), QColor(theme.color("bg_dark")))
        ...
                color = QColor(theme.color("fg")) if block_number == current_line else QColor(theme.color("gutter"))
```

`set_highlighter_for_file`'a `force` ekle — `:reload` aynı sınıfla yeniden
kurabilsin:

```python
    def set_highlighter_for_file(self, file_path, force=False):
        """ Dosya uzantısına göre uygun highlighter'a geçer. force=True ise
        aynı sınıf olsa bile yeniden kurar (':reload' tema değiştirdiğinde). """
        highlighter_cls = PythonHighlighter if file_path and file_path.lower().endswith(".py") else CppHighlighter
        if isinstance(self.highlighter, highlighter_cls) and not force:
            return
        self.highlighter.setDocument(None)
        self.highlighter = highlighter_cls(self.document())
```

- [ ] **Adım 5: `bottom_panel.py`**

`MODE_COLORS` sabitini token adlarına çevir; renk `set_mode`'da okunsun:

```python
    # Mod -> palet tokeni. Gerçek renk set_mode'da okunuyor ki ':reload'
    # paleti değiştirdiğinde rozet de değişsin.
    MODE_TOKENS = {
        "NORMAL": "blue",
        "INSERT": "green",
        "COMMAND": "orange",
    }

    def set_mode(self, mode):
        self.mode_label.setText(f" {mode} ")
        color = theme.color(self.MODE_TOKENS.get(mode, "blue"))
        self.mode_label.setStyleSheet(
            f"background-color: {color}; color: {theme.color('bg')}; "
            f"font-weight: bold; padding: 0 6px; font-size: 11px;"
        )
```

- [ ] **Adım 6: `floating_list.py`**

`_ROW_STYLE` / `_SELECTED_ROW_STYLE` sınıf sabitlerini metoda çevir
(`set_rows` her çağrıldığında yeniden üretilir):

```python
    def _row_style(self, selected):
        """ Satır stili; renkler geçerli paletten. """
        common = "padding: 4px 12px; font-family: 'Fira Code', 'Consolas', monospace; font-size: 13px;"
        if selected:
            return (f"background-color: {theme.color('selection')}; "
                    f"color: {theme.color('fg_bright')}; border-radius: 4px; {common}")
        return f"color: {theme.color('fg')}; {common}"
```

`set_rows` içinde:

```python
            row.setStyleSheet(self._row_style(i == selected_index))
```

- [ ] **Adım 7: `terminal_panel.py`**

`_ANSI_COLORS` sabitini token eşlemesine çevir, renk boyama anında okunsun:

```python
    # pyte'ın Char.fg / Char.bg alanlarında dönebilecek isimli renkler
    # (vt102 mirasından: "brown" aslında sarıdır) palet tokenlarına eşlenir.
    _ANSI_TOKENS = {
        "black": "bg", "red": "red", "green": "green", "brown": "yellow",
        "blue": "blue", "magenta": "purple", "cyan": "cyan", "white": "fg",
        "brightblack": "border", "brightred": "red", "brightgreen": "green",
        "brightbrown": "yellow", "brightblue": "blue", "brightmagenta": "purple",
        "brightcyan": "cyan", "brightwhite": "fg_bright",
    }

    def _ansi_color(self, name, default_token):
        token = self._ANSI_TOKENS.get(name)
        return QColor(theme.color(token if token else default_token))
```

`DEFAULT_FG` / `DEFAULT_BG` sınıf sabitleri yerine boyama anında
`QColor(theme.color("fg"))` ve `QColor(theme.color("bg_dark"))`.

- [ ] **Adım 8: Çalıştır — hepsi geçmeli**

```bash
.venv/bin/python -m pytest -q
python3 main.py    # görünüm bugünküyle birebir aynı olmalı
```

- [ ] **Adım 9: Commit**

```bash
git add ui/ tests/test_no_hardcoded_colors.py
git commit -m "refactor: kalan renkleri de ui/theme paletine taşı"
```

---

## Görev 4: `IDEWindow` ayarları okusun ve uygulasın

**Files:**
- Modify: `ui/main_window.py` (`__init__`, `_apply_theme`), `main.py`
- Modify: `tests/conftest.py` (`pencere` fixture'ı)
- Test: `tests/test_settings_reload.py` (ilk testler)

**Interfaces:**
- Consumes: `core.config.load/default_settings/ensure_exists`,
  `ui.theme.build_palette/set_palette/stylesheet`
- Produces:
  - `IDEWindow(settings: dict | None = None)` — `None` ise dosyadan okur
  - `IDEWindow.settings: dict`
  - `IDEWindow.apply_settings() -> None` — paleti, QSS'i, editörleri ve
    terminali `self.settings`'e göre günceller

- [ ] **Adım 1: Düşen testi yaz**

`tests/test_settings_reload.py`:

```python
""" Ayarların pencereye uygulanması. """
import core.config as config
from ui.main_window import IDEWindow


def test_varsayilan_ayarlarla_acilir(pencere):
    assert pencere.settings == config.DEFAULTS


def test_renk_ayari_stylesheete_gecer(qapp):
    ayarlar = config.default_settings()
    ayarlar["colors"] = {"bg": "#11111b"}

    pencere = IDEWindow(settings=ayarlar)
    try:
        assert "#11111b" in pencere.styleSheet()
    finally:
        pencere.terminal_panel.shutdown()
        pencere.close()
        pencere.deleteLater()
        qapp.processEvents()


def test_font_ayari_stylesheete_gecer(qapp):
    """ Font'u QSS sahipleniyor; ayarın oraya ulaştığını doğruluyoruz. """
    ayarlar = config.default_settings()
    ayarlar["editor"]["font_family"] = "JetBrains Mono"
    ayarlar["editor"]["font_size"] = 20

    pencere = IDEWindow(settings=ayarlar)
    try:
        qss = pencere.styleSheet()
        assert "'JetBrains Mono'" in qss
        assert "font-size: 20px" in qss     # editör
        assert "font-size: 16px" in qss     # statusline (-4)
    finally:
        pencere.terminal_panel.shutdown()
        pencere.close()
        pencere.deleteLater()
        qapp.processEvents()


def test_bilinmeyen_renk_tokeni_uyarir(qapp, capsys):
    ayarlar = config.default_settings()
    ayarlar["colors"] = {"pembe": "#ff00ff"}

    pencere = IDEWindow(settings=ayarlar)
    try:
        assert "pembe" in capsys.readouterr().out
    finally:
        pencere.terminal_panel.shutdown()
        pencere.close()
        pencere.deleteLater()
        qapp.processEvents()
```

- [ ] **Adım 2: Çalıştır — düşmeli**

```bash
.venv/bin/python -m pytest tests/test_settings_reload.py -q
```

- [ ] **Adım 3: `IDEWindow.__init__`'i ayarlara bağla**

```python
    def __init__(self, settings=None):
        super().__init__()

        # settings=None ise dosyadan okunur. Testler ve gömülü kullanım açık
        # sözlük verir; bir IDEWindow oluşturmak kullanıcının gerçek ayar
        # dosyasına bağımlı olmasın.
        if settings is None:
            settings, warnings = config.load()
            for warning in warnings:
                print(warning)
        self.settings = settings

        self.setWindowTitle("DeCode IDE - v0.2")
        ...
        self._setup_ui()
        self.apply_settings()
```

(`self._apply_theme()` çağrısı `self.apply_settings()` ile değişiyor.)

- [ ] **Adım 4: `apply_settings`'i yaz**

```python
    def apply_settings(self):
        """ self.settings'i her yere dağıtır: palet, QSS, editörler, terminal.
        Hem açılışta hem ':reload'da aynı yoldan geçilir. """
        palette, warnings = theme.build_palette(self.settings["colors"])
        for warning in warnings:
            print(warning)
        theme.set_palette(palette)

        self._apply_theme()

        for editor in self.editor_tabs.editors():
            editor.apply_settings(self.settings["editor"])

        self.terminal_panel.apply_settings(self.settings["terminal"])
```

> `ModalEditor.apply_settings` Görev 5'te, `TerminalPanel.apply_settings`
> Görev 6'da geliyor. Bu görevde ikisini de tek satırlık birer saplama olarak
> ekle (`def apply_settings(self, settings): pass`) ki `apply_settings` şimdiden
> çalışsın; sonraki görevler gövdelerini dolduracak.

`_apply_theme` artık ayarlardan okur (Görev 2'deki geçici sabitler kalkar):

```python
        editor_settings = self.settings["editor"]
        self.setStyleSheet(theme.stylesheet(
            theme.palette(), editor_settings["font_family"], editor_settings["font_size"]))
```

Yeni sekme açıldığında da ayarlar uygulanmalı — `_on_tab_count_changed`'in
dolu dalına ekle:

```python
            editor.apply_settings(self.settings["editor"])
            self.terminal_panel.sync_font_with_editor(editor)
```

- [ ] **Adım 5: `main.py` açılışta dosyayı oluştursun**

```python
import sys
import os
from PyQt6.QtWidgets import QApplication

from core import config
from ui.main_window import IDEWindow


def main():
    # Wayland üzerinde sorunsuz çalışması için Qt'ye ipucu veriyoruz
    os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

    # Ayar dosyası yoksa yorumlu şablonu yaz; ardından oku. Ev dizinine yazan
    # tek yer burası (IDEWindow oluşturmak dosya yaratmaz).
    path = config.config_path()
    if config.ensure_exists(path):
        print(f"Ayar dosyası oluşturuldu: {path}")

    settings, warnings = config.load(path)
    for warning in warnings:
        print(warning)

    app = QApplication(sys.argv)

    window = IDEWindow(settings=settings)
    window.show()

    sys.exit(app.exec())
```

- [ ] **Adım 6: `pencere` fixture'ını hermetik yap**

`tests/conftest.py` içindeki fixture, kullanıcının gerçek ayar dosyasını
okumasın:

```python
    from core import config
    from ui.main_window import IDEWindow

    window = IDEWindow(settings=config.default_settings())
```

- [ ] **Adım 7: Çalıştır ve commit**

```bash
.venv/bin/python -m pytest -q
python3 main.py
```

```bash
git add ui/main_window.py main.py tests/ ui/components/
git commit -m "feat: ayarları oku ve pencereye uygula; açılışta ayar dosyasını oluştur"
```

---

## Görev 5: Editör ayarları — font, sekme genişliği, satır numarası

**Files:**
- Modify: `ui/components/code_editor.py`
- Test: `tests/test_editor_settings.py`

**Interfaces:**
- Consumes: `settings["editor"]` sözlüğü (`font_family`, `font_size`,
  `tab_width`, `expand_tabs`, `line_numbers`)
- Produces: `ModalEditor.apply_settings(editor_settings: dict) -> None`;
  `ModalEditor.tab_width: int`, `ModalEditor.expand_tabs: bool`,
  `ModalEditor.line_numbers: bool`

- [ ] **Adım 1: Düşen testleri yaz**

`tests/test_editor_settings.py`:

```python
""" Ayarların editör davranışına yansıması. """
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

import core.config as config
from ui.components.code_editor import ModalEditor


def _editor(qapp, **degisiklikler):
    ayarlar = config.default_settings()["editor"]
    ayarlar.update(degisiklikler)
    editor = ModalEditor()
    editor.apply_settings(ayarlar)
    return editor


def test_sekme_genisligi_uygulanir(qapp):
    dar = _editor(qapp, tab_width=2)
    genis = _editor(qapp, tab_width=8)
    assert genis.tabStopDistance() > dar.tabStopDistance() > 0


def test_expand_tabs_kapaliyken_gercek_tab_yazilir(qapp):
    editor = _editor(qapp, expand_tabs=False)
    QTest.keyClicks(editor, "i")          # INSERT
    QTest.keyClick(editor, Qt.Key.Key_Tab)
    assert editor.toPlainText() == "\t"


def test_expand_tabs_acikken_bosluk_yazilir(qapp):
    editor = _editor(qapp, expand_tabs=True, tab_width=4)
    QTest.keyClicks(editor, "i")
    QTest.keyClick(editor, Qt.Key.Key_Tab)
    assert editor.toPlainText() == "    "


def test_satir_numarasi_kapatilabilir(qapp):
    acik = _editor(qapp, line_numbers=True)
    kapali = _editor(qapp, line_numbers=False)
    assert acik.line_number_area_width() > 0
    assert kapali.line_number_area_width() == 0
    assert not kapali.line_number_area.isVisible()


def test_normal_modda_tab_metne_dokunmaz(qapp):
    """ Tab yalnız INSERT modunda yazar; NORMAL modda hiçbir şey olmamalı. """
    editor = _editor(qapp, expand_tabs=True)
    QTest.keyClick(editor, Qt.Key.Key_Tab)
    assert editor.toPlainText() == ""
```

- [ ] **Adım 2: Çalıştır — düşmeli**

```bash
.venv/bin/python -m pytest tests/test_editor_settings.py -q
```

- [ ] **Adım 3: Uygula**

> **Font'u kim sahipleniyor:** Aile ve boyut **QSS'ten** gelir
> (`QPlainTextEdit { font-family/font-size }`, Görev 2'de ayarlardan üretiliyor).
> QSS, `setFont()`'un üstüne yazdığı için burada `setFont` çağırmıyoruz —
> çağırsaydık pencere içinde sessizce etkisiz kalır, testte ise çalışıyormuş gibi
> görünürdü. `apply_settings` fontu yalnız **ölçmek** için okur; bu yüzden
> `IDEWindow.apply_settings` önce `_apply_theme()` (stylesheet), sonra
> `editor.apply_settings()` çağırır ve ölçümden önce `ensurePolished()` ile
> stilin çözülmesi beklenir — `TerminalPanel.sync_font_with_editor`'ın yıllardır
> yaptığı numaranın aynısı.

`ui/components/code_editor.py` — `__init__`'e varsayılanlar
(`apply_settings` çağrılmadan da editör çalışsın):

```python
        # Ayar dosyasından gelen editör davranışı (bkz. apply_settings).
        self.tab_width = 4
        self.expand_tabs = False
        self.line_numbers = True
```

Yeni metot (import'a `QFontMetricsF` eklenir:
`from PyQt6.QtGui import QTextCursor, QTextCharFormat, QPainter, QColor, QFontMetricsF`):

```python
    def apply_settings(self, editor_settings):
        """ Ayar dosyasındaki [editor] bölümünü uygular. Açılışta ve ':reload'da
        çağrılır.

        Font ailesi/boyutu buradan ayarlanmaz: onları QSS veriyor (bkz.
        ui/theme.stylesheet). Burada font yalnız sekme genişliğini ölçmek için
        okunuyor, o yüzden önce ensurePolished() ile stilin çözülmesi
        bekleniyor. """
        self.tab_width = editor_settings["tab_width"]
        self.expand_tabs = editor_settings["expand_tabs"]
        self.line_numbers = editor_settings["line_numbers"]

        # Sekme genişliği piksel cinsinden isteniyor; boşluk genişliğinden
        # hesaplıyoruz ki 'tab_width' karakter sayısı anlamına gelsin.
        self.ensurePolished()
        self.setTabStopDistance(
            QFontMetricsF(self.font()).horizontalAdvance(" ") * self.tab_width)

        self.line_number_area.setVisible(self.line_numbers)
        self._update_line_number_area_width(0)
        self.viewport().update()
```

`line_number_area_width` kapalıyken 0 dönsün (gutter payı da kalksın):

```python
    def line_number_area_width(self):
        if not self.line_numbers:
            return 0
        digits = len(str(max(1, self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits
```

`handle_insert_mode`'da Tab'ı boşluğa çevir:

```python
    def handle_insert_mode(self, event):
        if event.key() == Qt.Key.Key_Escape:
            ...
        elif event.key() == Qt.Key.Key_Tab and self.expand_tabs:
            # Ayar açıkken Tab gerçek '\t' değil, tab_width kadar boşluk yazar.
            self.insertPlainText(" " * self.tab_width)
        else:
            super().keyPressEvent(event)
```

- [ ] **Adım 4: Çalıştır — geçmeli**

```bash
.venv/bin/python -m pytest -q
```

- [ ] **Adım 5: Commit**

```bash
git add ui/components/code_editor.py tests/test_editor_settings.py
git commit -m "feat: font, sekme genişliği ve satır numarası ayarları"
```

---

## Görev 6: Terminal satır sayısı ayarı

**Files:**
- Modify: `ui/components/terminal_panel.py:21,52,58-71,243-246,298-311`
- Test: `tests/test_editor_settings.py` (ek)

**Interfaces:**
- Consumes: `settings["terminal"]["rows"]`
- Produces: `TerminalPanel.apply_settings(terminal_settings: dict) -> None`;
  `TerminalView(rows=9, parent=None)`, `TerminalView.set_rows(rows: int)`

- [ ] **Adım 1: Düşen testi yaz**

`tests/test_editor_settings.py` sonuna:

```python
def test_terminal_satir_sayisi_ayardan_gelir(pencere):
    """ Görünümün kendi yüksekliğine bakıyoruz (setFixedHeight ile anında
    kesinleşir); panelin yüksekliği layout turuna bağlı olduğu için offscreen'de
    kırılgan olurdu. """
    pencere.show()
    pencere.terminal_panel.toggle()          # ':term'
    goruntu = pencere.terminal_panel.stack.currentWidget()
    assert goruntu.rows == 9
    onceki_yukseklik = goruntu.height()

    pencere.settings["terminal"]["rows"] = 20
    pencere.apply_settings()

    assert goruntu.rows == 20
    assert goruntu.height() > onceki_yukseklik
```

- [ ] **Adım 2: Çalıştır — düşmeli**

- [ ] **Adım 3: `TerminalView.ROWS`'u örnek alanına çevir**

`ROWS = 9` sınıf sabiti **varsayılan** olarak kalır, ama örnek kendi
`self.rows`'unu kullanır:

```python
    ROWS = 9   # varsayılan; ayar dosyası ezebilir

    def __init__(self, rows=ROWS, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._process = TerminalProcess(rows=self.rows, cols=80, parent=self)
        ...

    def set_rows(self, rows):
        """ Satır sayısını değiştirir. Yüksekliği ve PTY boyutunu yeniden
        ölçmek panelin işi: apply_font'u o çağırıyor (bkz.
        TerminalPanel.apply_settings). """
        self.rows = rows
```

`apply_font` ve `_recompute_cols` içindeki `self.ROWS` kullanımları `self.rows`
olur:

```python
        self.setFixedHeight(self.rows * line_height + 2 * self.PADDING)
        ...
        self._process.resize(self.rows, max(1, available // char_width))
```

- [ ] **Adım 4: `TerminalPanel`'e ayarı bağla**

```python
    def __init__(self, parent=None):
        ...
        self._rows = TerminalView.ROWS

    def apply_settings(self, terminal_settings):
        """ Ayar dosyasındaki [terminal] bölümü. Açık oturumlar kapanmadan
        yeniden boyutlanır. """
        self._rows = terminal_settings["rows"]
        for i in range(self.stack.count()):
            view = self.stack.widget(i)
            view.set_rows(self._rows)
            if self._font is not None:
                # Yükseklik ve PTY satır sayısı fontla birlikte ölçülüyor.
                view.apply_font(self._font)
        self._recompute_height()
```

`new_tab` yeni görünümü aynı satır sayısıyla kursun:

```python
    def new_tab(self):
        view = TerminalView(rows=self._rows)
```

- [ ] **Adım 5: Çalıştır ve commit**

```bash
.venv/bin/python -m pytest -q
```

```bash
git add ui/components/terminal_panel.py tests/test_editor_settings.py
git commit -m "feat: terminal satır sayısı ayardan geliyor"
```

---

## Görev 7: `:reload` komutu

**Files:**
- Modify: `core/state_machine.py` (`KNOWN_COMMANDS`, `COMMAND_DESCRIPTIONS`,
  `_execute_command_line`), `ui/components/code_editor.py`,
  `ui/components/welcome_page.py`, `ui/components/editor_tabs.py`,
  `ui/main_window.py`
- Test: `tests/test_settings_reload.py` (ek)

**Interfaces:**
- Produces: `ModalEditor.settings_reload_requested = pyqtSignal()` (aynısı
  `WelcomePage` ve `EditorTabs`'ta); `IDEWindow.reload_settings() -> None`

- [ ] **Adım 1: Düşen testleri yaz**

`tests/test_settings_reload.py` sonuna:

```python
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest


def test_reload_dosyayi_yeniden_okur(pencere, tmp_path, monkeypatch):
    yol = tmp_path / "config.toml"
    yol.write_text('[colors]\nbg = "#11111b"\n\n[editor]\ntab_width = 8\n',
                   encoding="utf-8")
    monkeypatch.setattr("core.config.config_path", lambda: str(yol))

    pencere.show()
    QTest.keyClicks(pencere.editor, ":reload")
    QTest.keyClick(pencere.editor, Qt.Key.Key_Return)

    assert pencere.settings["editor"]["tab_width"] == 8
    assert "#11111b" in pencere.styleSheet()


def test_reload_acik_sekmeleri_korur(pencere, tmp_path, monkeypatch):
    monkeypatch.setattr("core.config.config_path", lambda: str(tmp_path / "yok.toml"))
    pencere.show()
    pencere.editor.setPlainText("kaybolmamalı")

    pencere.reload_settings()

    assert pencere.editor_tabs.count() == 1
    assert pencere.editor.toPlainText() == "kaybolmamalı"


def test_reload_karsilama_sayfasinda_da_var(pencere):
    pencere.show()
    pencere.editor_tabs.close_current_tab()
    adlar = [ad for ad, _a in pencere.welcome_page.state_machine._matches_for("")]
    assert "reload" in adlar
```

- [ ] **Adım 2: Çalıştır — düşmeli**

- [ ] **Adım 3: Komutu ekle**

`core/state_machine.py`:

```python
        "find", "replace", "openfile", "sym", "reload",
```

```python
        "reload": "ayar dosyasını yeniden oku",
```

`_execute_command_line` içindeki `match` bloğuna:

```python
                case "reload":
                    self.editor.settings_reload_requested.emit()
```

- [ ] **Adım 4: Sinyali zincire ekle**

`ui/components/code_editor.py` sinyallerine:

```python
    settings_reload_requested = pyqtSignal()
```

`ui/components/editor_tabs.py` — aynı adla sinyal ve `_wire` içinde aktarım:

```python
        editor.settings_reload_requested.connect(
            lambda e=editor: self._relay(e, self.settings_reload_requested))
```

`ui/components/welcome_page.py` — aynı sinyal, ve `available_commands`'a ekle
(sekme gerektirmiyor):

```python
    available_commands = ("b", "cd", "openfile", "qa", "reload", "tabnew", "term", "termnew", "ts")
```

`ui/main_window.py` — `_connect_modal_host` tablosuna:

```python
            "settings_reload_requested": self.reload_settings,
```

- [ ] **Adım 5: `reload_settings`'i yaz**

```python
    def reload_settings(self):
        """ ':reload' — ayar dosyasını yeniden okuyup uygular. Açık sekmeler,
        imleçler ve terminal oturumları korunur. """
        settings, warnings = config.load()
        for warning in warnings:
            print(warning)
        self.settings = settings
        self.apply_settings()

        # Renklendirici kuralları QTextCharFormat içine kopyalandığı için
        # paletle kendiliğinden güncellenmiyor; yeniden kuruluyorlar.
        for editor in self.editor_tabs.editors():
            editor.set_highlighter_for_file(editor.file_path, force=True)
            editor._highlight_matches()

        print("Ayarlar yeniden yüklendi.")
```

- [ ] **Adım 6: Çalıştır ve elle doğrula**

```bash
.venv/bin/python -m pytest -q
python3 main.py
```

`:openfile ~/.config/decode/config.toml` → `[colors]` altına `bg = "#11111b"`
yaz → `:w` → `:reload` → zemin anında değişmeli, sekmeler yerinde kalmalı.

- [ ] **Adım 7: Commit**

```bash
git add core/state_machine.py ui/ tests/test_settings_reload.py
git commit -m "feat: ':reload' ile ayarları uygulamayı kapatmadan uygula"
```

---

## Görev 8: Belgeler ve kısayol kararı

**Files:**
- Create: `docs/sprint/sprint-09.md`
- Modify: `docs/sprint/README.md`, `docs/Roadmap.md`, `CLAUDE.md`

- [ ] **Adım 1: Roadmap'te Faz 3'ü güncelle**

`docs/Roadmap.md`, "Faz 3 — Editör olgunluğu" bölümünde:

1. **Ayar dosyası** maddesini tamamlandı olarak işaretle ve gerçek yolu/anahtarları yaz.
2. Hareket komutları maddesini **kullanıcı kararına göre** yeniden yaz. Bugünkü metin:

   > - Hareket ve düzenleme komutları: `h/j/k/l`, `w/b`, `gg`/`G`, `dd`, `yy`, `x`,
   >   `o`/`O` ve sayı önekleri (`3dd`) — bugün navigasyon Qt'nin ok tuşlarına
   >   bırakılmış durumda.

   Yerine:

   > - **Navigasyon ok tuşlarında kalıyor** (bilinçli olarak Vim'den ayrılıyoruz):
   >   Ok, Home/End, PageUp/PageDown; Shift+Ok seçer, Ctrl+Ok kelime atlar.
   >   `h/j/k/l`, `w/b`, `gg`/`G` gibi harf tabanlı hareket komutları
   >   **uygulanmayacak**.
   > - Düzenleme komutları (`dd`, `yy`, `x`, `o`/`O` ve sayı önekleri) açık
   >   duruyor; hareketten bağımsız olarak ele alınacak.

3. Teknik borç tablosundaki "Tema kodda sabit — renkler `IDEWindow._apply_theme`
   içinde string olarak" satırını çözüldü olarak güncelle
   (`ui/theme.py` + `[colors]`).
4. "Bugünkü durum" listesine ayar dosyası satırı ekle; test sayısını güncelle.

- [ ] **Adım 2: Sprint 09'u yaz**

`docs/sprint/sprint-09.md` — `docs/sprint/README.md`'deki şablonla; hedef "Faz
3'ün ayar dosyası maddesi", çıktılar bu planın görevleri, teknik notlara şunlar:

- Palet neden modül düzeyinde tek bir sözlük (tema gerçekten global; `:reload`
  boyama anında okunan renkler sayesinde ek tesisat istemiyor).
- `QTextCharFormat`'a kopyalanan renkler istisna: renklendirici ve arama vurgusu
  `:reload`'da elle yeniden kuruluyor.
- `bool`'un `int` alt sınıfı olması yüzünden `font_size = true`'nun ayrıca
  elenmesi.
- Ev dizinine yalnız `main.py` yazıyor; `IDEWindow(settings=...)` testleri
  kullanıcının gerçek ayar dosyasından yalıtıyor.
- **Davranış değişikliği:** sekme genişliği artık 4 karakter (bugüne kadar
  Qt'nin 80 piksellik varsayılanı yürürlükteydi).

`docs/sprint/README.md` tablosuna 09 satırı, "Aktif sprint" satırını güncelle.

- [ ] **Adım 3: `CLAUDE.md`'yi güncelle**

- Mimari listesine `core/config.py` ve `ui/theme.py` ekle; renklerin artık
  yalnız `ui/theme.py`'de olduğunu ve bunu bir testin koruduğunu yaz
  (`tests/test_no_hardcoded_colors.py`).
- "Modal editing model" bölümüne `:reload`'u ekle.
- Navigasyon kararını yaz: ok tuşları kalıcı, `h/j/k/l` gelmeyecek.
- `IDEWindow(settings=None)` sözleşmesini ve testlerin neden açık ayar verdiğini
  yaz.

- [ ] **Adım 4: Commit**

```bash
git add docs/ CLAUDE.md
git commit -m "docs: ayar dosyası sprint kaydı, Roadmap Faz 3 ve navigasyon kararı"
```

---

## Doğrulama

**Otomatik:**

```bash
.venv/bin/python -m pytest -q
```

Beklenen: mevcut 72 test + bu planın ~40 testi geçer.

**Uçtan uca:**

```bash
rm -f ~/.config/decode/config.toml   # ilk açılışı taklit et
python3 main.py
```

| # | Adım | Beklenen |
|---|---|---|
| 1 | Uygulamayı aç | `Ayar dosyası oluşturuldu: ...` yazar, dosya oluşur |
| 2 | Görünüm | Bugünküyle birebir aynı (renkler, font boyutları, 9 satır terminal) |
| 3 | `:openfile ~/.config/decode/config.toml` | Şablon sekmede açılır |
| 4 | `bg = "#11111b"` satırını aç, `:w`, `:reload` | Zemin anında değişir; sekmeler, imleç ve terminal oturumu yerinde |
| 5 | `font_size = 20`, `:w`, `:reload` | Editör ve statusline birlikte büyür (16px statusline) |
| 6 | `line_numbers = false`, `:w`, `:reload` | Gutter kaybolur, metin sola yaslanır |
| 7 | `expand_tabs = true`, `tab_width = 2`, `:reload`, `i` + Tab | İki boşluk yazar |
| 8 | `rows = 20`, `:reload` | Terminal paneli büyür, shell oturumu kapanmaz |
| 9 | Dosyaya `font_size = "kocaman"` yaz, `:reload` | Uyarı basılır, boyut 15'e döner, uygulama çalışmaya devam eder |
| 10 | Dosyaya `[uzay]\nx = 1` ekle, `:reload` | "Bilinmeyen ayar bölümü" uyarısı, gerisi çalışır |
| 11 | Dosyayı bozuk TOML yap, `:reload` | Tek uyarı, tüm ayarlar varsayılana döner, çökme yok |
| 12 | Tüm sekmeleri kapat, karşılama sayfasında `:reload` | Çalışır; öneri listesinde `:reload` görünür |
| 13 | NORMAL modda Ok / Shift+Ok / Ctrl+Ok | Sırasıyla gezinir, seçer, kelime atlar (navigasyon kararı) |

---

## Riskler ve kabul edilmiş sınırlar

- **Modül düzeyinde tek palet.** `ui/theme._current` global bir sözlük. Gerekçe:
  uygulamanın teması gerçekten global ve `:reload`'un beş ayrı yapıcıya palet
  taşımasını önlüyor. Bedeli: aynı süreçte iki farklı temalı pencere açılamaz —
  bu uygulamada böyle bir gereksinim yok.
- **`QTextCharFormat`'a kopyalanan renkler.** Sözdizimi renklendirici ve arama
  vurgusu rengi biçim nesnesine kopyalanıyor, palet değişince kendiliğinden
  güncellenmiyor; `:reload` bunları elle yeniden kuruyor. Yeni bir yerde renk
  bir `QTextCharFormat`'a konursa `reload_settings`'e eklenmesi gerekir.
- **Font'u QSS sahipleniyor, `setFont` değil.** Editörün ailesi/boyutu
  stylesheet'ten gelir; `ModalEditor.apply_settings` fontu yalnız sekme
  genişliğini ölçmek için okur. Bu yüzden sıralama önemli: önce stylesheet,
  sonra editör ayarları, ölçümden önce `ensurePolished()`. Bunu bozan bir
  değişiklik sekme genişliğini sessizce yanlış hesaplar.
- **Font boyutu sapmaları sabit.** Arayüz boyutları editör boyutuna göre
  `+1/-1/-2/-3/-4/+13` kayıyor. Ayrı bir `ui_font_size` anahtarı istenirse
  `FONT_SIZE_OFFSETS`'in yanına eklenmesi kolay ama bu planda yok.
- **Sekme genişliği davranış değiştiriyor.** Bugüne kadar Qt'nin 80 piksellik
  varsayılanı yürürlükteydi; artık 4 karakter. Bilinçli.
- **Dosya izleme yok.** Ayar dosyası kaydedildiğinde kendiliğinden uygulanmıyor;
  `:reload` gerekiyor (kullanıcı kararı).
- **`:reload` sekme başlıklarını ve paleti yeniler, düzeni yenilemez.** Splitter
  oranları, açık sekmeler ve terminal oturumları olduğu gibi kalır — istenen de
  budur.
- **Navigasyon için kod yazılmıyor.** Ok tuşları kararı bugünkü davranışın
  tescili; Görev 8 yalnız belgeyi düzeltiyor. Harf tabanlı hareket komutları
  isteniyorsa bu ayrı bir plandır.
