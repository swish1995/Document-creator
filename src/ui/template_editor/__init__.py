"""템플릿 편집기 모듈

위지윅 방식의 템플릿 편집기를 제공합니다.
"""

from .editor_widget import EditorWidget
from .template_manager_dialog import TemplateManagerDialog
from .undo_manager import UndoManager
from .auto_save import AutoSaveManager, BackupInfo

__all__ = [
    "EditorWidget",
    "TemplateManagerDialog",
    "UndoManager",
    "AutoSaveManager",
    "BackupInfo",
]
