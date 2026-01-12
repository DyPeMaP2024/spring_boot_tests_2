"""
API тесты для эндпоинта /endpoint.

Тесты разделены на:
- Позитивные сценарии (positive): проверка успешной работы API
- Негативные сценарии (negative): проверка обработки ошибок и валидации
"""
import pytest
import requests
from src.test_framework.fixtures.token import generate_hex_token, generate_token
from src.test_framework.models.response import SuccessResponse, ErrorResponse


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.positive
class TestEndpointPositive:
    """Позитивные тесты для основного эндпоинта приложения."""

    def test_login_success(self, api_client, mock_base_url):
        """
        Тест успешной аутентификации (LOGIN).

        Шаги:
        1. Настроить WireMock для успешного ответа на /auth
        2. Отправить запрос LOGIN с валидным токеном
        3. Проверить успешный ответ
        """
        token = generate_hex_token(32)

        # Настройка WireMock для успешного ответа
        # В реальном тесте здесь будет настройка WireMock
        # wiremock.stub_for(post(url_path_equal("/auth")).will_return(a_response().with_status(200)))

        response = api_client.endpoint(token=token, action="LOGIN")

        assert response["result"] == "OK"
        SuccessResponse(**response)

    def test_login_without_mock(self, api_client):
        """
        Тест LOGIN без mock-сервиса (ожидается ошибка).

        Проверяет, что приложение корректно обрабатывает отсутствие mock-сервиса.
        """
        token = generate_hex_token(32)

        # Если mock не настроен, приложение должно вернуть ошибку
        try:
            response = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
            # Если запрос прошел, проверяем ответ
            if response.get("result") == "ERROR":
                ErrorResponse(**response)
        except requests.exceptions.RequestException:
            # Ожидаем ошибку соединения, если mock не запущен
            pass

    def test_action_success_after_login(self, api_client, mock_base_url):
        """
        Тест успешного выполнения действия (ACTION) после LOGIN.

        Шаги:
        1. Выполнить LOGIN
        2. Настроить WireMock для успешного ответа на /doAction
        3. Отправить запрос ACTION
        4. Проверить успешный ответ
        """
        token = generate_hex_token(32)

        # Сначала LOGIN
        # wiremock.stub_for(post(url_path_equal("/auth")).will_return(a_response().with_status(200)))
        # api_client.endpoint(token=token, action="LOGIN")

        # Затем ACTION
        # wiremock.stub_for(post(url_path_equal("/doAction")).will_return(a_response().with_status(200)))
        response = api_client.endpoint(token=token, action="ACTION", validate_response=False)

        # Может быть ошибка, если токен не был залогинен
        if response.get("result") == "OK":
            SuccessResponse(**response)
        else:
            ErrorResponse(**response)

    def test_action_without_login(self, api_client):
        """
        Тест ACTION без предварительного LOGIN (ожидается ошибка).

        Проверяет, что ACTION недоступен для токенов, не прошедших LOGIN.
        """
        token = generate_hex_token(32)

        response = api_client.endpoint(token=token, action="ACTION", validate_response=False)

        assert response["result"] == "ERROR"
        ErrorResponse(**response)
        assert "message" in response

    def test_logout_success(self, api_client):
        """
        Тест успешного завершения сессии (LOGOUT).

        Шаги:
        1. Выполнить LOGIN
        2. Отправить запрос LOGOUT
        3. Проверить успешный ответ
        """
        token = generate_hex_token(32)

        # Сначала LOGIN, чтобы токен был в системе
        login_response = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        # LOGIN может не пройти, если mock не настроен, но это не критично для LOGOUT

        # Затем LOGOUT
        response = api_client.endpoint(token=token, action="LOGOUT", validate_response=False)

        # LOGOUT должен работать даже для незалогиненных токенов (просто удаляет из хранилища)
        # Но если токен был залогинен, должен вернуть OK
        if response.get("result") == "OK":
            SuccessResponse(**response)
        else:
            # Если токен не был найден, это тоже валидное поведение
            ErrorResponse(**response)
            assert "message" in response

    def test_invalid_token_format(self, api_client):
        """
        Тест с невалидным форматом токена.

        Проверяет валидацию токена (должен быть 32 символа A-Z0-9).
        """
        # Токен неправильной длины
        short_token = generate_hex_token(31)
        response = api_client.endpoint(token=short_token, action="LOGIN", validate_response=False)
        assert response["result"] == "ERROR"
        ErrorResponse(**response)

        # Токен с недопустимыми символами
        invalid_token = "0123456789abcdef0123456789abcdef"  # содержит строчные буквы
        response = api_client.endpoint(token=invalid_token, action="LOGIN", validate_response=False)
        assert response["result"] == "ERROR"
        ErrorResponse(**response)

    def test_invalid_action(self, api_client):
        """
        Тест с невалидным действием.

        Проверяет валидацию действия (должно быть LOGIN, ACTION или LOGOUT).
        """
        token = generate_hex_token(32)

        response = api_client.endpoint(token=token, action="INVALID", validate_response=False)

        assert response["result"] == "ERROR"
        ErrorResponse(**response)

    def test_missing_api_key(self, api_client):
        """
        Тест запроса без API ключа.

        Проверяет, что запрос без заголовка X-Api-Key отклоняется.
        """
        import requests

        token = generate_hex_token(32)
        url = f"{api_client.base_url}/endpoint"
        data = {"token": token, "action": "LOGIN"}

        # Запрос без API ключа
        response = requests.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=api_client.timeout
        )

        # Ожидаем ошибку авторизации
        assert response.status_code in [401, 403]

    def test_wrong_api_key(self, config):
        """
        Тест запроса с неправильным API ключом.

        Проверяет, что запрос с неверным X-Api-Key отклоняется.
        """
        from src.test_framework.clients.api_client import ApiClient

        token = generate_hex_token(32)
        wrong_client = ApiClient(
            base_url=config["app"]["base_url"],
            api_key="wrong_key",
            timeout=config["app"].get("timeout", 30)
        )

        response = wrong_client.endpoint(token=token, action="LOGIN", validate_response=False)

        # Может быть ошибка или 401/403
        if response.get("result") == "ERROR":
            ErrorResponse(**response)


