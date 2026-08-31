import os

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTabWidget

from ui.components.code_editor import ModalEditor


class EditorTabs(QTabWidget):
    """ Birden fazla dosyayı sekmeler halinde tutan kapsayıcı. Her sekmenin
    kendi ModalEditor örneği (dolayısıyla kendi modu, imleci ve state
    machine'i) vardır.

    IDEWindow tek bir editörle konuşuyormuş gibi kalabilsin diye, aktif
    sekmenin sinyalleri buradan aynen dışarı aktarılır; arka plandaki
    sekmelerden gelenler yok sayılır. """

    # --- Aktif editörden aynen aktarılan sinyaller ---
    save_requested = pyqtSignal()
    sidebar_toggle_requested = pyqtSignal()
    telescope_requested = pyqtSignal()
    open_path_requested = pyqtSignal(str)   # ':openfile <yol>'
    symbol_search_requested = pyqtSignal()  # ':sym'
    change_directory_requested = pyqtSignal(str)
    quit_requested = pyqtSignal()             # ':qa' — uygulamadan çık
    terminal_toggle_requested = pyqtSignal()
    terminal_new_requested = pyqtSignal()
    terminal_focus_requested = pyqtSignal()
    mode_changed = pyqtSignal(str)
    command_line_changed = pyqtSignal(str)
    command_suggestions_changed = pyqtSignal(list, int)
    cursor_position_changed = pyqtSignal()

    # --- Sekme durumu ---
    active_file_changed = pyqtSignal(str)     # statusline/pencere başlığı için
    tab_count_changed = pyqtSignal(int)       # 0 olunca IDEWindow karşılama sayfasına geçer

    PLACEHOLDER = "Normal Mod: Yazmak için 'i', komut için ':' tuşuna basın. Çıkmak için 'Esc'."
    UNTITLED = "[No Name]"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("editorTabs")
        self.setDocumentMode(True)
        self.setMovable(True)
        self.setTabsClosable(True)

        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self._on_current_changed)

        self.new_tab()  # açılışta her zaman bir boş sekme bulunsun

    # --- Erişimciler ---

    def current_editor(self):
        return self.currentWidget()

    def editors(self):
        return [self.widget(i) for i in range(self.count())]

    # --- Sekme oluşturma / dosya açma ---

    def new_tab(self, file_path=None, content=""):
        editor = ModalEditor()
        editor.setPlaceholderText(self.PLACEHOLDER)
        self._load_into(editor, file_path, content)
        self._wire(editor)

        index = self.addTab(editor, self._title_for(editor))
        self.setCurrentIndex(index)
        editor.setFocus()
        self.tab_count_changed.emit(self.count())
        return editor

    def open_file(self, file_path, content):
        """ Dosya zaten bir sekmede açıksa o sekmeye geçer; değilse boş/adsız
        ve değiştirilmemiş bir sekme varsa onu kullanır (editörlerdeki
        standart davranış), yoksa yeni bir sekme açar. """
        for index, editor in enumerate(self.editors()):
            if editor.file_path == file_path:
                self.setCurrentIndex(index)
                editor.setFocus()
                return editor

        current = self.current_editor()
        if self._is_reusable(current):
            self._load_into(current, file_path, content)
            self._refresh_title(current)
            current.setFocus()
            return current

        return self.new_tab(file_path, content)

    def _is_reusable(self, editor):
        return (editor is not None
                and editor.file_path is None
                and not editor.document().isModified()
                and not editor.toPlainText())

    def _load_into(self, editor, file_path, content):
        editor.setPlainText(content)
        editor.file_path = file_path
        editor.set_highlighter_for_file(file_path)
        editor.document().setModified(False)

    # --- Sekme kapatma / geçiş ---

    def close_current_tab(self):
        self.close_tab(self.currentIndex())

    def close_tab(self, index):
        if not 0 <= index < self.count():
            return
        editor = self.widget(index)
        self.removeTab(index)
        editor.setParent(None)
        # deleteLater: bu çağrı ':q' işlenirken state machine'in içinden
        # gelebiliyor; C++ nesnesi olay döngüsü turu bitene kadar yaşasın.
        editor.deleteLater()

        # Son sekme de kapansa uygulama kapanmaz: IDEWindow karşılama
        # sayfasına geçer (çıkış için ':qa' var).
        self.tab_count_changed.emit(self.count())
        if self.count():
            self.current_editor().setFocus()

    def switch_tab(self, step):
        if self.count() < 2:
            return
        self.setCurrentIndex((self.currentIndex() + step) % self.count())

    # --- Başlıklar ---

    def _title_for(self, editor):
        name = os.path.basename(editor.file_path) if editor.file_path else self.UNTITLED
        return f"{name} ●" if editor.document().isModified() else name

    def _refresh_title(self, editor):
        index = self.indexOf(editor)
        if index == -1:
            return
        title = self._title_for(editor)
        self.setTabText(index, title)
        if editor is self.current_editor():
            self.active_file_changed.emit(title)

    # --- Sinyal aktarımı ---

    def _wire(self, editor):
        """ Bir sekmenin editörünü dışa aktarılan sinyallere bağlar. Aktarım
        _relay üzerinden yapılır: sadece aktif sekmeden gelenler geçer. """
        editor.save_requested.connect(
            lambda e=editor: self._relay(e, self.save_requested))
        editor.sidebar_toggle_requested.connect(
            lambda e=editor: self._relay(e, self.sidebar_toggle_requested))
        editor.telescope_requested.connect(
            lambda e=editor: self._relay(e, self.telescope_requested))
        editor.open_path_requested.connect(
            lambda path, e=editor: self._relay(e, self.open_path_requested, path))
        editor.symbol_search_requested.connect(
            lambda e=editor: self._relay(e, self.symbol_search_requested))
        editor.change_directory_requested.connect(
            lambda path, e=editor: self._relay(e, self.change_directory_requested, path))
        editor.quit_requested.connect(
            lambda e=editor: self._relay(e, self.quit_requested))
        editor.terminal_toggle_requested.connect(
            lambda e=editor: self._relay(e, self.terminal_toggle_requested))
        editor.terminal_new_requested.connect(
            lambda e=editor: self._relay(e, self.terminal_new_requested))
        editor.terminal_focus_requested.connect(
            lambda e=editor: self._relay(e, self.terminal_focus_requested))
        editor.mode_changed.connect(
            lambda mode, e=editor: self._relay(e, self.mode_changed, mode))
        editor.command_line_changed.connect(
            lambda text, e=editor: self._relay(e, self.command_line_changed, text))
        editor.command_suggestions_changed.connect(
            lambda matches, i, e=editor: self._relay(e, self.command_suggestions_changed, matches, i))
        editor.cursorPositionChanged.connect(
            lambda e=editor: self._relay(e, self.cursor_position_changed))

        # Sekme yönetimi doğrudan burada karşılanır, dışarı taşınmaz
        editor.tab_new_requested.connect(lambda: self.new_tab())
        editor.tab_close_requested.connect(self.close_current_tab)
        editor.tab_next_requested.connect(lambda: self.switch_tab(1))
        editor.tab_prev_requested.connect(lambda: self.switch_tab(-1))

        # Kaydedilmemiş değişiklik göstergesi ('●') sekme başlığında
        editor.document().modificationChanged.connect(
            lambda _modified, e=editor: self._refresh_title(e))

    def _relay(self, editor, signal, *args):
        if editor is self.current_editor():
            signal.emit(*args)

    def _on_current_changed(self, index):
        """ Sekme değişince alt panelleri yeni sekmenin durumuyla senkronlar. """
        editor = self.widget(index)
        if editor is None:
            return
        editor.setFocus()
        self.active_file_changed.emit(self._title_for(editor))
        self.mode_changed.emit(editor.current_mode)
        self.cursor_position_changed.emit()
