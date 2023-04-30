import random
import asyncio
import pandas as pd
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
            await page.goto(url, timeout=1000000)
            # break out of the loop if the request was successful
            break
        except:
            # if an exception occurs, increment the retry counter
            retry_count += 1
            # if maximum retries have been reached, raise an exception
            if retry_count == MAX_RETRIES:
                raise Exception("Request timed out")
            # wait for a random amount of time between 1 and 5 seconds before retrying
            await asyncio.sleep(random.uniform(1, 10))


async def get_product_urls(browser, page):
    product_urls = []

    # Loop through all pages
    while True:
        # Find all elements with the product urls
        all_items = await page.querySelectorAll('.adept-product-display__title-container')
        
        # Extract the href attribute for each item and append to product_urls list
        for item in all_items:
            url = await item.getAttribute('href')
            product_urls.append(url)

        num_products = len(product_urls)
        print(f"Scraped {num_products} products.")
        
        # Find the next button
        next_button = await page.querySelector('.adept-pagination__item:not(.adept-pagination__disabled) a[aria-label="Go to next page"]')
        
        # Exit the loop if there is no next button
        if not next_button:
            break  

        # Click the next button with retry mechanism and delay
        MAX_RETRIES = 5
        for retry_count in range(MAX_RETRIES):
            try:
                # Click the next button
                await next_button.click()
                # Wait for the next page to load
                await page.waitForSelector('.adept-product-display__title-container', timeout=800000)
                # Add a delay
                await asyncio.sleep(random.uniform(2, 5))
                # Break out of the loop if successful
                break
            except:
                # If an exception occurs, retry up to MAX_RETRIES times
                if retry_count == MAX_RETRIES - 1:
                    raise Exception("Clicking next button timed out")
                # Wait for a random amount of time between 1 and 3 seconds before retrying
                await asyncio.sleep(random.uniform(1, 3))

    return product_urls


async def filter_products(browser, page):
    # Expand the product category section
    category_button = await page.query_selector('.adept-filter-list__title[aria-label="product category Filter"]')
    await category_button.click(timeout=600000)
    # Check if category section is already expanded
    is_expanded = await category_button.get_attribute('aria-expanded')
    if is_expanded == 'false':
        await category_button.click(timeout=600000)
    else:
        pass

    # Click the "Show All" button to show all categories
    show_all_button = await page.query_selector('.adept-filter__checkbox__show-toggle')
    await show_all_button.click(timeout=400000)
    # Check if "Show All" button is already clicked
    show_all_text = await show_all_button.text_content()
    if show_all_text == 'Show All':
        await show_all_button.click(timeout=400000)
    else:
        pass

    # Wait for the category list to load
    await page.wait_for_selector('.adept-checkbox__input-container', timeout=400000)

    # Define a list of checkbox labels to select and clear
    categories = ["Base Layer", "Cap", "Cropped Leggings", "Cycling Shorts", "Fleece", "Gloves", "Legging 7/8",
                  "Long-Sleeved T-Shirt", "Padded Jacket", "Short-Sleeved Jersey", "Down Jacket", "Socks",
                  "Sports Bra", "Sweatshirt", "Tank", "Tracksuit", "Trousers/Pants", "Windbreaker", "Zip-Off Pants",
                  "Shoes", "Sunglasses","Sport Bag", "Fitness Mat", "Shorts", "T-Shirt", "Jacket", "Leggings"]

    product_urls = []

    # Iterate over the list of category to select and clear
    for category in categories:
        # Select the checkbox
        checkbox = await page.query_selector(f'label.adept-checkbox__label:has-text("{category}")')
        await checkbox.click(timeout=600000)
        # Check if checkbox is already selected
        is_checked = await checkbox.get_attribute('aria-checked')
        if is_checked == 'false':
            await checkbox.click(timeout=600000)
        else:
            print(f"{category} checkbox is checked.")
        # Wait for the page to load
        await asyncio.sleep(10)

        # Get the list of product URLs
        product_urls += [(url, category) for url in await get_product_urls(browser, page)]

        # Clear the checkbox filter
        clear_filter_button = await page.query_selector(
            f'button.adept-selection-list__close[aria-label="Clear {category.lower()} Filter"]')
        if clear_filter_button is not None:
            await clear_filter_button.click(timeout=600000)
            print(f"{category} filter cleared.")
        else:
            clear_buttons = await page.query_selector_all('button[aria-label^="Clear"]')
            for button in clear_buttons:
                await button.click(timeout=600000)
                print(f"{category} filter cleared.")
        # Wait for the page to load
        await asyncio.sleep(10)

    return product_urls


async def get_product_name(page):
    try:
        # Find the product title element and get its text content
        product_name_elem = await page.query_selector(".de-u-textGrow1.de-u-md-textGrow2.de-u-textMedium.de-u-spaceBottom06")
        product_name = await product_name_elem.text_content()
    except:
        # If an exception occurs, set the product name as "Not Available"
        product_name = "Not Available"

    # Remove any leading/trailing whitespace from the product name and return it
    return product_name.strip()


async def get_brand_name(page):
    try:
        # Find the SVG title element and get its text content
        brand_name_elem = await page.query_selector("svg[role=\'img\'] title")
        brand_name = await brand_name_elem.text_content()
    except:
        # If an exception occurs, set the brand name as "Not Available"
        brand_name = "Not Available"

    # Return the cleaned up brand name
    return brand_name


async def get_star_rating(page):
    try:
        # Find the star rating element and get its text content
        star_rating_elem = await page.wait_for_selector(".de-StarRating-fill + .de-u-hiddenVisually")
        star_rating_text = await star_rating_elem.inner_text()
        star_rating = star_rating_text.split(" ")[2]
    except:
        star_rating = "Not Available"

    # Return the star rating
    return star_rating


