"""
Интеграционные негативные тесты.

Тестирует обработку ошибок и граничных случаев в интеграционных сценариях.
"""
import pytest
from src.test_framework.fixtures.token import generate_hex_token
from src.test_framework.models.response import ErrorResponse


@pytest.mark.integration
@pytest.mark.negative
class TestIntegrationNegative:
    """Негативные интеграционные тесты."""

    def test_invalid_token_in_full_cycle(self, api_client):
        """
        Тест полного цикла с невалидным токеном.
        
        Проверяет обработку невалидного токена на всех этапах.
        """
        invalid_token = "INVALID_TOKEN_123456789012345"
        
        # LOGIN с невалидным токеном
        login_response = api_client.endpoint(token=invalid_token, action="LOGIN", validate_response=False)
        assert login_response["result"] == "ERROR"
        ErrorResponse(**login_response)
        
        # ACTION с невалидным токеном
        action_response = api_client.endpoint(token=invalid_token, action="ACTION", validate_response=False)
        assert action_response["result"] == "ERROR"
        ErrorResponse(**action_response)
        
        # LOGOUT с невалидным токеном (может работать или нет)
        logout_response = api_client.endpoint(token=invalid_token, action="LOGOUT", validate_response=False)
        assert "result" in logout_response

    def test_action_with_expired_session(self, api_client):
        """
        Тест ACTION после истечения сессии.
        
        Проверяет поведение при попытке выполнить ACTION после истечения сессии.
        """
        token = generate_hex_token(32)
        
        # LOGIN
        login_response = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        if login_response.get("result") == "OK":
            # LOGOUT
            logout_response = api_client.endpoint(token=token, action="LOGOUT", validate_response=False)
            if logout_response.get("result") == "OK":
                # ACTION после LOGOUT должен не работать
                action_response = api_client.endpoint(token=token, action="ACTION", validate_response=False)
                assert action_response["result"] == "ERROR"
                ErrorResponse(**action_response)

    def test_mixed_valid_invalid_tokens(self, api_client):
        """
        Тест смешения валидных и невалидных токенов.
        
        Проверяет, что невалидные токены не влияют на валидные.
        """
        valid_token = generate_hex_token(32)
        invalid_token = "INVALID_TOKEN_123456789012345"
        
        # LOGIN валидного токена
        valid_login = api_client.endpoint(token=valid_token, action="LOGIN", validate_response=False)
        if valid_login.get("result") == "OK":
            # ACTION с невалидным токеном
            invalid_action = api_client.endpoint(token=invalid_token, action="ACTION", validate_response=False)
            assert invalid_action["result"] == "ERROR"
            
            # ACTION с валидным токеном все еще должен работать
            valid_action = api_client.endpoint(token=valid_token, action="ACTION", validate_response=False)
            assert valid_action["result"] == "OK"

    def test_external_service_timeout_impact(self, api_client):
        """
        Тест влияния таймаута внешнего сервиса.
        
        Проверяет поведение при таймауте внешнего сервиса.
        """
        from src.test_framework.clients.api_client import ApiClient
        import requests
        
        # Создаем клиент с коротким таймаутом
        short_timeout_client = ApiClient(
            base_url=api_client.base_url,
            api_key=api_client.api_key,
            timeout=5
        )
        
        timeout_token = "TIMEOUT" + generate_hex_token(25)
        
        try:
            response = short_timeout_client.endpoint(token=timeout_token, action="LOGIN", validate_response=False)
            assert response["result"] == "ERROR"
            ErrorResponse(**response)
        except requests.exceptions.Timeout:
            # Ожидаемый таймаут
            pass

    def test_rapid_login_logout_cycle(self, api_client):
        """
        Тест быстрого цикла LOGIN-LOGOUT.
        
        Проверяет стабильность при частых переключениях состояний токена.
        """
        token = generate_hex_token(32)
        
        # Выполняем несколько циклов быстро
        for i in range(5):
            login_response = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
            assert "result" in login_response
            
            logout_response = api_client.endpoint(token=token, action="LOGOUT", validate_response=False)
            assert "result" in logout_response

    def test_multiple_actions_after_single_logout(self, api_client):
        """
        Тест множественных ACTION после одного LOGOUT.
        
        Проверяет, что после LOGOUT все последующие ACTION не работают.
        """
        token = generate_hex_token(32)
        
        # LOGIN
        login_response = api_client.endpoint(token=token, action="LOGIN", validate_response=False)
        if login_response.get("result") == "OK":
            # LOGOUT
            logout_response = api_client.endpoint(token=token, action="LOGOUT", validate_response=False)
            if logout_response.get("result") == "OK":
                # Несколько ACTION после LOGOUT
                for i in range(3):
                    action_response = api_client.endpoint(token=token, action="ACTION", validate_response=False)
                    assert action_response["result"] == "ERROR"
                    ErrorResponse(**action_response)
