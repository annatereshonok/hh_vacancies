import os
from typing import List, Union

from dotenv import load_dotenv
import psycopg2
from psycopg2 import Error

from src.api import Vacancy, Company

load_dotenv()


class DBManager:
    """
    Класс для управления подключением к PostgreSQL и взаимодействием с таблицами employers и vacancies.
    Использует библиотеку psycopg2.
    """

    def __init__(self):
        """Инициализирует подключение к базе данных и создает курсор."""
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT")
            )
            self.conn.autocommit = True
            self.cur = self.conn.cursor()
            print("Успешное подключение к базе данных.")
        except Error as e:
            print(f"Ошибка подключения к БД: {e}")
            self.conn = None
            self.cur = None

    def _create_employers_table(self):
        """Создает таблицу employers, если она не существует."""
        if not self.cur:
            print("Нет соединения с БД.")
            return
        try:
            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS employers (
                    employer_id BIGINT PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    site_url VARCHAR,
                    region VARCHAR,
                    industries TEXT,
                    trusted BOOLEAN,
                    description TEXT,
                    vacancies_url VARCHAR,
                    hh_url VARCHAR
                );
                """
            )
            print("Таблица employers успешно создана или уже существует.")
        except Error as e:
            print(f"Ошибка при создании таблицы employers: {e}")

    def _create_vacancy_table(self):
        """Создает таблицу vacancies, если она не существует."""
        if not self.cur:
            print("Нет соединения с БД.")
            return
        try:
            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS vacancies (
                    vacancy_id BIGINT PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    url VARCHAR NOT NULL,
                    salary_from FLOAT,
                    salary_to FLOAT,
                    currency VARCHAR,
                    description TEXT,
                    company VARCHAR,
                    area VARCHAR,
                    employment VARCHAR,
                    experience VARCHAR,
                    employer_id BIGINT REFERENCES employers(employer_id)
                );
                """
            )
            print("Таблица vacancies успешно создана или уже существует.")
        except Error as e:
            print(f"Ошибка при создании таблицы vacancies: {e}")

    def _delete_tables(self):
        self.cur.execute("DROP TABLE IF EXISTS employers CASCADE;")
        self.cur.execute("DROP TABLE IF EXISTS vacancies CASCADE;")
        print("Таблицы vacancies и vacancies успешно удалены.")

    def _close(self):
        """Закрывает соединение и курсор с базой данных."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            print("Соединение с БД закрыто.")

    def _save_data(self, data: List[Union[Vacancy, Company]], table_name: str) -> None:
        """
        Сохраняет список объектов Vacancy или Company в соответствующую таблицу базы данных.

        :param data: Список объектов Vacancy или Company
        :param table_name: Название таблицы ('vacancies' или 'employers')
        """
        if not self.cur:
            print("Нет подключения к БД.")
            return

        try:
            if table_name == 'vacancies':
                for vacancy in data:
                    self.cur.execute(
                        """
                        INSERT INTO vacancies (
                            vacancy_id,
                            name,
                            url,
                            salary_from,
                            salary_to,
                            currency,
                            description,
                            company,
                            area,
                            employment,
                            experience,
                            employer_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (vacancy_id) DO NOTHING;
                        """,
                        (
                            vacancy.vacancy_id,
                            vacancy.name,
                            vacancy.url,
                            vacancy.salary_from,
                            vacancy.salary_to,
                            vacancy.currency,
                            vacancy.description,
                            vacancy.company,
                            vacancy.area,
                            vacancy.employment,
                            vacancy.experience,
                            vacancy.employer_id
                        )
                    )
                print("Данные вакансий успешно сохранены.")

            elif table_name == 'employers':
                for company in data:
                    self.cur.execute(
                        """
                        INSERT INTO employers (
                            employer_id,
                            name,
                            site_url,
                            region,
                            industries,
                            trusted,
                            description,
                            vacancies_url,
                            hh_url
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (employer_id) DO NOTHING;
                        """,
                        (
                            company.employer_id,
                            company.name,
                            company.site_url,
                            company.region,
                            ", ".join(company.industries),
                            company.trusted,
                            company.description,
                            company.vacancies_url,
                            company.hh_url
                        )
                    )
                print("Данные компаний успешно сохранены.")

            else:
                print(f"Неизвестная таблица: {table_name}")

        except psycopg2.Error as e:
            print(f"Ошибка при сохранении данных в {table_name}: {e}")

    def get_companies_and_vacancies_count(self):
        """
        Получает список всех компаний и количество вакансий у каждой компании.
        Возвращает список кортежей: (employer_id, name, num_vacancies)
        """
        if not self.cur:
            print("Нет подключения к БД.")
            return

        try:
            self.cur.execute("""
            SELECT e.employer_id, e.name, COUNT(DISTINCT v.vacancy_id) AS num_vacancies
            FROM employers e
            LEFT JOIN vacancies v USING (employer_id)
            GROUP BY e.employer_id, e.name
            ORDER BY num_vacancies DESC;
            """)
            return self.cur.fetchall()
        except psycopg2.Error as e:
            print(f"Ошибка при подсчете количества вакансий: {e}")
            return []

    def get_all_vacancies(self):
        """
        Получает список всех вакансий с указанием названия компании, названия вакансии, зарплаты и ссылки на вакансию.
        Возвращает список кортежей.
        """
        if not self.cur:
            print("Нет подключения к БД.")
            return []

        try:
            self.cur.execute("""
                SELECT company, name, salary_from, salary_to, url
                FROM vacancies;
            """)
            return self.cur.fetchall()
        except psycopg2.Error as e:
            print(f"Не удалось получить список вакансий: {e.pgerror or str(e)}")
            return []

    def get_avg_salary(self):
        """
        Получает среднюю зарплату по вакансиям.
        Возвращает одно значение (float) или None.
        """
        if not self.cur:
            print("Нет подключения к БД.")
            return None

        try:
            self.cur.execute("""
                SELECT AVG(COALESCE(salary_from, salary_to)) AS avg_salary
                FROM vacancies
                WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL;
            """)
            result = self.cur.fetchone()
            return result[0] if result else None
        except psycopg2.Error as e:
            print(f"Ошибка при вычислении средней зарплаты: {e.pgerror or str(e)}")
            return None

    def get_vacancies_with_higher_salary(self):
        """
        Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям.
        Возвращает список кортежей.
        """
        if not self.cur:
            print("Нет подключения к БД.")
            return []

        try:
            self.cur.execute("""
                WITH avg_salary_cte AS (
                SELECT AVG(COALESCE(salary_from, salary_to)) AS avg_salary FROM vacancies
                )
                SELECT *
                FROM vacancies, avg_salary_cte
                WHERE
                (salary_from IS NOT NULL AND salary_from > avg_salary_cte.avg_salary)
                OR
                (salary_to IS NOT NULL AND salary_to > avg_salary_cte.avg_salary);
            """)
            return self.cur.fetchall()

        except psycopg2.Error as e:
            print(f"Ошибка при получении вакансий с ЗП выше средней: {e.pgerror or str(e)}")
            return []

    def get_vacancies_with_keyword(self, keyword: str):
        """
        Получает список всех вакансий, в названии которых содержатся переданные в метод слова, например "python".
        Возвращает список кортежей.

        :param keyword: Ключевое слово для поиска
        """
        if not self.cur:
            print("Нет подключения к БД.")
            return []

        try:
            sql = """
            SELECT * 
            FROM vacancies
            WHERE name ILIKE %s
            """
            self.cur.execute(sql, (f'%{keyword}%',))
            return self.cur.fetchall()

        except psycopg2.Error as e:
            print(f"Ошибка при получении вакансий с ключевым словом: {e.pgerror or str(e)}")
            return []
