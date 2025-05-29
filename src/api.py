import os
from abc import ABC, abstractmethod
from typing import Dict, Hashable, List, Optional, Union

import requests

from src.utils import find_area_id_by_name, find_id_by_name, load_reference_data

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
        self.__vacancy_url = "https://api.hh.ru/vacancies"
        self.__employer_url = "https://api.hh.ru/employers"
        self.__headers = {"User-Agent": "HHVacancyApp/1.0 (ananatereshonok@yandex.ru)"}
        self.params = {"text": "", "page": 0, "per_page": 100}
        self.vacancies = []

    def _connect(self, params: Dict[str, Union[str, int]], vacancy=True) -> Optional[requests.Response]:
        if vacancy:
            response = requests.get(self.__vacancy_url, headers=self.__headers, params=params)
        else:
            response = requests.get(self.__employer_url, headers=self.__headers, params=params)
        if response.status_code == 200:
            return response
        return None

    def _build_search_params(
            self,
            text: str,
            area=None,
            experience=None,
            employment=None,
            professional_roles=None,
            specializations=None,
            employer_id: Optional[int] = None
    ) -> dict:
        params = {
            "text": text,
            "page": 0,
            "per_page": 100
        }
        if employer_id:
            params["employer_id"] = employer_id
        if area:
            params["area"] = find_area_id_by_name(area, reference_data["areas"])
        if experience:
            params["experience"] = find_id_by_name(experience, reference_data["experience"])
        if employment:
            params["employment"] = find_id_by_name(employment, reference_data["employment"])
        if professional_roles:
            params["professional_roles"] = find_id_by_name(
                professional_roles, reference_data["professional_roles"]["categories"], nested_field="roles"
            )
        if specializations:
            params["specializations"] = find_id_by_name(
                specializations, reference_data["specializations"], nested_field="specializations"
            )
        return params

    def get_vacancies(
            self,
            text="",
            area=None,
            experience=None,
            employment=None,
            professional_roles=None,
            specializations=None
    ):
        self.vacancies = []
        params = self._build_search_params(text, area, experience, employment, professional_roles, specializations)

        while params["page"] < 20:
            response = self._connect(params)
            if not response:
                break

            vacancies = response.json().get("items", [])
            self.vacancies.extend(vacancies)

            if not vacancies:
                break

            params["page"] += 1

        return self.vacancies

    def get_vacancies_by_employers(
            self,
            employer_ids: List[int],
            text="",
            area=None,
            experience=None,
            employment=None,
            professional_roles=None,
            specializations=None
    ):
        all_vacancies = []

        for employer_id in employer_ids:
            params = self._build_search_params(
                text, area, experience, employment, professional_roles, specializations, employer_id
            )

            while params["page"] < 20:
                response = self._connect(params)
                if not response:
                    break

                vacancies = response.json().get("items", [])
                all_vacancies.extend(vacancies)

                if not vacancies:
                    break

                params["page"] += 1

        return all_vacancies

    def _find_employer_id(self, company_name: str):
        params = {
            "text": company_name,
            "per_page": 10
        }
        response = self._connect(params, vacancy=False)
        data = response.json()
        employers = data.get("items", [])

        if not employers:
            print(f'id компании {company_name} не удалось найти.')
            return None

        if len(employers) == 1:
            return int(employers[0]["id"])

        print("Найдено несколько компаний:")
        for i, emp in enumerate(employers, 1):
            print(f"{i}. {emp['name']} (ID: {emp['id']})")

        while True:
            choice = input("Выберите номер нужной компании: ")
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(employers):
                    return int(employers[index]["id"])
            print("Неверный ввод. Попробуйте снова.")

    @staticmethod
    def _get_company_info(employer_id: int):
        url = f"https://api.hh.ru/employers/{employer_id}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Ошибка при получении данных компании {employer_id}: {response.status_code}")
            return None

        data = response.json()
        return {
            "id": data["id"],
            "name": data["name"],
            "site_url": data.get("site_url"),
            "region": data["area"]["name"],
            "industries": [i["name"] for i in data.get("industries", [])],
            "trusted": data.get("trusted", False),
            "description": data.get("description", ""),
            "vacancies_url": data.get("vacancies_url"),
            "hh_url": data.get("alternate_url")
        }

    def get_companies(self, company_names: List[str]):
        result = []
        for company_name in company_names:
            company_id = self._find_employer_id(company_name)
            if company_id is None:
                continue
            company_info = self._get_company_info(company_id)
            if company_info:
                result.append(company_info)
        return result


class Vacancy:
    """
    Класс для представления одной вакансии.

    Атрибуты:
        vacancy_id (int | str): Уникальный идентификатор вакансии.
        employer_id (int): Уникальный идентификатор компании.
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
        "vacancy_id",
        "employer_id",
        "name",
        "url",
        "salary_from",
        "salary_to",
        "currency",
        "description",
        "company",
        "area",
        "employment",
        "experience",
    )

    vacancy_id: int
    employer_id: int
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
            employer_id,
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
        self.employer_id = employer_id
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
            employer_id=vacancy_json.get("employer", {}).get("id", ""),
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
            f"Вакансия {self.name} ({self.vacancy_id}): \n "
            f"- Опыт работы: {self.experience}\n"
            f"- Зарплата: {salary_str}\n"
            f"- Описание: {self.description[:150]}...\n"
            f"Подробнее по ссылке: {self.url}\n"
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


class Company:
    """
    Класс для представления компании с hh.ru.

    Атрибуты:
        employer_id (int): Уникальный идентификатор компании.
        name (str): Название компании.
        site_url (str | None): Сайт компании.
        region (str): Географический регион.
        industries (List[str]): Отрасли деятельности.
        trusted (bool): Признак верификации компании.
        description (str): Описание компании.
        vacancies_url (str): URL страницы с вакансиями.
        hh_url (str): Ссылка на страницу компании на hh.ru.
    """

    __slots__ = (
        "employer_id",
        "name",
        "site_url",
        "region",
        "industries",
        "trusted",
        "description",
        "vacancies_url",
        "hh_url",
    )

    def __init__(
        self,
        employer_id: int,
        name: str,
        site_url: str = None,
        region: str = "",
        industries: List[str] = None,
        trusted: bool = False,
        description: str = "",
        vacancies_url: str = "",
        hh_url: str = ""
    ):
        self.employer_id = employer_id
        self.name = name
        self.site_url = site_url
        self.region = region
        self.industries = industries or []
        self.trusted = trusted
        self.description = description
        self.vacancies_url = vacancies_url
        self.hh_url = hh_url

    @classmethod
    def from_json(cls, data: dict) -> "Company":
        area = data.get("area", {})
        industries = data.get("industries", [])

        return cls(
            employer_id=int(data.get("id", 0)),
            name=data.get("name", "Без названия"),
            site_url=data.get("site_url"),
            region=area.get("name", ""),
            industries=[i.get("name", "") for i in industries if isinstance(i, dict)],
            trusted=data.get("trusted", False),
            description=data.get("description", ""),
            vacancies_url=data.get("vacancies_url", ""),
            hh_url=data.get("alternate_url", "")
        )

    @classmethod
    def new_companies_from_json(cls, data_list: List[dict]) -> List["Company"]:
        return [cls.from_json(data) for data in data_list]

    def to_dict(self) -> dict:
        return {slot: getattr(self, slot) for slot in self.__slots__}

    def __str__(self):
        return f"{self.name} ({self.region}) — {', '.join(self.industries)}"
