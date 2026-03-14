import asyncio
import sys
import json
from playwright.async_api import async_playwright

async def run_workflow(steps_json):
    steps = json.loads(steps_json)
    async with async_playwright() as p:
        # headless=False открывает видимое окно браузера
        # slow_mo=500 добавляет задержку 500мс
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        
        step_counter = 0
        for step in steps:
            action = step.get("action")
            url = step.get("url")
            selector = step.get("selector")
            text = step.get("text")
            wait = step.get("wait", 1)

            if action == "goto":
                print(f"🌐 Навигация: {url}")
                await page.goto(url)
            elif action == "fill":
                print(f"⌨️ Ввод в {selector}: {text}")
                await page.fill(selector, text)
            elif action == "click":
                print(f"🖱️ Клик: {selector}")
                await page.click(selector)
            
            await asyncio.sleep(wait)
            
            # Делаем скриншот после каждого шага
            screenshot_path = f"step_{step_counter}_{action}.png"
            await page.screenshot(path=screenshot_path)
            print(f"📸 Шаг {step_counter} заскринен: {screenshot_path}")
            step_counter += 1

        print("🛑 Сценарий завершен. Браузер оставлен открытым! (Нажми Ctrl+C в консоли для выхода)")
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        content = sys.argv[1]
        if content.endswith(".json"):
            with open(content, "r", encoding="utf-8") as f:
                content = f.read()
        asyncio.run(run_workflow(content))
    else:
        with open("workflow.json", "r", encoding="utf-8") as f:
            asyncio.run(run_workflow(f.read()))
