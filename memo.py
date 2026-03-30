#!/usr/bin/env python3
"""Ann's Memo - 바탕화면 포스트잇 메모 앱"""

import sys
import json
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QPushButton, QMenu, QMessageBox, QScrollArea, QFrame,
    QLineEdit, QToolButton
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import (
    QFont, QColor, QIcon, QPixmap, QPainter, QCursor,
    QPen, QBrush, QPainterPath, QAction
)

# ── 설정 ──
DATA_DIR = Path(__file__).parent
DATA_FILE = DATA_DIR / "memos.json"

TEXT_COLOR = "#111827"
FONT_EN = "Pretendard"
FONT_KR = "Noto Sans CJK KR"

COLORS = {
    "yellow":  {"bg": "#FFE066", "header": "#F5D245", "name": "노랑"},
    "pink":    {"bg": "#FF8FAB", "header": "#E87A96", "name": "핑크"},
    "green":   {"bg": "#8ECF6D", "header": "#7BBF5A", "name": "초록"},
    "blue":    {"bg": "#7EC8E3", "header": "#6AB8D3", "name": "파랑"},
    "purple":  {"bg": "#C4A1E0", "header": "#B48FD0", "name": "보라"},
    "orange":  {"bg": "#FFB347", "header": "#F0A035", "name": "주황"},
    "white":   {"bg": "#F5F5F5", "header": "#E0E0E0", "name": "흰색"},
}
COLOR_NAMES = list(COLORS.keys())


def app_font(size_pt=10, weight=QFont.Weight.Normal):
    font = QFont(FONT_EN, size_pt, weight)
    font.setFamilies([FONT_EN, FONT_KR, "Malgun Gothic", "sans-serif"])
    return font


