"""
Нагрузочные тесты для Spring Boot приложения с использованием Locust.

Тестирует производительность эндпоинта /endpoint при различных нагрузках.
"""
import random
import string
from locust import HttpUser, task, between, events
import yaml
from pathlib import Path


def load_config() -> dict:
    """Загружает конфигурацию из local.yaml."""
    import os
    # Путь относительно locustfile.py: tests/performance/locustfile.py -> spring-boot-tests/config/...
    config_path = Path(__file__).parent.parent.parent / "config" / "environments" / "local.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    # Переопределение URL для Docker окружения
    if os.getenv("APP_URL"):
        config["app"]["base_url"] = os.getenv("APP_URL")
    
    return config


def generate_token(length: int = 32) -> str:
    """Генерирует токен заданной длины из символов 0-9A-F."""
    characters = string.digits + "ABCDEF"
    return "".join(random.choice(characters) for _ in range(length))


class SpringBootUser(HttpUser):
    """
    Пользователь для нагрузочного тестирования Spring Boot приложения.
    
    Симулирует поведение пользователя:
    - LOGIN для получения доступа
    - Выполнение ACTION
    - LOGOUT для завершения сессии
    """
    wait_time = between(1, 3)  # Ожидание между запросами 1-3 секунды
    
    def on_start(self):
        """Инициализация пользователя при старте."""
        config = load_config()
        self.api_key = config["app"]["api_key"]
        self.token = generate_token(32)
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "X-Api-Key": self.api_key,
        }
        # Выполняем LOGIN при старте
        self.login()
    
    def login(self):
        """Выполняет LOGIN для получения доступа."""
        with self.client.post(
            "/endpoint",
            data={"token": self.token, "action": "LOGIN"},
            headers=self.headers,
            catch_response=True,
            name="LOGIN"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("result") == "OK":
                        response.success()
                    else:
                        response.failure(f"LOGIN failed: {result}")
                except Exception as e:
                    response.failure(f"Invalid response: {e}")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(3)
    def perform_action(self):
        """
        Выполняет ACTION.
        
        Вес задачи: 3 (выполняется чаще, чем LOGIN/LOGOUT).
        """
        with self.client.post(
            "/endpoint",
            data={"token": self.token, "action": "ACTION"},
            headers=self.headers,
            catch_response=True,
            name="ACTION"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("result") == "OK":
                        response.success()
                    else:
                        response.failure(f"ACTION failed: {result}")
                except Exception as e:
                    response.failure(f"Invalid response: {e}")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def logout(self):
        """
        Выполняет LOGOUT.
        
        Вес задачи: 1 (выполняется реже).
        """
        with self.client.post(
            "/endpoint",
            data={"token": self.token, "action": "LOGOUT"},
            headers=self.headers,
            catch_response=True,
            name="LOGOUT"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("result") == "OK":
                        response.success()
                        # После LOGOUT генерируем новый токен и делаем LOGIN
                        self.token = generate_token(32)
                        self.login()
                    else:
                        response.failure(f"LOGOUT failed: {result}")
                except Exception as e:
                    response.failure(f"Invalid response: {e}")
            else:
                response.failure(f"HTTP {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Событие при старте теста."""
    print("=" * 60)
    print("Нагрузочное тестирование Spring Boot приложения")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Событие при остановке теста."""
    print("=" * 60)
    print("Нагрузочное тестирование завершено")
    print("=" * 60)


class SpringBootNegativeUser(HttpUser):
    """
    Пользователь для негативного нагрузочного тестирования.
    
    Симулирует негативные сценарии:
    - Невалидные токены
    - Неправильные действия
    - Запросы без авторизации
    """
    wait_time = between(0.5, 2)  # Более быстрое выполнение для негативных тестов
    
    def on_start(self):
        """Инициализация пользователя при старте."""
        config = load_config()
        self.api_key = config["app"]["api_key"]
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "X-Api-Key": self.api_key,
        }
    
    @task(5)
    def test_invalid_token(self):
        """Тест с невалидным токеном."""
        invalid_token = "INVALID_TOKEN_123456789012345"
        with self.client.post(
            "/endpoint",
            data={"token": invalid_token, "action": "LOGIN"},
            headers=self.headers,
            catch_response=True,
            name="LOGIN_INVALID_TOKEN"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("result") == "ERROR":
                        response.success()
                    else:
                        response.failure(f"Expected ERROR, got: {result}")
                except Exception as e:
                    response.failure(f"Invalid response: {e}")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(3)
    def test_action_without_login(self):
        """Тест ACTION без LOGIN."""
        token = generate_token(32)
        with self.client.post(
            "/endpoint",
            data={"token": token, "action": "ACTION"},
            headers=self.headers,
            catch_response=True,
            name="ACTION_WITHOUT_LOGIN"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("result") == "ERROR":
                        response.success()
                    else:
                        response.failure(f"Expected ERROR, got: {result}")
                except Exception as e:
                    response.failure(f"Invalid response: {e}")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)
    def test_invalid_action(self):
        """Тест с невалидным действием."""
        token = generate_token(32)
        with self.client.post(
            "/endpoint",
            data={"token": token, "action": "INVALID_ACTION"},
            headers=self.headers,
            catch_response=True,
            name="INVALID_ACTION"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("result") == "ERROR":
                        response.success()
                    else:
                        response.failure(f"Expected ERROR, got: {result}")
                except Exception as e:
                    response.failure(f"Invalid response: {e}")
            else:
                response.failure(f"HTTP {response.status_code}")


class SpringBootSpikeUser(HttpUser):
    """
    Пользователь для тестирования скачков нагрузки.
    
    Симулирует резкие изменения нагрузки на систему.
    """
    wait_time = between(0.1, 0.5)  # Очень быстрое выполнение
    
    def on_start(self):
        """Инициализация пользователя при старте."""
        config = load_config()
        self.api_key = config["app"]["api_key"]
        self.token = generate_token(32)
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "X-Api-Key": self.api_key,
        }
        self.login()
    
    def login(self):
        """Выполняет LOGIN."""
        with self.client.post(
            "/endpoint",
            data={"token": self.token, "action": "LOGIN"},
            headers=self.headers,
            catch_response=True,
            name="LOGIN_SPIKE"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("result") == "OK":
                        response.success()
                except Exception:
                    pass
    
    @task(10)
    def perform_action_spike(self):
        """Выполняет ACTION с высокой частотой."""
        with self.client.post(
            "/endpoint",
            data={"token": self.token, "action": "ACTION"},
            headers=self.headers,
            catch_response=True,
            name="ACTION_SPIKE"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("result") == "OK":
                        response.success()
                except Exception:
                    pass


class SpringBootStressUser(HttpUser):
    """
    Пользователь для стресс-тестирования.
    
    Симулирует максимальную нагрузку на систему.
    """
    wait_time = between(0.05, 0.2)  # Минимальные задержки
    
    def on_start(self):
        """Инициализация пользователя при старте."""
        config = load_config()
        self.api_key = config["app"]["api_key"]
        self.token = generate_token(32)
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "X-Api-Key": self.api_key,
        }
        # Не делаем LOGIN при старте для стресс-теста
    
    @task(3)
    def stress_login(self):
        """Стресс-тест LOGIN."""
        token = generate_token(32)
        with self.client.post(
            "/endpoint",
            data={"token": token, "action": "LOGIN"},
            headers=self.headers,
            catch_response=True,
            name="STRESS_LOGIN"
        ) as response:
            if response.status_code == 200:
                response.success()
    
    @task(7)
    def stress_action(self):
        """Стресс-тест ACTION."""
        token = generate_token(32)
        with self.client.post(
            "/endpoint",
            data={"token": token, "action": "ACTION"},
            headers=self.headers,
            catch_response=True,
            name="STRESS_ACTION"
        ) as response:
            if response.status_code == 200:
                response.success()
