import json
import os
from typing import Any, Dict, List, Optional, Union

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = "data"


def fetch_hh_reference_data(endpoint: str) -> None:
    """
    Загружает справочные данные с HH.ru по указанному эндпоинту.

    Параметры:
        endpoint (str): Короткое имя справочника (например, 'areas', 'professional_roles', 'specializations').

    Возвращает:
        Список словарей с данными справочника.

    Исключения:
        ValueError: Если получен неверный код ответа от API.
    """
    url = f"https://api.hh.ru/{endpoint}"

    headers = {"User-Agent": "YourAppName/1.0 (ananatereshonok@yandex.ru)"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Ошибка при получении данных с HH.ru: {response.status_code}")

    response_json = response.json()

    with open(os.path.join(BASE_DIR, DATA_FOLDER, f"{endpoint}.json"), "w", encoding="utf-8") as f:
        json.dump(response_json, f, ensure_ascii=False, indent=2)


def find_area_id_by_name(name: str, areas: List[Dict]) -> Optional[str]:
    """
    Ищет ID региона или города по имени, рекурсивно обходя все уровни справочника areas.

    :param name: Название региона/города
    :param areas: Список данных из areas.json
    :return: ID найденной области, либо None
    """
    name = name.lower()

    def recursive_search(area_list):
        for area in area_list:
            if name in area["name"].lower():
                return area["id"]
            if area.get("areas"):
                found = recursive_search(area["areas"])
                if found:
                    return found
        return None

    return recursive_search(areas)


def find_id_by_name(
    name: Union[str, List[str]], data: List[Dict[str, Any]], nested_field: Optional[str] = None
) -> Optional[Union[str, List[str]]]:
    """
    Находит ID или список ID по имени (или списку имён) в справочных данных HH.ru.

    Параметры:
        name (Union[str, List[str]]): Название или список названий для поиска.
        data (List[Dict[str, Any]]): Список справочных данных.
        nested_field (Optional[str]): Название вложенного поля (например, "specializations").

    Возвращает:
        str | List[str] | None: Найденный ID или список ID. None — если ничего не найдено.
    """

    def search(single_name: str) -> Optional[str]:
        for item in data:
            if nested_field:
                for nested_item in item.get(nested_field, []):
                    if single_name.lower() in nested_item["name"].lower():
                        return nested_item["id"]
            else:
                if single_name.lower() in item["name"].lower():
                    return item["id"]
        return None

    if isinstance(name, list):
        ids = [search(n) for n in name]
        return list(filter(None, ids))
    else:
        return search(name)


def load_reference_data() -> Dict[str, Any]:
    """
    Загружает все справочные данные из папки data.

    Возвращает:
        Dict[str, Any]: Словарь с ключами - названиями файлов без расширения, и данными из JSON-файлов.
    """
    data_dir = os.path.join(BASE_DIR, "data")
    files = ["areas.json", "specializations.json", "experience.json", "employment.json", "professional_roles.json"]

    reference_data = {}

    for filename in files:
        path = os.path.join(data_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            key = filename.replace(".json", "")
            reference_data[key] = json.load(f)

    return reference_data


def load_companies_from_file(filename='companies.json'):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            companies = json.load(f)
        return companies
    except FileNotFoundError:
        print(f"Файл {filename} не найден.")
        return []
    except json.JSONDecodeError:
        print(f"Ошибка чтения JSON из файла {filename}.")
        return []
