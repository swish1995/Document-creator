"""스타일이 적용된 메시지 박스 모듈

스켈레톤 분석기와 동일한 스타일의 메시지 박스를 제공합니다.
"""

from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox, QWidget, QStyle


class StyledMessageBox:
    """스타일이 적용된 메시지 박스 (스켈레톤 분석기와 동일)"""

    # 버튼 색상 정의 (스켈레톤 분석기와 동일)
    BUTTON_COLORS = {
        'primary': ('#5a7ab8', '#4a6aa8', '#6a8ac8'),    # 파란색 (아니오/기본)
        'secondary': ('#555555', '#444444', '#666666'),   # 어두운 회색 (예)
        'success': ('#5ab87a', '#4aa86a', '#6ac88a'),     # 초록색
        'danger': ('#c55a5a', '#b54a4a', '#d56a6a'),      # 빨간색
    }

    @classmethod
    def _get_button_style(cls, color_key: str) -> str:
        """버튼 스타일 생성"""
        colors = cls.BUTTON_COLORS.get(color_key, cls.BUTTON_COLORS['secondary'])
        base, dark, light = colors

        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {base}, stop:1 {dark});
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {light}, stop:1 {base});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {dark}, stop:1 {base});
            }}
        """

    @classmethod
    def question(
        cls,
        parent: QWidget,
        title: str,
        text: str,
        yes_text: str = "예",
        no_text: str = "아니오",
    ) -> bool:
        """예/아니오 질문 다이얼로그

        Args:
            parent: 부모 위젯
            title: 다이얼로그 제목
            text: 메시지 텍스트
            yes_text: "예" 버튼 텍스트
            no_text: "아니오" 버튼 텍스트

        Returns:
            bool: "예" 선택 시 True, "아니오" 선택 시 False
        """
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)

        # 물음표 아이콘 사용 (스켈레톤 분석기와 동일)
        icon = parent.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
        msg_box.setIconPixmap(icon.pixmap(64, 64))

        # 버튼 순서: 아니오(파란색) -> 예(회색)
        no_btn = msg_box.addButton(no_text, QMessageBox.ButtonRole.NoRole)
        yes_btn = msg_box.addButton(yes_text, QMessageBox.ButtonRole.YesRole)

        # 버튼 스타일 적용 (스켈레톤 분석기와 동일: 아니오=파란색, 예=회색)
        no_btn.setStyleSheet(cls._get_button_style('primary'))
        yes_btn.setStyleSheet(cls._get_button_style('secondary'))

        # 기본 버튼은 "아니오"
        msg_box.setDefaultButton(no_btn)
        msg_box.exec()

        return msg_box.clickedButton() == yes_btn

    @classmethod
    def confirm_save(
        cls,
        parent: QWidget,
        title: str = "저장",
        text: str = "저장하시겠습니까?",
    ) -> bool:
        """저장 확인 다이얼로그

        Args:
            parent: 부모 위젯
            title: 다이얼로그 제목
            text: 메시지 텍스트

        Returns:
            bool: "예" 선택 시 True, "아니오" 선택 시 False
        """
        return cls.question(parent, title, text)

    @classmethod
    def warning(
        cls,
        parent: QWidget,
        title: str,
        text: str,
    ) -> None:
        """경고 다이얼로그

        Args:
            parent: 부모 위젯
            title: 다이얼로그 제목
            text: 메시지 텍스트
        """
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)

        icon = parent.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        msg_box.setIconPixmap(icon.pixmap(64, 64))

        ok_btn = msg_box.addButton("확인", QMessageBox.ButtonRole.AcceptRole)
        ok_btn.setStyleSheet(cls._get_button_style('primary'))

        msg_box.exec()
