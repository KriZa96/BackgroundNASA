import requests
import json
import os
import platform
import ctypes
import sys
import time
from datetime import datetime
from datetime import timedelta
from random import randint


def get_data(api_key, pic_date):
    raw_response = requests.get(f'https://api.nasa.gov/planetary/apod?api_key={api_key}&date={pic_date}').text
    response = json.loads(raw_response)
    if is_image(response):
        return response
    raise ValueError


def get_title(response):  # Will be used later on.
    return response['title']


def get_date(response):  # Will be used later on.
    return response['date']


def get_explaination(response):  # Will be used later on.
    return response['explanation']


def get_hdurl(response):
    return response['hdurl']


def download_image(url, date):
    raw_image = requests.get(url).content
    with open(os.path.normpath(os.path.dirname(__file__) + f'/{date}.jpg'), 'wb') as file:
        file.write(raw_image)


def is_image(response):
    return response["media_type"] == 'image'


def is_leap_year(year):
    return year % 4 == 0 and year % 100 != 0 or year % 400 == 0


def is_file_present(name):
    return os.path.isfile(os.path.normpath(os.path.dirname(__file__) + f'/{name}.jpg'))


def new_date():
    """Sets random date"""
    start_year = 1996
    year = randint(start_year, datetime.now().year)
    month = randint(1, 12)
    if month == 2:
        day = randint(1, 28 if not is_leap_year(year) else 29)
    elif month in [4, 6, 9, 11]:
        day = randint(1, 30)
    else:
        day = randint(1, 31)

    final_year = str(year)
    final_month = ('0' + str(month)) if len(str(month)) == 1 else month
    final_day = ('0' + str(day)) if len(str(day)) == 1 else day

    return f'{final_year}-{final_month}-{final_day}'


def delete_previous_picture(name):
    for file in os.listdir(os.path.dirname(__file__)):
        if file.endswith('.jpg') and not file.startswith(name):
            os.remove(os.path.normpath(os.path.dirname(__file__) + f'/{file}'))


def set_wallpaper(pic_name):
    system_name = platform.system().lower()
    path = os.path.normpath(os.path.dirname(__file__) + f'/{pic_name}')
    if system_name == 'linux':
        set_pic = f"nitrogen --set-auto --save {path}"
        os.system(set_pic)
    elif system_name == 'windows':
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)


def is_connected_to_internet():
    system = platform.system().lower()
    ping = {
        'windows': 'ping -n 1',
        'linux': 'ping -c 1'
    }
    host = 'google.com'
    response = os.system(f'{ping[system]} {host}')
    return not response


def activate_script():
    key = 'DEMO_KEY'
    local_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    # local_date = '1995-06-16'
    while not is_file_present(local_date):
        try:
            data = get_data(key, local_date)
            picture_url = get_hdurl(data)
        except (KeyError, ValueError):
            local_date = new_date()
            continue
        download_image(picture_url, local_date)
    delete_previous_picture(local_date)
    image_name = local_date + '.jpg'
    set_wallpaper(image_name)


def main():
    start_time = time.time()
    while time.time() - start_time < 180:
        if is_connected_to_internet():
            activate_script()
            sys.exit()
        time.sleep(5)


if __name__ == '__main__':
    main()
