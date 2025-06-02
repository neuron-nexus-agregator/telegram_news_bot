from modules.rss.service import RSS
from modules.telegram.service import Telegram
import queue
import threading
import os

token = os.environ.get('TELEGRAM_TOKEN')
telegram_id = int(os.environ.get('TELEGRAM_CHAT_ID'))
yandex_token = os.environ.get('YANDEX_TOKEN')
yandex_rewrite = os.environ.get('YANDEX_REWRITE', 'false') == 'true'

def main():
    print('Starting bot...')
    print('Telegram token:', token)
    print('Telegram chat ID:', telegram_id)
    opQueue = queue.Queue()
    rss = RSS(url='https://realnoevremya.ru/rss/feed', queue=opQueue)
    telegram = Telegram(token=token, chat_id=telegram_id, queue=opQueue, yandex_token=yandex_token, yandex_rewrite=yandex_rewrite)
    threading.Thread(target=telegram.start).start()
    threading.Thread(target=rss.start).start()
    opQueue.join()


if __name__ == '__main__':
    main()