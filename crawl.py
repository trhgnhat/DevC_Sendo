# import libraries
import urllib.request
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import json
import urllib.parse
import requests
import re


def crawl_selenium(page, item_name, time_wait=10):
    driver = webdriver.Chrome('chromedriver.exe')
    driver.implicitly_wait(time_wait)
    params = {'q': item_name}
    driver.get(page+"/tim-kiem?{}".format(urllib.parse.urlencode(params)))
    first_item = driver.find_element_by_css_selector("div[class^='list_'] a[class^='item_']")
    item = dict()
    item["href"] = first_item.get_attribute("href").split("?")[0]
    item["image_url"] = first_item.find_element_by_tag_name("img").get_attribute("src")
    item["name"] = first_item.find_element_by_css_selector("div[class^='caption_'] h3[class^='productName_'] span").text
    item["price"] = first_item.find_element_by_css_selector("div[class^='caption_'] div[class^='productPrice_'] strong").text
    print(item)
    input("ENTER to exit")
    driver.quit()

# specify the url
url = 'https://www.sendo.vn'
crawl_selenium(url, 'áo kiểu from dài chất đẹp TB1008')
print("done".upper())

