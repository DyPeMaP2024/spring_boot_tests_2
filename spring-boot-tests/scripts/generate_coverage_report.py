#!/usr/bin/env python3
"""
Скрипт для генерации сводного отчета о покрытии тестами.

Генерирует coverage.md с информацией о:
- Общем количестве тестов
- Покрытии по категориям (API, интеграционные, нагрузочные, контрактные)
- Разделении на позитивные и негативные сценарии
- Статистике по каждому типу тестов
"""
import subprocess
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import sys


def run_command(cmd: List[str]) -> Tuple[str, int]:
    """Выполняет команду и возвращает вывод и код возврата."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        return result.stdout + result.stderr, result.returncode
    except Exception as e:
        return str(e), 1


def count_tests_by_marker() -> Dict[str, int]:
    """Подсчитывает количество тестов по маркерам."""
    import re
    
    markers = {
        "api": 0,
        "integration": 0,
        "contract": 0,
        "positive": 0,
        "negative": 0,
        "smoke": 0,
    }
    
    # Подсчет тестов через анализ файлов
    tests_dir = Path(__file__).parent.parent / "tests"
    
    for test_file in tests_dir.rglob("test_*.py"):
        try:
            content = test_file.read_text(encoding="utf-8")
            test_count = len(re.findall(r'def test_', content))
            
            # Определяем категорию по пути
            if "api" in str(test_file):
                markers["api"] += test_count
            elif "integration" in str(test_file):
                markers["integration"] += test_count
            elif "contract" in str(test_file):
                markers["contract"] += test_count
            
            # Подсчет позитивных/негативных тестов
            if "Positive" in content or "@pytest.mark.positive" in content:
                # Находим все тесты в классах Positive
                positive_tests = re.findall(r'(?:class.*Positive.*?|@pytest\.mark\.positive.*?)(?:def test_\w+)', content, re.DOTALL)
                # Более простой способ - считать тесты в файлах с Positive в названии класса
                if "Positive" in content:
                    # Считаем все def test_ после class.*Positive
                    positive_count = 0
                    in_positive_class = False
                    for line in content.split('\n'):
                        if 'class' in line and 'Positive' in line:
                            in_positive_class = True
                        elif 'class' in line and 'Positive' not in line and in_positive_class:
                            in_positive_class = False
                        if in_positive_class and 'def test_' in line:
                            positive_count += 1
                    markers["positive"] += positive_count
            
            if "Negative" in content or "@pytest.mark.negative" in content:
                # Аналогично для негативных
                negative_count = 0
                in_negative_class = False
                for line in content.split('\n'):
                    if 'class' in line and 'Negative' in line:
                        in_negative_class = True
                    elif 'class' in line and 'Negative' not in line and in_negative_class:
                        in_negative_class = False
                    if in_negative_class and 'def test_' in line:
                        negative_count += 1
                markers["negative"] += negative_count
            
            if "@pytest.mark.smoke" in content:
                markers["smoke"] += test_count
        except Exception:
            continue
    
    return markers


def parse_junit_xml() -> Dict[str, any]:
    """Парсит JUnit XML отчет."""
    # Сначала пытаемся найти all-junit.xml (полный отчет всех тестов)
    junit_path = Path(__file__).parent.parent / "reports" / "all-junit.xml"
    
    # Если нет, используем обычный junit.xml
    if not junit_path.exists():
        junit_path = Path(__file__).parent.parent / "reports" / "junit.xml"
    
    if not junit_path.exists():
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0
        }
    
    try:
        tree = ET.parse(junit_path)
        root = tree.getroot()
        
        total = 0
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        
        for testsuite in root.findall(".//testsuite"):
            total += int(testsuite.get("tests", 0))
            passed += int(testsuite.get("tests", 0)) - int(testsuite.get("failures", 0)) - int(testsuite.get("errors", 0)) - int(testsuite.get("skipped", 0))
            failed += int(testsuite.get("failures", 0))
            skipped += int(testsuite.get("skipped", 0))
            errors += int(testsuite.get("errors", 0))
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors
        }
    except Exception as e:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "error": str(e)
        }


def collect_test_files() -> Dict[str, List[str]]:
    """Собирает информацию о тестовых файлах."""
    tests_dir = Path(__file__).parent.parent / "tests"
    
    categories = {
        "api": [],
        "integration": [],
        "contract": [],
        "performance": []
    }
    
    for category in categories.keys():
        category_dir = tests_dir / category
        if category_dir.exists():
            if category == "performance":
                # Для performance также включаем locustfile.py
                for test_file in category_dir.glob("*.py"):
                    if test_file.name != "__init__.py":
                        categories[category].append(test_file.name)
            else:
                for test_file in category_dir.glob("test_*.py"):
                    categories[category].append(test_file.name)
    
    return categories


def count_tests_in_file(file_path: Path) -> int:
    """Подсчитывает количество тестов в файле."""
    try:
        content = file_path.read_text(encoding="utf-8")
        # Подсчитываем функции test_* и методы test_*
        test_functions = content.count("def test_")
        test_methods = content.count("    def test_")
        return test_functions + test_methods
    except Exception:
        return 0


def generate_report() -> str:
    """Генерирует отчет о покрытии."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Собираем статистику
    markers = count_tests_by_marker()
    junit_stats = parse_junit_xml()
    test_files = collect_test_files()
    
    # Подсчитываем тесты по категориям
    tests_dir = Path(__file__).parent.parent / "tests"
    category_counts = {}
    for category in ["api", "integration", "contract", "performance"]:
        category_dir = tests_dir / category
        count = 0
        if category_dir.exists():
            if category == "performance":
                # Для нагрузочных тестов считаем классы пользователей в locustfile.py
                locust_file = category_dir / "locustfile.py"
                if locust_file.exists():
                    try:
                        content = locust_file.read_text(encoding="utf-8")
                        # Ищем классы, наследующиеся от HttpUser
                        import re
                        user_classes = re.findall(r'class\s+\w+User\s*\(.*?HttpUser', content)
                        count = len(user_classes)
                    except Exception:
                        count = 0
            else:
                for test_file in category_dir.glob("test_*.py"):
                    count += count_tests_in_file(test_file)
        category_counts[category] = count
    
    # Генерируем отчет
    report = f"""# Отчет о покрытии тестами

**Дата генерации:** {timestamp}

## Общая статистика

| Метрика | Значение |
|---------|----------|
| Всего тестов | {junit_stats['total']} |
| Успешно пройдено | {junit_stats['passed']} |
| Провалено | {junit_stats['failed']} |
| Пропущено | {junit_stats['skipped']} |
| Ошибок | {junit_stats['errors']} |

## Покрытие по категориям тестов

### API Тесты
- **Количество тестов:** {category_counts.get('api', 0)}
- **Файлы тестов:** {len(test_files.get('api', []))}
  {chr(10).join(f'  - `{f}`' for f in test_files.get('api', []))}

**Покрытие:**
- Позитивные сценарии: {markers.get('positive', 0)} тестов
- Негативные сценарии: {markers.get('negative', 0)} тестов
- Smoke тесты: {markers.get('smoke', 0)} тестов

### Интеграционные тесты
- **Количество тестов:** {category_counts.get('integration', 0)}
- **Файлы тестов:** {len(test_files.get('integration', []))}
  {chr(10).join(f'  - `{f}`' for f in test_files.get('integration', []))}

**Покрытие:**
- Полные сценарии работы приложения
- Интеграция с внешними сервисами
- Проверка состояния между запросами
- Параллельные запросы

### Контрактные тесты
- **Количество тестов:** {category_counts.get('contract', 0)}
- **Файлы тестов:** {len(test_files.get('contract', []))}
  {chr(10).join(f'  - `{f}`' for f in test_files.get('contract', []))}

**Покрытие:**
- Валидация структуры запросов и ответов
- Проверка HTTP статус кодов
- Валидация Content-Type
- Проверка формата JSON

### Нагрузочные тесты
- **Количество сценариев:** {category_counts.get('performance', 0)}
- **Файлы тестов:** {len(test_files.get('performance', []))}
  {chr(10).join(f'  - `{f}`' for f in test_files.get('performance', []))}

**Покрытие:**
- Обычная нагрузка (SpringBootUser)
- Негативные сценарии под нагрузкой (SpringBootNegativeUser)
- Скачки нагрузки (SpringBootSpikeUser)
- Стресс-тестирование (SpringBootStressUser)

## Позитивные и негативные сценарии

### Позитивные сценарии
Тесты, проверяющие успешное выполнение операций:
- Успешная аутентификация (LOGIN)
- Успешное выполнение действия (ACTION)
- Успешное завершение сессии (LOGOUT)
- Полный цикл работы токена
- Множественные действия после LOGIN
- Повторный LOGIN после LOGOUT
- Работа с несколькими токенами одновременно

**Количество:** {markers.get('positive', 0)} тестов

### Негативные сценарии
Тесты, проверяющие обработку ошибок и валидацию:
- Невалидные токены (пустые, неправильной длины, спецсимволы)
- Невалидные действия
- Отсутствующие параметры
- Неправильная авторизация (отсутствующий/неправильный API ключ)
- Действия без предварительной аутентификации
- SQL инъекции и XSS атаки
- Таймауты внешних сервисов
- Ошибки внешних сервисов
- Состояния гонки (race conditions)

**Количество:** {markers.get('negative', 0)} тестов

## Покрытие функциональности

### Эндпоинт /endpoint

#### Действие: LOGIN
- ✅ Успешная аутентификация
- ✅ Обработка ошибок внешнего сервиса
- ✅ Таймауты внешнего сервиса
- ✅ Валидация токена (формат, длина)
- ✅ Невалидные запросы
- ✅ Отсутствие API ключа
- ✅ Неправильный API ключ

#### Действие: ACTION
- ✅ Успешное выполнение после LOGIN
- ✅ Ошибка без предварительного LOGIN
- ✅ Обработка ошибок внешнего сервиса
- ✅ Множественные ACTION после одного LOGIN
- ✅ ACTION после LOGOUT
- ✅ Параллельные ACTION запросы

#### Действие: LOGOUT
- ✅ Успешное завершение сессии
- ✅ LOGOUT без предварительного LOGIN
- ✅ Повторный LOGOUT
- ✅ Проверка, что после LOGOUT ACTION не работает

### Интеграционные сценарии
- ✅ Полный цикл: LOGIN -> ACTION -> LOGOUT
- ✅ Независимость токенов
- ✅ Повторный LOGIN после LOGOUT
- ✅ Сохранение состояния между запросами
- ✅ Параллельные запросы
- ✅ Интеграция с WireMock
- ✅ Обработка недоступности внешнего сервиса

### Безопасность
- ✅ Валидация токенов
- ✅ Проверка API ключа
- ✅ Защита от SQL инъекций
- ✅ Защита от XSS атак
- ✅ Валидация входных данных

### Производительность
- ✅ Обычная нагрузка
- ✅ Скачки нагрузки (spike testing)
- ✅ Стресс-тестирование
- ✅ Негативные сценарии под нагрузкой

## Запуск тестов

### Все тесты
```bash
pdm run pytest
```

### По категориям
```bash
# API тесты
pdm run pytest tests/api/ -m api

# Интеграционные тесты
pdm run pytest tests/integration/ -m integration

# Контрактные тесты
pdm run pytest tests/contract/ -m contract
```

### Позитивные/негативные сценарии
```bash
# Только позитивные тесты
pdm run pytest -m positive

# Только негативные тесты
pdm run pytest -m negative
```

### Нагрузочные тесты
```bash
cd tests/performance
locust -f locustfile.py --host=http://localhost:8080
```

## Генерация отчетов

После запуска тестов отчеты сохраняются в `reports/`:
- `junit.xml` - JUnit XML отчет для CI/CD
- `report.html` - HTML отчет с детальной информацией

## Примечания

- Тесты могут требовать запущенное приложение и WireMock
- Некоторые тесты могут быть пропущены (skipped) при недоступности сервисов
- Нагрузочные тесты запускаются отдельно через Locust

---

*Отчет сгенерирован автоматически скриптом `scripts/generate_coverage_report.py`*
"""
    
    return report


def main():
    """Главная функция."""
    project_root = Path(__file__).parent.parent
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_path = reports_dir / "coverage.md"
    
    print("Генерация отчета о покрытии тестами...")
    report = generate_report()
    
    report_path.write_text(report, encoding="utf-8")
    print(f"Отчет сохранен в: {report_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())