"""Ann's Memo 자동 업데이트 모듈 — GitHub Releases 기반"""
import os
import sys
import json
import threading
import subprocess
import tempfile
from urllib.request import urlopen, Request
from urllib.error import URLError
from version import VERSION, GITHUB_REPO


def get_latest_release():
    """GitHub API에서 최신 릴리즈 정보 가져오기"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    req = Request(url, headers={"Accept": "application/vnd.github.v3+json"})
    try:
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "").lstrip("v")
            assets = data.get("assets", [])
            exe_url = None
            for a in assets:
                if a["name"].endswith(".exe"):
                    exe_url = a["browser_download_url"]
                    break
            return {"version": tag, "exe_url": exe_url, "html_url": data.get("html_url", "")}
    except (URLError, json.JSONDecodeError, KeyError):
        return None


def is_newer(remote_ver, local_ver):
    """버전 비교 (semantic versioning)"""
    def parse(v):
        return tuple(int(x) for x in v.split("."))
    try:
        return parse(remote_ver) > parse(local_ver)
    except (ValueError, TypeError):
        return False


def check_update_async(callback):
    """백그라운드에서 업데이트 체크 후 callback(result) 호출"""
    def _check():
        result = get_latest_release()
        if result and is_newer(result["version"], VERSION):
            callback(result)
        else:
            callback(None)
    t = threading.Thread(target=_check, daemon=True)
    t.start()


def download_and_replace(exe_url, callback_progress=None):
    """새 exe 다운로드 후 교체 (백그라운드)"""
    def _download():
        try:
            current_exe = sys.executable
            if not current_exe.endswith(".exe"):
                # 개발 모드 (python으로 실행 중)
                if callback_progress:
                    callback_progress("dev_mode")
                return

            # 임시 파일에 다운로드
            tmp_path = current_exe + ".new"
            req = Request(exe_url)
            with urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                with open(tmp_path, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if callback_progress and total > 0:
                            pct = int(downloaded / total * 100)
                            callback_progress(f"{pct}%")

            # 배치 파일로 교체 (현재 exe를 종료 후 덮어쓰기)
            bat_path = os.path.join(tempfile.gettempdir(), "ann_memo_update.bat")
            with open(bat_path, "w") as f:
                f.write(f"""@echo off
timeout /t 2 /nobreak >nul
del "{current_exe}"
move "{tmp_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
""")
            subprocess.Popen(["cmd", "/c", bat_path],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            if callback_progress:
                callback_progress("restart")

        except Exception as e:
            if callback_progress:
                callback_progress(f"error: {e}")

    t = threading.Thread(target=_download, daemon=True)
    t.start()
