import requests
from requests.exceptions import RequestException
import re
import json

def get_one_page(url):

    #模拟模拟器请求 反爬机制
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
    }
    try:
        response = requests.get(url, headers = headers)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except: RequestException
    # parse_one_page(response.text)

def parse_one_page(html):
    pattern = re.compile('<dd>.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?name"><a'
                      + '.*?>(.*?)</a>.*?star">(.*?)</p>.*?releasetime">(.*?)</p>'
                      + '.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?</dd>', re.S)
    results = re.findall(pattern, html)

    for result in results:
        yield {
            'index': result[0],
            'image': result[1],
            'title': result[2],
            'actors': result[3].strip()[3:],
            'time': result[4].strip()[5:],
            'point': result[5] + result[6]
        }

def write_to_file(content):
    with open('top-100.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')
        f.close()


def main(offset):
    url = 'http://maoyan.com/board/4?offset=' + str(offset)
    html = get_one_page(url)
    for result in parse_one_page(html):
        print(result)
        write_to_file(result)

if __name__ == '__main__':
    for i in range(10):
        main(i*10)