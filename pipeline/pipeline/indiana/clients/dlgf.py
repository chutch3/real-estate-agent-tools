import re
import urllib.parse
import urllib.request


class DLGFClient:
    _DOWNLOAD_PATH = "/public/download.aspx"

    def __init__(self, base_url: str = "https://gateway.ifionline.org") -> None:
        self._download_url = f"{base_url}{self._DOWNLOAD_PATH}"

    def fetch_taxbill_zip(self, *, county_num: str, year: str) -> bytes:
        """Download the Tax Bill zip for a given Gateway county code and pay year."""
        session_id, hidden_fields = self._get_session()
        params = {
            **hidden_fields,
            "ctl00$ContentPlaceHolder1$DropDownList1": "3",  # Tax Bill
            "ctl00$ContentPlaceHolder1$DropDownList2": year,
            "ctl00$ContentPlaceHolder1$DropDownList3": county_num,
            "ctl00$ContentPlaceHolder1$button2": "Download",
        }
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(
            self._download_url,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0",
                "Referer": self._download_url,
                "Cookie": f"ASP.NET_SessionId={session_id}",
            },
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            return resp.read()

    def _get_session(self) -> tuple[str, dict[str, str]]:
        """Fetch the download page and return (session_id, hidden_form_fields)."""
        req = urllib.request.Request(
            self._download_url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        cookie_jar: dict[str, str] = {}
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
        with opener.open(req) as resp:
            raw_cookies = resp.headers.get_all("Set-Cookie") or []
            for c in raw_cookies:
                m = re.search(r"ASP\.NET_SessionId=([^;]+)", c)
                if m:
                    cookie_jar["ASP.NET_SessionId"] = m.group(1)
            content = resp.read().decode("utf-8", errors="replace")

        fields: dict[str, str] = {}
        for hidden in re.findall(r'<input[^>]+type=["\']hidden["\'][^>]*>', content, re.I):
            name_m = re.search(r'name=["\']([^"\']+)["\']', hidden, re.I)
            val_m = re.search(r'value=["\']([^"\']*)["\']', hidden, re.I)
            if name_m:
                fields[name_m.group(1)] = val_m.group(1) if val_m else ""

        return cookie_jar.get("ASP.NET_SessionId", ""), fields
