""" Windows transport: ConPTY (pywinpty) tabanlı sözde-terminal.

Sözleşme ve iki güvencesi için bkz. core/pty_posix.py'nin docstring'i.

Neden POSIX'ten yapısal olarak farklı: QSocketNotifier Windows'ta yalnız
SOCKET tanıtıcılarıyla çalışır, ConPTY ise boru verir. Bu yüzden okuma,
bloklayan bir QThread'de yapılıp sonuç KUYRUKLU bağlantıyla ana thread'e
taşınıyor -- 1. güvence böyle sağlanıyor. Desen depoda zaten var:
core/file_index.py, FileIndexWorker. """
import os
import shutil
import subprocess
import time

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from winpty import PtyProcess


# close() süre dolduğu için BIRAKTIĞI thread'ler. Modül düzeyinde referans
# tutuluyor: sahibi yok edilirken hâlâ koşan bir QThread, Qt'de
# "QThread: Destroyed while thread is still running" ile süreci çökertir.
# Başıboş bir thread, çöken bir kapanıştan iyidir (POSIX'te zombiyi bırakma
# kararının aynı gerekçesi).
_BIRAKILAN_THREADLER = []


class _ReaderThread(QThread):
    """ ConPTY'den bloklayarak okur; her parçayı sinyalle ana thread'e taşır.

    Kendi UTF-8 tamponunu TUTMUYOR ve tutmamalı: pyte.ByteStream zaten artık
    tutan bir incremental decoder taşıyor (codecs.getincrementaldecoder), yani
    çok baytlı bir karakter iki parçaya bölünse bile doğru birleşiyor. Burada
    ikinci bir tampon kurmak yalnız aynı işi iki kez yapardı. """

    data_received = pyqtSignal(bytes)
    eof = pyqtSignal()

    def __init__(self, pty, parent=None):
        super().__init__(parent)
        self._pty = pty
        self._durduruldu = False

    def durdur(self):
        """ Döngü bayrağını düşürür. Okuma o an bloklu olabilir; asıl
        uyandırma pty'nin kapatılmasından gelir (bkz. WindowsTransport.close). """
        self._durduruldu = True

    def run(self):
        while not self._durduruldu:
            try:
                parca = self._pty.read(65536)
            except Exception:
                break          # EOF ya da kapatılmış pty; ikisi de normal çıkış
            if not parca:
                break
            if not self._durduruldu:
                self.data_received.emit(_to_bytes(parca))
        self.eof.emit()


def _to_bytes(parca):
    """ pywinpty str döndürüyorsa UTF-8'e geri kodlar. Sözleşme bytes;
    sınır birleştirme işi pyte.ByteStream'in. """
    if isinstance(parca, bytes):
        return parca
    return parca.encode("utf-8", errors="replace")


