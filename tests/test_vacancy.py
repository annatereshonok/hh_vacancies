import pytest

from src.main import Vacancy


@pytest.fixture
def fake_vacancy_data():
    return {
        "id": "123",
        "name": "Python Developer",
        "alternate_url": "http://example.com/vacancy",
        "salary": {"from": 100000, "to": 150000, "currency": "RUB"},
        "snippet": {"requirement": "Python, Django"},
        "employer": {"name": "Test Company"},
        "area": {"name": "Москва"},
        "employment": {"name": "Полная занятость"},
        "experience": {"name": "От 1 года до 3 лет"},
    }


def test_vacancy_creation(fake_vacancy_data):
    vacancy = Vacancy.new_vacancy_json(fake_vacancy_data)
    assert vacancy.name == "Python Developer"
    assert vacancy.salary_from == 100000
    assert vacancy.salary_to == 150000
    assert vacancy.currency == "RUB"


def test_invalid_vacancy_name():
    with pytest.raises(ValueError):
        Vacancy(1, "", "http://example.com")


def test_invalid_vacancy_url():
    with pytest.raises(ValueError):
        Vacancy(1, "Name", "invalid_url")


def test_vacancy_str(fake_vacancy_data):
    vacancy = Vacancy.new_vacancy_json(fake_vacancy_data)
    result = str(vacancy)
    assert "Python Developer" in result
    assert "Опыт работы: От 1 года до 3 лет" in result


def test_vacancy_comparison():
    v1 = Vacancy(1, "Dev", "http://url", salary_from=100000)
    v2 = Vacancy(2, "Lead", "http://url", salary_to=150000)
    assert v2 > v1


def test_to_dict(fake_vacancy_data):
    vacancy = Vacancy.new_vacancy_json(fake_vacancy_data)
    data = vacancy.to_dict()
    assert isinstance(data, dict)
    assert data["name"] == "Python Developer"
