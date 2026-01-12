### Документация к тестовому заданию 
Задача : покрыть тестами java-приложение.
Результат : ссылка на git-репозиторий с кодом тестов.

Стек технологий: Python, pytest, WireMock, Allure, PDM

1. Ядро тестирования 
    - Python 3.11+ - основной язык тестирования
    - pytest - фреймворк для тестирования
    - requests/httpx - HTTP клиенты для обращения к Spring Boot
    - pydantic - валидация ответов от Spring Boot API
    
  2. Мокирование зависимостей Spring Boot
    - WireMock - для мокинга внешних сервисов, от которых зависит Spring Boot
    - TestContainers (Python) - для поднятия тестовых БД и других сервисов
    
  3. Отчетность и утилиты 
    - Allure-pytest - продвинутая отчетность
    - Faker - генерация тестовых данных
    - deepdiff - сравнение сложных структур


### Запуск приложения
Тестируемое приложение - классический веб-сервис на Spring Boot. Для запуска необходима Java 17 или выше:
```
java -jar -Dsecret=qazWSXedc -Dmock=http://localhost:8888/ internal-0.0.1-SNAPSHOT.jar 
```

### Эндпоинты приложения
У тестируемого приложения только один эндпоинт, который принимает на вход POST-запросы вида:
```
POST http://localhost:8080/endpoint
Content-Type: application/x-www-form-urlencoded
Accept: application/json
X-Api-Key: qazWSXedc

token=${token}&action=${action}
```
Для доступа к эндпоинту требуется заголовок `X-Api-Key`.  
Это статический API-ключ, который проверяется приложением при каждом запросе.

token - строка длиной 32 символа, состоящая только из символов A-Z0-9
action - действие пользователя. Всего их три:
* LOGIN - аутентификация. Триггерит отправку запроса /auth на внешний сервис. В случае успеха токен сохраняется во внутреннем хранилище
* ACTION - действие. Триггерит отправку запроса /doAction на внешний сервис. Доступно только для токенов, ранее прошедших LOGIN
* LOGOUT - завершение сессии юзера. Удаляет токен из внутреннего хранилища

В ответ приходит json.
* Тело успешного ответа:
```json
{
  "result": "OK"
}
```

* Тело неуспешного ответа:
```json
{
  "result": "ERROR",
  "message": "reason"
}
```


### Эндпоинты внешнего сервиса
У внешнего сервиса только два эндпоинта. На них отправляет запросы тестируемое приложение.
Оба могут возвращать любое тело ответа, тестируемое приложение смотрит только на код.

Примеры запросов от тестируемого приложения:
#### /auth
```
POST ${mock}/auth
Content-Type: application/x-www-form-urlencoded
Accept: application/json

token=${token}
```

#### /doAction
```
POST ${mock}/doAction
Content-Type: application/x-www-form-urlencoded
Accept: application/json

token=${token}
```