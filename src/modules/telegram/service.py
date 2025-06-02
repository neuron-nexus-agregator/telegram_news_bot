import telebot
from bs4 import BeautifulSoup
import time
import re
import g4f
import logging
from modules.yandex.service import Yandex

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (можно заменить на DEBUG для отладки)
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Логи выводятся только в консоль
    ]
)

class Telegram:
    def __init__(self, token: str, chat_id: int | str, queue, yandex_token: str, yandex_rewrite: bool = False):
        self.bot = telebot.TeleBot(token=token, parse_mode='HTML')
        self.chat_id = chat_id
        self.queue = queue
        self.yandex_rewrite = yandex_rewrite
        self.yandex = Yandex(yandex_token)

    def _get_enclosure(self, item):
        for link in item['links']:
            if link['rel'] == 'enclosure':
                return link['href']
        return ''
    
    def _get_full_text(self, item) -> str:
        yandex = item['yandex_full-text']
        soup = BeautifulSoup(yandex, 'html.parser')
        elements = soup.find_all(['p', 'li'])
        text = '\n\n'.join(['* ' + e.get_text() if e.name == 'li' else e.get_text() for e in elements])
            
        text = re.sub(r'"(.*?)"', r'«\1»', text)
        return text
    
    def _replace_quotes(self, text):
        return re.sub(r'"(.*?)"', r'«\1»', text)

    def _create_message(self, item):
        title = self._replace_quotes(item["title"])
        description = self._replace_quotes(item["description"])
        message = f'<b>{title}</b>'

        if self.yandex_rewrite:
            try:
                text = self._get_full_text(item)
                message += f'\n\n{self._replace_quotes(self.yandex.rewrite(text))}'
            except Exception as e:
                logging.error(f'Ошибка перевода текста в Yandex: {e}', extra={'chat_id': self.chat_id})
                message += f'\n\n{description}'
        else:
            message += f'\n\n{description}'

        if not message.endswith('.'):
                message += '.'

        if not self._need_markup(item):
            message += f' <a href="{item["link"]}">Подробнее...</a>'
        

        message += '\n\n@rv_shorts'
        return message
    

    def _need_image(self, item):
        return True
    

    def _need_markup(self, item):
        return len(item['title']) + len(item['description']) >= 180
    

    def _send_message(self, enclosure, message, needImage, link=None):
        markup = None
        if link:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(text='Подробнее...', url=link))
        self._send(message=message, enclosure=enclosure, needImage=needImage, markup=markup)


    def _handle_send_error(self, message, enclosure, needImage, markup, e):
        logging.error(f'Ошибка первой отправки сообщения в Telegram: {e}', extra={'chat_id': self.chat_id, 'link': enclosure})
        try:
            if needImage:
                self.bot.send_photo(self.chat_id, enclosure, caption=message, reply_markup=markup)
            else:
                self.bot.send_message(self.chat_id, message, disable_web_page_preview=True, reply_markup=markup)
        except Exception as e:
            logging.error(f'Ошибка второй отправки сообщения в Telegram: {e}', extra={'chat_id': self.chat_id, 'link': enclosure})
            self.bot.send_message(self.chat_id, message, disable_web_page_preview=True, reply_markup=markup)

# Использование в _send:
    def _send(self, message, enclosure, needImage, markup):
        try:
            if enclosure and needImage:
                self.bot.send_photo(self.chat_id, enclosure.replace('.md.', '.xl.'), caption=message, reply_markup=markup)
            else:
                self.bot.send_message(self.chat_id, message, disable_web_page_preview=True, reply_markup=markup)
        except Exception as e:
            self._handle_send_error(message, enclosure, needImage, markup, e)


    def send_message(self, item):
        enclosure = self._get_enclosure(item)
        message = self._create_message(item)
        needImage = self._need_image(item)
        link = item['link']
        if self._need_markup(item):
            self._send_message(enclosure, message, needImage, link)
        else:
            self._send_message(enclosure, message, needImage)

    
    def start(self):
        while True:
            item = self.queue.get()
            self.send_message(item)
            self.queue.task_done()
            time.sleep(3)