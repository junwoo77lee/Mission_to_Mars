from selenium import webdriver
from bs4 import BeautifulSoup
import requests

import pandas as pd

import time
import re


def scrape():
    # Set-up for Selenium headless browsing
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=options)

    # 1. Mars NASA News
    # Tagget url and fake-user agent (don't need this for Selenium to work)
    nasa_url = 'https://mars.nasa.gov/news/'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'}

    # Use Selenium + Beautiful Soup to get proper data from the page that implement React.js for dynamic data loading
    # Then, get the loaded page source into the Soup object
    driver.get(nasa_url)
    time.sleep(1)
    page_source = driver.page_source

    soup = BeautifulSoup(page_source, 'lxml')
    driver.quit()

    # ul.item_list > every li.slide has below information > div.image_and_description_container
    # div.list_text
        # div.list_date.get_text() -> posted date
        # div.content_title > a.get_text -> News title
        # div.article_teaser_body.get_text() -> News thumbnail (paragraph)
        # div.content_title > a.get('href') -> News link

    css_selector = 'ul.item_list > li.slide > div.image_and_description_container'# > div.list_text'    

    news_list = soup.select(css_selector)

    news_info_list = []
    base_url = 'https://mars.nasa.gov'

    for news in news_list:
        news_text = news.select_one('div.list_text')
        news_img = news.select_one('div.list_image')
        
        post_date = news_text.select_one('div.list_date').string.strip()
        news_title = news_text.select_one('div.content_title > a').string.strip()
        news_paragraph = news_text.select_one('div.article_teaser_body').string.strip()
        news_link = base_url + news_text.select_one('div.content_title > a').get('href').strip()
        
        news_img_link = base_url + news_img.select_one('img').get('src').strip()
        
        news_info_list.append({"post_date" : post_date,
                            "title" : news_title,
                            "paragraph" : news_paragraph,
                            "news_link" : news_link,
                            "news_image": news_img_link}
                            )

    # 2. Mars JPL
    jpl_url = 'https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars'
    driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=options)
    driver.get(jpl_url)
    time.sleep(2)
    driver.find_element_by_id('full_image').click()
    time.sleep(2)
    driver.find_element_by_partial_link_text('more info').click()
    time.sleep(2)
    featured_image_url = driver.find_element_by_class_name('main_image').get_attribute('src')
    featured_image_desc = driver.find_element_by_class_name('main_image').get_attribute('title')

    featured_image = {"image_url": featured_image_url,
                    "description": featured_image_desc}

    # 3. Mars tweeter

    # For practice purpose, I used soup.select() with css selector, not find() or find_all().

    # 1) Get the weather information if a paragraph contains "Sol ###":
    # div#timeline > div.stream-container > div.stream > ol#stream-items-id >
    # li.js-stream-item stream-item stream-item >
    # div.tweet js-stream-tweet js-actionable-tweet js-profile-popup-actionable dismissible-content original-tweet js-original-tweet has-cards has-content
    # > div.content > div.js-tweet-text-container > p.string

    # 2) Get the dashboard image URL as well as the tweeted date and time:
    #  2-1) image
    # .... > div.content > div.AdaptiveMediaOuterContainer > div.AdaptiveMedia is-square >
    # div.AdaptiveMedia-container > div.AdaptiveMedia-singlePhoto >
    # div.AdaptiveMedia-photoContainer js-adaptive-photo > img.get('src')
    #  2-2) date and time
    # .... > div.content > div.stream-item-header > small.time > a.get('data-original-title')

    tweeter_url = 'https://twitter.com/marswxreport?lang=en'
    resp = requests.get(tweeter_url, headers=headers) 
    soup = BeautifulSoup(resp.text, 'lxml')

    # Use :has() pseudo-class for CSS selectr
    ordered_list = soup.select('div.content:has(p)') # a list

    for list_ in ordered_list:
        
        a_list_of_string = list(list_.p.strings)
    
        if re.search(re.compile('sol \d{3}'), a_list_of_string[0]):
            mars_weather = a_list_of_string[0]

            # tweet date
            tweet_date = list_.select_one('[class*=js-short-timestamp]').string
            
            # image URL
            temp_html = list_.select_one('[class~=AdaptiveMedia-singlePhoto]')
            
            if temp_html is not None:
                image_url = temp_html.img.get('src').strip()
            else:
                image_url = ''
            break
            
        else:
            continue
        
    tweeter_output_dict = {"weather": mars_weather,
                        "image": image_url,
                        "tweet_at": tweet_date}                                        

    # 4. Mars Facts
    pd.set_option("colheader_justify","center")

    facts_url = 'https://space-facts.com/mars/'
    df_facts = pd.read_html(facts_url)

    # Comparison table between Mars and Earth
    df_comparison = df_facts[0]
    html_comparison = df_comparison.to_html(index=False,
                                            classes='table table-sm table-borderless table-striped text-center')

    # Fact table about Mars
    df_mars = df_facts[1].rename(columns={0:'Fact', 1:'Value'})
    html_mars = df_mars.to_html(index=False,
                                classes='table table-sm table-borderless table-striped text-center')


    # 5. Mars Hemispheres
    hemisphere_url = 'https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars'
    base_url = 'https://astrogeology.usgs.gov' # to get the full image_url

    driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=options)
    driver.get(hemisphere_url)
    hemispheres = [(link.get_attribute('href'), link.text) for link in driver.find_elements_by_partial_link_text('Hemisphere Enhanced')]
    hemisphere_image_urls = []

    for link, title  in hemispheres:
        driver.get(link)
        time.sleep(2)
        img_url = driver.find_element_by_class_name('wide-image').get_attribute('src')
        
        hemisphere_image_urls.append({"title": title,
                                    "img_url": img_url})
    driver.quit()

    return {"news": news_info_list,
            "jpl": featured_image,
            "tweeter": tweeter_output_dict,
            "comparison": html_comparison,
            "mars_facts": html_mars,
            "hemispheres": hemisphere_image_urls}


if __name__ == '__main__':
    scrape()