# Spring Boot Tests Project

Проект автоматизированного тестирования Spring Boot приложения с полным покрытием функциональности.

## Структура проекта

```
.
├── app/                      # Тестируемое Spring Boot приложение
│   ├── internal-0.0.1-SNAPSHOT.jar
│   └── README.md
└── spring-boot-tests/        # Тестовый фреймворк
    ├── src/                  # Код тестовых утилит
    ├── tests/                # Тесты
    ├── config/               # Конфигурации
    ├── docker/               # Docker конфигурация
    └── reports/              # Отчеты о тестировании
```

## Быстрый старт

### Запуск через Docker (рекомендуется)

```bash
cd spring-boot-tests/docker

# Запустить WireMock mock сервер
docker-compose -f docker-compose.test.yml up -d wiremock

# Запустить Spring Boot приложение
docker-compose -f docker-compose.test.yml up -d app

# Запустить все тесты (включая нагрузочные)
docker-compose -f docker-compose.test.yml run --rm tests-all
```

### Локальный запуск

1. Запустить Spring Boot приложение:
```bash
cd app
java -jar -Dsecret=qazWSXedc -Dmock=http://localhost:8888/ internal-0.0.1-SNAPSHOT.jar
```

2. Запустить WireMock:
```bash
docker run -d -p 8888:8080 \
  -v $(pwd)/spring-boot-tests/config/wiremock/mappings:/home/wiremock/mappings \
  wiremock/wiremock:latest
```

3. Запустить тесты:
```bash
cd spring-boot-tests
pdm install
pdm run pytest
```

## Покрытие тестами

### Статистика

- **API тесты**: 30 тестов (позитивные + негативные)
- **Интеграционные тесты**: 18 тестов
- **Контрактные тесты**: 9 тестов
- **Нагрузочные тесты**: 4 пользовательских класса (Locust)

**Всего: 57 тестов**

### Типы тестов

- ✅ Позитивные сценарии - проверка успешной работы
- ✅ Негативные сценарии - проверка обработки ошибок
- ✅ Интеграционные тесты - полные сценарии работы
- ✅ Контрактные тесты - валидация API контракта
- ✅ Нагрузочные тесты - производительность и стабильность

## Документация

Подробная информация о тестах доступна в:
- `spring-boot-tests/README.md` - общая информация
- `spring-boot-tests/TEST_COVERAGE.md` - детальное описание покрытия
- `spring-boot-tests/reports/coverage.md` - отчет о покрытии

## Отчеты

После запуска тестов отчеты сохраняются в `spring-boot-tests/reports/`:
- HTML отчеты
- JUnit XML отчеты
- Отчеты Locust (нагрузочные тесты)
- Сводный отчет о покрытии

## Технологии

- Python 3.11+
- pytest - фреймворк тестирования
- Locust - нагрузочное тестирование
- WireMock - мокирование внешних сервисов
- Docker - контейнеризация
- Pydantic - валидация данных

## Лицензия

См. `spring-boot-tests/LICENSE`
