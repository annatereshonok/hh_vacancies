import os

from src.utils import load_reference_data, load_companies_from_file
from src.api import HeadHunterAPI, Vacancy, Company
from src.database import DBManager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = "data"

reference_data = load_reference_data()


if __name__ == "__main__":
    db = DBManager()

    db._delete_tables()

    db._create_employers_table()
    db._create_vacancy_table()

    companies_names = load_companies_from_file(os.path.join(BASE_DIR, DATA_FOLDER, "companies.json"))

    print("Загружаю данные о компаниях...")
    api = HeadHunterAPI()
    employers_data = api.get_companies(companies_names)
    companies = Company.new_companies_from_json(employers_data)

    db._save_data(companies, 'employers')

    employer_ids = [int(emp['id']) for emp in employers_data]
    print("Загружаю данные о вакансиях...")
    vacancies_raw = api.get_vacancies_by_employers(employer_ids=employer_ids)
    vacancies = Vacancy.new_vacancies_from_json(vacancies_raw)
    db._save_data(vacancies, 'vacancies')
    print("Импорт завершён успешно.")

    print(db.get_companies_and_vacancies_count())
    print(db.get_avg_salary())
    print(db.get_vacancies_with_higher_salary())
    print(db.get_all_vacancies())

    db._close()
