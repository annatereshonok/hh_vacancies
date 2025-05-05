import os
from abc import ABC, abstractmethod
import requests
import json
from typing import List, Dict, Hashable, Union, Optional

from src.utils import find_id_by_name, load_reference_data, find_area_id_by_name

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = "data"

reference_data = load_reference_data()


class BaseAPI(ABC):
    @abstractmethod
    def _connect(self, params: Dict[str, Union[str, int]]) -> Optional[requests.Response]:
        pass

    @abstractmethod
    def get_vacancies(self, text: str) -> List[Dict]:
        pass


class HeadHunterAPI(BaseAPI):
    """
    Класс для взаимодействия с API платформы hh.ru. Наследуется от абстрактного класса BaseApi.

    Атрибуты:
        url (str): URL-адрес для запросов к API вакансий hh.ru.
        headers (dict): Заголовки запроса, включая User-Agent.
        params (dict): Параметры запроса, такие как текст поиска, страница и количество вакансий на странице.
        vacancies (list): Список полученных вакансий в сыром JSON-формате.

    Методы:
        get_vacancies(...): Получает список вакансий с hh.ru с учётом указанных фильтров:
            - текст (ключевое слово)
            - регион (area)
            - опыт (experience)
            - занятость (employment)
            - профессиональная роль (professional_roles)
            - специализация (specializations)

    Возвращает список вакансий в формате JSON.
    """

    def __init__(self):
        self.__url = "https://api.hh.ru/vacancies"
        self.__headers = {"User-Agent": "HHVacancyApp/1.0 (ananatereshonok@yandex.ru)"}
        self.params = {"text": "", "page": 0, "per_page": 100}
        self.vacancies = []

    def _connect(self, params: Dict[str, Union[str, int]]) -> Optional[requests.Response]:
        response = requests.get(self.__url, headers=self.__headers, params=params)
        if response.status_code == 200:
            return response
        return None

    def get_vacancies(
            self, text="", area=None, experience=None, employment=None, professional_roles=None, specializations=None
    ):
        self.params["text"] = text
        if area:
            self.params["area"] = find_area_id_by_name(area, reference_data["areas"])
        if experience:
            self.params["experience"] = find_id_by_name(experience, reference_data["experience"])
        if employment:
            self.params["employment"] = find_id_by_name(employment, reference_data["employment"])
        if professional_roles:
            self.params["professional_roles"] = find_id_by_name(
                professional_roles, reference_data["professional_roles"]["categories"], nested_field="roles"
            )
        if specializations:
            self.params["specializations"] = find_id_by_name(
                specializations, reference_data["specializations"], nested_field="specializations"
            )

        while self.params.get("page") != 20:
            response = self._connect(self.params)
            if not response:
                break
            vacancies = response.json()
            vacancies = vacancies["items"]
            self.vacancies.extend(vacancies)
            self.params["page"] += 1

        return self.vacancies


