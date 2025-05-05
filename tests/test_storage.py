import os
import pytest
from src.main import VacancyStorage

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = "data"


@pytest.fixture
def storage():
    file_path = os.path.join(BASE_DIR, DATA_FOLDER, "test_vacancies.json")

    if os.path.exists(file_path):
        os.remove(file_path)

    return VacancyStorage(filename="test_vacancies.json")


def test_add_and_get_vacancy(storage):
    vacancy = {
        "vacancy_id": 1,
        "name": "Dev",
        "url": "http://url",
        "salary_from": 0,
        "salary_to": 0,
        "currency": "RUB",
    }
    storage.add_vacancy(vacancy)
    result = storage.get_vacancies()
    assert len(result) == 1
    assert result[0]["name"] == "Dev"


def test_delete_vacancy(storage):
    vacancy = {
        "vacancy_id": 1,
        "name": "Dev",
        "url": "http://url",
        "salary_from": 0,
        "salary_to": 0,
        "currency": "RUB",
    }
    storage.add_vacancy(vacancy)
    storage.delete_vacancy(1)
    assert storage.get_vacancies() == []


def test_prevent_duplicate_vacancies(storage):
    vacancy = {
        "vacancy_id": 1,
        "name": "Dev",
        "url": "http://url",
        "salary_from": 0,
        "salary_to": 0,
        "currency": "RUB",
    }
    storage.add_vacancy(vacancy)
    storage.add_vacancy(vacancy)
    result = storage.get_vacancies()
    assert len(result) == 1


def test_get_vacancies_with_filter(storage):
    vacancies = [
        {"vacancy_id": 1, "name": "Python Dev", "url": "http://url1", "salary_from": 100000, "salary_to": 150000, "currency": "RUB"},
        {"vacancy_id": 2, "name": "Java Dev", "url": "http://url2", "salary_from": 80000, "salary_to": 120000, "currency": "RUB"},
    ]
    for v in vacancies:
        storage.add_vacancy(v)

    filtered = storage.get_vacancies(name="Python Dev")
    assert len(filtered) == 1
    assert filtered[0]["vacancy_id"] == 1

