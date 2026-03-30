"""heymi memo - Windows 스티커 메모 스타일"""

import tkinter as tk
from tkinter import messagebox, font as tkfont
import json
import os
import sys
import ctypes
from datetime import datetime
from version import VERSION
from updater import check_update_async, download_and_replace

# ── 설정 ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "memos.json")

TEXT_COLOR = "#111827"
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_settings(s):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)


def get_app_name():
    return load_settings().get("app_name", "heymi memo")
FONT_SIZE = 10
FONT_SIZE_SMALL = 8
PLACEHOLDER = "메모를 작성하세요..."

COLORS = {
    "yellow":  {"bg": "#FFF9B1", "header": "#F5E44D", "name": "노랑"},
    "pink":    {"bg": "#FFD1DC", "header": "#F5A0B5", "name": "핑크"},
    "green":   {"bg": "#D4EDBC", "header": "#A8D88A", "name": "초록"},
    "blue":    {"bg": "#D0E8FF", "header": "#8CC8F0", "name": "파랑"},
    "purple":  {"bg": "#E8D5F5", "header": "#C9A5E0", "name": "보라"},
    "orange":  {"bg": "#FFE0B2", "header": "#F5C36D", "name": "주황"},
    "white":   {"bg": "#F5F5F5", "header": "#E0E0E0", "name": "흰색"},
    "black":   {"bg": "#2C2C2C", "header": "#1A1A1A", "name": "블랙"},
}
COLOR_NAMES = list(COLORS.keys())

_FF = None


def init_font(root):
    global _FF
    available = list(tkfont.families(root))
    for f in ["Pretendard", "Segoe UI", "맑은 고딕"]:
        if f in available:
            _FF = f
            return
    _FF = ""


def ff():
    return _FF or ""


