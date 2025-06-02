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
            'Cache-Control': 'no-cache',
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
            