def load_memos():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_memos(memos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(memos, f, ensure_ascii=False, indent=2)


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def make_color_icon(hex_color, size=14):
    pix = QPixmap(size, size)
    pix.fill(QColor(hex_color))
    return QIcon(pix)


def make_app_icon():
    size = 64
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor("#1E1E1E")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(0, 0, size, size, 10, 10)
    memo_path = QPainterPath()
    memo_path.moveTo(14, 12)
    memo_path.lineTo(50, 12)
    memo_path.lineTo(50, 38)
    memo_path.lineTo(38, 52)
    memo_path.lineTo(14, 52)
    memo_path.closeSubpath()
    p.setBrush(QBrush(QColor("#FFE066")))
    p.drawPath(memo_path)
    fold = QPainterPath()
    fold.moveTo(38, 52)
    fold.lineTo(50, 38)
    fold.lineTo(38, 38)
    fold.closeSubpath()
    p.setBrush(QBrush(QColor("#E0C040")))
    p.drawPath(fold)
    p.setPen(QPen(QColor("#B8960080"), 2))
    for y in [22, 30, 38]:
        p.drawLine(20, y, 44, y)
    p.end()
    return QIcon(pix)


# ── 개별 메모 창 (일반 타이틀바 사용) ──
class MemoWindow(QWidget):
    def __init__(self, data, manager):
        super().__init__()
        self.data = data
        self.manager = manager
        self.setup_ui()
        self.apply_color()
        self.restore_geometry()
        self.apply_pin_state()

    def setup_ui(self):
        # 일반 윈도우 (OS 타이틀바로 이동 가능!)
        self.setWindowFlags(Qt.WindowType.Tool)
        self.setMinimumSize(220, 160)
        self._update_title()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 툴바 (색상변경 + 고정 + 날짜) ──
        toolbar = QWidget()
        toolbar.setFixedHeight(28)
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(8, 2, 8, 2)
        tl.setSpacing(4)

        # 고정/반고정 토글 버튼
        self.btn_pin = QToolButton()
        self.btn_pin.setFixedSize(22, 22)
        self.btn_pin.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_pin.clicked.connect(self.toggle_pin)
        self._update_pin_button()
        tl.addWidget(self.btn_pin)

        # 색상 순환 버튼
        self.btn_color = QToolButton()
        self.btn_color.setText("●")
        self.btn_color.setFixedSize(22, 22)
        self.btn_color.setToolTip("색상 변경")
        self.btn_color.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_color.clicked.connect(self.cycle_color)
        tl.addWidget(self.btn_color)

        # 삭제 버튼
        self.btn_delete = QToolButton()
        self.btn_delete.setText("✕")
        self.btn_delete.setFixedSize(22, 22)
        self.btn_delete.setToolTip("삭제")
        self.btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_delete.clicked.connect(self.delete_memo)
        tl.addWidget(self.btn_delete)

        tl.addStretch()

        # 날짜
        self.date_label = QLabel()
        self.date_label.setFont(app_font(7))
        self._update_date_label()
        tl.addWidget(self.date_label)

        self.toolbar = toolbar
        layout.addWidget(toolbar)

        # ── 텍스트 ──
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.data.get("text", ""))
        self.text_edit.setFont(app_font(10))
        self.text_edit.setFrameStyle(0)
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.text_edit.setPlaceholderText("메모를 입력하세요...")
        self.text_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.text_edit)

    def _update_title(self):
        text = self.data.get("text", "").strip()
        preview = text[:20] if text else "새 메모"
        pin = "📌 " if self.data.get("pinned") else ""
        color_name = COLORS.get(self.data.get("color", "yellow"), {}).get("name", "")
        self.setWindowTitle(f"{pin}{preview} [{color_name}]")

    def _update_pin_button(self):
        pinned = self.data.get("pinned", False)
        self.btn_pin.setText("📌" if pinned else "☐")
        self.btn_pin.setToolTip("맨 위 고정 해제" if pinned else "맨 위 고정")

    def _update_date_label(self):
        created = self.data.get("created", "")
        modified = self.data.get("modified", "")
        parts = []
        if created:
            parts.append(f"생성 {created}")
        if modified and modified != created:
            parts.append(f"편집 {modified}")
        self.date_label.setText("  ·  ".join(parts))

    def apply_color(self):
        cn = self.data.get("color", "yellow")
        c = COLORS.get(cn, COLORS["yellow"])
        bg = c["bg"]
        hdr = c["header"]

        self.toolbar.setStyleSheet(f"background: {hdr};")
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {bg};
                color: {TEXT_COLOR};
                border: none;
                padding: 8px 10px;
                selection-background-color: {hdr};
            }}
        """)
        self.date_label.setStyleSheet(f"color: {TEXT_COLOR}; background: transparent;")
        self.btn_pin.setStyleSheet(f"""
            QToolButton {{
                background: transparent; border: none;
                font-size: 13px;
            }}
            QToolButton:hover {{ background: rgba(0,0,0,0.1); border-radius: 4px; }}
        """)
        self.btn_delete.setStyleSheet(f"""
            QToolButton {{
                background: transparent; border: none;
                color: {TEXT_COLOR}; font-size: 13px;
            }}
            QToolButton:hover {{ background: rgba(220,53,69,0.8); color: #fff; border-radius: 4px; }}
        """)
        # 색상 버튼 = 다음 색상 미리보기
        next_idx = (COLOR_NAMES.index(cn) + 1) % len(COLOR_NAMES)
        next_c = COLORS[COLOR_NAMES[next_idx]]
        self.btn_color.setStyleSheet(f"""
            QToolButton {{
                background: transparent; border: none;
                color: {next_c['bg']}; font-size: 16px;
            }}
            QToolButton:hover {{ background: rgba(0,0,0,0.1); border-radius: 4px; }}
        """)
        self._update_title()
        self.setWindowIcon(make_color_icon(bg, 32))

    def apply_pin_state(self):
        pinned = self.data.get("pinned", False)
        flags = Qt.WindowType.Tool
        if pinned:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        was_visible = self.isVisible()
        self.setWindowFlags(flags)
        if was_visible:
            self.show()

    def restore_geometry(self):
        self.setGeometry(
            self.data.get("x", 200), self.data.get("y", 200),
            self.data.get("w", 260), self.data.get("h", 220)
        )

    def save_geometry(self):
        g = self.geometry()
        self.data["x"] = g.x()
        self.data["y"] = g.y()
        self.data["w"] = g.width()
        self.data["h"] = g.height()

    def on_text_changed(self):
        self.data["text"] = self.text_edit.toPlainText()
        self.data["modified"] = now_str()
        self._update_date_label()
        self._update_title()
        self.manager.schedule_save()

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setFont(app_font(9))
        menu.setStyleSheet("""
            QMenu {
                background: #1E1E1E; color: #E0E0E0;
                border: 1px solid #444; padding: 4px;
            }
            QMenu::item { padding: 6px 20px; }
            QMenu::item:selected { background: #333; }
            QMenu::separator { background: #333; height: 1px; margin: 4px 8px; }
        """)

        pinned = self.data.get("pinned", False)
        pin_act = menu.addAction("📌 맨 위 고정 해제" if pinned else "📌 맨 위 고정")
        pin_act.triggered.connect(self.toggle_pin)
        menu.addSeparator()

        for cn in COLOR_NAMES:
            c = COLORS[cn]
            act = menu.addAction(make_color_icon(c["bg"]), c["name"])
            act.triggered.connect(lambda _, n=cn: self.change_color(n))
        menu.addSeparator()

        del_act = menu.addAction("🗑 삭제")
        del_act.triggered.connect(self.delete_memo)

        menu.exec(self.text_edit.mapToGlobal(pos))

    def toggle_pin(self):
        self.data["pinned"] = not self.data.get("pinned", False)
        self._update_pin_button()
        self._update_title()
        self.apply_pin_state()
        self.manager.schedule_save()
        self.manager.refresh_list()

    def cycle_color(self):
        idx = COLOR_NAMES.index(self.data.get("color", "yellow"))
        self.data["color"] = COLOR_NAMES[(idx + 1) % len(COLOR_NAMES)]
        self.apply_color()
        self.manager.schedule_save()
        self.manager.refresh_list()

    def change_color(self, color_name):
        self.data["color"] = color_name
        self.apply_color()
        self.manager.schedule_save()
        self.manager.refresh_list()

    def delete_memo(self):
        reply = QMessageBox.question(
            self, "메모 삭제", "이 메모를 삭제할까요?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.save_geometry()
            self.hide()
            self.manager.on_memo_deleted(self.data["id"])

    def closeEvent(self, event):
        """X 닫기 = 숨기기 (삭제 아님, 자동저장)"""
        self.save_geometry()
        self.data["visible"] = False
        self.manager.on_memo_hidden(self.data["id"])
        event.accept()


# ── 메인 관리 창 ──
class MemoManager(QWidget):
    def __init__(self):
        super().__init__()
        self.memos_data = load_memos()
        self.memo_windows = {}

        self.setWindowTitle("Ann's Memo")
        self.setWindowIcon(make_app_icon())
        self.setMinimumSize(340, 480)
        self.resize(340, 560)

        self.setup_ui()
        self.open_visible_memos()
        self.refresh_list()

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._do_save)

    def schedule_save(self):
        self._save_timer.start(2000)

    def _do_save(self):
        for win in self.memo_windows.values():
            win.save_geometry()
        save_memos(self.memos_data)
        self.refresh_list()

    def setup_ui(self):
        self.setStyleSheet("QWidget { background: #1E1E1E; color: #E0E0E0; }")
        self.setFont(app_font(10))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 상단
        top = QHBoxLayout()
        title = QLabel("Ann's Memo")
        title.setFont(app_font(14, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFE066;")
        top.addWidget(title)
        top.addStretch()

        self.count_label = QLabel("")
        self.count_label.setFont(app_font(9))
        self.count_label.setStyleSheet("color: #888;")
        top.addWidget(self.count_label)

        btn_new = QPushButton("+ 새 메모")
        btn_new.setFont(app_font(10, QFont.Weight.Bold))
        btn_new.setFixedHeight(32)
        btn_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_new.setStyleSheet("""
            QPushButton {
                background: #FFE066; color: #333;
                border: none; border-radius: 16px; padding: 0 16px;
            }
            QPushButton:hover { background: #FFD633; }
        """)
        btn_new.clicked.connect(self.new_memo)
        top.addWidget(btn_new)
        layout.addLayout(top)

        # 검색
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("검색...")
        self.search_box.setFont(app_font(10))
        self.search_box.setFixedHeight(32)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background: #2C2C2C; border: 1px solid #444;
                border-radius: 16px; padding: 0 14px; color: #DDD;
            }
            QLineEdit:focus { border-color: #FFE066; }
        """)
        self.search_box.textChanged.connect(self.refresh_list)
        layout.addWidget(self.search_box)

        # 카드 리스트
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(0)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll)

    def new_memo(self):
        memo_id = datetime.now().strftime("%Y%m%d%H%M%S") + f"_{len(self.memos_data)}"
        data = {
            "id": memo_id,
            "text": "",
            "color": COLOR_NAMES[len(self.memos_data) % len(COLOR_NAMES)],
            "pinned": False,
            "visible": True,
            "created": now_str(),
            "modified": now_str(),
            "x": 200 + (len(self.memos_data) % 5) * 40,
            "y": 200 + (len(self.memos_data) % 5) * 30,
            "w": 260,
            "h": 220,
        }
        self.memos_data.append(data)
        self.open_memo_window(data)
        self._do_save()

    def open_memo_window(self, data):
        mid = data["id"]
        if mid in self.memo_windows:
            win = self.memo_windows[mid]
            win.show()
            win.raise_()
            win.text_edit.setFocus()
            return
        win = MemoWindow(data, self)
        self.memo_windows[mid] = win
        data["visible"] = True
        win.show()
        win.text_edit.setFocus()

    def open_visible_memos(self):
        for data in self.memos_data:
            if data.get("visible", False):
                self.open_memo_window(data)

    def on_memo_hidden(self, memo_id):
        if memo_id in self.memo_windows:
            del self.memo_windows[memo_id]
        self._do_save()

    def on_memo_deleted(self, memo_id):
        if memo_id in self.memo_windows:
            del self.memo_windows[memo_id]
        self.memos_data = [m for m in self.memos_data if m["id"] != memo_id]
        self._do_save()

    def refresh_list(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        query = self.search_box.text().lower()
        sorted_memos = sorted(
            self.memos_data,
            key=lambda m: (0 if m.get("pinned") else 1, m.get("modified", "")),
        )
        sorted_memos.reverse()

        count = 0
        for data in sorted_memos:
            if query and query not in data.get("text", "").lower():
                continue
            count += 1
            card = self._make_card(data)
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)

        self.count_label.setText(f"{count}개" if count else "")

    def _make_card(self, data):
        cn = data.get("color", "yellow")
        c = COLORS.get(cn, COLORS["yellow"])
        pinned = data.get("pinned", False)
        visible = data.get("visible", False)
        text = data.get("text", "").strip()
        preview = text[:60] + "..." if len(text) > 60 else (text or "(빈 메모)")

        card = QFrame()
        card.setFixedHeight(68)
        card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        card.setStyleSheet(f"""
            QFrame {{
                background: {c['bg']};
                border-radius: 8px;
                border-left: 5px solid {c['header']};
            }}
            QFrame:hover {{ border: 1px solid #ffffff33; border-left: 5px solid {c['header']}; }}
        """)

        cl = QHBoxLayout(card)
        cl.setContentsMargins(12, 8, 8, 8)
        cl.setSpacing(8)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title = QLabel(("📌 " if pinned else "") + preview)
        title.setFont(app_font(10, QFont.Weight.Bold if pinned else QFont.Weight.Normal))
        title.setStyleSheet(f"color: {TEXT_COLOR}; background: transparent;")
        title.setWordWrap(False)
        text_col.addWidget(title)

        parts = []
        cr = data.get("created", "")
        md = data.get("modified", "")
        if cr:
            parts.append(f"생성 {cr}")
        if md and md != cr:
            parts.append(f"편집 {md}")
        dl = QLabel("  ·  ".join(parts))
        dl.setFont(app_font(7))
        dl.setStyleSheet(f"color: {TEXT_COLOR}; background: transparent;")
        text_col.addWidget(dl)

        cl.addLayout(text_col)
        cl.addStretch()

        status = QLabel("열림" if visible else "숨김")
        status.setFont(app_font(8))
        status.setStyleSheet(f"color: {'#15803d' if visible else '#888'}; background: transparent;")
        cl.addWidget(status)

        card.mousePressEvent = lambda e, d=data: self._on_card_click(d)
        return card

    def _on_card_click(self, data):
        data["visible"] = True
        self.open_memo_window(data)
        self._do_save()

    def closeEvent(self, event):
        for win in list(self.memo_windows.values()):
            win.save_geometry()
        save_memos(self.memos_data)
        for win in list(self.memo_windows.values()):
            win.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Ann's Memo")
    app.setWindowIcon(make_app_icon())
    app.setFont(app_font(10))
    manager = MemoManager()
    manager.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
