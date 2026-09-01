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
