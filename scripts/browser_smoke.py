"""Run a real local Chrome smoke test and capture actual Streamlit screenshots.

Optional developer check; requires installed Chrome or Edge. Uses a fresh temporary
browser profile and Chrome DevTools Protocol; no personal browser state is read.
"""

import argparse
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from websockets.sync.client import connect

ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_until(predicate, timeout: float = 35):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        try:
            result = predicate()
            if result:
                return result
        except (OSError, ValueError, KeyError) as exc:
            last = exc
        time.sleep(0.25)
    raise TimeoutError(f"Browser smoke check timed out. Last error: {last}")


def http_json(url: str):
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.load(response)


class Browser:
    def __init__(self, websocket):
        self.websocket = websocket
        self.sequence = 0

    def call(self, method: str, params: dict | None = None) -> dict:
        self.sequence += 1
        self.websocket.send(
            json.dumps({"id": self.sequence, "method": method, "params": params or {}})
        )
        while True:
            message = json.loads(self.websocket.recv(timeout=20))
            if message.get("id") == self.sequence:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})

    def evaluate(self, expression: str):
        response = self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        if "exceptionDetails" in response:
            raise RuntimeError(response["exceptionDetails"])
        return response.get("result", {}).get("value")

    def wait_text(self, text: str):
        return wait_until(
            lambda: self.evaluate(f"document.body?.innerText.includes({json.dumps(text)})")
        )

    def click(self, selector: str, text: str):
        # Only static selectors and internally selected labels are passed here.
        expression = f"(() => {{const e = [...document.querySelectorAll({json.dumps(selector)})].find(e => e.textContent.trim().endsWith({json.dumps(text)})); if(e){{e.click();return true;}} return false;}})()"
        wait_until(lambda: self.evaluate(expression))

    def page(self, label: str):
        self.click("a", label)
        wait_until(
            lambda: self.evaluate(
                f"document.querySelector('h1')?.innerText.includes({json.dumps(label)})"
            )
        )

    def select_dataset(self, label: str):
        rect = self.evaluate(
            "(() => {const r = document.querySelector('[data-testid=stSelectbox] [role=combobox]').getBoundingClientRect(); return {x:r.x+r.width/2,y:r.y+r.height/2};})()"
        )
        self.call(
            "Input.dispatchMouseEvent",
            {"type": "mousePressed", "button": "left", "clickCount": 1, **rect},
        )
        self.call(
            "Input.dispatchMouseEvent",
            {"type": "mouseReleased", "button": "left", "clickCount": 1, **rect},
        )
        self.click('[role="option"]', label)
        self.wait_text(
            "CSV file" if label == "Upload CSV" else "400 rows" if "Wine" in label else "1,200 rows"
        )

    def screenshot(self, destination: Path, *, plots: int = 0):
        if plots:
            wait_until(
                lambda: self.evaluate(
                    f"[...document.querySelectorAll('.js-plotly-plot')].filter(e => e.querySelector('.main-svg')).length >= {plots}"
                )
            )
        self.evaluate("window.scrollTo(0,0)")
        time.sleep(1)
        assert self.evaluate("document.querySelectorAll('[data-testid=stException]').length") == 0
        content = self.call(
            "Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False}
        )
        destination.write_bytes(base64.b64decode(content["data"]))