def load_memos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_memos(memos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(memos, f, ensure_ascii=False, indent=2)


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ── 개별 메모 창 ──
class MemoWindow:
    def __init__(self, data, manager):
        self.data = data
        self.manager = manager
        self._has_text = bool(data.get("text", "").strip())
        self._drag_x = 0
        self._drag_y = 0

        self.win = tk.Toplevel(manager.root)
        if hasattr(manager, '_ico_path') and manager._ico_path:
            try:
                self.win.iconbitmap(manager._ico_path)
            except Exception:
                pass
        self.win.withdraw()
        self.setup_ui()
        self.apply_color()
        self.restore_geometry()
        self.apply_pin_state()
        self.win.deiconify()
        self.win.update_idletasks()
        self._dark_titlebar()
        self.win.protocol("WM_DELETE_WINDOW", self._on_win_close)

    def _dark_titlebar(self):
        """타이틀바를 다크 모드로 (Windows 10/11)"""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.win.winfo_id())
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
            )
        except Exception:
            pass

    def setup_ui(self):
        self.win.minsize(200, 150)
        self.win.resizable(True, True)

        # ── 툴바 ──
        self.toolbar = tk.Frame(self.win, height=30)
        self.toolbar.pack(fill="x", side="top")
        self.toolbar.pack_propagate(False)

        TB_FONT = (ff(), 11)
        TB_PAD = 5

        # 왼쪽: + 새 메모
        self.btn_new = tk.Label(
            self.toolbar, text="+", cursor="hand2",
            font=(ff(), 11, "bold"), padx=TB_PAD
        )
        self.btn_new.pack(side="left", padx=(8, 0))
        self.btn_new.bind("<Button-1>", lambda e: self.manager.new_memo())

        # 왼쪽: 고정 (압정)
        self.btn_pin = tk.Label(
            self.toolbar, text="📌", cursor="hand2",
            font=("Segoe UI Emoji", 9), padx=TB_PAD
        )
        self.btn_pin.pack(side="left")
        self.btn_pin.bind("<Button-1>", lambda e: self.toggle_pin())

        # 왼쪽: B 볼드
        self.btn_bold = tk.Label(
            self.toolbar, text="B", cursor="hand2",
            font=(ff(), 11, "bold"), padx=TB_PAD
        )
        self.btn_bold.pack(side="left")
        self.btn_bold.bind("<Button-1>", lambda e: self.toggle_bold())

        # 왼쪽: • 글머리 기호
        self.btn_bullet = tk.Label(
            self.toolbar, text="•", cursor="hand2",
            font=TB_FONT, padx=TB_PAD
        )
        self.btn_bullet.pack(side="left")
        self.btn_bullet.bind("<Button-1>", lambda e: self.insert_bullet())

        # 왼쪽: 1. 번호 목록
        self.btn_number = tk.Label(
            self.toolbar, text="1.", cursor="hand2",
            font=TB_FONT, padx=TB_PAD
        )
        self.btn_number.pack(side="left")
        self.btn_number.bind("<Button-1>", lambda e: self.insert_number())

        # 오른쪽: 삭제 (휴지통)
        self.btn_delete = tk.Label(
            self.toolbar, text="🗑", cursor="hand2",
            font=("Segoe UI Emoji", 9), padx=TB_PAD
        )
        self.btn_delete.pack(side="right")
        self.btn_delete.bind("<Button-1>", lambda e: self.delete_memo())

        # 오른쪽: 투명도
        self.btn_alpha = tk.Label(
            self.toolbar, text="◐", cursor="hand2",
            font=TB_FONT, padx=TB_PAD
        )
        self.btn_alpha.pack(side="right")
        self.btn_alpha.bind("<Button-1>", lambda e: self.cycle_alpha())

        # 오른쪽: ● 색상
        self.btn_color = tk.Label(
            self.toolbar, text="●", cursor="hand2",
            font=TB_FONT, padx=TB_PAD
        )
        self.btn_color.pack(side="right")
        self.btn_color.bind("<Button-1>", lambda e: self.cycle_color())

        # ── 텍스트 ──
        self.text = tk.Text(
            self.win, wrap="word", bd=0, padx=14, pady=10,
            insertbackground=TEXT_COLOR, undo=True,
            font=(ff(), FONT_SIZE), relief="flat",
            highlightthickness=0, spacing1=2, spacing3=5
        )
        self.text.pack(fill="both", expand=True)
        # 기본 폰트를 명시적으로 설정 (입력 시 깜빡임 방지)
        default_font = tkfont.Font(family=ff(), size=FONT_SIZE)
        self.text.configure(font=default_font)
        self.text.tag_configure("sel", font=default_font)
        # 볼드 태그 설정
        self.text.tag_configure("bold", font=(ff(), FONT_SIZE, "bold"))
        self.text.bind("<Control-b>", lambda e: self.toggle_bold())
        self.text.bind("<Control-y>", lambda e: self._redo())
        self.text.bind("<Control-Shift-z>", lambda e: self._redo())

        if not self._has_text:
            self.text.insert("1.0", PLACEHOLDER)
            self.text.config(fg="#999999")
        else:
            self.text.insert("1.0", self.data.get("text", ""))
            self.text.config(fg=TEXT_COLOR)
            self._restore_bold_ranges()

        self.win.bind("<MouseWheel>", lambda e: "break")
        self.text.bind("<Return>", self._on_return)
        self.text.bind("<FocusIn>", self._on_focus_in)
        self.text.bind("<FocusOut>", self._on_focus_out)
        self.text.bind("<FocusOut>", lambda e: (self._update_title(), self._update_date_label(), self.manager.refresh_list()), add="+")
        self.text.bind("<<Modified>>", self.on_text_changed)

        # ── 하단 날짜 ──
        self.footer = tk.Frame(self.win, height=20)
        self.footer.pack(fill="x", side="bottom")
        self.footer.pack_propagate(False)

        self.date_label = tk.Label(
            self.footer, text="", anchor="w",
            font=(ff(), 8), padx=10
        )
        self.date_label.pack(fill="x")
        self._update_date_label()
        self._update_title()

    def _on_focus_in(self, event):
        if self.text.get("1.0", "end-1c") == PLACEHOLDER:
            self.text.delete("1.0", "end")
            self.text.config(fg=TEXT_COLOR)

    def _on_focus_out(self, event):
        if not self.text.get("1.0", "end-1c").strip():
            self.text.insert("1.0", PLACEHOLDER)
            self.text.config(fg="#999999")

    def _update_pin_button(self):
        self.btn_pin.config(text="📌" if self.data.get("pinned") else "📍")

    def _update_title(self):
        text = self.data.get("text", "").strip()
        preview = text.split('\n')[0][:20] if text else "새 메모"
        pin = "📌 " if self.data.get("pinned") else ""
        new_title = f"{pin}{preview}"
        if self.win.title() != new_title:
            self.win.title(new_title)

    def _update_date_label(self):
        created = self.data.get("created", "")
        modified = self.data.get("modified", "")
        parts = []
        if created:
            parts.append(f"생성 {created}")
        if modified and modified != created:
            parts.append(f"편집 {modified}")
        self.date_label.config(text="  ·  ".join(parts))

    def apply_color(self):
        cn = self.data.get("color", "yellow")
        c = COLORS.get(cn, COLORS["yellow"])
        bg = c["bg"]
        hdr = c["header"]

        self.win.config(bg=bg)
        self.toolbar.config(bg=hdr)
        fg = "#E0E0E0" if cn == "black" else TEXT_COLOR
        self.text.config(bg=bg, selectbackground=hdr, insertbackground=fg)
        if self._has_text or self.text.get("1.0", "end-1c") != PLACEHOLDER:
            self.text.config(fg=fg)
        self.footer.config(bg=bg)
        self.date_label.config(bg=bg, fg="#666" if cn == "black" else "#888")

        # 툴바는 항상 다크 (웨일 스타일)
        dark_bar = "#1A1A1A"
        dark_fg = "#CCCCCC"
        self.toolbar.config(bg=dark_bar)
        for btn in [self.btn_new, self.btn_delete, self.btn_pin,
                     self.btn_bold, self.btn_bullet, self.btn_number]:
            btn.config(bg=dark_bar, fg=dark_fg)

        # 색상 버튼 = 다음 색상
        next_idx = (COLOR_NAMES.index(cn) + 1) % len(COLOR_NAMES)
        next_c = COLORS[COLOR_NAMES[next_idx]]
        self.btn_color.config(bg=dark_bar, fg=next_c["bg"])
        self.btn_alpha.config(bg=dark_bar, fg=dark_fg)

        self._update_pin_button()

    def apply_pin_state(self):
        self.win.attributes("-topmost", self.data.get("pinned", False))
        self._update_pin_button()

    def restore_geometry(self):
        x = self.data.get("x", 200)
        y = self.data.get("y", 200)
        w = self.data.get("w", 300)
        h = self.data.get("h", 300)
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        if x < -50 or x > sw - 50 or y < -50 or y > sh - 50:
            x, y = 200, 200
        self.win.geometry(f"{w}x{h}+{x}+{y}")
        self.win.attributes("-alpha", self.data.get("alpha", 1.0))

    def save_geometry(self):
        try:
            self.data["w"] = self.win.winfo_width()
            self.data["h"] = self.win.winfo_height()
            self.data["x"] = self.win.winfo_x()
            self.data["y"] = self.win.winfo_y()
        except tk.TclError:
            pass

    def _redo(self):
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass
        return "break"

    def on_text_changed(self, event=None):
        if self.text.edit_modified():
            content = self.text.get("1.0", "end-1c")
            if content != PLACEHOLDER:
                # 실행취소로 빈 텍스트가 됐을 때 — 이전 텍스트가 있었으면 저장 안 함
                if not content.strip() and self.data.get("text", "").strip():
                    self.text.edit_modified(False)
                    return
                self.data["text"] = content
                self.data["modified"] = now_str()
                self._has_text = bool(content.strip())
            self.text.edit_modified(False)
            self.manager.schedule_save()

    def toggle_bold(self):
        """선택 영역 볼드 토글 (Ctrl+B)"""
        try:
            sel_start = self.text.index("sel.first")
            sel_end = self.text.index("sel.last")
        except tk.TclError:
            return  # 선택 없음
        if "bold" in self.text.tag_names(sel_start):
            self.text.tag_remove("bold", sel_start, sel_end)
        else:
            self.text.tag_add("bold", sel_start, sel_end)
        self._save_bold_ranges()
        self.manager.schedule_save()

    def _save_bold_ranges(self):
        """볼드 태그 위치를 데이터에 저장"""
        ranges = []
        idx = "1.0"
        while True:
            start = self.text.tag_nextrange("bold", idx)
            if not start:
                break
            ranges.append([str(start[0]), str(start[1])])
            idx = start[1]
        self.data["bold_ranges"] = ranges

    def _restore_bold_ranges(self):
        """저장된 볼드 태그 복원"""
        for r in self.data.get("bold_ranges", []):
            try:
                self.text.tag_add("bold", r[0], r[1])
            except tk.TclError:
                pass

    def _on_return(self, event):
        """엔터 시 • 또는 번호 자동 이어쓰기"""
        import re
        line = self.text.index("insert").split(".")[0]
        line_text = self.text.get(f"{line}.0", f"{line}.end")
        # 빈 글머리/번호만 있으면 제거하고 끝
        if line_text.strip() in ("•", "") or re.match(r"^\d+\.\s*$", line_text):
            if line_text.startswith("• ") or re.match(r"^\d+\.\s*$", line_text):
                self.text.delete(f"{line}.0", f"{line}.end")
                return "break"
        # • 글머리 이어쓰기
        if line_text.startswith("• "):
            self.text.insert("insert", "\n• ")
            return "break"
        # 번호 이어쓰기
        m = re.match(r"^(\d+)\.\s", line_text)
        if m:
            next_num = int(m.group(1)) + 1
            self.text.insert("insert", f"\n{next_num}. ")
            return "break"
        return None

    def _get_target_lines(self):
        """선택 영역이 있으면 해당 줄 범위, 없으면 현재 줄"""
        try:
            start_line = int(self.text.index("sel.first").split(".")[0])
            end_line = int(self.text.index("sel.last").split(".")[0])
            return list(range(start_line, end_line + 1))
        except tk.TclError:
            return [int(self.text.index("insert").split(".")[0])]

    def insert_bullet(self):
        """선택된 줄들에 • 글머리 기호 추가/제거"""
        lines = self._get_target_lines()
        # 전부 •이면 제거, 아니면 추가
        all_bullet = all(self.text.get(f"{l}.0", f"{l}.end").startswith("• ") for l in lines)
        for line in lines:
            line_text = self.text.get(f"{line}.0", f"{line}.end")
            if all_bullet:
                if line_text.startswith("• "):
                    self.text.delete(f"{line}.0", f"{line}.2")
            else:
                if not line_text.startswith("• "):
                    self.text.insert(f"{line}.0", "• ")
        self.on_text_changed(None)

    def insert_number(self):
        """선택된 줄들에 번호 추가/제거"""
        import re
        lines = self._get_target_lines()
        # 전부 번호면 제거, 아니면 추가
        all_numbered = all(re.match(r"^\d+\.\s", self.text.get(f"{l}.0", f"{l}.end")) for l in lines)
        if all_numbered:
            for line in reversed(lines):
                m = re.match(r"^\d+\.\s", self.text.get(f"{line}.0", f"{line}.end"))
                if m:
                    self.text.delete(f"{line}.0", f"{line}.{len(m.group())}")
        else:
            num = 1
            # 위쪽 줄에서 시작 번호 찾기
            for i in range(lines[0] - 1, 0, -1):
                pm = re.match(r"^(\d+)\.\s", self.text.get(f"{i}.0", f"{i}.end"))
                if pm:
                    num = int(pm.group(1)) + 1
                    break
            for line in lines:
                line_text = self.text.get(f"{line}.0", f"{line}.end")
                m = re.match(r"^\d+\.\s", line_text)
                if m:
                    self.text.delete(f"{line}.0", f"{line}.{len(m.group())}")
                self.text.insert(f"{line}.0", f"{num}. ")
                num += 1
        self.on_text_changed(None)

    def toggle_pin(self):
        self.data["pinned"] = not self.data.get("pinned", False)
        self.apply_pin_state()
        self._update_title()
        self.manager.schedule_save()
        self.manager.refresh_list()

    def cycle_alpha(self):
        """투명도 순환: 100% → 80% → 60% → 40% → 100%"""
        alphas = [1.0, 0.8, 0.6, 0.4]
        current = self.data.get("alpha", 1.0)
        idx = alphas.index(current) if current in alphas else 0
        new_alpha = alphas[(idx + 1) % len(alphas)]
        self.data["alpha"] = new_alpha
        self.win.attributes("-alpha", new_alpha)
        self.manager.schedule_save()

    def cycle_color(self):
        idx = COLOR_NAMES.index(self.data.get("color", "yellow"))
        self.data["color"] = COLOR_NAMES[(idx + 1) % len(COLOR_NAMES)]
        self.apply_color()
        self.manager.schedule_save()
        self.manager.refresh_list()

    def delete_memo(self):
        if messagebox.askyesno("메모 삭제", "이 메모를 삭제할까요?", parent=self.win):
            self.save_geometry()
            self.win.destroy()
            self.manager.on_memo_deleted(self.data["id"])

    def _on_win_close(self):
        """창 닫기 — visible 유지 (재실행 시 다시 열림)"""
        self.save_geometry()
        self.win.withdraw()
        self.manager.schedule_save()

    def hide_memo(self):
        """숨기기 — visible False (리스트에서만 열 수 있음)"""
        self.save_geometry()
        self.data["visible"] = False
        self.win.withdraw()
        self.manager.on_memo_hidden(self.data["id"])

    def show_memo(self):
        self.data["visible"] = True
        self.win.deiconify()
        self.win.lift()
        self.text.focus_set()

    def destroy(self):
        self.save_geometry()
        try:
            self.win.destroy()
        except tk.TclError:
            pass


