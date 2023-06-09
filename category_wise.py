import random
import asyncio
from playwright.async_api import async_playwright

async def perform_request_with_retry(page, url):
    # set maximum retries
    MAX_RETRIES = 5
    # initialize retry counter
    retry_count = 0

    # loop until maximum retries are reached
    while retry_count < MAX_RETRIES:
        try:
            # try to make request to the URL using the page object and a timeout of 30 seconds
            await page.goto(url, timeout=150000)
            # break out of the loop if the request was successful
            break
        except:
            # if an exception occurs, increment the retry counter
            retry_count += 1
            # if maximum retries have been reached, raise an exception
            if retry_count == MAX_RETRIES:
                raise Exception("Request timed out")
            # wait for a random amount of time between 1 and 5 seconds before retrying
            await asyncio.sleep(random.uniform(1, 5))

async def get_product_urls(browser, page):
    product_urls = []

    # Loop through all pages
    while True:
        # Select all elements with the product urls
        all_items = await page.query_selector_all('.adept-product-display__title-container')
        # Loop through each item and extract the href attribute
        for item in all_items:
            url = await item.get_attribute('href')
            product_urls.append(url)

        num_products = len(product_urls)
        print(f"Scraped {num_products} products.")

        next_button = await page.query_selector('.adept-pagination__item:not(.adept-pagination__disabled) a[aria-label="Go to next page"]')
        if not next_button:
            break  # Exit the loop if there is no next button

        # Click the next button with retry mechanism and delay
        retry_count = 0
        MAX_RETRIES = 5
        while retry_count < MAX_RETRIES:
            try:
                await next_button.click()
                await page.wait_for_selector('.adept-product-display__title-container', timeout=800000)
                await asyncio.sleep(random.uniform(2, 5)) # add a delay
                break
            except:
                retry_count += 1
                if retry_count == MAX_RETRIES:
                    raise Exception("Clicking next button timed out")
                await asyncio.sleep(random.uniform(1, 3))

    return product_urls



async def filter_products(browser, page):
    # Expand the product category section
    category_button = await page.query_selector('.adept-filter-list__title[aria-label="product category Filter"]')
    await category_button.click(timeout=600000)
    category_text_element = await category_button.query_selector('.adept-filter__list__title__text')
    category_text = await category_text_element.inner_text()
    print(category_text)
    is_expanded = await category_button.get_attribute('aria-expanded')
    if is_expanded == 'false':
        await category_button.click(timeout=600000)
        print("Category section expanded.")
    else:
        print("Category section is already expanded.")

    # Click the "Show All" button to show all categories
    show_all_button = await page.query_selector('.adept-filter__checkbox__show-toggle')
    await show_all_button.click(timeout=600000)
    show_all_text = await show_all_button.text_content()
    print(show_all_text)
    if show_all_text == 'Show All':
        await show_all_button.click(timeout=600000)
        print('not expanded')
    else:
        pass
        print('expanded')

    # Wait for the category list to load
    await page.wait_for_selector('.adept-checkbox__input-container', timeout=800000)

    # Define a list of checkbox labels to select and clear
    checkbox_labels = ["Shorts", "T-Shirt", "Hardbait", "Backpack", "Base Layer", "Basketball", "Bikini Bottom", "Bikini Top", "Boardshorts", "Cap",
                       "Cycling Shorts", "Fleece", "Flip-Flops", "Gloves", "Hooks", "Jacket", "Long-Sleeved T-Shirt",
                       "Lure", "One-Piece Swimsuit", "Shoes", "Short-Sleeved Jersey",  "Socks", "Sport Bag",
                       "Sports Bra", "Sweatshirt", "T-Shirt", "Tennis Racquet/Racket", "Top", "Trousers/Pants",
                       "Water Bottle", "Shorts", "Leggings"]

    product_urls = []

    # Iterate over the list of checkboxes to select and clear
    for label in checkbox_labels:
        # Select the checkbox
        checkbox = await page.query_selector(f'label.adept-checkbox__label:has-text("{label}")')
        await checkbox.click(timeout=2000000)
        is_checked = await checkbox.get_attribute('aria-checked')
        if is_checked == 'false':
            await checkbox.click(timeout=2000000)
            print(f"{label} checkbox not clicked.")
        else:
            print(f"{label} checkbox is already checked.")
        await asyncio.sleep(60)

        # Get the list of product URLs
        product_urls += await get_product_urls(browser, page)

        # Clear the checkbox filter
        clear_filter_button = await page.query_selector(
            f'button.adept-selection-list__close[aria-label="Clear {label.lower()} Filter"]')
        await clear_filter_button.click(timeout=800000)
        print(f"{label} filter cleared.")
        await asyncio.sleep(10)

    return product_urls


async def main():
    # Launch a Firefox browser using Playwright
    async with async_playwright() as pw:
        browser = await pw.firefox.launch()
        page = await browser.new_page()

        # Make a request to the Amazon search page and extract the product URLs
        await perform_request_with_retry(page, 'https://www.decathlon.com/search?q=Sports+Gear+%26+Apparel')
        product_urls = await filter_products(browser, page)

        # Print the list of URLs
        print(product_urls)
        len(product_urls)
        # Close the browser
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
