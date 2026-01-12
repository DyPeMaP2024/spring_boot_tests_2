# Spring Boot Tests

Тестовый фреймворк для тестирования Spring Boot приложения на Python.

## Структура проекта

```
spring-boot-tests/
├── src/                          # Код тестовых утилит
│   └── test_framework/
│       ├── clients/              # Клиенты для Spring Boot API
│       ├── models/               # Pydantic модели
│       ├── fixtures/             # Фикстуры и утилиты
│       └── assertions/           # Кастомные проверки
├── tests/
│   ├── api/                      # API тесты
│   ├── integration/              # Интеграционные тесты
│   ├── contract/                 # Контрактные тесты
│   └── performance/              # Нагрузочные тесты
├── config/                          # Конфигурации
└── docker/                       # Docker файлы
```

## Установка

```bash
# Установка PDM (если еще не установлен)
pip install pdm

# Установка зависимостей
pdm install

# Установка тестовых зависимостей
pdm install -G test
```

## Запуск тестов

```bash
# Все тесты
pdm run pytest

# Только API тесты
pdm run pytest tests/api/

# Только smoke тесты
pdm run pytest -m smoke

# С отчетом Allure
pdm run pytest --alluredir=./allure-results
pdm run allure serve ./allure-results
```

## Конфигурация

Настройки окружений находятся в `config/environments/`:
- `local.yaml` - локальное окружение

## Отчеты

После запуска тестов отчеты сохраняются в директории `reports/`:
- `junit.xml` - JUnit XML отчет для CI/CD
- `report.html` - HTML отчет с детальной информацией
- `coverage.md` - Сводный отчет о покрытии тестами (генерируется скриптом)

### Генерация coverage.md

```bash
python3 scripts/generate_coverage_report.py
```

## Покрытие тестами

Система полностью покрыта автотестами с разделением на позитивные и негативные сценарии:
- **API тесты** - 56+ тестов (позитивные и негативные)
- **Интеграционные тесты** - 42+ тестов
- **Контрактные тесты** - 16+ тестов
- **Нагрузочные тесты** - 4 пользовательских класса

Подробная информация о покрытии доступна в `TEST_COVERAGE.md` и `reports/coverage.md`.

### Запуск по категориям

```bash
# Позитивные тесты
pdm run pytest -m positive

# Негативные тесты
pdm run pytest -m negative

# По категориям
pdm run pytest -m api          # API тесты
pdm run pytest -m integration  # Интеграционные тесты
pdm run pytest -m contract     # Контрактные тесты
```

## Docker

Для запуска тестов в Docker:

```bash
cd docker
docker-compose -f docker-compose.test.yml up tests
```

## WireMock

WireMock используется для мокинга внешних сервисов. Конфигурации моков находятся в `config/wiremock/mappings/`.
