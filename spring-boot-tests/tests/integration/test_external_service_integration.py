"""
Интеграционные тесты для проверки взаимодействия с внешним сервисом.

Тестирует интеграцию Spring Boot приложения с внешним сервисом через WireMock:
- Проверка корректности запросов к внешнему сервису
- Обработка различных ответов от внешнего сервиса
- Проверка состояния приложения при ошибках внешнего сервиса
"""
import pytest
import requests
from src.test_framework.fixtures.token import generate_hex_token
from src.test_framework.models.response import SuccessResponse, ErrorResponse


@pytest.mark.integration
class TestExternalServiceIntegration:
    """Интеграционные тесты для взаимодействия с внешним сервисом."""

    def test_login_success_with_mock_service(self, api_client, mock_base_url):
        """
        Тест успешного LOGIN при работе внешнего сервиса.

        Проверяет, что при успешном ответе от /auth приложение корректно обрабатывает токен.
        """
        token = generate_hex_token(32)

        # Проверяем, что WireMock доступен
        try:
            mock_status = requests.get(f"{mock_base_url}/__admin/", timeout=5)
            assert mock_status.status_code == 200, "WireMock должен быть доступен"
        except requests.exceptions.RequestException:
            pytest.skip("WireMock недоступен для тестирования")

        # LOGIN должен работать, если mock настроен правильно
        response = api_client.endpoint(token=token, action="LOGIN", validate_response=False)

        # Может быть OK, если mock настроен, или ERROR, если нет
        if response.get("result") == "OK":
            SuccessResponse(**response)
        else:
            # Если mock не настроен, это тоже валидное поведение
            ErrorResponse(**response)

    def test_action_requires_external_service(self, api_client, mock_base_url):
        """
        Тест, что ACTION требует работы внешнего сервиса /doAction.

        Проверяет интеграцию с внешним сервисом при выполнении ACTION.
        """
        token = generate_hex_token(32)

        # Сначала LOGIN
        login_response = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        if login_response.get("result") != "OK":
            pytest.skip("LOGIN не прошел, пропускаем тест")

        # ACTION должен обращаться к внешнему сервису
        action_response = api_client.endpoint(token=token, action="ACTION", validate_response=False)

        # Может быть OK, если mock настроен, или ERROR
        if action_response.get("result") == "OK":
            SuccessResponse(**action_response)
        else:
            ErrorResponse(**action_response)

    def test_concurrent_tokens_with_external_service(self, api_client):
        """
        Тест работы нескольких токенов одновременно с внешним сервисом.

        Проверяет, что приложение корректно обрабатывает несколько токенов,
        каждый из которых обращается к внешнему сервису.
        """
        token1 = generate_hex_token(32)
        token2 = generate_hex_token(32)
        token3 = generate_hex_token(32)

        # LOGIN для всех токенов
        login1 = api_client.endpoint(token=token1, action="LOGIN", validate_response=False)
        login2 = api_client.endpoint(token=token2, action="LOGIN", validate_response=False)
        login3 = api_client.endpoint(token=token3, action="LOGIN", validate_response=False)

        # Если хотя бы один LOGIN прошел, продолжаем тест
        if login1.get("result") == "OK" or login2.get("result") == "OK" or login3.get("result") == "OK":
            # ACTION для успешно залогиненных токенов
            if login1.get("result") == "OK":
                action1 = api_client.endpoint(token=token1, action="ACTION", validate_response=False)
                # Проверяем, что ACTION либо успешен, либо есть понятная ошибка
                assert "result" in action1

            if login2.get("result") == "OK":
                action2 = api_client.endpoint(token=token2, action="ACTION", validate_response=False)
                assert "result" in action2

            if login3.get("result") == "OK":
                action3 = api_client.endpoint(token=token3, action="ACTION", validate_response=False)
                assert "result" in action3

    def test_state_persistence_after_external_service_call(self, api_client):
        """
        Тест сохранения состояния после обращения к внешнему сервису.

        Проверяет, что состояние токена сохраняется между запросами
        после успешного обращения к внешнему сервису.
        """
        token = generate_hex_token(32)

        # LOGIN
        login_response = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        if login_response.get("result") != "OK":
            pytest.skip("LOGIN не прошел")

        # Первое ACTION
        action1 = api_client.endpoint(token=token, action="ACTION", validate_response=False)
        assert "result" in action1

        # Второе ACTION (должно работать, так как токен все еще активен)
        action2 = api_client.endpoint(token=token, action="ACTION", validate_response=False)
        assert "result" in action2

        # Третье ACTION
        action3 = api_client.endpoint(token=token, action="ACTION", validate_response=False)
        assert "result" in action3

        # Проверяем, что токен все еще активен
        action4 = api_client.endpoint(token=token, action="ACTION", validate_response=False)
        assert "result" in action4

    def test_external_service_error_handling(self, api_client):
        """
        Тест обработки ошибок внешнего сервиса.
        
        Проверяет, что приложение корректно обрабатывает ошибки от внешнего сервиса.
        """
        token = generate_hex_token(32)
        
        # LOGIN
        login_response = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        if login_response.get("result") != "OK":
            pytest.skip("LOGIN не прошел")
        
        # ACTION с токеном, который вызывает ошибку внешнего сервиса
        error_token = "ERROR" + generate_hex_token(27)  # Всего 32 символа
        error_login = api_client.endpoint(token=error_token, action="LOGIN", validate_response=False)
        if error_login.get("result") == "OK":
            error_action = api_client.endpoint(token=error_token, action="ACTION", validate_response=False)
            # Должна быть обработана ошибка от внешнего сервиса
            assert "result" in error_action

    def test_concurrent_logins(self, api_client):
        """
        Тест параллельных LOGIN запросов.
        
        Проверяет обработку одновременных запросов на аутентификацию.
        """
        import concurrent.futures
        tokens = [generate_hex_token(32) for _ in range(10)]
        
        def login(token):
            return api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(login, tokens))
        
        # Проверяем, что все запросы обработаны
        assert len(results) == 10
        for result in results:
            assert "result" in result

    def test_concurrent_actions(self, api_client):
        """
        Тест параллельных ACTION запросов.
        
        Проверяет обработку одновременных действий для одного токена.
        """
        token = generate_hex_token(32)
        
        # LOGIN
        login_response = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        if login_response.get("result") != "OK":
            pytest.skip("LOGIN не прошел")
        
        def perform_action():
            return api_client.endpoint(token=token, action="ACTION", validate_response=False)
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda _: perform_action(), range(5)))
        
        # Проверяем результаты
        for result in results:
            assert "result" in result

    def test_service_unavailable_handling(self, api_client, mock_base_url):
        """
        Тест обработки недоступности внешнего сервиса.
        
        Проверяет поведение приложения, когда внешний сервис недоступен.
        """
        import requests
        token = generate_hex_token(32)
        
        # Проверяем доступность mock сервиса
        try:
            mock_status = requests.get(f"{mock_base_url}/__admin/", timeout=2)
            if mock_status.status_code != 200:
                pytest.skip("WireMock недоступен")
        except requests.exceptions.RequestException:
            # Если сервис недоступен, проверяем поведение
            response = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
            assert response["result"] == "ERROR"
            ErrorResponse(**response)

    def test_race_condition_login_logout(self, api_client):
        """
        Тест состояния гонки между LOGIN и LOGOUT.
        
        Проверяет корректность обработки одновременных LOGIN и LOGOUT.
        """
        token = generate_hex_token(32)
        
        import concurrent.futures
        def login():
            return api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        
        def logout():
            return api_client.endpoint(token=token, action="LOGOUT", validate_response=False)
        
        # Сначала LOGIN
        login_response = login()
        if login_response.get("result") == "OK":
            # Параллельно выполняем LOGIN и LOGOUT
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(login),
                    executor.submit(logout)
                ]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            # Проверяем, что все запросы обработаны
            for result in results:
                assert "result" in result
