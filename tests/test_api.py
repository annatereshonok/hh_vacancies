from unittest.mock import patch, MagicMock
from src.main import HeadHunterAPI


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
    # Мокаем ответ от requests.get()
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
        specializations="Разработка"
    )

    # Проверяем результат
    assert isinstance(result, list)
    assert len(result) == 20
    assert result[0]["name"] == "Dev"
    assert mock_requests_get.call_count == 20
