from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0008/1619711/fairbairn-eap.pdf"
INDEX = "https://www.business.qld.gov.au/industries/mining-energy-water/water/industry-infrastructure/dams/referable-dam-eaps"
OUT = Path("fairbairn_probe")
OUT.mkdir(exist_ok=True)


def main() -> None:
    result = {"url": URL, "attempts": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            accept_downloads=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        try:
            page.goto(INDEX, wait_until="domcontentloaded", timeout=120_000)
            page.wait_for_timeout(5_000)
        except Exception as exc:
            result["index_error"] = repr(exc)

        for attempt in range(1, 5):
            rec = {"attempt": attempt}
            try:
                with page.expect_download(timeout=150_000) as download_info:
                    page.goto(URL, wait_until="commit", timeout=150_000)
                download = download_info.value
                target = OUT / "fairbairn-eap.pdf"
                download.save_as(str(target))
                body = target.read_bytes()
                rec.update({
                    "suggested_filename": download.suggested_filename,
                    "bytes": len(body),
                    "prefix": body[:20].decode("latin-1", "replace"),
                })
                if body.lstrip().startswith(b"%PDF"):
                    result["status"] = "pdf_saved"
                    result["attempts"].append(rec)
                    break
                rec["error"] = "Downloaded file is not a PDF"
            except Exception as exc:
                rec["error"] = repr(exc)
                try:
                    rec["final_url"] = page.url
                    rec["title"] = page.title()
                    page.screenshot(path=str(OUT / f"attempt-{attempt}.png"), full_page=True)
                except Exception:
                    pass
            result["attempts"].append(rec)
            try:
                page.goto(INDEX, wait_until="domcontentloaded", timeout=120_000)
                page.wait_for_timeout(5_000)
            except Exception:
                pass

        if "status" not in result:
            result["status"] = "not_saved"
        browser.close()

    (OUT / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
