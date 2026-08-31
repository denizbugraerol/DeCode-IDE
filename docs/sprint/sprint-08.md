# Sprint 08 — Kısayol eşitliği ve karşılama sayfası
**Tarih:** 31 Ağu 2026 · **Durum:** Tamamlandı · **Commit:** —

## Hedef
Alt+Shift ailesini editör sekmelerinde de terminaldeki gibi çalıştırmak ve son sekme kapandığında uygulamanın kapanmasını engellemek.

## Çıktılar
- [x] Alt+Shift ailesi editörde tamamlandı: `N` yeni sekme, `W` sekmeyi kapat (`T`, `←`, `→` zaten vardı). Eşleme artık `TerminalView`'daki ile birebir aynı sözlük — komut, odağın bulunduğu yere uygulanıyor — `ui/components/code_editor.py`
- [x] `ui/components/welcome_page.py` (`WelcomePage`): son sekme kapanınca editörün yerini alan sayfa. Uygulama kapanmıyor
- [x] Karşılama sayfasının kendi `StateMachine`'i var: `:` komut satırı orada da çalışıyor (`:ts`, `:openfile`, `:cd`, `:tabnew`, `:term`, `:termnew`, `:b`, `:qa`)
- [x] `StateMachine._available_commands()`: öneri listesi konağa göre daralıyor — sekme yokken `:w`, `:find`, `:sym` gibi tampon gerektiren komutlar önerilmiyor
- [x] `EditorTabs.last_tab_closed` yerine `tab_count_changed(int)`; `IDEWindow._on_tab_count_changed` iki görünüm arasında geçiş yapıyor
- [x] `IDEWindow.modal_host` özelliği ve `_connect_modal_host` tablosu: `ModalEditor` ile `WelcomePage` aynı sinyal adlarını yaydığı için bağlantılar tek yerden kuruluyor
- [x] Statusline sekme yokken `[Sekme yok]` gösteriyor, satır:sütun alanı boşalıyor
- [x] `:d`'nin imleç işi `ModalEditor.delete_current_line()`'a taşındı (arama/değiştirme/goto ile aynı desen)
- [x] 12 yeni test — `tests/test_welcome_page.py`, `tests/test_editor_shortcuts.py`

## Teknik notlar
- `:q` artık son sekmede uygulamayı kapatmıyor, karşılama sayfasına düşürüyor. Çıkış `:qa` / `:wqa` ya da pencere kapatma düğmesiyle.
- Karşılama sayfası `StateMachine`'in yalnızca komut satırı yarısını kullanıyor: `handle_normal_key` hiç çağrılmıyor, dolayısıyla `i`, `n`, `N` orada anlamsızca çalışmıyor. `StateMachine`'in editörde beklediği işlemler (`copy`, `paste`, `delete_current_line`, `goto_line`, `search`, `search_next`, `replace_all_text`) sayfada sessiz birer saplama.
- Açılışta hâlâ bir `[No Name]` sekmesiyle başlanıyor; karşılama sayfası yalnızca son sekme kapandığında görünüyor.

## Devreden
- `core/terminal_process.py`'deki `os.forkpty()`, süreçte bir `QThread` (`FileIndexWorker`) çalışırken çağrılırsa Python 3.14 `DeprecationWarning` veriyor: "multi-threaded, use of forkpty() may lead to deadlocks". Pratikte `:ts`'den sonra `:term` açmak bu duruma giriyor. Kilitlenme görülmedi ama terminalin `posix_spawn`/`fork+exec` ile yeniden kurgulanması ayrı bir iş.
