import json

import os
from hashlib import md5
from multiprocessing import Pool
from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException
import re
from urllib.parse import urlencode
import time
from json.decoder import JSONDecodeError
from config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]

def get_page_index(offset, keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': '20',
        'cur_tab': 1,
        'from': 'search_tab'
    }
    params = urlencode(data)
    baseurl = 'http://www.toutiao.com/search_content/'
    url = baseurl + '?' + params

    time.sleep(1)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
    }
    try:
        response = requests.get(url, headers = headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求索引失败')
        return None

def parse_page_index(html):

    #首先把得到的html页面用json格式化，然后看是否有'data'这个data pair中，如果有就进行'data' key下的内容的筛选article_url来访问子节点
    try:
        data = json.loads(html)
        if data and 'data' in data.keys():
            for item in data.get('data'):
                if item.get('article_url'):
                    yield item.get('article_url')
    except JSONDecodeError:
        pass

def get_page_detail(url):
    time.sleep(1)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
    }
    try:
        response = requests.get(url, headers = headers)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        print('请求详情页失败')
        return None

def parse_page_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')

    #用beautifulsoup找到title
    result = soup.select('title')
    title = result[0].get_text() if result else ''

    #用regex来匹配需要的image_url
    images_pattern = re.compile('gallery: JSON.parse\("(.*?)"\)', re.S)
    result = re.search(images_pattern, html)

    if result:
        #先把结果表示成json数据
        data = json.loads(result.group(1).replace('\\', ''))
        if data and 'sub_images' in data.keys():
            sub_images = data.get('sub_images')
            #把对应的detail的链接放到一个数组中
            images = [item.get('url') for item in sub_images]
            for image in images: download_image(image)
            return {
                'title': title,
                'url': url,
                'images': images,
            }

def save_to_mongodb(result):
    if db[MONGO_TABLE].insert(result):
        print('Successfully Saved to Mongo', result)
        return True
    return False

#下载并保存图片
def download_image(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
    }
    try:
        response = requests.get(url, headers = headers)
        if response.status_code == 200:
            save_image(response.content)
        return None
    except ConnectionError:
        return None

def save_image(content):
    file_path = '{0}/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    print(file_path)
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()

def main(offset):
    html = get_page_index(offset, KEYWORD)
    for url in parse_page_index(html):
        html = get_page_detail(url)
        if html:
            result = parse_page_detail(html, url)
            if result:
                save_to_mongodb(result)


if __name__ == '__main__':
    pool = Pool()
    groups = ([x * 20 for x in range(GROUP_START, GROUP_END + 1)])
    pool.map(main, groups)
    pool.close()
    pool.join()


