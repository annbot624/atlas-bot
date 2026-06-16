import asyncio
import datetime
import requests
from playwright.async_api import async_playwright

# === НАСТРОЙКИ ===
TELEGRAM_TOKEN = "8838672993:AAGuqUR036X5JPnKDOuYlK8aFNZYibSx0u4"
USER_ID = "1324794860"

TRACKED_TRIPS = [
    {"from": "Минск", "to": "Вильнюс", "time": "03:00"},
    {"from": "Минск", "to": "Вильнюс", "time": "04:20"},
    {"from": "Вильнюс", "to": "Минск", "time": "11:35"},
    {"from": "Вильнюс", "to": "Минск", "time": "15:10"},
]

def send_telegram(message):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": USER_ID, "text": message})
    except Exception as e:
        print(f"Ошибка Telegram: {e}")

async def check_atlas_with_browser():
    print(f"[{datetime.datetime.now()}] Открываю виртуальный браузер...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        for trip in TRACKED_TRIPS:
            try:
                url = f"https://atlasbus.by{trip['from']}/{trip['to']}"
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(5000)
                
                rides = await page.evaluate("""() => {
                    let results = [];
                    document.querySelectorAll('[data-background]').forEach(el => {
                        let timeText = el.querySelector('[class*="time"]')?.innerText || "";
                        let carrierText = el.innerText.toLowerCase();
                        results.push({time: timeText, info: carrierText});
                    });
                    return results;
                }""")
                
                trip_found = False
                for ride in rides:
                    if trip["time"] in ride["time"] and "ваджен" in ride["info"]:
                        trip_found = True
                        if "мест нет" in ride["info"] or " 0 мест" in ride["info"]:
                            send_telegram(f"🚨 МЕСТ НЕТ!\n🚌 {trip['from']} -> {trip['to']}\n⏰ Время: {trip['time']}\nℹ️ Ваджен Трэвел")
                        else:
                            print(f"✅ Рейс {trip['from']}-{trip['to']} в {trip['time']}: места еще есть.")
                
                if not trip_found:
                    send_telegram(f"❌ Рейс {trip['from']}-{trip['to']} в {trip['time']} отсутствует на экране (мест нет)!")
                    
            except Exception as e:
                print(f"Ошибка при загрузке страницы: {e}")
                
        await browser.close()

async def main():
    print("🤖 Бот успешно запущен на платформе Render!")
    send_telegram("🤖 Бот успешно запущен на новом сервере Render!")
    
    while True:
        now = datetime.datetime.now() + datetime.timedelta(hours=3)
        current_time = now.strftime("%H:%M")
        
        if current_time == "10:00" or current_time == "15:00":
            await check_atlas_with_browser()
            await asyncio.sleep(65)
            
        await asyncio.sleep(10)

if name == "main":
    asyncio.run(main())
