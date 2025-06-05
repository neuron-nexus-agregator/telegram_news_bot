from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.auth import APIKeyAuth
import re
import os

class Yandex:
    def __init__(self, token):
        self.token = token
        self.headers = {
            'Authorization': f'Api-Key {self.token}'
        }
        self.bucket = 'b1g7e364b5giim9tajta'
        try:
            tokens = int(os.environ.get('YANDEX_MAX_TOKENX', '50'))
        except ValueError:
            tokens = 50
        self.max_tokens = tokens

    def rewrite(self, text: str) -> str:
        model = self._create_model()
        messages = self._create_messages(text)
        response = model.run(messages)
        return response.alternatives[0].text.replace('ё', 'е').replace('Ё', 'Е').replace('`', '').strip()

    def _create_model(self):
        sdk = YCloudML(
            folder_id=self.bucket,
            auth=APIKeyAuth(self.token),
        )
        model = sdk.models.completions('yandexgpt', model_version='rc')
        model = model.configure(temperature=0.5)
        model = model.configure(
            max_tokens=self.max_tokens,
        )
        model = model.configure(
            reasoning_mode='enabled_hidden',
        )
        return model
    
    def _create_messages(self, text: str) -> list:
        # delete all html tags from text
        text = re.sub(r'<[^>]*>', '', text)
        # delete all extra spaces from text
        text = re.sub(r'\s+', ' ', text)
        # remove spaces before and after text
        text = text.strip()
        return [
            {
                'role': 'system',
                'text': 'Ты — профессиональный редактор и журналист. Твоя задача — изучить этот текст, выделить из него наиболее важную часть и сократить ее в 2-3 предложения. В ответ пришли только то сокращение, которое ты сделал. Не придумывай заголовок, только сократи текст.'
            },
            {
                'role': 'user',
                'text': text
            }
        ]