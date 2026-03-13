import requests
from config import TELEGRAM_CHAT_ID, URL

def send_message(text: str):
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }

    response = requests.post(URL, data=data)
    data = response.json()

    return data

if __name__ == "__main__":
    print(
        send_message(
            "Hello World!"
        )
    )
        