class Vacancy:
    """
    Класс для представления одной вакансии.

    Атрибуты:
        vacancy_id (int | str): Уникальный идентификатор вакансии.
        name (str): Название вакансии.
        url (str): Ссылка на вакансию.
        salary_from (float): Нижняя граница зарплаты.
        salary_to (float): Верхняя граница зарплаты.
        currency (str): Валюта зарплаты.
        description (str): Краткое описание или требования.
        company (str): Название компании-работодателя.
        area (str): Город или регион.
        employment (str): Тип занятости.
        experience (str): Требуемый опыт работы.

    Методы:
        new_vacancy_json(json): Класс-метод для создания объекта Vacancy из JSON-данных одной вакансии.
        new_vacancies_from_json(json_list): Класс-метод для создания списка объектов Vacancy из списка JSON-данных.
        to_dict(): Преобразует объект в словарь (для сохранения в JSON).
        __str__(): Возвращает строковое представление вакансии.
        __eq__, __lt__, __gt__(): Методы сравнения вакансий по зарплате.
    """

    __slots__ = (
        "vacancy_id", "name", "url", "salary_from", "salary_to", "currency",
        "description", "company", "area", "employment", "experience"
    )

    vacancy_id: int
    name: str
    url: str
    salary: str
    salary_from: float
    salary_to: float
    currency: str
    description: str
    company: str
    area: str
    employment: str
    experience: str

    def __init__(
            self,
            vacancy_id,
            name,
            url,
            salary_from=0,
            salary_to=0,
            currency="RUB",
            description="",
            company="",
            area="",
            employment="",
            experience="",
    ):
        self.__validate_string(name, "Название вакансии")
        self.__validate_url(url)
        self.__validate_salary(salary_from, salary_to)

        self.vacancy_id = vacancy_id
        self.name = name
        self.url = url
        self.salary_from = float(salary_from)
        self.salary_to = float(salary_to)
        self.currency = currency
        self.description = description
        self.company = company
        self.area = area
        self.employment = employment
        self.experience = experience

    @staticmethod
    def __validate_string(value: str, field_name: str):
        if not value or not isinstance(value, str):
            raise ValueError(f"{field_name} должно быть непустой строкой.")

    @staticmethod
    def __validate_url(url: str):
        if not url.startswith("http"):
            raise ValueError("Некорректный URL.")

    @staticmethod
    def __validate_salary(salary_from: float, salary_to: float):
        if not isinstance(salary_from, (int, float)) or salary_from < 0:
            raise ValueError("salary_from должно быть числом >= 0.")
        if not isinstance(salary_to, (int, float)) or salary_to < 0:
            raise ValueError("salary_to должно быть числом >= 0.")

    @classmethod
    def new_vacancy_json(cls, vacancy_json: Dict[Hashable, Union[str, int, float]]):
        salary_data = vacancy_json.get("salary") or {}

        salary_from = salary_data.get("from") or 0
        salary_to = salary_data.get("to") or 0
        currency = salary_data.get("currency") or "RUB"

        return cls(
            vacancy_id=vacancy_json.get("id", ""),
            name=vacancy_json.get("name", ""),
            url=vacancy_json.get("alternate_url", ""),
            salary_from=salary_from,
            salary_to=salary_to,
            currency=currency,
            description=vacancy_json.get("snippet", {}).get("requirement", "") or "",
            company=vacancy_json.get("employer", {}).get("name", "") or "",
            area=vacancy_json.get("area", {}).get("name", "") or "",
            employment=vacancy_json.get("employment", {}).get("name", "") or "",
            experience=vacancy_json.get("experience", {}).get("name", "") or "",
        )
        return vacancy

    @classmethod
    def new_vacancies_from_json(cls, vacancies_json: List[Dict[Hashable, Union[str, int, float]]]):
        return [cls.new_vacancy_json(vacancy) for vacancy in vacancies_json]

    @property
    def _salary_for_comparison(self):
        return self.salary_to if self.salary_to else self.salary_from

    def __str__(self):
        salary_str = f"{self.salary_to} - {self.salary_from} {self.currency}"
        return (
            f"Вакансия {self.name} ({self.vacancy_id}): "
            f"- Опыт работы: {self.experience}"
            f"- Зарплата: {salary_str}"
            f"- Описание: {self.description[:150]}..."
            f"Подробнее по ссылке: {self.url}"
        )

    def __eq__(self, other):
        if not isinstance(other, Vacancy):
            return NotImplemented
        return self._salary_for_comparison == other._salary_for_comparison

    def __lt__(self, other):
        if not isinstance(other, Vacancy):
            return NotImplemented
        return self._salary_for_comparison < other._salary_for_comparison

    def __gt__(self, other):
        if not isinstance(other, Vacancy):
            return NotImplemented
        return self._salary_for_comparison > other._salary_for_comparison

    def to_dict(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}


class AbstractVacancyStorage(ABC):
    """
    Абстрактный базовый класс, определяющий интерфейс для работы с хранилищем вакансий.
    """

    @abstractmethod
    def add_vacancy(self, vacancy: Dict[str, Union[str, int, float]]) -> None:
        pass

    @abstractmethod
    def get_vacancies(self, **criteria) -> List[Dict[str, Union[str, int, float]]]:
        pass

    @abstractmethod
    def delete_vacancy(self, vacancy_id: Union[int, str]) -> None:
        pass


