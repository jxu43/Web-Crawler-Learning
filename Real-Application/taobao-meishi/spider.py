import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from pyquery import PyQuery as pq
from config import *
import pymongo
from selenium.webdriver.chrome.options import Options

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]

#selenium不支持PhantomJS 用headless chrome代替
chrome_options = Options()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(chrome_options=chrome_options)

wait = WebDriverWait(browser, 10)


def search(url):
    print('正在搜索')
    try:
        browser.get(url)
        #找到搜索界面的框
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )

        #找到搜索button
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))
        )

        input.send_keys(KEYWORD)
        submit.click()

        #找到一共的页数
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total'))
        )
        get_items()
        return total.text
    except TimeoutException:
        search()

def next_page(page_number):
    print('正在打开第%d页' % page_number)
    try:
        #找到想要跳转的页面的input
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )

        #找到submit button
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        input.clear()
        input.send_keys(page_number)

        submit.click()
        #用来判定是否已经跳转到指定页面
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number))
        )
        get_items()
    except TimeoutException:
        next_page(page_number)

def get_items():

    #判定items是不是已经被加载出来了
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item'))
    )

    #用pyQuery解析
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items() #.items()可以得到所有选择的内容
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('Successfully Saved to Mongo', result)
    except Exception:
        print('fail to save to mongo', result)


def main():
    try:
        total = search('https://www.taobao.com/')
        total = int(re.compile('(\d+)').search(total).group(1))
        for i in range(2, total):
            next_page(i)
    except Exception:
        print('访问错误')
    finally:
        browser.close()



if __name__ == '__main__':
    main()

