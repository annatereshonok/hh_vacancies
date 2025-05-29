from unittest.mock import MagicMock, patch
import pytest

from src.main import HeadHunterAPI
from src.main import Vacancy, Company


@patch("src.main.find_area_id_by_name", return_value=1)
@patch("src.main.find_id_by_name", return_value=1)
@patch(
    "src.main.load_reference_data",
    return_value={
        "areas": [],
        "experience": [],
        "employment": [],
        "professional_roles": {"categories": []},
        "specializations": [],
    },
)
@patch("src.main.requests.get")
def test_get_vacancies(
    mock_requests_get,
    mock_load_reference_data,
    mock_find_id_by_name,
    mock_find_area_id_by_name,
):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = [
        {"items": [{"id": "1", "name": "Dev", "alternate_url": "http://url"}]} for _ in range(20)
    ]
    mock_requests_get.return_value = mock_response

    api = HeadHunterAPI()
    result = api.get_vacancies(
        text="developer",
        area="Москва",
        experience="Нет опыта",
        employment="Полная занятость",
        professional_roles="Программист, разработчик",
        specializations="Разработка",
    )

    assert isinstance(result, list)
    assert len(result) == 20
    assert result[0]["name"] == "Dev"
    assert mock_requests_get.call_count == 20

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


def test_company_from_json():
    raw = {
        "id": "1",
        "name": "Company",
        "area": {"name": "Москва"},
        "industries": [{"name": "IT"}],
        "description": "desc",
        "logo_urls": {"90": "url"},
        "vacancies_url": "vacancies",
        "alternate_url": "alt"
    }
    company = Company.from_json(raw)
    assert company.employer_id == 1
    assert company.region == "Москва"
    assert company.industries == ["IT"]


def test_company_to_dict():
    company = Company(1, "Test")
    result = company.to_dict()
    assert result['employer_id'] == 1
    assert result['name'] == "Test"
