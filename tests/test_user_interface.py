import pytest
from unittest.mock import patch, MagicMock
from src.main import user_interface


@patch("builtins.input")
@patch("builtins.print")
@patch("src.main.VacancyStorage")
@patch("src.main.HeadHunterAPI")
def test_user_interface_search_and_exit(mock_api, mock_storage, mock_print, mock_input):
    mock_api_instance = mock_api.return_value
    mock_api_instance.get_vacancies.return_value = [
        {
            "id": "1",
            "name": "Dev",
            "alternate_url": "http://example.com",
            "salary": {},
            "snippet": {},
            "employer": {},
            "area": {},
            "employment": {},
            "experience": {},
        }
    ]
    mock_storage_instance = mock_storage.return_value
    mock_input.side_effect = [
        "1",
        "Python",
        "",
        "",
        "",
        "",
        "",
        "5",
    ]
    user_interface()

    mock_api_instance.get_vacancies.assert_called_once()
    mock_storage_instance.add_vacancies.assert_called_once()
    mock_print.assert_any_call("Завершение программы.")
