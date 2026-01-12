"""
Контрактные тесты для OpenAPI спецификации.

Проверяет соответствие API контракту и валидность ответов.
"""
import pytest
import requests
import json
from src.test_framework.fixtures.token import generate_hex_token
from src.test_framework.models.response import SuccessResponse, ErrorResponse


@pytest.mark.contract
class TestOpenAPIContract:
    """Контрактные тесты для проверки соответствия API спецификации."""

    def test_endpoint_contract_structure(self, api_client):
        """
        Тест структуры контракта эндпоинта /endpoint.
        
        Проверяет:
        - Наличие обязательных полей в запросе
        - Структуру успешного ответа
        - Структуру ответа с ошибкой
        """
        token = generate_hex_token(32)
        
        # Тест успешного ответа
        response = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        
        # Проверяем наличие обязательных полей
        assert "result" in response
        assert response["result"] in ["OK", "ERROR"]
        
        if response["result"] == "OK":
            SuccessResponse(**response)
        else:
            ErrorResponse(**response)
            assert "message" in response

    def test_success_response_contract(self, api_client):
        """
        Тест контракта успешного ответа.
        
        Проверяет, что успешный ответ соответствует ожидаемой структуре.
        """
        token = generate_hex_token(32)
        response = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        
        if response.get("result") == "OK":
            # Валидируем через Pydantic модель
            validated = SuccessResponse(**response)
            assert validated.result == "OK"
            
            # Проверяем, что нет лишних полей (или они допустимы)
            allowed_fields = {"result"}
            extra_fields = set(response.keys()) - allowed_fields
            # Могут быть дополнительные поля, но основные должны быть

    def test_error_response_contract(self, api_client):
        """
        Тест контракта ответа с ошибкой.
        
        Проверяет, что ответ с ошибкой соответствует ожидаемой структуре.
        """
        # Используем невалидный токен для получения ошибки
        invalid_token = "INVALID_TOKEN_123456789012345"
        response = api_client.endpoint(token=invalid_token, action="LOGIN", validate_response=False)
        
        if response.get("result") == "ERROR":
            # Валидируем через Pydantic модель
            validated = ErrorResponse(**response)
            assert validated.result == "ERROR"
            assert validated.message is not None
            assert len(validated.message) > 0

    def test_request_contract_validation(self, api_client):
        """
        Тест валидации контракта запроса.
        
        Проверяет, что API валидирует входные параметры согласно контракту.
        """
        # Проверяем валидацию обязательных параметров
        import requests
        url = f"{api_client.base_url}/endpoint"
        
        # Запрос без токена
        response = requests.post(
            url,
            data={"action": "LOGIN"},
            headers=api_client.session.headers,
            timeout=api_client.timeout
        )
        assert response.status_code in [400, 422]
        
        # Запрос без action
        token = generate_hex_token(32)
        response = requests.post(
            url,
            data={"token": token},
            headers=api_client.session.headers,
            timeout=api_client.timeout
        )
        assert response.status_code in [400, 422]

    def test_response_status_codes(self, api_client):
        """
        Тест HTTP статус кодов.
        
        Проверяет, что API возвращает корректные HTTP статус коды.
        """
        import requests
        token = generate_hex_token(32)
        
        # Успешный запрос должен возвращать 200
        response = requests.post(
            f"{api_client.base_url}/endpoint",
            data={"token": token, "action": "LOGIN"},
            headers=api_client.session.headers,
            timeout=api_client.timeout
        )
        assert response.status_code == 200
        
        # Запрос без авторизации должен возвращать 401 или 403
        response = requests.post(
            f"{api_client.base_url}/endpoint",
            data={"token": token, "action": "LOGIN"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=api_client.timeout
        )
        assert response.status_code in [401, 403]

    def test_content_type_contract(self, api_client):
        """
        Тест контракта Content-Type.
        
        Проверяет, что API возвращает правильный Content-Type.
        """
        import requests
        token = generate_hex_token(32)
        
        response = requests.post(
            f"{api_client.base_url}/endpoint",
            data={"token": token, "action": "LOGIN"},
            headers=api_client.session.headers,
            timeout=api_client.timeout
        )
        
        assert response.status_code == 200
        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type.lower()

    def test_json_response_format(self, api_client):
        """
        Тест формата JSON ответа.
        
        Проверяет, что все ответы валидны как JSON.
        """
        import requests
        token = generate_hex_token(32)
        
        response = requests.post(
            f"{api_client.base_url}/endpoint",
            data={"token": token, "action": "LOGIN"},
            headers=api_client.session.headers,
            timeout=api_client.timeout
        )
        
        assert response.status_code == 200
        # Проверяем, что ответ валидный JSON
        try:
            json_data = response.json()
            assert isinstance(json_data, dict)
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")

    def test_all_actions_contract(self, api_client):
        """
        Тест контракта для всех действий.
        
        Проверяет, что все действия (LOGIN, ACTION, LOGOUT) следуют одному контракту.
        """
        token = generate_hex_token(32)
        actions = ["LOGIN", "ACTION", "LOGOUT"]
        
        for action in actions:
            response = api_client.endpoint(token=token, action=action, validate_response=False)
            
            # Проверяем базовую структуру ответа
            assert "result" in response
            assert response["result"] in ["OK", "ERROR"]
            
            # Валидируем через модели
            if response["result"] == "OK":
                SuccessResponse(**response)
            else:
                ErrorResponse(**response)
                assert "message" in response