class WindowsTransport(QObject):
    """ QObject: reader thread'in sinyalini kuyruklu bağlantıyla almak için
    bir QObject'e ihtiyaç var (POSIX transport'un QObject olmasına gerek yok,
    bu asimetri bilinçli). """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pty = None
        self._reader = None
        self._exit_code = None
        self._on_data = None
        self._on_eof = None

    def default_shell_argv(self):
        """ Windows'ta '$SHELL' yok. PowerShell 7 -> Windows PowerShell ->
        cmd.exe sırası: ilki en yetenekli, sonuncusu her kurulumda var. """
        for name in ("pwsh.exe", "powershell.exe"):
            yol = shutil.which(name)
            if yol:
                return [yol]
        return [os.environ.get("COMSPEC", "cmd.exe")]

    def spawn(self, argv, cwd, env, rows, cols, on_data, on_eof):
        self._on_data, self._on_eof = on_data, on_eof
        self._exit_code = None

        # ConPTY argv listesi değil tek bir KOMUT SATIRI dizesi alıyor.
        # list2cmdline, boşluklu yolları ('C:\Program Files\...') MS C çalışma
        # zamanı kurallarına göre tırnaklayan tek doğru yol; elle ' '.join
        # sessizce bozar.
        komut = subprocess.list2cmdline(argv)
        try:
            self._pty = PtyProcess.spawn(komut, dimensions=(rows, cols),
                                         cwd=cwd, env=env)
        except Exception:
            # POSIX'te exec başarısızlığı child'da os._exit(127) oluyor;
            # burada exception geliyor. Aynı anlamı taşısın diye 127.
            self._pty = None
            self._exit_code = 127
            on_eof()
            return

        self._reader = _ReaderThread(self._pty, parent=self)
        # Kuyruklu bağlantı: thread'den gelen veri ANA iş parçacığında
        # işlensin (sözleşmenin 1. güvencesi). QThread'in kendisi bu nesnenin
        # thread'inde yaşadığı için Qt bağlantıyı otomatik olarak kuyruklu
        # seçiyor; yine de açıkça yazmıyoruz ki varsayılan davranış değişirse
        # sessizce bozulmasın -- bkz. testler.
        self._reader.data_received.connect(self._on_reader_data)
        self._reader.eof.connect(self._on_reader_eof)
        self._reader.start()

    def _on_reader_data(self, data):
        if self._on_data:
            self._on_data(data)

    def _on_reader_eof(self):
        if self._pty is not None:
            # EOF ile çıkış kodunun okunabilir hâle gelmesi arasında yarış
            # var -- POSIX'teki waitpid yarışının birebir karşılığı. Orada
            # bloklayan bir waitpid kullanılıyor ("EOF geldiyse çocuk zaten
            # ölmek üzere"); burada aynı gerekçeyle KISA ve SÜRELİ yokluyoruz.
            # Yoklamazsak exitstatus None gelir ve sekme gerçek kodu yerine
            # '✗ (-1)' gösterir.
            #
            # Bu ana iş parçacığında çalışıyor ama üst sınırı 0.5 saniye ve
            # yalnız süreç ölürken bir kez; 2. güvence close() hakkında.
            son = time.monotonic() + 0.5
            while time.monotonic() < son:
                try:
                    if not self._pty.isalive():
                        break
                except Exception:
                    break
                time.sleep(0.02)
            try:
                self._exit_code = self._pty.exitstatus
            except Exception:
                self._exit_code = None
        if self._exit_code is None:
            self._exit_code = -1
        self._pty = None
        if self._on_eof:
            self._on_eof()

    def set_size(self, rows, cols):
        if self._pty is None:
            return
        try:
            # DİKKAT: PtyProcess.setwinsize (rows, cols) sırasında, alt seviye
            # winpty.PTY.set_size ise (cols, rows) sırasında bekliyor. Depoda
            # pyte.Screen'in aynı tuzağı zaten belgeli.
            self._pty.setwinsize(rows, cols)
        except Exception:
            pass  # süreç tam o anda öldüyse sessizce yok say

    def write(self, data: bytes):
        if self._pty is None:
            return
        try:
            self._pty.write(data.decode("utf-8", errors="replace"))
        except Exception:
            pass

    def is_alive(self):
        return self._pty is not None

    def exit_code(self):
        return self._exit_code

    def close(self, timeout=0.5):
        """ Üç adım, hepsi SÜRELİ -- sözleşmenin 2. güvencesi.

        Sıra önemli: bağlantı ÖNCE kesiliyor ki 3. adımda bırakılan bir
        thread silinmiş bir nesneye sinyal gönderemesin. """
        if self._reader is not None:
            self._reader.durdur()
            try:
                self._reader.data_received.disconnect()
                self._reader.eof.disconnect()
            except TypeError:
                pass          # zaten bağlı değil

        if self._pty is not None:
            try:
                self._pty.terminate(force=False)
            except Exception:
                pass
            if self._pty is not None and self._pty.isalive():
                try:
                    self._pty.terminate(force=True)
                except Exception:
                    pass
            self._pty = None

        if self._reader is not None:
            # Süre dolarsa thread BIRAKILIYOR. POSIX'te zombiyi bırakma
            # kararının birebir karşılığı ve aynı gerekçeyle: donmuş bir
            # arayüz, başıboş bir thread'den kesinlikle kötüdür. Bu kod
            # IDEWindow.closeEvent'ten, yani ANA İŞ PARÇACIĞINDA çalışıyor.
            if not self._reader.wait(int(timeout * 1000)):
                # Ebeveynlikten çıkarıp modül düzeyinde tutuyoruz: bu nesne
                # yok edilirken hâlâ koşan bir çocuk QThread, Qt'de süreci
                # çökertir.
                self._reader.setParent(None)
                _BIRAKILAN_THREADLER.append(self._reader)
            self._reader = None
