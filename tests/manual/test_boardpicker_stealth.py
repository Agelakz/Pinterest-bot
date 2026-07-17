#!/usr/bin/env python3
import json
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def main():
    cookies = json.load(open("cookies.json"))
    print(f"Loaded {len(cookies)} cookies")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )

        page = await ctx.new_page()
        st = Stealth()
        await st.apply_stealth_async(page)

        print("Navigating...")
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
            return {status:r.status, body:await r.text()};
        }""")

        print(f"Status: {res['status']}")
        print(f"Body: {res['body'][:600]}")
        await browser.close()


asyncio.run(main())