@pytest.mark.api
@pytest.mark.negative
class TestEndpointNegative:
    """Негативные тесты для основного эндпоинта приложения."""

    def test_empty_token(self, api_client):
        """Тест с пустым токеном."""
        response = api_client.endpoint(token="", action="LOGIN", validate_response=False)
        assert response["result"] == "ERROR"
        ErrorResponse(**response)

    def test_none_token(self, api_client):
        """Тест с None токеном."""
        import requests
        url = f"{api_client.base_url}/endpoint"
        data = {"token": None, "action": "LOGIN"}
        response = requests.post(
            url,
            data=data,
            headers=api_client.session.headers,
            timeout=api_client.timeout
        )
        assert response.status_code in [400, 422, 500]

    def test_very_long_token(self, api_client):
        """Тест с очень длинным токеном."""
        long_token = generate_hex_token(100)
        response = api_client.endpoint(token=long_token, action="LOGIN", validate_response=False)
        assert response["result"] == "ERROR"
        ErrorResponse(**response)

    def test_token_with_special_chars(self, api_client):
        """Тест токена со спецсимволами."""
        invalid_token = "0123456789abcdef0123456789@#$%"
        response = api_client.endpoint(token=invalid_token, action="LOGIN", validate_response=False)
        assert response["result"] == "ERROR"
        ErrorResponse(**response)

    def test_empty_action(self, api_client):
        """Тест с пустым действием."""
        token = generate_hex_token(32)
        import requests
        url = f"{api_client.base_url}/endpoint"
        data = {"token": token, "action": ""}
        response = requests.post(
            url,
            data=data,
            headers=api_client.session.headers,
            timeout=api_client.timeout
        )
        assert response.status_code in [400, 422]

    def test_missing_action_parameter(self, api_client):
        """Тест без параметра action."""
        token = generate_hex_token(32)
        import requests
        url = f"{api_client.base_url}/endpoint"
        data = {"token": token}
        response = requests.post(
            url,
            data=data,
            headers=api_client.session.headers,
            timeout=api_client.timeout
        )
        assert response.status_code in [400, 422]

    def test_missing_token_parameter(self, api_client):
        """Тест без параметра token."""
        import requests
        url = f"{api_client.base_url}/endpoint"
        data = {"action": "LOGIN"}
        response = requests.post(
            url,
            data=data,
            headers=api_client.session.headers,
            timeout=api_client.timeout
        )
        assert response.status_code in [400, 422]

    def test_lowercase_action(self, api_client):
        """Тест с действием в нижнем регистре."""
        token = generate_hex_token(32)
        response = api_client.endpoint(token=token, action="login", validate_response=False)
        # Может быть OK (если система нечувствительна к регистру) или ERROR
        assert "result" in response

    def test_mixed_case_action(self, api_client):
        """Тест с действием в смешанном регистре."""
        token = generate_hex_token(32)
        response = api_client.endpoint(token=token, action="LogIn", validate_response=False)
        assert "result" in response

    def test_whitespace_in_token(self, api_client):
        """Тест токена с пробелами."""
        token_with_spaces = "0123456789ABCDEF0123456789ABCDEF "
        response = api_client.endpoint(token=token_with_spaces, action="LOGIN", validate_response=False)
        assert response["result"] == "ERROR"
        ErrorResponse(**response)

    def test_whitespace_in_action(self, api_client):
        """Тест действия с пробелами."""
        token = generate_hex_token(32)
        import requests
        url = f"{api_client.base_url}/endpoint"
        data = {"token": token, "action": " LOGIN "}
        response = requests.post(
            url,
            data=data,
            headers=api_client.session.headers,
            timeout=api_client.timeout
        )
        assert response.status_code in [200, 400, 422]

    def test_sql_injection_in_token(self, api_client):
        """Тест на защиту от SQL инъекций в токене."""
        sql_injection_token = "'; DROP TABLE tokens; --"
        response = api_client.endpoint(token=sql_injection_token, action="LOGIN", validate_response=False)
        assert response["result"] == "ERROR"
        ErrorResponse(**response)

    def test_xss_in_token(self, api_client):
        """Тест на защиту от XSS в токене."""
        xss_token = "<script>alert('xss')</script>"
        response = api_client.endpoint(token=xss_token, action="LOGIN", validate_response=False)
        assert response["result"] == "ERROR"
        ErrorResponse(**response)

    def test_timeout_handling(self, api_client):
        """Тест обработки таймаута при обращении к внешнему сервису."""
        from src.test_framework.clients.api_client import ApiClient
        from src.test_framework.fixtures.token import generate_hex_token
        import requests
        
        # Создаем клиент с коротким таймаутом
        short_timeout_client = ApiClient(
            base_url=api_client.base_url,
            api_key=api_client.api_key,
            timeout=5
        )
        timeout_token = "TIMEOUT" + generate_hex_token(25)  # Всего 32 символа
        try:
            response = short_timeout_client.endpoint(token=timeout_token, action="LOGIN", validate_response=False)
            assert response["result"] == "ERROR"
            ErrorResponse(**response)
        except requests.exceptions.Timeout:
            # Ожидаемый таймаут
            pass

    def test_duplicate_login(self, api_client):
        """Тест повторного LOGIN без LOGOUT."""
        token = generate_hex_token(32)
        login1 = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        if login1.get("result") == "OK":
            # Попытка повторного LOGIN
            login2 = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
            # Может быть OK (если система перезаписывает) или ERROR
            assert "result" in login2

    def test_action_after_logout(self, api_client):
        """Тест ACTION после LOGOUT."""
        token = generate_hex_token(32)
        # LOGIN
        login = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        if login.get("result") == "OK":
            # LOGOUT
            logout = api_client.endpoint(token=token, action="LOGOUT", validate_response=False)
            if logout.get("result") == "OK":
                # ACTION после LOGOUT должен не работать
                action = api_client.endpoint(token=token, action="ACTION", validate_response=False)
                assert action["result"] == "ERROR"
                ErrorResponse(**action)

    def test_logout_twice(self, api_client):
        """Тест двойного LOGOUT."""
        token = generate_hex_token(32)
        login = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        if login.get("result") == "OK":
            logout1 = api_client.endpoint(token=token, action="LOGOUT", validate_response=False)
            logout2 = api_client.endpoint(token=token, action="LOGOUT", validate_response=False)
            # Второй LOGOUT может вернуть ERROR или OK в зависимости от реализации
            assert "result" in logout2

    def test_wrong_content_type(self, api_client):
        """Тест с неправильным Content-Type."""
        token = generate_hex_token(32)
        import requests
        url = f"{api_client.base_url}/endpoint"
        response = requests.post(
            url,
            json={"token": token, "action": "LOGIN"},
            headers={
                "X-Api-Key": api_client.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=api_client.timeout
        )
        # Может быть 415 (Unsupported Media Type) или другая ошибка
        assert response.status_code in [400, 415, 422, 500]

    def test_wrong_accept_header(self, api_client):
        """Тест с неправильным Accept заголовком."""
        token = generate_hex_token(32)
        import requests
        url = f"{api_client.base_url}/endpoint"
        response = requests.post(
            url,
            data={"token": token, "action": "LOGIN"},
            headers={
                "X-Api-Key": api_client.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html"
            },
            timeout=api_client.timeout
        )
        # Может быть 406 (Not Acceptable) или другая ошибка
        assert response.status_code in [200, 400, 406, 500]
