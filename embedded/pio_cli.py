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
