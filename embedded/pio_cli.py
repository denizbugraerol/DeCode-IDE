""" PlatformIO CLI sarmalayıcısı: çalıştırılabiliri bulur ve alt komutlar için
argv üretir. Süreci başlatmak bu modülün işi DEĞİL — argv'yi terminal paneline
IDEWindow veriyor (bkz. ui/main_window.py). Saf Python, Qt yok. """
import os
import shutil
import sys

# Öneri listesinin ve ':pio ' tamamlamasının TEK kaynağı. 'env' süreç
# başlatmaz (paleti açar), o yüzden PROCESS_SUBCOMMANDS'ta yoktur.
SUBCOMMANDS = {
    "build": "projeyi derle",
    "upload": "karta yükle",
    "monitor": "seri monitörü aç",
    "clean": "derleme çıktılarını sil",
    "env": "ortam seç",
    "init": "yeni proje oluştur (:pio init [kart])",
}

_ARGUMENTS = {
    "build": ["run"],
    "upload": ["run", "-t", "upload"],
    "clean": ["run", "-t", "clean"],
    # '-e' ile koşunca monitor_speed / monitor_port da platformio.ini'den
    # okunur; baud'u IDE'nin sorması gerekmiyor.
    "monitor": ["device", "monitor"],
    # Ötekilerin AKSİNE var olan bir projeyi değil, projeyi OLUŞTURAN komut.
    "init": ["project", "init"],
}

# '-e <ortam>' yalnız bunlara eklenir: 'pio project init -e esp32dev' anlamsız.
_ENV_SUBCOMMANDS = ("build", "upload", "clean", "monitor")

PROCESS_SUBCOMMANDS = tuple(_ARGUMENTS)


def find_executable(platform_name=None):
    """ 'pio' ya da 'platformio'yu PATH'te arar; bulamazsa PlatformIO'nun
    kendi kurucusunun kullandığı penv yolunu dener. Hiçbiri yoksa None --
    çağıran kullanıcıya kurulum ipucu verir.

    platform_name parametre olarak alınıyor ki Windows dalı LINUX'ta da test
    edilebilsin (core.config.config_path ve main._qt_platform_hint ile aynı
    desen). """
    platform_name = sys.platform if platform_name is None else platform_name

    # shutil.which PATHEXT'i zaten doğru işliyor: Windows'ta 'pio' araması
    # 'pio.exe'yi bulur.
    for name in ("pio", "platformio"):
        path = shutil.which(name)
        if path:
            return path

    home = os.path.expanduser("~")
    if platform_name == "win32":
        # Windows'ta penv betikleri 'bin' değil 'Scripts' altında.
        # os.access(X_OK) burada KULLANILMIYOR: orada var olan hemen her
        # dosya için True döner, yani hiçbir şey elemez.
        fallback = os.path.join(home, ".platformio", "penv", "Scripts", "pio.exe")
        return fallback if os.path.isfile(fallback) else None

    fallback = os.path.join(home, ".platformio", "penv", "bin", "pio")
    return fallback if os.access(fallback, os.X_OK) else None


def build_argv(subcommand, executable, env=None, board=None):
    """ Alt komut için tam argv listesi. Süreç başlatmayan ('env') ve
    bilinmeyen alt komutlarda None döner.

    Ortam verilmemişse '-e' HİÇ eklenmez: kararı platformio.ini'deki
    default_envs verir, IDE onu ezmez. '-e' ayrıca yalnız _ENV_SUBCOMMANDS'a
    eklenir; 'board' ise yalnız 'init'e -- 'pio run --board' diye bir şey
    yok, seçili ortamın 'init'e sızması da anlamsız olurdu. """
    arguments = _ARGUMENTS.get(subcommand)
    if arguments is None:
        return None

    argv = [executable] + list(arguments)
    if subcommand == "init":
        if board:
            argv += ["--board", board]
    elif env and subcommand in _ENV_SUBCOMMANDS:
        argv += ["-e", env]
    return argv
