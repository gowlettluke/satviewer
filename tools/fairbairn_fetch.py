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

        captured: list[dict] = []

        def on_response(response):
            if "fairbairn-eap.pdf" not in response.url.lower():
                return
            rec = {
                "url": response.url,
                "status": response.status,
                "content_type": response.headers.get("content-type"),
            }
            try:
                body = response.body()
                rec["bytes"] = len(body)
                rec["prefix"] = body[:80].decode("utf-8", "replace")
                if body.lstrip().startswith(b"%PDF"):
                    (OUT / "fairbairn-eap.pdf").write_bytes(body)
                    rec["saved_pdf"] = True
            except Exception as exc:
                rec["body_error"] = repr(exc)
            captured.append(rec)

        page.on("response", on_response)

        for attempt in range(1, 4):
            rec = {"attempt": attempt}
            try:
                response = page.goto(URL, wait_until="domcontentloaded", timeout=120_000)
                rec["goto_status"] = response.status if response else None
                rec["final_url"] = page.url
                page.wait_for_timeout(15_000)
                rec["title"] = page.title()
                rec["html_prefix"] = page.content()[:500]
                page.screenshot(path=str(OUT / f"attempt-{attempt}.png"), full_page=True)
                if (OUT / "fairbairn-eap.pdf").exists():
                    result["status"] = "pdf_saved"
                    result["attempts"].append(rec)
                    break
            except Exception as exc:
                rec["error"] = repr(exc)
            result["attempts"].append(rec)
            try:
                page.goto(INDEX, wait_until="domcontentloaded", timeout=120_000)
                page.wait_for_timeout(5_000)
            except Exception:
                pass

        result["captured_responses"] = captured
        if "status" not in result:
            result["status"] = "not_saved"
        browser.close()

    (OUT / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
