import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor

from core.search import parse_replace_args
from embedded import pio_cli

class StateMachine:
    """ NORMAL moddaki çıplak tuşları (i, :) ve COMMAND moddaki gerçek
    ':' komut satırını (Enter'a basılana kadar serbestçe yazılıp sonra
    çalıştırılan) yönetir. """

    # Bilinen komutlar ve öneri listesinde gösterilecek açıklamaları.
    # Yeni bir komut eklerken burayı ve _execute_command_line'daki match'i
    # birlikte güncelleyin.
    KNOWN_COMMANDS = (
        "d", "w", "b", "y", "p", "wq", "q", "qa", "wqa", "ts", "cd",
        "term", "termnew", "tabnew", "tabclose", "tabnext", "tabprev",
        "find", "replace", "openfile", "sym", "reload", "pio",
    )
    COMMAND_DESCRIPTIONS = {
        "d": "geçerli satırı sil",
        "w": "dosyayı kaydet",
        "b": "sidebar/editör arasında odak değiştir",
        "y": "kopyala",
        "p": "yapıştır",
        "wq": "kaydet ve sekmeyi kapat",
        "q": "sekmeyi kapat",
        "qa": "her şeyi kapat ve çık",
        "wqa": "kaydet, her şeyi kapat ve çık",
        "ts": "bulanık dosya arama",
        "find": "dosya içinde ara (:find <desen>)",
        "replace": "metni değiştir (:replace eski yeni)",
        "openfile": "dosya aç (:openfile <yol>)",
        "sym": "dosyadaki tanımlara atla",
        # Alt komut listesi tek kaynaktan (pio_cli.SUBCOMMANDS) türetiliyor;
        # yeni bir alt komut eklenince bu açıklama kendiliğinden güncellenir.
        "pio": f"PlatformIO (:pio {'|'.join(pio_cli.SUBCOMMANDS)})",
        "reload": "ayar dosyasını yeniden oku",
        "cd": "çalışma dizinini değiştir (:cd <yol>)",
        "term": "terminali aç/kapat",
        "termnew": "yeni terminal sekmesi",
        "tabnew": "yeni sekme",
        "tabclose": "sekmeyi kapat",
        "tabnext": "sonraki sekme",
        "tabprev": "önceki sekme",
    }

    def __init__(self, editor):
        self.editor = editor
        self.command_text = ""
        self._reset_completion_state()

    # --- NORMAL MOD ---

    def handle_normal_key(self, event):
        """ NORMAL moddaki çıplak tuşlar: 'i' Insert moduna, ':' gerçek komut
        satırına, 'n'/'N' son aramanın sonraki/önceki eşleşmesine gider.

        Büyük/küçük harf ayrımı korunur ('N' ile 'n' farklı komut); bu yüzden
        event.text() küçük harfe indirilmiyor. """
        text = event.text()
        if text == "i":
            self._enter_insert_mode()
        elif text == ":":
            self.start_command_line()
        elif text == "n":
            self.editor.search_next()
        elif text == "N":
            self.editor.search_next(backward=True)

    # --- COMMAND MOD (gerçek ':' komut satırı) ---

    def start_command_line(self):
        """ ':' tuşuna basılınca COMMAND moduna geçer ve boş bir komut satırı açar. """
        self.editor.current_mode = "COMMAND"
        self.command_text = ""
        self.editor.mode_changed.emit("COMMAND")
        self.editor.command_line_changed.emit(":")
        self._refresh_suggestions()

    def handle_command_key(self, event):
        """ COMMAND moddayken her tuş komut metnine eklenir; komut ancak Enter'a
        basılınca çalıştırılır (gerçek Vim komut satırı gibi). Tab/Shift+Tab ise
        öneriler arasında gezinip yazılanı tamamlar. """
        if event.key() == Qt.Key.Key_Escape:
            self._exit_command_line()

        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._execute_command_line()

        elif event.key() == Qt.Key.Key_Tab:
            self._cycle_completion(reverse=event.modifiers() == Qt.KeyboardModifier.ShiftModifier)

        elif event.key() == Qt.Key.Key_Backspace:
            if self.command_text:
                self.command_text = self.command_text[:-1]
                self.editor.command_line_changed.emit(":" + self.command_text)
                self._refresh_suggestions()
            else:
                # ':' de silinirse (Vim'deki gibi) komut satırından tamamen çık
                self._exit_command_line()

        elif event.text():
            self.command_text += event.text()
            self.editor.command_line_changed.emit(":" + self.command_text)
            self._refresh_suggestions()

    def _matches_for(self, prefix):
        """ Verilen önekle başlayan bilinen komutları (ad, açıklama) çiftleri
        olarak, alfabetik sırayla döndürür. Önek boşsa hepsini döndürür.
        ':cd <yol>' ve ':openfile <yol>' için sabit komut listesi yerine dosya
        sisteminden yol tamamlaması üretilir (':cd' sadece dizinleri,
        ':openfile' dosyaları da gösterir). """
        if prefix.startswith("cd "):
            return self._path_matches_for("cd", prefix[3:], include_files=False)
        if prefix.startswith("openfile "):
            return self._path_matches_for("openfile", prefix[9:], include_files=True)
        if prefix.startswith("pio "):
            return self._pio_matches_for(prefix[4:])
        available = self._available_commands()
        names = [c for c in available if c.startswith(prefix)] if prefix else list(available)
        names.sort()
        return [(name, self.COMMAND_DESCRIPTIONS.get(name, "")) for name in names]

    def _available_commands(self):
        """ Konağın desteklediği komutlar. ModalEditor hepsini destekler;
        karşılama sayfası (sekme yokken) yalnızca tampon gerektirmeyenleri —
        öneri listesinde çalışmayan komut görünmesin diye. """
        return getattr(self.editor, "available_commands", self.KNOWN_COMMANDS)

    def _path_matches_for(self, command, path_part, include_files):
        """ ':cd' / ':openfile' için shell tarzı yol tamamlaması. Yazılanı
        'hangi dizinde' (head) / 'hangi önekle' (fragment) diye ikiye ayırıp o
        dizindeki girdileri fragment'e göre filtreler. Dizinler sondaki '/'
        ile döner (ör. 'DeCode-IDE/') — Tab'a tekrar basıp iç içe dizinlere
        inmeye devam edilebilsin diye. """
        head, fragment = os.path.split(path_part)
        search_dir = os.path.expanduser(head) if head else "."

        try:
            entries = os.listdir(search_dir)
        except OSError:
            return []

        show_hidden = fragment.startswith(".")
        matches = []
        for name in sorted(entries):
            if not name.startswith(fragment):
                continue
            if not show_hidden and name.startswith("."):
                continue

            is_dir = os.path.isdir(os.path.join(search_dir, name))
            if not is_dir and not include_files:
                continue

            # Tamamlanan metinde kullanıcının yazdığı 'head' aynen korunur ('~'
            # burada genişletilmez — sadece arama dizini için genişletildi).
            joined = os.path.join(head, name)
            matches.append((f"{command} {joined}/" if is_dir else f"{command} {joined}", ""))

        return matches

    def _pio_matches_for(self, fragment):
        """ ':pio <alt-komut>' tamamlaması. Alt komut listesinin tek kaynağı
        embedded/pio_cli.SUBCOMMANDS — komut satırındaki liste ile gerçekten
        çalışan komutlar ayrışmasın diye. """
        fragment = fragment.strip()
        return [(f"pio {ad}", aciklama)
                for ad, aciklama in sorted(pio_cli.SUBCOMMANDS.items())
                if ad.startswith(fragment)]

    def _refresh_suggestions(self):
        """ Yazma/silme sonrası (Tab dışı her değişiklikte) tamamlama döngüsünü
        sıfırlar ve o anki metne göre öneri listesini yeniden hesaplayıp yayınlar. """
        self._reset_completion_state()
        matches = self._matches_for(self.command_text)
        self.editor.command_suggestions_changed.emit(matches, 0 if matches else -1)

    def _cycle_completion(self, reverse):
        """ Tab/Shift+Tab: ilk basışta o anki metne göre öneri listesini sabitler,
        sonraki basışlarda aynı liste içinde ileri/geri gezinir. """
        if self._completion_prefix is None:
            matches = self._matches_for(self.command_text)
            if not matches:
                return
            self._completion_prefix = self.command_text
            self._completion_matches = matches
            self._completion_index = 0
        else:
            step = -1 if reverse else 1
            self._completion_index = (self._completion_index + step) % len(self._completion_matches)

        self.command_text = self._completion_matches[self._completion_index][0]
        self.editor.command_line_changed.emit(":" + self.command_text)
        self.editor.command_suggestions_changed.emit(self._completion_matches, self._completion_index)

    def _reset_completion_state(self):
        self._completion_prefix = None
        self._completion_matches = []
        self._completion_index = -1

    def _execute_command_line(self):
        """ Enter'a basılınca komut metnini yorumlar. Sayısal bir metin ise ilgili
        satıra atlar (Vim'deki ':42' gibi); değilse bilinen komutlarla eşleştirir. """
        text = self.command_text

        if text.isdigit():
            self._goto_line(int(text))
        elif text == "cd" or text.startswith("cd "):
            # ':cd [yol]' — gerçek Vim'deki gibi çalışma dizinini değiştirir.
            # Argümansızsa (sadece 'cd') boş string yollanır: ana dizine gidilir.
            path = text[2:].strip()
            self.editor.change_directory_requested.emit(path)
        elif text.startswith("openfile "):
            # ':openfile <yol>' — dosyayı sekmede açar (IDEWindow karşılar).
            path = text[9:].strip()
            if path:
                self.editor.open_path_requested.emit(path)
        elif text == "find" or text.startswith("find "):
            # ':find <desen>' — argümansız kullanım son deseni tekrar arar
            # (Vim'de çıplak '/' + Enter'ın karşılığı).
            pattern = text[4:].strip()
            if pattern:
                self.editor.search(pattern)
            else:
                self.editor.search_next()
        elif text == "pio" or text.startswith("pio "):
            self._run_pio(text[3:].strip())
        elif text.startswith("replace "):
            arguments = parse_replace_args(text[8:])
            if arguments is None:
                print("Kullanım: :replace eski yeni  (boşluk içeren metin için tırnak)")
            else:
                old, new = arguments
                count = self.editor.replace_all_text(old, new)
                print(f"{count} değiştirme yapıldı." if count else f"Bulunamadı: {old}")
        else:
            match text:
                case "d":
                    self._delete_current_line()
                case "w":
                    self.editor.save_requested.emit()
                case "b":
                    self.editor.sidebar_toggle_requested.emit()
                case "y":
                    self.editor.copy()
                case "p":
                    self.editor.paste()
                case "wq":
                    # Gerçek Vim'deki gibi: kaydet ve pencereyi (burada sekmeyi)
                    # kapat. Son sekme de kapanırsa uygulamadan çıkılır.
                    self.editor.save_requested.emit()
                    self.editor.tab_close_requested.emit()
                case "q" | "tabclose":
                    self.editor.tab_close_requested.emit()
                case "qa":
                    self.editor.quit_requested.emit()
                case "wqa":
                    self.editor.save_requested.emit()
                    self.editor.quit_requested.emit()
                case "tabnew":
                    self.editor.tab_new_requested.emit()
                case "tabnext":
                    self.editor.tab_next_requested.emit()
                case "tabprev":
                    self.editor.tab_prev_requested.emit()
                case "ts":
                    self.editor.telescope_requested.emit()
                case "sym":
                    self.editor.symbol_search_requested.emit()
                case "term":
                    self.editor.terminal_toggle_requested.emit()
                case "termnew":
                    self.editor.terminal_new_requested.emit()
                case "reload":
                    self.editor.settings_reload_requested.emit()
                # bilinmeyen komut: sessizce yok sayılır

        self._exit_command_line()

    def _exit_command_line(self):
        """ Komut çalıştıktan sonra ya da Escape/':' silinince NORMAL moda döner. """
        self.command_text = ""
        self._reset_completion_state()
        self.editor.current_mode = "NORMAL"
        self.editor.mode_changed.emit("NORMAL")
        self.editor.command_line_changed.emit("")
        self.editor.command_suggestions_changed.emit([], -1)

    def _goto_line(self, line_number):
        """ ':42' gibi sayısal komutlarla belirtilen satıra imleci taşır.
        (Asıl iş editörde; ':sym' paleti de aynı yeri kullanıyor.) """
        self.editor.goto_line(line_number)

    # --- KOMUT FONKSİYONLARI ---

    def _enter_insert_mode(self):
        self.editor.current_mode = "INSERT"
        self.editor.setCursorWidth(self.editor.cursor_width_insert)
        self.editor.mode_changed.emit("INSERT")
        print("MOD: INSERT")

    def _run_pio(self, arguments):
        """ ':pio <alt-komut> [argüman]' — asıl iş IDEWindow'da (proje kökü,
        pio'nun yeri, terminal sekmesi); burada yalnız alt komut doğrulanıp
        sinyal yayılıyor.

        Argüman alan tek alt komut bugün 'init' (kart adı). Doğrulama İLK
        tokene bakar, sinyal dizenin TAMAMINI taşır — böylece sinyalin imzası
        (pyqtSignal(str)) değişmiyor ve EditorTabs._relay'e dokunmak
        gerekmiyor. """
        subcommand = arguments.split(" ", 1)[0]
        if subcommand in pio_cli.SUBCOMMANDS:
            self.editor.pio_requested.emit(arguments)
        else:
            print(f"Kullanım: :pio {'|'.join(pio_cli.SUBCOMMANDS)}")

    def _delete_current_line(self):
        """ ':d' — asıl iş editörde; burada yalnızca dağıtım yapılıyor. """
        self.editor.delete_current_line()
