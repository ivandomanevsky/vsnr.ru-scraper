import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup

logging.basicConfig(filename="logging.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_URL = "http://vsnr.ru/"
AJAX_PLAN_LIST_URL = BASE_URL + "local/ajax/plan_list.php?PAGEN_1="
HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}
PAGE_LIMIT = 756


def main():
    # Логирование о начале работы парсера
    logging.info("Начало работы парсера")

    links = get_links()
    data = get_data(links)

    data = sorted(data, key=lambda x: x["complex"])
    save_to_excel(data)

    # Логирование о завершении работы парсера
    logging.info("Парсер успешно завершил работу")


def get_links() -> []:
    # Создание списка для хранения ссылок
    links = []

    for i in range(1, PAGE_LIMIT + 1):
        # Получение ссылок на жилье
        ajax_plan_list_response = requests.post(f"{AJAX_PLAN_LIST_URL}{i}", headers=HEADERS)
        plan_soup = BeautifulSoup(ajax_plan_list_response.text, "html.parser")

        # Добавление ссылок в список
        for link in plan_soup.find_all(class_="btn-reset btn-secondary btn-secondary--arrow"):
            links.append(BASE_URL + link["href"])

        # Логирование о процессе сбора ссылок
        logging.info(f"Со страницы {i} собраны ссылки на недвижимость")

    return links


def get_data(links: []) -> []:
    # Создание списка для хранения данных
    data = []
    i = 0

    for link in links:
        response = requests.get(link)
        flat_soup = BeautifulSoup(response.text, "html.parser")

        # Получение названия комплекса
        complex_name = get_complex_name(flat_soup)
        # Получение типа жилья (квартира, апартаменты и т.д.)
        flat_type = get_flat_type(flat_soup)
        # Получение цены жилья
        flat_price = get_flat_price(flat_soup)

        # Получение прочих данных о жилье
        flat_other_data = [
            get_flat_other_data(other_data)
            for other_data in flat_soup.find_all(class_="apartment__mid_item-name")
        ]

        data.append({
            "complex": complex_name,
            "faza": None,
            "building": flat_other_data[0] if flat_other_data else None,
            "floor": flat_other_data[1] if len(flat_other_data) > 1 else None,
            "section": flat_other_data[2] if len(flat_other_data) > 2 else None,
            "number": flat_other_data[3] if len(flat_other_data) > 3 else None,
            "rooms": flat_other_data[5] if len(flat_other_data) > 5 else None,
            "area": flat_other_data[4].replace('.', ',') if len(flat_other_data) > 4 else None,
            "area_living": None,
            "area_kitchen": None,
            "price": flat_price.replace('.', ','),
            "price_sale": None,
            "furnished": flat_other_data[6] if len(flat_other_data) > 6 else None,
            "is_furniture": None,
            "type": flat_type,
            "plan": None,
            "source": link,
            "deadline": None,
            "ceil_height": None,
        })

        i += 1
        # Логирование о количестве обработанных страниц
        logging.info(f"Обработано страниц {i}/{len(links)}")

    return data


def get_complex_name(soup):
    try:
        # Обработка ошибки NoneType
        return soup.find(class_="card-secondary__title").text
    except AttributeError:
        return None


def get_flat_type(soup):
    try:
        # Обработка ошибки NoneType
        title = soup.find(class_="apartment__description-title").text.lower()
        return "Квартира" if "квартира" in title else "Кладовка" if "кладовка" in title \
            else "Машиноместо" if "машиноместо" in title else "Апартаменты"
    except AttributeError:
        return None


def get_flat_price(soup):
    try:
        # Обработка ошибки NoneType
        return (soup.find(class_="regular_64 apartment__price-sum")
                .text.replace(" ", "")
                .replace("₽", "")
                .strip())
    except AttributeError:
        return None


def get_flat_other_data(other_data):
    try:
        # Обработка ошибки NoneType
        return other_data.text.replace("м²", "").replace("№", "").replace("Корпус", "").replace("отделка", "").strip()
    except AttributeError:
        return None


def save_to_excel(data):
    df = pd.DataFrame(data)
    df.to_excel("result.xlsx", index=False)


if __name__ == "__main__":
    main()
