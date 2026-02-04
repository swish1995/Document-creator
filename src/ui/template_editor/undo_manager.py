"""실행 취소/다시 실행 관리 모듈

QUndoStack을 활용한 편집 히스토리 관리입니다.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QUndoStack, QUndoCommand


class TextEditCommand(QUndoCommand):
    """텍스트 편집 명령"""

    def __init__(
        self,
        description: str,
        old_text: str,
        new_text: str,
        apply_func: Callable[[str], None],
        parent: Optional[QUndoCommand] = None,
    ):
        super().__init__(description, parent)
        self._old_text = old_text
        self._new_text = new_text
        self._apply_func = apply_func

    def undo(self):
        """실행 취소"""
        self._apply_func(self._old_text)

    def redo(self):
        """다시 실행"""
        self._apply_func(self._new_text)


class MappingCommand(QUndoCommand):
    """매핑 변경 명령"""

    def __init__(
        self,
        description: str,
        field_id: str,
        old_mapping: Optional[str],
        new_mapping: Optional[str],
        apply_func: Callable[[str, Optional[str]], None],
        parent: Optional[QUndoCommand] = None,
    ):
        super().__init__(description, parent)
        self._field_id = field_id
        self._old_mapping = old_mapping
        self._new_mapping = new_mapping
        self._apply_func = apply_func

    def undo(self):
        """실행 취소"""
        self._apply_func(self._field_id, self._old_mapping)

    def redo(self):
        """다시 실행"""
        self._apply_func(self._field_id, self._new_mapping)


class PlaceholderInsertCommand(QUndoCommand):
    """플레이스홀더 삽입 명령"""

    def __init__(
        self,
        description: str,
        html_before: str,
        html_after: str,
        position: int,
        field_id: str,
        apply_func: Callable[[str], None],
        parent: Optional[QUndoCommand] = None,
    ):
        super().__init__(description, parent)
        self._html_before = html_before
        self._html_after = html_after
        self._position = position
        self._field_id = field_id
        self._apply_func = apply_func

    def undo(self):
        """실행 취소"""
        self._apply_func(self._html_before)

    def redo(self):
        """다시 실행"""
        self._apply_func(self._html_after)


class UndoManager(QObject):
    """실행 취소/다시 실행 관리자"""

    # 시그널
    can_undo_changed = pyqtSignal(bool)
    can_redo_changed = pyqtSignal(bool)
    clean_changed = pyqtSignal(bool)
    index_changed = pyqtSignal(int)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._stack = QUndoStack(self)
        self._stack.canUndoChanged.connect(self.can_undo_changed.emit)
        self._stack.canRedoChanged.connect(self.can_redo_changed.emit)
        self._stack.cleanChanged.connect(self.clean_changed.emit)
        self._stack.indexChanged.connect(self.index_changed.emit)

    def push_text_edit(
        self,
        description: str,
        old_text: str,
        new_text: str,
        apply_func: Callable[[str], None],
    ):
        """텍스트 편집 명령 추가"""
        if old_text == new_text:
            return

        cmd = TextEditCommand(description, old_text, new_text, apply_func)
        self._stack.push(cmd)

    def push_mapping_change(
        self,
        description: str,
        field_id: str,
        old_mapping: Optional[str],
        new_mapping: Optional[str],
        apply_func: Callable[[str, Optional[str]], None],
    ):
        """매핑 변경 명령 추가"""
        if old_mapping == new_mapping:
            return

        cmd = MappingCommand(description, field_id, old_mapping, new_mapping, apply_func)
        self._stack.push(cmd)

    def push_placeholder_insert(
        self,
        html_before: str,
        html_after: str,
        position: int,
        field_id: str,
        apply_func: Callable[[str], None],
    ):
        """플레이스홀더 삽입 명령 추가"""
        description = f"플레이스홀더 삽입: {field_id}"
        cmd = PlaceholderInsertCommand(
            description, html_before, html_after, position, field_id, apply_func
        )
        self._stack.push(cmd)

    def undo(self):
        """실행 취소"""
        self._stack.undo()

    def redo(self):
        """다시 실행"""
        self._stack.redo()

    def clear(self):
        """히스토리 초기화"""
        self._stack.clear()

    def set_clean(self):
        """현재 상태를 '저장됨'으로 표시"""
        self._stack.setClean()

    def is_clean(self) -> bool:
        """저장된 상태인지 확인"""
        return self._stack.isClean()

    def can_undo(self) -> bool:
        """실행 취소 가능 여부"""
        return self._stack.canUndo()

    def can_redo(self) -> bool:
        """다시 실행 가능 여부"""
        return self._stack.canRedo()

    def undo_text(self) -> str:
        """실행 취소 설명"""
        return self._stack.undoText()

    def redo_text(self) -> str:
        """다시 실행 설명"""
        return self._stack.redoText()

    def count(self) -> int:
        """명령 수"""
        return self._stack.count()

    def index(self) -> int:
        """현재 인덱스"""
        return self._stack.index()

    @property
    def stack(self) -> QUndoStack:
        """내부 QUndoStack 반환"""
        return self._stack
