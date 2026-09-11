# -*- mode: python ; coding: utf-8 -*-
""" PyInstaller yapılandırması: tek dosya Linux çalıştırılabiliri.

console=True bilinçli: uygulama ayar dosyası uyarılarını ve "pio bulunamadı"
gibi tanıları print ediyor; --windowed bunları yutardı.

excludes listesi boyutun ana kaldıracı. Uygulama yalnız QtCore/QtGui/QtWidgets
kullanıyor (QtTest sadece testlerde), oysa PyQt6 260 MB ve içinde Quick, Qml,
Designer, ShaderTools, Quick3D, Pdf var. QtNetwork/QtDBus/QtOpenGL DIŞLANMIYOR:
Qt Widgets yığını bunları çalışma anında dolaylı arayabilir, kazancı riskine
değmez.

Windows'ta iki ek var: hide_console (konsol GERÇEKTEN var, stdout ve
'--version' çalışıyor, ama bootloader kendi açtığı pencereyi anında
gizliyor) ve pywinpty'nin DLL'lerinin elle toplanması. """
import os
import platform
import sys

ROOT = os.path.dirname(SPECPATH)          # noqa: F821 - PyInstaller enjekte eder
sys.path.insert(0, ROOT)

from core.version import __version__      # noqa: E402

# Çıktı adı platformu ve mimariyi taşır. PyInstaller çapraz derleme yapamaz --
# her dosya üzerinde derlendiği sistemi anlatır, o yüzden adı buradan
# türetmek doğru: 'DeCode-v0.1.2-linux-x86_64', 'DeCode-v0.1.2-macos-arm64'.
_OS = {"linux": "linux", "darwin": "macos", "win32": "windows"}.get(
    sys.platform, sys.platform)

# platform.machine() Windows'ta 'x86_64' değil 'AMD64' döner; normalleştirilmezse
# çıktı 'DeCode-v0.3.0-windows-AMD64' olur ve release.yml'deki ad kontrolü
# release'i kırar. Linux ('x86_64') ve macOS ('arm64') adları değişmiyor.
_ARCH_ADLARI = {
    "amd64": "x86_64",
    "x86_64": "x86_64",
    "arm64": "arm64",
    "aarch64": "arm64",
}
_MAKINE = platform.machine().lower()
_ARCH = _ARCH_ADLARI.get(_MAKINE, _MAKINE)
CIKTI_ADI = f"DeCode-v{__version__}-{_OS}-{_ARCH}"

# PyInstaller Windows'ta ada '.exe' ekliyor; gerçek dosya
# 'DeCode-v0.3.0-windows-x86_64.exe' oluyor.

_HIDDEN = []
_BINARIES = []
_EXE_EK = {}

if sys.platform == "win32":
    # PyInstaller pywinpty'nin uzantısını ve yanındaki DLL'leri kendiliğinden
    # bulmayabiliyor. Eksik DLL'in belirtisi sinsi: kaynaktan çalışırken her
    # şey normal, YALNIZ donmuş binary'de terminal açılmıyor.
    from PyInstaller.utils.hooks import collect_dynamic_libs

    _HIDDEN.append("winpty")
    _BINARIES += collect_dynamic_libs("winpty")

    # Konsol gerçekten var (stdout çalışır, '--version' duman testi hiç
    # değişmeden geçer) ama bootloader kendi açtığı pencereyi anında gizler:
    # çift tıklamayla açılışta siyah kutu görünmez, cmd'den çalıştırılırsa
    # mevcut konsol devralınır ve çıktı görünür.
    #
    # Yalnız Windows'ta ekleniyor: PyInstaller başka platformlarda
    # "Ignoring hide_console; supported only on Windows!" uyarısı basıp yok
    # sayar ve her build'in logunu kirletir.
    _EXE_EK["hide_console"] = "hide-early"


a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=_BINARIES,
    datas=[],
    hiddenimports=_HIDDEN,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt6.QtQml", "PyQt6.QtQuick", "PyQt6.QtQuick3D",
        "PyQt6.QtQuickWidgets", "PyQt6.QtQuickControls2",
        "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtPdf", "PyQt6.QtPdfWidgets", "PyQt6.QtDesigner",
        "PyQt6.QtMultimedia", "PyQt6.QtMultimediaWidgets",
        "PyQt6.QtCharts", "PyQt6.QtDataVisualization",
        "PyQt6.QtBluetooth", "PyQt6.QtNfc", "PyQt6.QtPositioning",
        "PyQt6.QtSql", "PyQt6.QtTest",
        "tkinter", "unittest", "pydoc",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)                          # noqa: F821

exe = EXE(                                 # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=CIKTI_ADI,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    **_EXE_EK,
)
