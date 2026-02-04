"""템플릿 편집기 모듈

위지윅 방식의 템플릿 편집기를 제공합니다.
"""

from .editor_widget import EditorWidget
from .template_manager_dialog import TemplateManagerDialog
from .mapping_overlay import MappingOverlay, extract_placeholders_from_html
from .field_picker import FieldPicker, FieldListWidget
from .undo_manager import UndoManager
from .auto_save import AutoSaveManager, BackupInfo

__all__ = [
    "EditorWidget",
    "TemplateManagerDialog",
    "MappingOverlay",
    "FieldPicker",
    "FieldListWidget",
    "UndoManager",
    "AutoSaveManager",
    "BackupInfo",
    "extract_placeholders_from_html",
]
