import requests
import json
import os
import platform
import ctypes
from datetime import datetime
from datetime import timedelta
from random import randint


def get_data(api_key, pic_date):
    raw_response = requests.get(f'https://api.nasa.gov/planetary/apod?api_key={api_key}&date={pic_date}').text
    response = json.loads(raw_response)
    if is_image(response):
        return response
    raise ValueError


def get_title(response):
    return response['title']


def get_date(response):
    return response['date']


def get_explaination(response):
    return response['explanation']


def get_hdurl(response):
    return response['hdurl']


def download_image(url, date):
    raw_image = requests.get(url).content
    with open(f'{date}.jpg', 'wb') as file:
        file.write(raw_image)


def is_image(response):
    return response["media_type"] == 'image'


def is_leap_year(year):
    return year % 4 == 0 and year % 100 != 0 or year % 400 == 0


def is_file_present(date):
    return os.path.isfile(f'{date}.jpg')


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


def delete_previous_picture():
    for file in os.listdir():
        if file.endswith('.jpg') and not file.startswith(local_date):
            os.remove(file)


def set_wallpaper(pic_name):
    system_name = platform.system().lower()
    if system_name == 'linux':
        path = os.getcwd() + f'/{pic_name}'
        command = "gsettings set org.gnome.desktop.background picture-uri file:" + path
        os.system(command)
    elif system_name == 'windows':
        path = os.getcwd() + f'\\{pic_name}'
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)


if __name__ == '__main__':
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
    delete_previous_picture()
    image_name = local_date + '.jpg'
    set_wallpaper(image_name)
