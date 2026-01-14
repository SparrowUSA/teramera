import os
import asyncio
from playwright.async_api import async_playwright

async def upload_via_browser(file_path, ndus_cookie):
    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Inject the ndus cookie so we are logged in automatically
        await context.add_cookies([{
            'name': 'ndus',
            'value': ndus_cookie,
            'domain': '.terabox.com',
            'path': '/'
        }])
        
        page = await context.new_page()
        filename = os.path.basename(file_path)

        try:
            # 1. Navigate to TeraBox
            await page.goto("https://www.terabox.com/main", timeout=60000)
            
            # 2. Trigger Upload (targeting the hidden file input)
            await page.set_input_files('input[type="file"]', file_path)
            
            # 3. Wait for upload to finish (looking for the success indicator)
            # TeraBox usually shows a transfer list; we wait for 'Completed' status
            print(f"Uploading {filename}...")
            await page.wait_for_selector(".transfer-list-item-success", timeout=600000) 
            
            # 4. Get the Share link (Logic to click the latest file's share button)
            # This is a fallback link as full UI automation for sharing is highly unstable
            # Instead, we return a success status to the main bot
            return f"https://www.terabox.com/main?path=%2F" 
            
        except Exception as e:
            print(f"Browser Upload Error: {e}")
            return None
        finally:
            await browser.close()
