#!/usr/bin/env python3
"""Document Creator - Entry Point

Skeleton Analyzer 출력 데이터를 인체공학적 평가 문서로 변환하는 도구
"""

import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from src.ui.main_window import MainWindow


def get_icon_path():
    """아이콘 파일 경로 반환 (macOS/Windows 지원)"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    if sys.platform == 'darwin':
        icon_file = 'icon.icns'
    else:
        icon_file = 'icon.ico'

    return os.path.join(base_path, 'resources', icon_file)


def main():
    """애플리케이션 실행"""
    app = QApplication(sys.argv)

    # 앱 아이콘 설정
    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.setWindowIcon(QIcon(icon_path))
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
