import asyncio
import sys
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        errors = []
        page.on("console", lambda msg: errors.append(f"CONSOLE {msg.type}: {msg.text}") if msg.type in ["error", "warning"] else None)
        page.on("pageerror", lambda err: errors.append(f"PAGE ERROR: {err}"))
        
        print("Navigating to http://127.0.0.1:8000/")
        await page.goto("http://127.0.0.1:8000/")
        await asyncio.sleep(2)
        
        print(f"Captured {len(errors)} errors/warnings.")
        for err in errors:
            print(err)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
