# HH Vacancies

Приложение для получения, обработки и хранения вакансий с сайта hh.ru. Поддерживает работу с API, преобразование вакансий в объекты, сравнение по зарплате и хранение в JSON-файле.

---

## Структура проекта

### 1. `BaseApi` (абстрактный класс)
Интерфейс для всех API. Обязывает реализовать метод `get_vacancies`.

### 2. `HeadHunterAPI`
Реализация API для hh.ru. Загружает вакансии по фильтрам:
- ключевые слова
- регион
- опыт работы
- тип занятости
- профессиональные роли
- специализации

Метод:  
`get_vacancies(text, area, experience, employment, professional_roles, specializations)`

---

### 3. `Vacancy`
Класс вакансии с полями:
- `name` — название вакансии
- `url` — ссылка
- `salary_from`, `salary_to`, `currency` — зарплата
- `description` — краткое описание
- `company`, `area`, `employment`, `experience` — дополнительные поля

Методы:
- `__eq__`, `__lt__`, `__gt__` — сравнение по зарплате
- `new_vacancy_json` — создание объекта из JSON
- `new_vacancies_from_json` — создание списка вакансий из JSON

---

### 4. `AbstractVacancyStorage` (абстрактный класс)
Интерфейс хранилища вакансий:
- `add_vacancy`
- `get_vacancies`
- `delete_vacancy`

---

### 5. `VacancyStorage`
Реализация хранилища в JSON-файле.

Методы:
- `add_vacancy(vacancy: Dict)`
- `get_vacancies(**criteria)`
- `delete_vacancy(vacancy_id: str|int)`

---

## Установка

```bash
git clone <repo>
cd hh-vacancies
poetry install
```

## Пример использования

```python
api = HeadHunterAPI()
vac_json = api.get_vacancies(text="python разработчик", area="Москва")
vacancies = Vacancy.new_vacancies_from_json(vac_json)

storage = VacancyStorage("vacancies.json")
for v in vacancies:
    storage.add_vacancy(v.__dict__)
```

## Тестирование

Этот проект использует `pytest` для написания и запуска тестов.


## Запуск тестов

Для запуска всех тестов выполните следующую команду:

```sh
pytest
```

## Покрытие кода тестами

Для проверки покрытия кода тестами можно использовать `pytest-cov`:

```sh
pytest --cov=src
```

Где `src` — папка с исходным кодом.

## Логирование и отчеты

Для генерации HTML-отчёта о покрытии выполните:

```sh
pytest --cov=src --cov-report=html
```

## Лицензия

Этот проект распространяется под лицензией MIT. Подробнее см. в файле LICENSE.
