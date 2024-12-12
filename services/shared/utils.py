import requests


def is_channel_exists(channel_name: str):
    name = channel_name.split("@")[-1]
    response = requests.get(f"https://t.me/{name}")
    return response.status_code == 200


def gen(n):
    for i in range(n):
        yield i