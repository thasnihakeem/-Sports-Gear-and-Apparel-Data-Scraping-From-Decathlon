# Import necessary libraries
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

        next_button = await page.query_selector('.adept-pagination__item a[aria-label="Go to next page"]')
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


async def get_bullet_points(page):
    try:
        # Get the main FeaturesContainer section
        FeaturesContainer = await page.query_selector(".FeaturesContainer")
        # Extract text content for the main section
        text = await FeaturesContainer.text_content()
        # Split the text into a list by newline characters
        bullet_points = text.split('\n')
        # Remove any empty strings from the list
        bullet_points = list(filter(None, bullet_points))
        bullet_points = [bp.strip() for bp in bullet_points if bp.strip() and "A photo" not in bp]

    except:
        # Set bullet_points to "Not Available" if sections not found or there's an error
        bullet_points = "Not Available"

    return bullet_points


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

        # Make a request to the Amazon search page and extract the product URLs
        await perform_request_with_retry(page, 'https://www.decathlon.com/search?q=Sports+Gear+%26+Apparel')
        product_urls = await get_product_urls(browser, page)
        data = []

        # Loop through each product URL and scrape the necessary information
        for i, url in enumerate(product_urls):
            await perform_request_with_retry(page, url)

            product_name = await get_product_name(page)
            brand = await get_brand_name(page)
            star_rating = await get_star_rating(page)
            num_reviews = await get_num_reviews(page)
            MRP = await get_MRP(page)
            sale_price = await get_sale_price(page)
            colour = await get_colour(page)
            ProductInformation = await get_ProductInformation(page)
            bullet_points = await get_bullet_points(page)
            print(product_name, brand, star_rating, num_reviews, MRP, sale_price, colour, ProductInformation, bullet_points)

            # Print progress message after processing every 10 product URLs
            if i % 10 == 0 and i > 0:
                print(f"Processed {i} links.")

            # Print completion message after all product URLs have been processed
            if i == len(product_urls) - 1:
                print(f"All information for url {i} has been scraped.")

            # Add the scraped information to a list
            data.append((url, product_name, brand, star_rating, num_reviews, MRP, sale_price, colour,
                         ProductInformation, bullet_points))

        # Convert the list of tuples to a Pandas DataFrame and save it to a CSV file
        df = pd.DataFrame(data,
                          columns=['product_url', 'product_name', 'brand', 'star_rating', 'number_of_reviews',
                                   'MRP', 'sale_price', 'colour', 'product information', 'description'])
        df.to_csv('product_data.csv', index=False)
        print('CSV file has been written successfully.')

        # Close the browser
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