async def get_num_reviews(page):
    try:
        # Find the number of reviews element and get its text content
        num_reviews_elem = await page.wait_for_selector("span.de-u-textMedium.de-u-textSelectNone.de-u-textBlue")
        num_reviews = await num_reviews_elem.inner_text()
        num_reviews = num_reviews.split(" ")[0]
    except:
        num_reviews = "Not Available"

    # Return the number of reviews
    return num_reviews


async def get_MRP(page):
    try:
        # Find the MRP element and get its text content
        MRP_elem = await page.query_selector(".js-de-CrossedOutPrice > .js-de-PriceAmount")
        MRP = await MRP_elem.inner_text()
    except:
        # If an exception occurs, set the MRP as "Not Available"
        MRP = "Not Available"

    # Return the MRP
    return MRP


async def get_sale_price(page):
    try:
        # Get sale price element and extract text content
        sale_price_element = await page.query_selector(".js-de-CurrentPrice > .js-de-PriceAmount")
        sale_price = await sale_price_element.text_content()
    except:
        # Set sale price to "Not Available" if element not found or text content cannot be extracted
        sale_price = "Not Available"
    return sale_price


async def get_colour(page):
    try:
        # Get color element and extract text content
        color_element = await page.query_selector("div.de-u-spaceTop06.de-u-lineHeight1.de-u-hidden.de-u-md-block.de-u-spaceBottom2 strong + span.js-de-ColorInfo")
        color = await color_element.inner_text()
    except:
        try:
            # Find the color element and get its text content
            color_elem = await page.query_selector("div.de-u-spaceTop06.de-u-lineHeight1 strong + span.js-de-ColorInfo")
            color = await color_elem.inner_text()
        except:
            # If an exception occurs, set the color as "Not Available"
            color = "Not Available"
    return color


async def get_Product_description(page):
    try:
        # Get the main FeaturesContainer section
        FeaturesContainer = await page.query_selector(".FeaturesContainer")
        # Extract text content for the main section
        text = await FeaturesContainer.text_content()
        # Split the text into a list by newline characters
        Product_description = text.split('\n')
        # Remove any empty strings from the list
        Product_description = list(filter(None, Product_description))
        Product_description = [bp.strip() for bp in Product_description if bp.strip() and "A photo" not in bp]

    except:
        # Set Product_description to "Not Available" if sections not found or there's an error
        Product_description = "Not Available"

    return Product_description


async def get_ProductInformation(page):
    try:
        # Get ProductInformation section element
        ProductInformation_element = await page.query_selector(".de-ProductInformation--multispec")
        # Get all ProductInformation entry elements
        ProductInformation_entries = await ProductInformation_element.query_selector_all(".de-ProductInformation-entry")
        # Loop through each entry and extract the text content of the "name" and "value" elements
        ProductInformation = {}
        for entry in ProductInformation_entries:
            name_element = await entry.query_selector("[itemprop=name]")
            name = await name_element.text_content()
            value_element = await entry.query_selector("[itemprop=value]")
            value = await value_element.text_content()
            # Remove newline characters from the name and value strings
            name = name.replace("\n", "")
            value = value.replace("\n", "")
            # Add name-value pair to product_information dictionary
            ProductInformation[name] = value
    except:
        # Set ProductInformation to "Not Available" if element not found or text content cannot be extracted
        ProductInformation = {"Not Available": "Not Available"}
    return ProductInformation


async def main():
    # Launch a Firefox browser using Playwright
    async with async_playwright() as pw:
        browser = await pw.firefox.launch()
        page = await browser.new_page()

        # Make a request to the Decathlon search page and extract the product URLs
        await perform_request_with_retry(page, 'https://www.decathlon.com/search?SOLD_OUT=%7B%22label_text%22%3A%22SOLD_OUT%22%2C%22value%22%3A%7B%22%24eq%22%3A%22FALSE%22%7D%7D&query_history=%5B%22Apparel%22%5D&q=Apparel&category_history=%5B%5D&sorting=NATURAL|desc')
        product_urls = await filter_products(browser, page)

        # Print the list of URLs
        print(product_urls)
        print(len(product_urls))
        data = []

        # Loop through each product URL and scrape the necessary information
        for i, (url, category) in enumerate(product_urls):
            await perform_request_with_retry(page, url)

            product_name = await get_product_name(page)
            brand = await get_brand_name(page)
            star_rating = await get_star_rating(page)
            num_reviews = await get_num_reviews(page)
            MRP = await get_MRP(page)
            sale_price = await get_sale_price(page)
            colour = await get_colour(page)
            ProductInformation = await get_ProductInformation(page)
            Product_description = await get_Product_description(page)


            # Print progress message after processing every 10 product URLs
            if i % 10 == 0 and i > 0:
                print(f"Processed {i} links.")

            # Print completion message after all product URLs have been processed
            if i == len(product_urls) - 1:
                print(f"All information for url {i} has been scraped.")

            # Add the scraped information to a list
            data.append((url, category, product_name, brand, star_rating, num_reviews, MRP, sale_price, colour,
                         ProductInformation, Product_description))

        # Convert the list of tuples to a Pandas DataFrame and save it to a CSV file
        df = pd.DataFrame(data,
                          columns=['product_url', 'category', 'product_name', 'brand', 'star_rating', 'number_of_reviews',
                                   'MRP', 'sale_price', 'colour', 'product information', 'Product description'])
        df.to_csv('product_data.csv', index=False)
        print('CSV file has been written successfully.')
        # Close the browser
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
