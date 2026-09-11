import os
import re
import json
from typing import Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HACClient:
    """
    Client for interacting with SAP Commerce Cloud (Hybris) Administration Console (HAC).
    Supports local instances, remote instances, form login, and SAP SSO sessions.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        sso_storage_path: Optional[str] = None
    ):
        self.username = username or os.environ.get("HAC_USER", "admin")
        self.password = password or os.environ.get("HAC_PASS", "nimda")
        effective_url = base_url or os.environ.get("HAC_URL", "https://localhost:9002")
        self.sso_storage_path = sso_storage_path or os.path.expanduser(
            "~/.gemini/antigravity-cli/brain/88fd2c1d-9fbd-4eea-b5d3-da3e40a970e9/scratch/hac_storage_state.json"
        )
        self.session = requests.Session()
        self.session.verify = False
        # Browser User-Agent to satisfy reverse proxies and Cloudflare/WAF
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
        
        self.set_base_url(effective_url)
        self._csrf_token: Optional[str] = None
        self.load_sso_session()

    def set_base_url(self, url: str) -> None:
        url = url.strip().rstrip("/")
        self.base_url = url
        self._csrf_token = None

    def load_sso_session(self, storage_path: Optional[str] = None) -> bool:
        path = storage_path or self.sso_storage_path
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cookies = data.get("cookies", [])
            for c in cookies:
                domain = c.get("domain", "").lstrip(".")
                self.session.cookies.set(
                    c["name"],
                    c["value"],
                    domain=domain,
                    path=c.get("path", "/")
                )
            return len(cookies) > 0
        except Exception:
            return False

    def get_csrf_token(self, force_refresh: bool = False, page_path: str = "/console/flexsearch") -> str:
        if self._csrf_token and not force_refresh:
            return self._csrf_token

        url = f"{self.base_url}{page_path}"
        resp = self.session.get(url, timeout=15)
        csrf = self._extract_csrf(resp.text)
        if not csrf:
            resp_home = self.session.get(f"{self.base_url}/", timeout=15)
            csrf = self._extract_csrf(resp_home.text)

        if csrf:
            self._csrf_token = csrf
            return csrf
        raise RuntimeError(f"Could not extract CSRF token from {url} (HTTP {resp.status_code})")

    def _extract_csrf(self, html: str) -> Optional[str]:
        m = re.search(r'name=["\']_csrf["\']\s+content=["\']([^"\']+)["\']', html)
        if m:
            return m.group(1)
        m = re.search(r'content=["\']([^"\']+)["\']\s+name=["\']_csrf["\']', html)
        if m:
            return m.group(1)
        m = re.search(r'<input[^>]+name=["\']_csrf["\'][^>]+value=["\']([^"\']+)["\']', html)
        if m:
            return m.group(1)
        return None

    def login_form(self) -> bool:
        """Attempts standard username/password login."""
        login_url = f"{self.base_url}/login"
        resp = self.session.get(login_url, timeout=10)
        csrf = self._extract_csrf(resp.text) or ""

        auth_url = f"{self.base_url}/j_spring_security_check"
        data = {
            "j_username": self.username,
            "j_password": self.password,
            "_csrf": csrf
        }
        auth_resp = self.session.post(auth_url, data=data, timeout=10, allow_redirects=True)
        if auth_resp.status_code in (200, 302) and "login" not in auth_resp.url.lower():
            return True
        return False

    def ensure_authenticated(self) -> None:
        """Tries active session, then SSO session, then form login."""
        try:
            check_resp = self.session.get(f"{self.base_url}/", timeout=10)
            if check_resp.status_code == 200 and "login" not in check_resp.url.lower():
                return
        except Exception:
            pass

        if self.load_sso_session():
            try:
                check_resp = self.session.get(f"{self.base_url}/", timeout=10)
                if check_resp.status_code == 200 and "login" not in check_resp.url.lower():
                    return
            except Exception:
                pass

        if not self.login_form():
            raise PermissionError(
                f"Failed to authenticate with HAC at {self.base_url}. "
                "If this instance is protected by SAP SSO, please run `hac_sso_login` to authenticate."
            )

    def execute_flexsearch(self, query: str, max_count: int = 50) -> Dict[str, Any]:
        """Executes a FlexibleSearch query on HAC."""
        self.ensure_authenticated()
        csrf = self.get_csrf_token(page_path="/console/flexsearch")
        url = f"{self.base_url}/console/flexsearch/execute"
        headers = {
            "X-CSRF-TOKEN": csrf,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        data = {
            "flexibleSearchQuery": query,
            "maxCount": str(max_count)
        }
        resp = self.session.post(url, headers=headers, data=data, timeout=60)
        if resp.status_code == 403:
            csrf = self.get_csrf_token(force_refresh=True, page_path="/console/flexsearch")
            headers["X-CSRF-TOKEN"] = csrf
            resp = self.session.post(url, headers=headers, data=data, timeout=60)

        try:
            return resp.json()
        except Exception:
            return {
                "status_code": resp.status_code,
                "raw_text": resp.text[:1000],
                "exception": f"Unexpected response from HAC (HTTP {resp.status_code})"
            }

    def import_impex(
        self,
        script_content: str,
        validation_enum: str = "IMPORT_STRICT",
        legacy_mode: bool = False,
        enable_code_execution: bool = True,
        max_threads: int = 1
    ) -> Dict[str, Any]:
        """Imports an ImpEx script through HAC."""
        self.ensure_authenticated()
        csrf = self.get_csrf_token(page_path="/console/impex/import")
        url = f"{self.base_url}/console/impex/import"
        headers = {
            "X-CSRF-TOKEN": csrf,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        data = {
            "scriptContent": script_content,
            "validationEnum": validation_enum,
            "encoding": "UTF-8",
            "maxThreads": str(max_threads),
            "legacyMode": str(legacy_mode).lower(),
            "enableCodeExecution": str(enable_code_execution).lower()
        }
        resp = self.session.post(url, headers=headers, data=data, timeout=180)
        if resp.status_code == 403:
            csrf = self.get_csrf_token(force_refresh=True, page_path="/console/impex/import")
            headers["X-CSRF-TOKEN"] = csrf
            resp = self.session.post(url, headers=headers, data=data, timeout=180)

        soup = BeautifulSoup(resp.text, "html.parser")
        result_span = soup.find(id="impexResult")
        
        if result_span:
            result_msg = result_span.get("data-result", "").strip()
            level = result_span.get("data-level", "").lower()
            is_error = level == "error" or "error" in result_msg.lower() or "failed" in result_msg.lower()
            status = "ERROR" if is_error else "SUCCESS"
            
            # Check if there is dump info or error details in neighboring elements
            dump_elem = soup.find(id="dump") or soup.find(class_="impexResultError")
            dump_text = dump_elem.get_text("\n", strip=True) if dump_elem else ""
            
            return {
                "status": status,
                "level": level,
                "message": result_msg,
                "dump": dump_text,
                "status_code": resp.status_code
            }

        # Fallback parsing
        raw_text = resp.text
        has_error = any(k in raw_text.lower() for k in ["impexerror", "exception", "dumped_lines"])
        has_success = any(k in raw_text.lower() for k in ["finished successfully", "import finished"])
        status = "SUCCESS" if (has_success and not has_error) else ("ERROR" if has_error else "UNKNOWN")

        return {
            "status": status,
            "status_code": resp.status_code,
            "message": "Import completed" if status == "SUCCESS" else "Import encountered issues",
            "raw_snippet": raw_text[:500]
        }

    def execute_groovy(self, script: str, commit: bool = True) -> Dict[str, Any]:
        """Executes a Groovy script in HAC Scripting Console."""
        self.ensure_authenticated()
        csrf = self.get_csrf_token(page_path="/console/scripting")
        url = f"{self.base_url}/console/scripting/execute"
        headers = {
            "X-CSRF-TOKEN": csrf,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        data = {
            "script": script,
            "scriptType": "groovy",
            "commit": str(commit).lower()
        }
        resp = self.session.post(url, headers=headers, data=data, timeout=180)
        if resp.status_code == 403:
            csrf = self.get_csrf_token(force_refresh=True, page_path="/console/scripting")
            headers["X-CSRF-TOKEN"] = csrf
            resp = self.session.post(url, headers=headers, data=data, timeout=180)

        try:
            return resp.json()
        except Exception:
            return {
                "status_code": resp.status_code,
                "raw_text": resp.text[:1000],
                "exception": f"Unexpected response from HAC (HTTP {resp.status_code})"
            }
