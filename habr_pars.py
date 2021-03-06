import requests
from bs4 import BeautifulSoup as bs
from time import sleep
import lxml
import sqlite3

URL = 'https://habr.com/ru/hub/autogadgets/'
HEADERS = {'ucer-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/86.0.4240.198 Safari/537.36', 'accept': '*/*'}


# берём код с каждой страницы
def get_html_page(url):
    page = requests.get(url, headers=HEADERS)
    return page


# Достаём номер последней страницы из текста ссылки с главной хаба.
def get_pages_count(html):
    soup = bs(html, 'html.parser')
    get_last_page = soup.find('ul', attrs={'id': 'nav-pagess'}).find('a', attrs={'title': 'Последняя страница'}).get(
        'href')
    start = get_last_page.find('page') + len('page')
    end = len(get_last_page)
    lastpage = int(get_last_page[start:end - 1])
    # print(get_last_page)
    # print(lastpage)
    return lastpage


# получаем список ссылок на посты
def get_links(html):
    soup = bs(html, 'html.parser')
    list_page = soup.find_all('article', class_='post post_preview')
    post_links = []
    for item in list_page:
        post_links.append(item.find('a', class_='post__title_link').get('href'))
    # print(post_links)
    return post_links


def parse():  # запукс
    create_db()
    html = get_html_page(URL)  # вызов на html
    if html.status_code == 200:  # если получили доступ
        pages_count = get_pages_count(html.text)  # находим количество страниц
        post_links = []  # создём пустой список ссылок на страницы
        for page in range(1, pages_count + 1):  # забираем ссылки с каждой страницы
            print(f'парсинг страницы {page} из {pages_count} ...')  # маркер, что программа работает
            url = URL + 'page' + str(page) + '/'  # меняем стандартную ссылку на следующию страницу
            html = get_html_page(url)  # забираем html с новой страницы
            post_links.extend(get_links(html.text))  # Расширяем список ссылками с новых страниц

        # TODO вынести отдельно def get_content():  # заходим по ссылкам и берём основной контент

        for links in post_links:
            go = requests.get(links)  # забираем код страницы по ссылке
            result = go.content
            soup = bs(result, 'html.parser')

            post_link = links
            title = soup.find('span', class_='post__title-text').get_text()
            post_dt = soup.find('span', class_='post__time').get('data-time_published')
            post_date = post_dt[0:10]
            author_name = soup.find('span', class_='user-info__nickname user-info__nickname_small').get_text()
            url_author = soup.find('a', class_='post__user-info user-info').get('href')
            post_text = soup.find('div', class_='post__text post__text-html post__text_v1').get_text().replace('\n', '')
            insert_data(title, post_date, author_name, url_author, post_text, post_link)

        get_links(html.text)
    else:
        print('Ошибка обращения к странице')
    sleep(600)


def create_db():
    conn = sqlite3.connect('hab_posts.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS posts'
              '(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,'
              'title TEXT,'
              'post_date DATE,'
              'author_name TEXT,'
              'url_author TEXT,'
              'post_text TEXT,'
              'post_link TEXT)')
    conn.commit()


def insert_data(title, post_date, author_name, url_author, post_text, post_link):
    conn = sqlite3.connect('hab_posts.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM posts WHERE post_link = '{post_link}'")
    if c.fetchone() is None:
        c.execute('INSERT INTO posts (title, post_date, author_name, url_author, post_text, post_link)'
                  ' VALUES(?,?,?,?,?,?)', (title, post_date, author_name, url_author, post_text, post_link))
        conn.commit()
    else:
        print('Статья дублируется.')


while True:
    parse()
