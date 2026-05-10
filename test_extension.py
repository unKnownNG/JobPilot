import asyncio
from playwright.async_api import async_playwright
import os
import shutil

async def main():
    extension_path = os.path.abspath('extension')
    print(f"Loading extension from {extension_path}")

    user_data_dir = os.path.abspath('test_profile')
    if os.path.exists(user_data_dir):
        shutil.rmtree(user_data_dir, ignore_errors=True)
        
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=[
                f"--disable-extensions-except={extension_path}",
                f"--load-extension={extension_path}",
            ],
        )

        background = None
        for i in range(10):
            if context.background_pages:
                background = context.background_pages[0]
                break
            if context.service_workers:
                background = context.service_workers[0]
                break
            await asyncio.sleep(0.5)
            
        if not background:
            print("Could not find extension service worker.")
            # Even if we don't find it easily, let's just wait a bit
            print("Continuing anyway...")

        # Find the extension ID by looking at the service workers
        extension_id = None
        if background:
            extension_id = background.url.split('/')[2]
            print(f"Extension ID: {extension_id}")
        else:
            # Another way to get extension ID is navigating to chrome://extensions and parsing it,
            # but usually service_workers populate quickly.
            for sw in context.service_workers:
                if sw.url.startswith('chrome-extension://'):
                    extension_id = sw.url.split('/')[2]
                    break

        if not extension_id:
            print("Could not retrieve extension ID")
            await context.close()
            return

        print("Testing extension interaction...")
        
        # Open a sample job page
        page = await context.new_page()
        test_html = """
        <html><body>
        <h1>Apply for Software Engineer</h1>
        <form>
            <label>First Name</label><input type="text" id="first_name" name="first_name" />
            <label>Email</label><input type="email" id="email" name="email" />
            <label>LinkedIn</label><input type="url" id="linkedin" name="linkedin" />
        </form>
        </body></html>
        """
        await page.goto(f"data:text/html;charset=utf-8,{test_html}")

        # Open popup
        popup = await context.new_page()
        await popup.goto(f"chrome-extension://{extension_id}/popup.html")
        
        await popup.wait_for_selector("#login-btn", timeout=5000)
        print("Popup rendered and login screen is visible!")
        
        await context.close()
        print("Test passed successfully.")

if __name__ == "__main__":
    asyncio.run(main())