def _get_resource_path(filename):
    """PyInstaller exe 내장 리소스 또는 스크립트 폴더에서 파일 경로 반환"""
    if getattr(sys, 'frozen', False):
        # exe로 실행 중 — _MEIPASS에서 찾기
        base = sys._MEIPASS
    else:
        base = SCRIPT_DIR
    return os.path.join(base, filename)


def _ensure_icon():
    """아이콘 파일 찾기/생성. 반환: ico 경로 또는 None"""
    import tempfile
    # 1. exe 내장 리소스
    bundled = _get_resource_path("memo.ico")
    if os.path.exists(bundled):
        # 앱 데이터 폴더로 복사 (exe 내장은 임시경로라 재시작 시 경로 변경됨)
        app_dir = os.path.join(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()), "HeymiMemo")
        os.makedirs(app_dir, exist_ok=True)
        local_ico = os.path.join(app_dir, "memo.ico")
        if not os.path.exists(local_ico):
            import shutil
            shutil.copy2(bundled, local_ico)
        return local_ico
    # 2. 스크립트 폴더
    local = os.path.join(SCRIPT_DIR, "memo.ico")
    if os.path.exists(local):
        return local
    # 3. 런타임에 생성
    try:
        from PIL import Image, ImageDraw
        import struct
        app_dir = os.path.join(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()), "HeymiMemo")
        os.makedirs(app_dir, exist_ok=True)
        ico_path = os.path.join(app_dir, "memo.ico")
        imgs = []
        for sz in [256, 64, 32, 16]:
            img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            pad = sz // 16
            r = sz // 8
            body = [pad, pad + sz//10, sz - pad, sz - pad]
            d.rounded_rectangle(body, radius=r, fill=(255, 225, 80, 255))
            fold_h = sz // 10
            d.rounded_rectangle([pad, pad, sz-pad, pad+fold_h+r], radius=r, fill=(255, 210, 50, 255))
            d.rectangle([pad, pad+fold_h, sz-pad, pad+fold_h+r], fill=(255, 210, 50, 255))
            pin_r = max(2, sz // 12)
            pin_cx, pin_cy = pad + sz//8, pad + sz//16
            d.ellipse([pin_cx-pin_r, pin_cy-pin_r, pin_cx+pin_r, pin_cy+pin_r], fill=(230, 70, 70, 230))
            imgs.append(img)
        imgs[0].save(ico_path, format="ICO", sizes=[(s, s) for s in [256, 64, 32, 16]], append_images=imgs[1:])
        return ico_path
    except Exception:
        return None


# ── 메인 관리 창 ──
class MemoManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(get_app_name())
        self.root.geometry("360x560")
        self.root.minsize(340, 400)
        self.root.configure(bg="#1E1E1E")
        # ICO 파일로 아이콘 설정 (작업표시줄 + 타이틀바)
        self._ico_path = _ensure_icon()
        if self._ico_path:
            try:
                self.root.iconbitmap(self._ico_path)
            except Exception:
                self._ico_path = None

        init_font(self.root)

        self.memos_data = load_memos()
        self.memo_windows = {}
        self._save_pending = False
        self._color_labels = self._load_color_labels()
        self._collapsed_colors = set()
        self._color_order = self._load_color_order()

        self.setup_ui()
        self.root.update_idletasks()
        self._dark_titlebar_root()
        self.open_visible_memos()
        self.refresh_list()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._auto_save_loop()
        self._check_for_updates()

    def _dark_titlebar_root(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
            )
        except Exception:
            pass

    def setup_ui(self):
        top = tk.Frame(self.root, bg="#1E1E1E")
        top.pack(fill="x", padx=12, pady=(12, 4))

        tk.Label(
            top, text=get_app_name(), bg="#1E1E1E", fg="#FFE066",
            font=(ff(), 14, "bold"), cursor="hand2"
        )
        self.title_label.pack(side="left")
        self.title_label.bind("<Double-Button-1>", lambda e: self._rename_app())

        self.count_label = tk.Label(
            top, text="", bg="#1E1E1E", fg="#888", font=(ff(), 10)
        )
        self.count_label.pack(side="left", padx=(10, 0))

        self.btn_toggle_all = tk.Label(
            top, text="▼", bg="#1E1E1E", fg="#888",
            font=(ff(), 9, "bold"), cursor="hand2", padx=6
        )
        self.btn_toggle_all.pack(side="left", padx=(6, 0))
        self.btn_toggle_all.bind("<Button-1>", lambda e: self._toggle_all_groups())

        # 업데이트 버튼 (숨김 상태, 새 버전 있을 때만 표시)
        self.btn_update = tk.Label(
            top, text=f"v{VERSION}", bg="#1E1E1E", fg="#555",
            font=(ff(), 8), padx=4
        )
        self.btn_update.pack(side="right", padx=(0, 4))

        tk.Button(
            top, text="+ 새 메모", bg="#FFE066", fg="#333",
            font=(ff(), 10, "bold"), bd=0, padx=14, pady=4,
            cursor="hand2", activebackground="#FFD633",
            command=self.new_memo
        ).pack(side="right")

        sf = tk.Frame(self.root, bg="#1E1E1E")
        sf.pack(fill="x", padx=12, pady=(4, 8))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_list())
        tk.Entry(
            sf, textvariable=self.search_var,
            bg="#2C2C2C", fg="#DDD", insertbackground="#DDD",
            bd=0, font=(ff(), 10)
        ).pack(fill="x", ipady=6, padx=2)

        lf = tk.Frame(self.root, bg="#1E1E1E")
        lf.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.canvas = tk.Canvas(lf, bg="#1E1E1E", highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.cards_frame = tk.Frame(self.canvas, bg="#1E1E1E")
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.cards_frame, anchor="nw"
        )
        self.cards_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.bind_all("<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def schedule_save(self):
        if not self._save_pending:
            self._save_pending = True
            self.root.after(2000, self._do_save)

    def _do_save(self):
        self._save_pending = False
        for w in self.memo_windows.values():
            w.save_geometry()
        save_memos(self.memos_data)

    def _last_memo_window(self):
        """마지막 열려있는 메모 창 반환"""
        for mid in reversed(list(self.memo_windows.keys())):
            try:
                w = self.memo_windows[mid]
                w.win.winfo_width()  # 살아있는지 체크
                return w
            except Exception:
                pass
        return None

    def _last_memo_size(self):
        """마지막 메모 창 크기"""
        w = self._last_memo_window()
        if w:
            return (w.win.winfo_width(), w.win.winfo_height())
        for d in reversed(self.memos_data):
            if d.get("w", 0) > 0:
                return (d["w"], d["h"])
        return (300, 300)

    def _last_memo_pos(self):
        """마지막 메모 창 위치"""
        w = self._last_memo_window()
        if w:
            return (w.win.winfo_x(), w.win.winfo_y())
        for d in reversed(self.memos_data):
            if d.get("x") is not None:
                return (d["x"], d["y"])
        return (200, 200)

    def new_memo(self):
        mid = datetime.now().strftime("%Y%m%d%H%M%S") + f"_{len(self.memos_data)}"
        lw, lh = self._last_memo_size()
        lx, ly = self._last_memo_pos()
        data = {
            "id": mid, "text": "",
            "color": COLOR_NAMES[len(self.memos_data) % len(COLOR_NAMES)],
            "pinned": False, "visible": True,
            "created": now_str(), "modified": now_str(),
            "x": lx + lw + 10, "y": ly,
            "w": lw, "h": lh,
        }
        self.memos_data.append(data)
        self.open_memo_window(data)
        self._do_save()
        self.refresh_list()

    def open_memo_window(self, data):
        mid = data["id"]
        if mid in self.memo_windows:
            self.memo_windows[mid].show_memo()
            return
        self.memo_windows[mid] = MemoWindow(data, self)
        data["visible"] = True

    def open_visible_memos(self):
        for d in self.memos_data:
            if d.get("visible"):
                self.open_memo_window(d)

    def on_memo_hidden(self, mid):
        self.memo_windows.pop(mid, None)
        self._do_save()
        self.refresh_list()

    def on_memo_deleted(self, mid):
        self.memo_windows.pop(mid, None)
        self.memos_data = [m for m in self.memos_data if m["id"] != mid]
        self._do_save()
        self.refresh_list()

    def refresh_list(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()
        q = self.search_var.get().lower()
        memos = sorted(self.memos_data,
            key=lambda m: (0 if m.get("pinned") else 1, m.get("modified","")))
        memos.reverse()

        # 검색 필터
        filtered = [d for d in memos if not q or q in d.get("text","").lower()]

        # 색상별 그룹
        if not hasattr(self, '_collapsed_colors'):
            self._collapsed_colors = set()

        groups = {}
        for d in filtered:
            cn = d.get("color", "yellow")
            groups.setdefault(cn, []).append(d)

        count = len(filtered)
        if not hasattr(self, '_color_headers'):
            self._color_headers = {}
        self._color_headers.clear()

        # 커스텀 순서 사용
        order = self._color_order if hasattr(self, '_color_order') else COLOR_NAMES
        for cn in order:
            if cn not in groups:
                continue
            items = groups[cn]
            c = COLORS[cn]
            collapsed = cn in self._collapsed_colors

            # 색상 그룹 헤더
            hdr = tk.Frame(self.cards_frame, bg=c["header"], cursor="hand2")
            hdr.pack(fill="x", pady=(6, 0))
            self._color_headers[cn] = hdr
            arrow = "▶" if collapsed else "▼"
            hdr_fg = "#E0E0E0" if cn == "black" else TEXT_COLOR
            label_name = self._color_labels.get(cn, c['name'])

            # 드래그 핸들
            grip = tk.Label(hdr, text="≡", bg=c["header"], fg=hdr_fg,
                font=(ff(), 11), cursor="fleur", padx=4)
            grip.pack(side="right", padx=(0, 6))
            grip.bind("<Button-1>", lambda e, n=cn: self._drag_start(e, n))
            grip.bind("<B1-Motion>", self._drag_motion)
            grip.bind("<ButtonRelease-1>", self._drag_end)

            lbl = tk.Label(hdr, text=f"{arrow}  {label_name} ({len(items)})",
                bg=c["header"], fg=hdr_fg,
                font=(ff(), 9, "bold"), padx=8, pady=3,
                anchor="w")
            lbl.pack(fill="x")
            hdr.bind("<Button-1>", lambda e, n=cn: self._delayed_toggle(n))
            hdr.bind("<Double-Button-1>", lambda e, n=cn: self._rename_color_group(n))
            for w in [lbl]:
                w.bind("<Button-1>", lambda e, n=cn: self._delayed_toggle(n))
                w.bind("<Double-Button-1>", lambda e, n=cn: self._rename_color_group(n))

            if not collapsed:
                for d in items:
                    self._card(d)

        self.count_label.config(text=f"{count}개" if count else "")

    def _delayed_toggle(self, color_name):
        """싱글클릭 → 300ms 대기 후 토글 (더블클릭과 구분)"""
        self._pending_toggle = color_name
        self.root.after(300, lambda: self._do_toggle(color_name))

    def _do_toggle(self, color_name):
        if getattr(self, '_pending_toggle', None) == color_name:
            self._pending_toggle = None
            self._toggle_color_group(color_name)

    def _toggle_color_group(self, color_name):
        if not hasattr(self, '_collapsed_colors'):
            self._collapsed_colors = set()
        if color_name in self._collapsed_colors:
            self._collapsed_colors.discard(color_name)
        else:
            self._collapsed_colors.add(color_name)
        self.refresh_list()

    def _rename_color_group(self, color_name):
        """색상 그룹 이름 인라인 편집"""
        self._pending_toggle = None
        hdr = self._color_headers.get(color_name)
        if hdr:
            for child in hdr.winfo_children():
                if isinstance(child, tk.Label):
                    self._inline_edit(hdr, child, color_name)
                    return

    def _inline_edit(self, hdr, label, color_name):
        """라벨 위치에 Entry를 덮어씌워 인라인 편집"""
        c = COLORS[color_name]
        current = self._color_labels.get(color_name, c["name"])

        entry = tk.Entry(hdr, bg=c["header"], fg=label.cget("fg"),
                         font=(ff(), 9, "bold"), bd=0, insertbackground=label.cget("fg"),
                         highlightthickness=1, highlightcolor="#FFE066")
        entry.place(x=label.winfo_x(), y=label.winfo_y(),
                    width=label.winfo_width(), height=label.winfo_height())
        entry.insert(0, current)
        entry.select_range(0, "end")
        entry.focus_set()

        def save(event=None):
            new_name = entry.get().strip()
            if new_name:
                self._color_labels[color_name] = new_name
                self._save_color_labels()
            entry.destroy()
            self.refresh_list()

        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)
        entry.bind("<Escape>", lambda e: (entry.destroy(), self.refresh_list()))

    def _save_color_labels(self):
        path = os.path.join(SCRIPT_DIR, "color_labels.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._color_labels, f, ensure_ascii=False, indent=2)

    def _load_color_labels(self):
        path = os.path.join(SCRIPT_DIR, "color_labels.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _drag_start(self, event, color_name):
        """그룹 드래그 시작"""
        self._dragging_color = color_name
        self._drag_start_y = event.y_root

    def _drag_motion(self, event):
        """드래그 중 — 위치에 따라 순서 변경"""
        if not hasattr(self, '_dragging_color') or not self._dragging_color:
            return
        dy = event.y_root - self._drag_start_y
        if abs(dy) < 25:
            return
        direction = 1 if dy > 0 else -1
        order = list(self._color_order)
        # 현재 보이는 순서에서만 이동
        visible = [cn for cn in order if cn in self._color_headers]
        cn = self._dragging_color
        if cn not in visible:
            return
        vi = visible.index(cn)
        new_vi = vi + direction
        if new_vi < 0 or new_vi >= len(visible):
            return
        # order에서 실제 위치 교환
        oi = order.index(cn)
        swap_cn = visible[new_vi]
        oj = order.index(swap_cn)
        order[oi], order[oj] = order[oj], order[oi]
        self._color_order = order
        self._drag_start_y = event.y_root
        self._save_color_order()
        self.refresh_list()

    def _drag_end(self, event):
        """드래그 끝"""
        self._dragging_color = None

    def _save_color_order(self):
        path = os.path.join(SCRIPT_DIR, "color_order.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._color_order, f, ensure_ascii=False)

    def _load_color_order(self):
        path = os.path.join(SCRIPT_DIR, "color_order.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return list(COLOR_NAMES)

    def _toggle_all_groups(self):
        if not hasattr(self, '_collapsed_colors'):
            self._collapsed_colors = set()
        used_colors = set(d.get("color", "yellow") for d in self.memos_data)
        if self._collapsed_colors >= used_colors:
            # 전부 닫혀있으면 → 모두 열기
            self._collapsed_colors.clear()
            self.btn_toggle_all.config(text="▼")
        else:
            # 하나라도 열려있으면 → 모두 닫기
            self._collapsed_colors = used_colors.copy()
            self.btn_toggle_all.config(text="▶")
        self.refresh_list()

    def _card(self, data):
        cn = data.get("color","yellow")
        c = COLORS.get(cn, COLORS["yellow"])
        pinned = data.get("pinned")
        visible = data.get("visible")
        text = data.get("text","").strip()
        line1 = text.split('\n')[0].strip() if text else ""
        preview = line1[:40]+"..." if len(line1)>40 else (line1 or "(빈 메모)")

        card = tk.Frame(self.cards_frame, bg=c["bg"], cursor="hand2")
        card.pack(fill="x", pady=3)

        ct = tk.Frame(card, bg=c["bg"], padx=10, pady=6)
        ct.pack(side="left", fill="both", expand=True)

        card_fg = "#E0E0E0" if cn == "black" else TEXT_COLOR
        tk.Label(ct, text=("📌 " if pinned else "")+preview,
            bg=c["bg"], fg=card_fg,
            font=(ff(), 10, "bold" if pinned else "normal"),
            anchor="w").pack(fill="x")

        parts = []
        if data.get("created"): parts.append(f"생성 {data['created']}")
        if data.get("modified") and data["modified"]!=data.get("created"):
            parts.append(f"편집 {data['modified']}")
        tk.Label(ct, text="  ·  ".join(parts),
            bg=c["bg"], fg="#666" if cn=="black" else "#888",
            font=(ff(), 8), anchor="w").pack(fill="x")

        right_frame = tk.Frame(card, bg=c["bg"])
        right_frame.pack(side="right", padx=(0, 4))

        del_btn = tk.Label(right_frame, text="✕", bg=c["bg"], fg="#999",
            font=(ff(), 10), cursor="hand2", padx=4)
        del_btn.pack(side="right")
        del_btn.bind("<Button-1>", lambda e, d=data: self._delete_card(d))

        for w in card.winfo_children():
            w.bind("<Button-1>", lambda e,d=data: self._click(d))
            for ww in w.winfo_children():
                ww.bind("<Button-1>", lambda e,d=data: self._click(d))

    def _delete_card(self, data):
        if messagebox.askyesno("메모 삭제", "이 메모를 삭제할까요?"):
            mid = data["id"]
            if mid in self.memo_windows:
                self.memo_windows[mid].destroy()
                del self.memo_windows[mid]
            self.memos_data = [m for m in self.memos_data if m["id"] != mid]
            self._do_save()
            self.refresh_list()

    def _click(self, data):
        data["visible"] = True
        self.open_memo_window(data)
        self._do_save()
        self.refresh_list()

    def _auto_save_loop(self):
        """10초마다 자동 저장 (강제종료 대비)"""
        for w in self.memo_windows.values():
            w.save_geometry()
        save_memos(self.memos_data)
        self.root.after(10000, self._auto_save_loop)

    def _rename_app(self):
        """앱 이름 더블클릭으로 변경"""
        current = get_app_name()
        entry = tk.Entry(self.title_label.master, bg="#1E1E1E", fg="#FFE066",
                         font=(ff(), 14, "bold"), bd=0, insertbackground="#FFE066",
                         highlightthickness=1, highlightcolor="#FFE066")
        entry.place(x=self.title_label.winfo_x(), y=self.title_label.winfo_y(),
                    width=self.title_label.winfo_width() + 50, height=self.title_label.winfo_height())
        entry.insert(0, current)
        entry.select_range(0, "end")
        entry.focus_set()

        def save(event=None):
            new_name = entry.get().strip()
            if new_name:
                s = load_settings()
                s["app_name"] = new_name
                save_settings(s)
                self.title_label.config(text=new_name)
                self.root.title(new_name)
            entry.destroy()

        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)
        entry.bind("<Escape>", lambda e: entry.destroy())

    def _check_for_updates(self):
        """시작 시 GitHub에서 최신 버전 체크"""
        def on_result(result):
            if result:
                self._update_info = result
                self.root.after(0, self._show_update_available)
        check_update_async(on_result)

    def _show_update_available(self):
        """새 버전 있으면 버튼 강조"""
        ver = self._update_info["version"]
        self.btn_update.config(
            text=f"🔄 v{ver}", fg="#FFE066", cursor="hand2",
            font=(ff(), 9, "bold")
        )
        self.btn_update.bind("<Button-1>", lambda e: self._do_update())

    def _do_update(self):
        """업데이트 실행"""
        info = getattr(self, '_update_info', None)
        if not info:
            return
        if not info.get("exe_url"):
            messagebox.showinfo("업데이트", f"v{info['version']} 사용 가능!\n{info['html_url']}")
            return
        self.btn_update.config(text="다운로드 중...", fg="#888")
        def on_progress(status):
            if status == "dev_mode":
                self.root.after(0, lambda: messagebox.showinfo(
                    "업데이트", f"v{info['version']} 사용 가능!\n개발 모드에서는 수동 업데이트 필요"))
            elif status == "restart":
                self.root.after(0, self.root.destroy)
            elif status.startswith("error"):
                self.root.after(0, lambda: self.btn_update.config(
                    text="업데이트 실패", fg="#FF6666"))
            elif status.endswith("%"):
                self.root.after(0, lambda s=status: self.btn_update.config(text=f"⬇ {s}"))
        download_and_replace(info["exe_url"], on_progress)

    def on_close(self):
        for w in list(self.memo_windows.values()):
            w.destroy()
        save_memos(self.memos_data)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MemoManager()
    app.run()
