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
    except (OSError, UnicodeDecodeError) as error:
        # UnicodeDecodeError bir ValueError'dur, OSError DEĞİL: dosya UTF-8
        # olmayan baytlar içeriyorsa file.read() bunu fırlatır ve sadece
        # OSError yakalamak onu kaçırırdı. main.py load()'u QApplication
        # kurulmadan ÖNCE çağırıyor; bu yüzden burada yakalanmazsa kullanıcı
        # pencere yerine çıplak bir traceback görür (bkz. sprint-09 kabul
        # edilmiş sınırlar/kod incelemesi notu).
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
