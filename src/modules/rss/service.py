from collections import deque
import feedparser
import time

import logging

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (можно заменить на DEBUG для отладки)
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Логи выводятся только в консоль
    ]
)

stopwords = ['erid=', '/articles/']

class RSS:
    def __init__(self, url:str, queue):
        self.queue = deque(maxlen=50)
        self.url = url
        self.opQueue = queue
        # if not elements in queue, add element N
        self.index = 0
        self.delay = 10  # 10 seconds
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/5374',
            # 'User-Agent': 'Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)',
            # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            # 'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            # 'Accept-Encoding': 'gzip, deflate, br, zstd',
            # 'Cookie': '__ddg1_=nTtEyV068cmDqRg7pWvL; adtech_uid=749ec629-a2d3-4763-9ae2-ecab94493844%3Arealnoevremya.ru; top100_id=t1.4420405.1950575489.1741942234299; t3_sid_4420405=s1.631236189.1741942234299.1741942245943.1.3.2.1; chash=q13YfZE2ed; _ga=GA1.2.1043914707.1741942236; _ym_uid=1741942236327542119; _ym_d=1741942236; _ga_NM7HXJPGDK=GS1.2.1741942238.1.1.1741942247.51.0.0; PHPSESSID=cq172b53dgi3fgu8nclgkcdnnc; __ddg8_=Kxx4SHzSR1Q4WP5A; __ddg10_=1747059130; __ddg9_=85.90.208.119; __ddgid_=NErBVOQibchunmV5; __ddgmark_=V3evAY1k0sZM840K; __ddg5_=qKQ3axT1UCb7XVPN; __ddg2_=UMXM3d6R4II0nSVh'
        }
    
    def _check(self, item='') -> bool:
        return self.queue.count(item) > 0
        
    def _parse(self):
        try:
            feed = feedparser.parse(self.url, agent=self.headers['User-Agent'],
                                    request_headers=self.headers)
            
            status = feed.get('status', 'Unknown')  # Если статус отсутствует, вернуть 'Unknown'
            logging.info(f"Response Status: {status}")
            if feed.bozo == 1:
                logging.error('Ошибка парсинга BOZO:', feed.bozo_exception, extra={'feed': feed})
            # if 'set-cookie' in feed.headers:
            #     new_cookies = feed.headers['set-cookie']
            #     self._update_cookies(new_cookies)
            
            return feed.entries
        except Exception as e:
            logging.error('Ошибка парсинга:', e)
            return []

    def update(self):
        items = self._parse()
        if len(self.queue) == 0:
            if len(items) <= self.index:
                logging.error('Нет элемента в RSS. Длина списка:', 'length', len(items),'items', items)
                return
            link = items[self.index]['link']
            self.queue.appendleft(link)
            logging.info('Добавлен начальный элемент в очередь:', link)
            return
        for item in items:
            if not item['link']:
                continue
            if any(stopword in item['link'] for stopword in stopwords):
                continue
            if self._check(item['link']):
                break  # Прерываем цикл, если элемент уже есть в self.queue
            self.queue.appendleft(item['link'])
            self.opQueue.put(item)
    
    def start(self, delay:int=-1):
        while True:
            self.update()
            if delay == -1:
                delay = self.delay
            time.sleep(delay)
            