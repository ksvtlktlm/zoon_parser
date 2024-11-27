import requests
from requests.exceptions import HTTPError, Timeout
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import time
from random import randrange
from urllib.parse import unquote
import json


headers = {"accept":
               "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
           "user-agent":
               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}


def get_source_html(url):
    with webdriver.Chrome() as driver:
        driver.maximize_window()
        actions = ActionChains(driver)
        page_source_collected = False  # Флаг успешного завершения операций
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'catalog-button-showMore')))
            while True:
                block_more = driver.find_element(By.CLASS_NAME, 'catalog-button-showMore')
                actions.move_to_element(block_more).perform()
                time.sleep(2)
                try:
                    button = block_more.find_element(By.CLASS_NAME, 'button')
                    actions.move_to_element(button).perform()
                    time.sleep(2)
                    button.click()
                    time.sleep(6)

                except:
                    print('Данные собраны!')
                    page_source_collected = True  # Устанавливаем флаг, что страница собрана
                    break

        except TimeoutException as e:
            print(f"Ошибка тайм-аута: {e}")
        except Exception as e:
            print(f"Непредвиденная ошибка в get_source_html: {e}")

        finally:
            if page_source_collected:
                with open('source_page.html', 'w', encoding='utf-8') as file:
                    file.write(driver.page_source)
            driver.quit()


def get_urls(file_path):  # функция находит ссылки на каждую больницу
    try:

        with open(file_path, 'r', encoding='utf-8') as file:
            src = file.read()

        soup = BeautifulSoup(src, 'lxml')
        items_div = soup.find_all('div', class_='minicard-item__info')
        links = [i.find('a', class_='title-link').get('href') for i in items_div]

        with open('links.txt', 'w', encoding='utf-8') as file:  # записываем ссылки на больницы в текстовый файл
            for link in links:
                file.write(f'{link}\n')
        return 'Ссылки собраны!'

    except Exception as e:
        print(f'Ошибка чтения файла html: {e}')


def get_data(file_path):

    # Настройка повторных попыток
    retry_strategy = Retry(
        total=10,                    # Максимум 10 попыток
        status_forcelist=[500, 502, 503, 504],     # Повторять попытки для статусов
        backoff_factor=1,           # Увеличение времени ожидания (1, 2, 4...)
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)

    result_list = []
    count = 0 #счетчик обработанных ссылок

    try:
        with open('links.txt', 'r', encoding='utf-8') as file:
            url_list = [url.strip() for url in file.readlines()]
    except Exception as e:
        print(f'Ошибка чтения файла txt: {e}')

    with requests.Session() as session:

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        for url in url_list:
            try:
                response = session.get(url=url, headers=headers, timeout=40)
                response.raise_for_status()  # Вызывает HTTPError при неудачном статусе
                soup = BeautifulSoup(response.text, 'lxml')

                #название ЛПУ
                try:
                    item_name = soup.find('span', {'itemprop': 'name'}).text.strip()
                except Exception:
                    item_name = None

                #список номеров телефонов
                try:
                    item_phones = soup.find('div', class_='service-phones-list').find_all('a', class_='js-phone-number')
                    item_phones_list = [phone.get('href').split(':')[-1].strip() for phone in item_phones]
                except Exception:
                    item_phones_list = None

                #адрес
                try:
                    item_address = ' '.join(soup.find('address', class_='iblock').text.strip().split())
                except Exception:
                    item_address = None

                # вебсайт
                try:
                    item_web = soup.find('div', class_='service-website-value').find('a').get('href')
                    if 'to=' in item_web:
                        item_web_clean = unquote(item_web).split('to=')[1].split('&')[0]
                    elif '?' in item_web:
                        item_web_clean = unquote(item_web).split('?')[0]
                    else:
                        item_web_clean = item_web
                except Exception:
                    item_web_clean = None


                #соцсети
                try:
                    item_social = soup.find('div', class_='js-service-socials').find_all('a')
                    item_social_clean = [unquote(i.get('href')).split('to=')[1].split('&')[0] for i in item_social]
                except Exception as e:
                    item_social_clean = None

                result_list.append(
                    {
                        'item_name': item_name,
                        'url': url,
                        'item_adress': item_address,
                        'item_phone_list': item_phones_list,
                        'item_website': item_web_clean,
                        'item_social_network_list': item_social_clean

                    }
                )
                time.sleep(randrange(2, 5))
                count += 1
                print(f'Обработано {count}/{len(url_list)}')

            except HTTPError as e:
                print(f"HTTP ошибка для {url}: {e}")
            except Timeout as e:
                print(f"Таймаут для {url}: {e}")
            except Exception as e:
                print(f"Необработанная ошибка для {url}: {e}")

    with open('result.json', 'w', encoding='utf-8') as file:
        json.dump(result_list, file, indent=4, ensure_ascii=False)

    return 'Данные успешно записаны в файл json!'


def main():
    get_source_html(url='https://zoon.ru/krasnodar/medical/type/poliklinika_dlya_vzroslyh/')
    print(get_urls(file_path='source_page.html'))
    print(get_data(file_path='links.txt'))


if __name__ == '__main__':
    main()
