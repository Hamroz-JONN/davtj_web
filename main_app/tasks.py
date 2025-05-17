from celery import shared_task
import os
from playwright.sync_api import sync_playwright
from django.conf import settings
from datetime import datetime

# saves graph to media/graph_images/graph_image and returns this path
@shared_task
def scrape_graph(graph_link):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(accept_downloads=True)  # important
        page = context.new_page()

        page.goto(graph_link)

        page.wait_for_selector(".vega-actions-wrapper")
        page.click(".vega-actions-wrapper")
        
        page.wait_for_selector('a[download="visualization.png"]')
        page.click("a[download='visualization.png']")  

        with page.expect_download() as download_info:
            page.click('a[download="visualization.png"]')
        download = download_info.value
        

        download_path = os.path.join(settings.MEDIA_ROOT, 'graph_images', f'graph{datetime.now().strftime("%dth/%H:%M:%S")}.png')

        download.save_as(download_path)

        print(f"Downloaded image saved to {download_path}")

        browser.close()
        return download_path