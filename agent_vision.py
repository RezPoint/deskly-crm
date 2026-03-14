import asyncio
import sys
import json
from playwright.async_api import async_playwright

async def run(url, action=None, selector=None, fill_text=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Устанавливаем размер окна, чтобы скриншот был понятным
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        
        print(f"👀 Навигация на: {url}")
        await page.goto(url)
        await asyncio.sleep(2) # Ждем загрузки SPA и анимаций Glassmorphism
        
        # Выполнение действия, если оно передано
        if action == "click" and selector:
            print(f"🖱️ Клик по элементу: {selector}")
            await page.click(selector)
            await asyncio.sleep(1)
        elif action == "fill" and selector and fill_text:
            print(f"⌨️ Ввод текста '{fill_text}' в {selector}")
            await page.fill(selector, fill_text)
            await asyncio.sleep(1)

        # 1. Делаем скриншот для визуального анализа
        screenshot_path = "current_view.png"
        await page.screenshot(path=screenshot_path)
        print(f"📸 Скриншот сохранен: {screenshot_path}")

        # 2. Извлекаем "Карту Интерактивности" (Accessibility Tree / Interactive DOM)
        # Собираем только кнопки, ссылки и инпуты, чтобы не перегружать контекст
        elements = await page.evaluate('''() => {
            const interactives = document.querySelectorAll('button, a, input, select, textarea');
            return Array.from(interactives).map(el => {
                const rect = el.getBoundingClientRect();
                return {
                    tag: el.tagName.toLowerCase(),
                    text: el.innerText || el.value || el.placeholder || '',
                    id: el.id,
                    className: el.className,
                    type: el.type || null,
                    visible: rect.width > 0 && rect.height > 0
                };
            }).filter(e => e.visible);
        }''')
        
        print("\n🗺️ Карта интерактивных элементов:")
        for el in elements:
            identifier = f"id='{el['id']}'" if el.get('id') else f"class='{el.get('className', '')}'"
            text_desc = f" | Текст: '{el['text']}'" if el.get('text') else ""
            print(f"- <{el['tag']} {identifier}{text_desc}>")

        await browser.close()

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/"
    action = sys.argv[2] if len(sys.argv) > 2 else None
    selector = sys.argv[3] if len(sys.argv) > 3 else None
    fill_text = sys.argv[4] if len(sys.argv) > 4 else None
    
    asyncio.run(run(url, action, selector, fill_text))
