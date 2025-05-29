from abc import ABC, abstractmethod
import os
import json
from typing import Dict, List, Union

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = "data"


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
