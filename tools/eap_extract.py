from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin

from curl_cffi import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fairbairn_probe"
OUT.mkdir(exist_ok=True)

SEEDS = [
    "https://www.sunwater.com.au/community/preparing-for-emergencies/emergency-management/",
    "https://www.sunwater.com.au/emergency-management/",
    "https://www.sunwater.com.au/dams/fairbairn-dam/",
    "https://www.sunwater.com.au/wp-json/wp/v2/search?search=Fairbairn&per_page=100",
    "https://www.sunwater.com.au/wp-json/wp/v2/media?search=Fairbairn&per_page=100",
    "https://www.sunwater.com.au/wp-sitemap-posts-attachment-1.xml",
    "https://www.sunwater.com.au/wp-sitemap.xml",
    "https://web.archive.org/cdx/search/cdx?url=www.dlgwv.qld.gov.au/__data/assets/pdf_file/0008/1619711/fairbairn-eap.pdf&output=json&filter=statuscode:200&collapse=digest",
    "https://web.archive.org/cdx/search/cdx?url=www.sunwater.com.au/wp-content/uploads/*Fairbairn*EAP*.pdf&output=json&filter=statuscode:200&collapse=digest",
]

GUESSES = [
    "https://www.sunwater.com.au/wp-content/uploads/Home/Community/Preparing-for-weather-events/Emergency-Management/EAPs/Fairbairn_Dam_EAP.pdf",
    "https://www.sunwater.com.au/wp-content/uploads/Home/Community/Preparing-for-weather-events/Emergency-Management/EAPs/Fairbairn_Dam_EAP_2025.pdf",
    "https://www.sunwater.com.au/wp-content/uploads/Home/Community/Preparing-for-weather-events/Emergency-Management/EAPs/Fairbairn_Dam_EAP_2026.pdf",
    "https://www.sunwater.com.au/wp-content/uploads/2025/09/Fairbairn-Dam-EAP.pdf",
    "https://www.sunwater.com.au/wp-content/uploads/2025/09/Fairbairn_Dam_EAP.pdf",
    "https://www.sunwater.com.au/wp-content/uploads/2024/09/Fairbairn-Dam-EAP.pdf",
]


def get(url: str):
    return requests.get(
        url,
        timeout=180,
        allow_redirects=True,
        impersonate="chrome",
        headers={"Accept": "application/pdf,text/html,application/json,*/*", "Accept-Language": "en-AU,en;q=0.9"},
    )


def main() -> None:
    report = {"seeds": [], "discovered_urls": [], "probes": []}
    discovered: set[str] = set(GUESSES)
    for url in SEEDS:
        rec = {"url": url}
        try:
            r = get(url)
            text = r.text
            rec.update({"status": r.status_code, "final_url": str(r.url), "content_type": r.headers.get("content-type"), "bytes": len(r.content), "prefix": text[:500]})
            (OUT / ("seed_" + str(len(report["seeds"])) + ".txt")).write_text(text, encoding="utf-8", errors="ignore")
            for candidate in re.findall(r'https?://[^\s"\'<>]+', text):
                clean = candidate.replace("\\/", "/").rstrip(",);]")
                if "fairbairn" in clean.lower() or ("eap" in clean.lower() and clean.lower().endswith(".pdf")):
                    discovered.add(clean)
            for href in re.findall(r'(?:href|src)=["\']([^"\']+)', text, flags=re.I):
                absolute = urljoin(str(r.url), href)
                if "fairbairn" in absolute.lower() or ("eap" in absolute.lower() and absolute.lower().endswith(".pdf")):
                    discovered.add(absolute)
        except Exception as exc:
            rec["error"] = repr(exc)
        report["seeds"].append(rec)
    report["discovered_urls"] = sorted(discovered)
    for url in sorted(discovered):
        rec = {"url": url}
        try:
            r = get(url)
            rec.update({"status": r.status_code, "final_url": str(r.url), "content_type": r.headers.get("content-type"), "bytes": len(r.content), "pdf": r.content.lstrip().startswith(b"%PDF"), "prefix": r.content[:200].decode("utf-8", "replace")})
            if rec["pdf"]:
                (OUT / "fairbairn-eap.pdf").write_bytes(r.content)
                rec["saved"] = True
        except Exception as exc:
            rec["error"] = repr(exc)
        report["probes"].append(rec)
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
