import subprocess
import os
import sys

DEFAULT_STORAGE_PATH = os.environ.get(
    "HAC_STORAGE_PATH",
    os.path.expanduser("~/.mcp-servers/sap-commerce-mcp/hac_storage_state.json")
)

SSO_SCRIPT = """
import time
import json
import os
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1]
storage_path = sys.argv[2]
os.makedirs(os.path.dirname(os.path.abspath(storage_path)), exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        ignore_https_errors=True
    )
    page = context.new_page()

    try:
        page.goto(url, timeout=45000)
    except Exception:
        pass

    start_time = time.time()
    while time.time() - start_time < 180:
        if page.is_closed():
            break

        try:
            cur_url = page.url
        except Exception:
            time.sleep(1)
            continue

        try:
            u_inp = page.query_selector('input[name="j_username"]')
            p_inp = page.query_selector('input[name="j_password"]')
            if u_inp and p_inp and u_inp.is_visible() and not u_inp.input_value():
                u_inp.fill("admin")
                p_inp.fill("nimda")
        except Exception:
            pass

        url_lower = cur_url.lower()
        is_in_hac = (
            ("hac" in url_lower) and
            ("login" not in url_lower) and
            ("sso" not in url_lower) and
            ("accounts.sap.com" not in url_lower)
        )

        if is_in_hac:
            context.storage_state(path=storage_path)
            browser.close()
            sys.exit(0)

        time.sleep(1)

    try:
        browser.close()
    except Exception:
        pass
    sys.exit(1)
"""

def perform_interactive_sso(
    hac_url: str = "https://chrisdemo.apjdemo.hybris.com/hac",
    storage_path: str = DEFAULT_STORAGE_PATH,
    timeout_seconds: int = 180
) -> bool:
    """
    Spawns the headed browser process using the system python (which has Playwright installed).
    """
    try:
        res = subprocess.run(
            ["/usr/bin/python3", "-c", SSO_SCRIPT, hac_url, storage_path],
            timeout=timeout_seconds,
            capture_output=True,
            text=True
        )
        return res.returncode == 0
    except Exception as e:
        print(f"[sso_helper] Error: {e}", file=sys.stderr)
        return False