class VacancyStorage(AbstractVacancyStorage):
    """
    Класс для работы с вакансиями, сохранёнными в JSON-файл.

    Реализует интерфейс AbstractVacancyStorage.
    """

    def __init__(self, filename: str = "vacancies.json"):
        self.__filepath = os.path.join(BASE_DIR, DATA_FOLDER, filename)
        if not os.path.exists(self.__filepath):
            with open(self.__filepath, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _load_data(self) -> List[Dict]:
        with open(self.__filepath, "r", encoding="utf-8") as file:
            return json.load(file)

    def _save_data(self, data: List[Dict]) -> None:
        with open(self.__filepath, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def add_vacancy(self, vacancy: Dict[str, Union[str, int, float]]) -> None:
        data = self._load_data()
        if vacancy not in data:
            data.append(vacancy)
            self._save_data(data)

    def add_vacancies(self, vacancies: List[Dict[str, Union[str, int, float]]]) -> None:
        data = self._load_data()
        data.extend(vacancies)
        self._save_data(data)

    def get_vacancies(self, **criteria) -> List[Dict[str, Union[str, int, float]]]:
        data = self._load_data()
        if not criteria:
            return data

        result = []
        for vacancy in data:
            if all(str(vacancy.get(k, "")).lower() == str(v).lower() for k, v in criteria.items()):
                result.append(vacancy)
        return result

    def delete_vacancy(self, vacancy_id: Union[int, str]) -> None:
        data = self._load_data()
        data = [v for v in data if str(v.get("vacancy_id", "")) != str(vacancy_id)]
        self._save_data(data)


def parse_semicolon_input(raw_input: str) -> Optional[List[str]]:
    if not raw_input.strip():
        return None
    return [s.strip() for s in raw_input.split(";") if s.strip()]


def user_interface():
    print("Добро пожаловать в программу поиска вакансий!\n")

    hh_api = HeadHunterAPI()
    storage = VacancyStorage("vacancies.json")

    while True:
        print("\nВыберите действие:")
        print("1 — Найти вакансии по ключевому слову и другим параметрам")
        print("2 — Показать топ N вакансий по зарплате")
        print("3 — Найти вакансии по ключевому слову в описании")
        print("4 — Показать все вакансии из локального файла")
        print("5 — Выйти")

        choice = input("Ваш выбор: ").strip()

        if choice == "1":
            keyword = input("Введите поисковый запрос (ключевое слово): ").strip()
            area = input("Введите регион (необязательно): ").strip() or None
            experience = parse_semicolon_input(
                input("Опыт работы (например, 'Нет опыта', 'От 1 года до 3 лет', 'От 3 до 6 лет', опционально): ")
            )
            employment = parse_semicolon_input(
                input("Тип занятости ('Полная занятость', 'Частичная занятость', 'Проектная работа', опционально): ")
            )
            professional_roles = parse_semicolon_input(
                input("Профессиональная роль ('Программист, разработчик', 'Продуктовый аналитик', опционально): ")
            )
            specializations = parse_semicolon_input(input("Специализация (например, 'Разработка', опционально): "))

            vacancies_json = hh_api.get_vacancies(
                text=keyword,
                area=area,
                experience=experience,
                employment=employment,
                professional_roles=professional_roles,
                specializations=specializations,
            )
            vacancies = Vacancy.new_vacancies_from_json(vacancies_json)
            storage.add_vacancies([v.to_dict() for v in vacancies])

            for v in vacancies:
                print(v)

        elif choice == "2":
            try:
                top_n = int(input("Сколько вакансий вывести в топе? "))
            except ValueError:
                print("Введите число.")
                continue

            data = storage.get_vacancies()
            vacancies = [Vacancy(**v) for v in data]
            sorted_vacancies = sorted(vacancies, reverse=True)
            for v in sorted_vacancies[:top_n]:
                print(v)

        elif choice == "3":
            keyword = input("Введите ключевое слово для поиска в описании: ").lower()
            data = storage.get_vacancies()
            found = [Vacancy(**v) for v in data if keyword in v.get("description", "").lower()]
            if found:
                for v in found:
                    print(v)
            else:
                print("Ничего не найдено по вашему запросу.")

        elif choice == "4":
            data = storage.get_vacancies()
            if not data:
                print("Файл с вакансиями пуст. Воспользуйтесь пунктом 1.")
            else:
                for v in data:
                    print(Vacancy(**v))

        elif choice == "5":
            print("Завершение программы.")
            break

        else:
            print("Некорректный выбор. Попробуйте снова.")


if __name__ == "__main__":
    user_interface()
