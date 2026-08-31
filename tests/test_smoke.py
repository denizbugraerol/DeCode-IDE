""" Altyapının ayakta olduğunu ve editörün NORMAL modda doğduğunu doğrular. """
from ui.components.code_editor import ModalEditor


def test_editor_normal_modda_baslar(qapp):
    editor = ModalEditor()
    assert editor.current_mode == "NORMAL"
    assert editor.cursorWidth() == editor.cursor_width_normal