def run(output_dir: Path) -> dict:
    candidates = [
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    executable = next((p for p in candidates if p and Path(p).is_file()), None)
    if not executable:
        raise FileNotFoundError(
            "Install Chrome/Chromium/Edge to run the optional real-browser smoke check."
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    local = ROOT / "reports/local"
    local.mkdir(parents=True, exist_ok=True)
    screenshots = []
    port, debug_port = free_port(), free_port()
    process_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with (
        tempfile.TemporaryDirectory(
            prefix="dataguard-browser-", ignore_cleanup_errors=True
        ) as profile,
        (local / "browser_server.log").open("w", encoding="utf-8") as log,
    ):
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app/main.py",
                "--server.address=127.0.0.1",
                f"--server.port={port}",
            ],
            cwd=ROOT,
            stdout=log,
            stderr=log,
            creationflags=process_flags,
        )
        chrome = None
        try:
            url = f"http://127.0.0.1:{port}"
            wait_until(
                lambda: urllib.request.urlopen(f"{url}/_stcore/health", timeout=2).status == 200
            )
            chrome = subprocess.Popen(
                [
                    executable,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-default-browser-check",
                    f"--user-data-dir={profile}",
                    f"--remote-debugging-port={debug_port}",
                    "--remote-debugging-address=127.0.0.1",
                    "--window-size=1480,1150",
                    url,
                ],
                stdout=log,
                stderr=log,
                creationflags=process_flags,
            )
            endpoint = f"http://127.0.0.1:{debug_port}/json/list"
            pages = wait_until(lambda: http_json(endpoint))
            target = next(p for p in pages if p["type"] == "page")
            with connect(
                target["webSocketDebuggerUrl"], open_timeout=10, max_size=20 * 1024**2
            ) as websocket:
                browser = Browser(websocket)
                browser.call("Page.enable")
                browser.call(
                    "Emulation.setDeviceMetricsOverride",
                    {"width": 1480, "height": 1150, "deviceScaleFactor": 1, "mobile": False},
                )
                browser.wait_text("Quality indicators")
                browser.screenshot(output_dir / "overview.png", plots=2)
                screenshots.append("overview.png")
                browser.page("Data quality report")
                browser.wait_text("Failed rule opportunities")
                browser.screenshot(output_dir / "retail_quality.png")
                screenshots.append("retail_quality.png")
                browser.select_dataset("Wine Quality · red")
                browser.page("Anomaly detection")
                browser.click("button", "Run Isolation Forest")
                browser.wait_text("Flagged records")
                browser.screenshot(output_dir / "wine_anomalies.png", plots=2)
                screenshots.append("wine_anomalies.png")
                assert browser.evaluate(
                    "[...document.querySelectorAll('[data-testid=stMetricValue]')].some(e => e.innerText === '20')"
                )
                browser.page("Export results")
                browser.wait_text("Download anomaly results with source rows (CSV)")
                download_dir = Path(tempfile.mkdtemp(prefix="browser-downloads-", dir=local))
                browser.call(
                    "Browser.setDownloadBehavior",
                    {"behavior": "allow", "downloadPath": str(download_dir.resolve())},
                )
                browser.click("button", "Download current dataset (CSV)")
                downloaded = wait_until(lambda: next(download_dir.glob("*dataset*.csv"), None))
                import pandas as pd

                assert pd.read_csv(downloaded).shape == (400, 12)
                browser.click("button", "Download anomaly results with source rows (CSV)")
                anomaly_file = wait_until(lambda: next(download_dir.glob("*anomalies.csv"), None))
                assert pd.read_csv(anomaly_file).shape == (400, 18)
                # Verify file upload through the browser.
                browser.select_dataset("Upload CSV")
                browser.wait_text("CSV file")
                document = browser.call("DOM.getDocument")
                node = browser.call(
                    "DOM.querySelector",
                    {"nodeId": document["root"]["nodeId"], "selector": "input[type=file]"},
                )
                browser.call(
                    "DOM.setFileInputFiles",
                    {
                        "nodeId": node["nodeId"],
                        "files": [str(ROOT / "data/sample/online_retail_sample.csv")],
                    },
                )
                browser.wait_text("1,200 rows")
                assert (
                    browser.evaluate(
                        "document.querySelectorAll('[data-testid=stException]').length"
                    )
                    == 0
                )
                # Native responsive layout smoke check.
                browser.call(
                    "Emulation.setDeviceMetricsOverride",
                    {"width": 430, "height": 932, "deviceScaleFactor": 1, "mobile": True},
                )
                browser.screenshot(output_dir / "mobile_exports.png")
                screenshots.append("mobile_exports.png")
                malformed = Path(profile) / "synthetic_malformed.csv"
                malformed.write_text("a,b\n1,2,3\n", encoding="utf-8")
                browser.call(
                    "DOM.setFileInputFiles", {"nodeId": node["nodeId"], "files": [str(malformed)]}
                )
                browser.wait_text("Record 1 has 3 fields; expected 2.")
                assert (
                    browser.evaluate(
                        "document.querySelectorAll('[data-testid=stException]').length"
                    )
                    == 0
                )
            result = {
                "startup_health": "passed",
                "retail_quality_page": "passed",
                "wine_model": "20 flags / 400 rows; 11 measurements, default seed 42 and contamination 0.05",
                "csv_download": "400 rows x 12 columns verified",
                "anomaly_download": "400 rows x 18 columns verified",
                "csv_upload": "real retail sample loaded through browser file input",
                "malformed_csv": "synthetic malformed upload rejected with actionable error",
                "mobile_viewport": "430 x 932 screenshot captured",
                "screenshots": screenshots,
            }
            (local / "browser_smoke.json").write_text(
                json.dumps(result, indent=2) + "\n", encoding="utf-8"
            )
            print(json.dumps(result, indent=2))
            return result
        finally:
            for process in (chrome, server):
                if process is not None:
                    process.terminate()
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "assets/screenshots")
    run(parser.parse_args().output_dir)
