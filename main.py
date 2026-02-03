#!/usr/bin/env python3
"""Document Creator - Entry Point

Skeleton Analyzer 출력 데이터를 인체공학적 평가 문서로 변환하는 도구
"""

import sys

from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


def main():
    """애플리케이션 실행"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
