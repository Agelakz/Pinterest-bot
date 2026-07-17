#!/usr/bin/env python3
import json
import asyncio
from playwright.async_api import async_playwright


async def main():
    cookies = json.load(open("cookies.json"))
    print(f"Loaded {len(cookies)} cookies")

    # Minimal cookie format - only what Playwright really needs
    pw_cookies = []
    for c in cookies:
        pw_cookies.append({
            "name": c["name"],
            "value": c["value"],
            "domain": c.get("domain", "pinterest.com").lstrip("."),
            "path": c.get("path", "/"),
        })

    print(f"Prepared {len(pw_cookies)} minimal cookies")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()

        try:
            await ctx.add_cookies(pw_cookies)
            print("Cookies added successfully")
        except Exception as e:
            print(f"Cookie error: {e}")
            # Continue anyway - some cookies may still work

        page = await ctx.new_page()
        await page.goto("https://id.pinterest.com/pin-creation-tool/", wait_until="networkidle")
        print("Navigation done")

        res = await page.evaluate("""async () => {
            const u = "https://id.pinterest.com/resource/BoardPickerBoardsResource/get/";
            const p = new URLSearchParams({
                source_url: "/pin-creation-tool/",
                data: JSON.stringify({options:{field_set_key:"board_picker",filter:"all"},context:{}}),
                _: Date.now()
            });
            const r = await fetch(u+"?"+p, {
                headers: {"X-Requested-With":"XMLHttpRequest","Accept":"application/json"},
                credentials: "include"
            });
            return {status: r.status, body: await r.text()};
        }""")

        print(f"\nStatus: {res['status']}")
        print(f"Body: {res['body'][:800]}")
        await browser.close()


asyncio.run(main())