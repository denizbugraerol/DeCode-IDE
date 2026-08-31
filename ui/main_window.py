import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QSplitter)
from PyQt6.QtCore import Qt, QTimer

from ui.components.sidebar import Sidebar
from ui.components.editor_tabs import EditorTabs
from ui.components.bottom_panel import StatusLine, CommandLine, CommandSuggestions
from ui.components.terminal_panel import TerminalPanel
from ui.components.command_palette import CommandPalette
from core.file_index import FileIndexWorker
from core.symbols import extract_symbols
from core.file_manager import FileManager


class IDEWindow(QMainWindow):
    # Öneri kutusunun komut satırıyla arasına ve statusline'ın üstüne
    # bıraktığı boşluklar (kutunun boyu bunlara göre sınırlanır).
    SUGGESTIONS_GAP = 6
    SUGGESTIONS_BOTTOM_MARGIN = 12

    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("DeCode IDE - v0.1")
        self.setGeometry(100, 100, 1200, 800)

        # Merkez widget ve ana layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Ekranı böleceğimiz ana splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        #Sol panel - Dosya Sistemi
        self.sidebar = Sidebar()

        # --- Sağ Panel: Sekmeli kod editörü + altında terminal paneli ---
        self.editor_tabs = EditorTabs()

        self.terminal_panel = TerminalPanel()
        self.terminal_panel.hide()  # ':term' çalıştırılana kadar gizli, layout'ta yer kaplamaz

        # Editör ve terminal panelini AYNI dikey layout içine koyuyoruz ki
        # panel gösterildiğinde editörün gerçek yüksekliği (dolayısıyla
        # görünen satır sayısı) küçülsün — overlay değil, gerçek daralma.
        self.editor_container = QWidget()
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        editor_layout.addWidget(self.editor_tabs, 1)     # kalan tüm alanı alır
        editor_layout.addWidget(self.terminal_panel, 0)  # sadece kendi sabit yüksekliğini alır

        # Bileşenleri Splitter'a ekliyoruz
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.editor_container)
        self.splitter.setSizes([300, 900])

        # --- Alt Panel: ince statusline (her zaman altta) ---
        self.status_line = StatusLine()
        self.main_layout.addWidget(self.status_line)

        # --- Komut satırı: bir bara bağlı değil, ekranın ortasında beliren
        # yüzen bir kutu (VSCode komut paleti gibi). Sadece COMMAND moddayken görünür. ---
        self.command_line = CommandLine()
        self.command_line.setParent(self.central_widget)
        self.command_line.hide()

        # --- Komut önerileri: komut kutusunun altında, Tab/Shift+Tab ile
        # gezinilip tamamlanabilen öneri listesi. ---
        self.command_suggestions = CommandSuggestions()
        self.command_suggestions.setParent(self.central_widget)
        self.command_suggestions.hide()

        # --- Telescope paleti: ':ts' ve ':sym' için ortak yüzen seçici.
        # Öneri kutusundan farkı, odağı kendisinin alması. ---
        self.command_palette = CommandPalette()
        self.command_palette.setParent(self.central_widget)
        self.command_palette.hide()
        self.command_palette.accepted.connect(self._on_palette_accepted)
        self.command_palette.cancelled.connect(self._close_palette)
        self._file_index_worker = None   # QThread; referans tutulmazsa toplanır

        #Çift tıklama, Enter ve (dosyalarda) sağ ok ile açma sinyallerini dinle ve open_file fonksiyonuna yönlendir
        self.sidebar.doubleClicked.connect(self.open_file)
        self.sidebar.activated.connect(self.open_file)

        # Komut satırı (':w', ':b', ':ts', ':wq') sinyallerini dinle. Sinyaller
        # artık tek bir editörden değil, aktif sekmeden EditorTabs üzerinden
        # geliyor — arka plandaki sekmelerinkiler yok sayılıyor.
        self.editor_tabs.save_requested.connect(self.save_file)
        self.editor_tabs.sidebar_toggle_requested.connect(self.toggle_sidebar_focus)
        self.editor_tabs.telescope_requested.connect(self.open_telescope_search)
        self.editor_tabs.open_path_requested.connect(self._open_relative_path)
        self.editor_tabs.symbol_search_requested.connect(self.open_symbol_search)
        self.editor_tabs.change_directory_requested.connect(self._change_directory)
        self.editor_tabs.quit_requested.connect(self.close)          # ':qa'
        self.editor_tabs.last_tab_closed.connect(self.close)         # son ':q'
        self.editor_tabs.terminal_toggle_requested.connect(self.terminal_panel.toggle)
        self.editor_tabs.terminal_new_requested.connect(self.terminal_panel.open_new_tab)
        self.editor_tabs.terminal_focus_requested.connect(self.terminal_panel.focus_terminal)
        self.terminal_panel.return_focus_requested.connect(self.focus_editor)

        # Mod, komut satırı, imleç konumu ve aktif sekme değiştikçe alt panelleri güncelle
        self.editor_tabs.mode_changed.connect(self._on_mode_changed)
        self.editor_tabs.command_line_changed.connect(self.command_line.set_text)
        self.editor_tabs.command_suggestions_changed.connect(self._on_suggestions_changed)
        self.editor_tabs.cursor_position_changed.connect(self._update_cursor_position)
        self.editor_tabs.active_file_changed.connect(self._on_active_file_changed)

        # Alt panellerin başlangıç durumunu aktif sekmeyle senkronla
        self._on_mode_changed(self.editor.current_mode)
        self._on_active_file_changed(self.current_file_name)
        self._update_cursor_position()

        # Sidebar'dayken Esc'e basılırsa odağı editöre geri ver
        self.sidebar.return_focus_requested.connect(self.focus_editor)

    # --- Aktif sekmeye kısayollar: main_window'un geri kalanı tek bir
    # editörle konuşuyormuş gibi kalabilsin diye. ---

    @property
    def editor(self):
        return self.editor_tabs.current_editor()

    @property
    def current_file_path(self):
        editor = self.editor
        return editor.file_path if editor is not None else None

    @property
    def current_file_name(self):
        path = self.current_file_path
        return os.path.basename(path) if path else "[No Name]"

    def focus_editor(self):
        editor = self.editor
        if editor is not None:
            editor.setFocus()

    def _on_active_file_changed(self, title):
        """ Aktif sekme (ya da onun kaydedilmemiş değişiklik durumu) değişince
        pencere başlığını ve statusline'daki dosya adını günceller. """
        self.setWindowTitle(f"DeCode IDE - {title}")
        self.status_line.set_file(title)

    def _on_mode_changed(self, mode):
        """ Statusline'ı günceller; komut satırı kutusunu (ve açıksa öneri
        listesini) sadece COMMAND moddayken ekranın ortasında gösterir. """
        self.status_line.set_mode(mode)

        if mode == "COMMAND":
            self._position_command_line()
            self.command_line.show()
            self.command_line.raise_()
        else:
            self.command_line.hide()
            self.command_suggestions.hide()

    def _on_suggestions_changed(self, matches, selected_index):
        """ Komut satırındaki metne uyan öneriler değiştikçe (yazarken ya da
        Tab/Shift+Tab ile gezinirken) öneri kutusunu günceller. """
        self.command_suggestions.set_suggestions(matches, selected_index)

        editor = self.editor
        if matches and editor is not None and editor.current_mode == "COMMAND":
            # Liste boyutu (ör. 9 satırdan 2'ye) küçüldüğünde Qt'nin layout
            # önbelleği aynı olay döngüsü turunda doğru boyutu vermiyor;
            # boyutlandırmayı bir sonraki tur'a erteliyoruz.
            QTimer.singleShot(0, self._show_command_suggestions)
        else:
            self.command_suggestions.hide()

    def _show_command_suggestions(self):
        editor = self.editor
        if editor is None or editor.current_mode != "COMMAND" or not self.command_suggestions.has_suggestions():
            return

        # Kutuya, komut satırının altı ile statusline arasında kalan boşluk
        # kadar yer veriyoruz; sığmayan öneriler (artık komut sayısı bir ekrana
        # sığmadığı için) kutunun içinde kaydırılarak görülüyor.
        top = self.command_line.geometry().bottom() + self.SUGGESTIONS_GAP
        available_height = self.status_line.y() - top - self.SUGGESTIONS_BOTTOM_MARGIN

        self.command_suggestions.fit_to(self.command_line.width(), available_height)
        self._position_command_suggestions()
        self.command_suggestions.show()
        self.command_suggestions.raise_()
        self.command_suggestions.scroll_to_selected()

    def _position_command_line(self):
        """ Komut satırı kutusunu merkez widget'ın tam ortasına yerleştirir. """
        area = self.central_widget.rect()
        x = (area.width() - self.command_line.width()) // 2
        y = (area.height() - self.command_line.height()) // 2
        self.command_line.move(x, y)

    def _position_command_suggestions(self):
        """ Öneri kutusunu komut satırının hemen altına yerleştirir. """
        command_line_geometry = self.command_line.geometry()
        self.command_suggestions.move(
            command_line_geometry.x(), command_line_geometry.bottom() + self.SUGGESTIONS_GAP
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.command_line.isVisible():
            self._position_command_line()
        if self.command_suggestions.isVisible():
            # Sadece taşımak yetmez: pencere alçaldıysa kutunun boyu da
            # yeniden sınırlanmalı.
            self._show_command_suggestions()
        if self.command_palette.isVisible():
            self._show_palette()

    def _update_cursor_position(self):
        """ İmleç her hareket ettiğinde (ve sekme değişince) statusline'daki
        satır:sütun bilgisini günceller. """
        editor = self.editor
        if editor is None:
            return
        cursor = editor.textCursor()
        self.status_line.set_position(cursor.blockNumber() + 1, cursor.columnNumber() + 1)

    def open_file(self, index):
        """ Sidebar'dan bir dosya açılınca: zaten bir sekmede açıksa o sekmeye
        geçer, değilse yeni bir sekmede açar (bkz. EditorTabs.open_file). """
        file_path = self.sidebar.get_file_path(index)
        if os.path.isdir(file_path):
            return
        self._open_path(file_path)

    def _open_relative_path(self, path):
        """ ':openfile <yol>' — göreli yollar çalışma dizinine göre çözülür. """
        expanded = os.path.expanduser(path)
        if not os.path.isabs(expanded):
            expanded = os.path.join(os.getcwd(), expanded)
        self._open_path(os.path.normpath(expanded))

    def _open_path(self, file_path):
        """ Dosyayı okuyup uygun sekmede açar. Sidebar, telescope paleti ve
        ':openfile <yol>' aynı yoldan geçer. """
        try:
            content = FileManager.read_file(file_path)
        except UnicodeDecodeError:
            print(f"'{os.path.basename(file_path)}' metin formatında değil (resim veya derlenmiş dosya).")
            return
        except ValueError:
            # FileManager, olmayan yol ya da dizin için ValueError fırlatıyor.
            print(f"Açılamadı (dosya değil ya da bulunamadı): {file_path}")
            return
        except Exception as e:
            print(f"Dosya okunurken bir hata oluştu: {e}")
            return

        self.editor_tabs.open_file(file_path, content)

    def save_file(self):
        """ ':w' — aktif sekmenin dosyasını kaydeder. Hatalar editörün metnine
        yazılmaz (sekmenin içeriğini bozmamak için), konsola bildirilir. """
        editor = self.editor
        if editor is None or not editor.file_path:
            print("Kaydedilecek dosya yok (':w' için önce bir dosya açın).")
            return

        try:
            FileManager.save_file(editor.file_path, editor.toPlainText())
            # Sekme başlığındaki '●' değişiklik göstergesi bununla temizlenir
            editor.document().setModified(False)
            print(f"Kaydedildi: {editor.file_path}")
        except Exception as e:
            print(f"Dosya kaydedilirken bir hata oluştu: {e}")

    def toggle_sidebar_focus(self):
            """ ':b' komutuyla odak Sidebar ile Editor arasında gidip gelir. """
            if self.sidebar.hasFocus():
                self.editor.setFocus()
            else:
                self.sidebar.setFocus()

    def open_telescope_search(self):
        """ ':ts' — çalışma dizinini arka planda tarar ve bulanık dosya arama
        paletini açar. Tarama bitene kadar palet boş ama kullanılabilir
        durumda durur; sonuç gelince kendiliğinden dolar. """
        root = os.getcwd()
        self.command_palette.open_with(f"Dosya ara ({os.path.basename(root)})", [], mode="file")
        self._show_palette()

        self._file_index_worker = FileIndexWorker(root, parent=self)
        self._file_index_worker.ready.connect(self._on_file_index_ready)
        self._file_index_worker.start()

    def open_symbol_search(self):
        """ ':sym' — açık dosyadaki tanımları telescope paletinde listeler;
        seçilen tanımın satırına atlar. """
        editor = self.editor
        if editor is None:
            return

        symbols = extract_symbols(editor.toPlainText(), editor.file_path)
        if not symbols:
            print("Bu dosyada tanım bulunamadı.")
            return

        items = [(f"{kind:<9} {name}    {line}", line) for kind, name, line in symbols]
        self.command_palette.open_with(f"Tanım ara ({self.current_file_name})", items, mode="symbol")
        self._show_palette()

    def _on_file_index_ready(self, paths):
        """ Arka plan taraması bitti: palet hâlâ dosya modunda açıksa doldur. """
        if self.command_palette.isVisible() and self.command_palette.mode == "file":
            self.command_palette.set_items([(path, path) for path in paths])

    def _show_palette(self):
        """ Paleti ekranın üst üçte birinde, yatayda ortalayarak gösterir ve
        odağı ona verir. """
        area = self.central_widget.rect()
        self.command_palette.adjustSize()
        x = (area.width() - self.command_palette.width()) // 2
        y = max(24, (area.height() - self.command_palette.height()) // 3)
        self.command_palette.move(x, y)
        self.command_palette.show()
        self.command_palette.raise_()
        self.command_palette.setFocus()

    def _close_palette(self):
        self.command_palette.hide()
        self.focus_editor()

    def _on_palette_accepted(self, payload):
        """ Palette Enter'a basılınca: dosya modunda dosyayı açar, sembol
        modunda o satıra atlar. """
        mode = self.command_palette.mode
        self._close_palette()

        if mode == "file":
            self._open_path(os.path.join(os.getcwd(), payload))
        elif mode == "symbol":
            editor = self.editor
            if editor is not None:
                editor.goto_line(payload)

    def _change_directory(self, path):
        """ ':cd [yol]' ile tetiklenir — gerçek Vim'deki :cd gibi çalışma dizinini
        değiştirir ve Sidebar'ı yeni dizine köklendirir. Argüman verilmemişse
        (boş string) ana dizine (~) gider. """
        target = os.path.expanduser(path) if path else os.path.expanduser("~")
        if not os.path.isabs(target):
            target = os.path.join(os.getcwd(), target)
        target = os.path.normpath(target)

        if not os.path.isdir(target):
            print(f"':cd' başarısız: '{target}' bir dizin değil.")
            return

        os.chdir(target)
        self.sidebar.set_root_path(target)
        print(f"Çalışma dizini değiştirildi: {target}")

    def _apply_theme(self):
        # Tokyo Night esintili arayüz renkleri
        stylesheet = """
            QMainWindow { background-color: #1a1b26; }
            QTreeView {
                background-color: #16161e;
                color: #c0caf5;
                border: none;
                font-size: 14px;
                outline: none;
            }
            QTreeView::item:selected { background-color: #283457; color: #ffffff; }
            QTreeView::item:hover { background-color: #1f2335; }
            QPlainTextEdit {
                background-color: #1a1b26;
                color: #c0caf5;
                border: none;
                font-family: 'Fira Code', 'Consolas', monospace;
                font-size: 15px;
                padding: 10px;
            }
            QSplitter::handle { background-color: #1f2335; width: 2px; }
            QWidget#statusLine {
                background-color: #1f2335;
            }
            QWidget#statusLine QLabel {
                color: #c0caf5;
                font-family: 'Fira Code', 'Consolas', monospace;
                font-size: 11px;
            }
            QLabel#commandLine {
                background-color: #1f2335;
                color: #c0caf5;
                border: 1px solid #414868;
                border-radius: 8px;
                padding: 4px 12px;
                font-family: 'Fira Code', 'Consolas', monospace;
                font-size: 16px;
            }
            QWidget#floatingList {
                background-color: #1f2335;
                border: 1px solid #414868;
                border-radius: 8px;
            }
            QWidget#commandPalette { background-color: transparent; }
            QLabel#palettePrompt {
                background-color: #1f2335;
                color: #c0caf5;
                border: 1px solid #414868;
                border-radius: 8px;
                padding: 8px 12px;
                font-family: 'Fira Code', 'Consolas', monospace;
                font-size: 15px;
            }
            QScrollArea#floatingListScroll {
                background: transparent;
                border: none;
            }
            QScrollArea#floatingListScroll QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0;
            }
            QScrollArea#floatingListScroll QScrollBar::handle:vertical {
                background-color: #414868;
                border-radius: 3px;
                min-height: 24px;
            }
            QScrollArea#floatingListScroll QScrollBar::handle:vertical:hover {
                background-color: #565f89;
            }
            QScrollArea#floatingListScroll QScrollBar::add-line:vertical,
            QScrollArea#floatingListScroll QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollArea#floatingListScroll QScrollBar::add-page:vertical,
            QScrollArea#floatingListScroll QScrollBar::sub-page:vertical {
                background: transparent;
            }
            QWidget#terminalPanel {
                background-color: #16161e;
                border-top: 2px solid #414868;
            }

            /* --- Sekmeler: editör (üstte) ve terminal (panel içinde) --- */
            QTabWidget#editorTabs::pane {
                border: none;
                background-color: #1a1b26;
            }
            QTabWidget#editorTabs > QTabBar,
            QTabBar#terminalTabBar {
                background-color: #16161e;
                qproperty-drawBase: 0;
            }
            QTabWidget#editorTabs > QTabBar::tab,
            QTabBar#terminalTabBar::tab {
                background-color: #16161e;
                color: #565f89;
                border: none;
                border-right: 1px solid #1a1b26;
                border-bottom: 2px solid transparent;
                padding: 5px 14px;
                font-family: 'Fira Code', 'Consolas', monospace;
                font-size: 12px;
            }
            QTabWidget#editorTabs > QTabBar::tab:hover,
            QTabBar#terminalTabBar::tab:hover {
                background-color: #1f2335;
                color: #c0caf5;
            }
            QTabWidget#editorTabs > QTabBar::tab:selected,
            QTabBar#terminalTabBar::tab:selected {
                background-color: #1a1b26;
                color: #7aa2f7;
                border-bottom: 2px solid #7aa2f7;
            }
            QTabBar#terminalTabBar::tab {
                font-size: 11px;
                padding: 3px 12px;
            }
        """
        self.setStyleSheet(stylesheet)
        self.terminal_panel.sync_font_with_editor(self.editor)

    def closeEvent(self, event):
        """ Uygulama kapanırken terminaldeki shell sürecini (ve PTY'yi)
        düzgünce temizler; ':q'/':wq' ve pencere kapatma düğmesi de
        quit_requested -> self.close üzerinden buraya düşer. """
        self.terminal_panel.shutdown()
        super().closeEvent(event)