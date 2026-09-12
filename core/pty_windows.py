""" Windows transport: ConPTY (pywinpty) tabanlı sözde-terminal.

Sözleşme ve iki güvencesi için bkz. core/pty_posix.py'nin docstring'i.

Neden POSIX'ten yapısal olarak farklı: QSocketNotifier Windows'ta yalnız
SOCKET tanıtıcılarıyla çalışır, ConPTY ise boru verir. Bu yüzden okuma,
bloklayan bir QThread'de yapılıp sonuç KUYRUKLU bağlantıyla ana thread'e
taşınıyor -- 1. güvence böyle sağlanıyor. Desen depoda zaten var:
core/file_index.py, FileIndexWorker. """
import os
import shutil
import time

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal

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
                break          # GERÇEK EOF (EOFError) ya da kapatılmış pty
            if not parca:
                # DİKKAT: bu EOF DEĞİL. pywinpty'nin okuma thread'i veri
                # yokken hattan b'0011Ignore' sentinel'i gönderiyor ve
                # PtyProcess.read bunu '' olarak döndürüyor -- gerçek EOF'un
                # TEK göstergesi yukarıdaki except (EOFError). Burada break
                # yaparsak kabuk hâlâ koşarken sekme "bitti" işaretlenir.
                # read() varsayılan olarak bloklu olduğu için continue sıkı
                # döngüye girmez.
                continue
            if not self._durduruldu:
                self.data_received.emit(_to_bytes(parca))
        self.eof.emit()
        # Referansı burada bırak, WindowsTransport.close()'a değil: bu thread
        # QObject olarak WindowsTransport'un Qt çocuğu, 'self._reader = None'
        # atamak yalnız BİZİM referansımızı düşürür, Qt'nin sahiplik
        # ilişkisini SİLMEZ -- nesne parent'ı (WindowsTransport) yok edilene
        # kadar yaşamaya devam eder. Thread kendi '_pty'sini bırakmazsa,
        # WindowsTransport._pty zaten None olsa bile PtyProcess (ve
        # soketleri) bu thread canlı kaldığı sürece GC'ye asla düşmez. Bu
        # satır, wait() içeride başarıyla dönse de (thread zaten bitmiş
        # demektir) ya da thread süre dolduğu için _BIRAKILAN_THREADLER'a
        # bırakılsa da (er ya da geç buraya kendi kendine ulaşır) her iki
        # yolda da çalışır.
        self._pty = None


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

        # argv listesi DOĞRUDAN geçiliyor, önceden list2cmdline ile tek
        # komut satırına çevrilmiyor. PtyProcess.spawn str aldığında
        # shlex.split(argv, posix=False) uyguluyor ve posix=False tırnakları
        # TOKEN'IN İÇİNDE bırakıyor -- 'C:\Program Files\...' gibi boşluklu
        # bir yolu list2cmdline ile tırnaklayıp geçirirsek shlex.split geri
        # '"C:\Program Files\..."' (tırnaklarıyla) üretir, shutil.which bu
        # adı bulamaz ve spawn FileNotFoundError ile 127'ye düşer -- yani
        # varsayılan kurulumdaki PowerShell 7 ':term'i hiç açmazdı. pywinpty
        # liste aldığında argv[1:] üzerinde list2cmdline'ı zaten kendisi
        # yapıyor; bizim önceden yapmamız çifte kodlamaydı.
        try:
            self._pty = PtyProcess.spawn(argv, dimensions=(rows, cols),
                                         cwd=cwd, env=env)
        except Exception:
            # POSIX'te exec başarısızlığı child'da os._exit(127) oluyor;
            # burada exception geliyor. Aynı anlamı taşısın diye 127.
            self._pty = None
            self._exit_code = 127
            on_eof()
            return

        self._reader = _ReaderThread(self._pty, parent=self)
        # Kuyruklu bağlantı AÇIKÇA yazılıyor (sözleşmenin 1. güvencesi).
        # Qt bağlantı tipini "QThread nesnesi kimin çocuğu" gibi bir şeye
        # göre değil, sinyalin EMIT edildiği thread ile alıcının thread
        # affinity'sine göre seçer: data_received/eof burada _ReaderThread.
        # run() içinden (worker thread) emit ediliyor, alıcı (bu
        # WindowsTransport) ana thread'de yaşıyor -- AutoConnection zaten
        # bunu kuyruklu seçerdi. Açıkça QueuedConnection yazmak sonucu
        # değiştirmiyor, niyeti sabitliyor: biri connect'i AutoConnection
        # varsayımıyla değil bilerek kuyruklu istediğimizi görsün.
        self._reader.data_received.connect(
            self._on_reader_data, Qt.ConnectionType.QueuedConnection)
        self._reader.eof.connect(
            self._on_reader_eof, Qt.ConnectionType.QueuedConnection)
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
        """ Dört adım, hepsi SÜRELİ -- sözleşmenin 2. güvencesi.

        Sıra önemli: bağlantı ÖNCE kesiliyor ki 4. adımda bırakılan bir
        thread silinmiş bir nesneye sinyal gönderemesin.

        Süre bütçesi: pywinpty'nin terminate(force=False) çağrısı en kötü
        durumda kendi delayafterterminate'i (~0.1s) kadar uyuyor,
        terminate(force=True) SIGINT'i tekrarlayıp bir ~0.1s, sonra SIGTERM
        için bir ~0.1s daha (toplam ~0.3s terminate'lerde); artık gerçekten
        çalışan self._pty.close() kendi delayafterclose'u (~0.1s) kadar bir
        uyku daha ekliyor VE GÖVDESİNDE 'if self.isalive(): self.terminate(
        force=False)' vardır -- süreç bu noktada hâlâ (en kötü durumda)
        ayaktaysa bu, kendi delayafterterminate'i (~0.1s daha) olan İKİNCİ
        bir terminate(force=False) çağrısıdır ve toplama eklenmeden önce
        gözden kaçması kolaydır. Sonra buradaki wait(timeout) en fazla
        'timeout' kadar (varsayılan 0.5s) daha bekliyor -- toplamda ana iş
        parçacığında en kötü durumda ~1.0s (0.1 + 0.3 + 0.1 + 0.1 + 0.5).
        _on_reader_eof'un ayrı 0.5s'lik yoklaması bu süreye dahil değil (o,
        EOF sinyali işlenirken çalışıyor). Testteki 5.0s üst sınırın altında
        kalıyor, bolca payla.

        TerminalPanel.shutdown() sekmeleri TEK TEK, sırayla kapatır (bkz.
        ui/components/terminal_panel.py) -- yani bu ~1.0s en kötü durum, tek
        bir oturum için değil, ÇOK SEKMELİ bir pencerede kapanışta üst üste
        BİRİKEN bir gecikme anlamına gelir. """
        # Kuyrukta bekleyen bir data_received/eof olayı, aşağıdaki
        # disconnect'ten SONRA bile teslim edilebilir -- kuyruklanmış bir
        # olay disconnect ile geri çekilmez. Callback'leri burada None'a
        # çekmek, _on_reader_data/_on_reader_eof'taki 'if self._on_data:' /
        # 'if self._on_eof:' korumasını gerçekten devreye sokan tek şey.
        self._on_data = None
        self._on_eof = None

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
            # pywinpty her spawn'da 127.0.0.1'e bağlanan bir dinleyen soket +
            # kabul edilmiş soket + kendi daemon thread'i açıyor; bunları
            # YALNIZ PtyProcess.close()'un GÖVDESİ (fileobj.close() +
            # _server.close()) kapatıyor. GC'ye bırakılamaz -- ama düz
            # 'self._pty.close()' çağrısı burada NO-OP: pywinpty'nin
            # close()'u 'if not self.closed:' kapısıyla başlıyor, isalive()
            # ise HER ÇAĞRILDIĞINDA self.closed = (not alive) YAZIYOR.
            # Yukarıdaki terminate() çağrıları kendi içinde isalive()'ı
            # birkaç kez çağırıyor (süreç ölünce closed zaten True olmuş
            # oluyor); pywinpty'nin kendi test paketi de bunu doğruluyor
            # (winpty/tests/test_ptyprocess.py::test_terminate: terminate()
            # sonrası close() hiç çağrılmadan 'assert pty.closed' geçiyor).
            # Yani bu noktaya geldiğimizde closed zaten True ve düz close()
            # çağrısı fileobj/_server'a hiç dokunmaz. Bayrağı elle geri
            # çekip kapıyı zorla açıyoruz -- GÜVENLİ, çünkü süreç zaten ölü:
            # close() içindeki 'if self.isalive(): terminate(...)' dalı
            # tekrar tetiklenmez (isalive() gerçek OS durumuna bakar, bizim
            # bayrağımızdan etkilenmez).
            try:
                self._pty.closed = False
                self._pty.close()
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
                # Ekleme öncesi bitmiş olanları süpür: aksi halde liste
                # süresiz büyür ve her kayıt bir PtyProcess'i (dolayısıyla
                # soketlerini) canlı tutmaya devam eder.
                _BIRAKILAN_THREADLER[:] = [
                    t for t in _BIRAKILAN_THREADLER if t.isRunning()]
                _BIRAKILAN_THREADLER.append(self._reader)
            self._reader = None
