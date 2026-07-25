# Auth Service

Бэкенд-сервис собственной системы аутентификации и авторизации.  
Реализован на **Django** без использования встроенных механизмов
аутентификации фреймворка — всё написано вручную: JWT, хэширование
паролей, middleware, система ролей и политик доступа.

---

## Стек технологий

| Компонент     | Технология              |
|---------------|-------------------------|
| Язык | Python 3.12 |
| Фреймворк | Django 5 |
| БД | PostgreSQL |
| Токены | PyJWT |
| Пароли | bcrypt |
| Контейнеры | Docker + Docker Compose |
| Тесты | pytest + pytest-django |

---

## Запуск локально

### 1. Клонируй репозиторий

```bash
git clone https://github.com/ArOb-1/auth_service
cd auth_service
```

### 2. Создай `.env` файл

```env
SECRET_KEY=your-secret-key-here
DEBUG=True

DB_NAME=auth_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

JWT_SECRET=your-jwt-secret
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=7
```

### 3. Подними контейнеры

```bash
docker compose up --build -d
```

### 4. Примени миграции

```bash
docker compose exec web python manage.py migrate
```

### 5. Запусти тесты (опционально)

```bash
source venv/bin/activate
pytest -v --tb=short
```

Сервис доступен по адресу: **http://localhost:8000**

---

## Архитектура

### Структура приложения



auth_service/  
├── core/               # Настройки Django, главный urls.py  
├── auth_core/          # Аутентификация: login, logout, register, JWT, middleware  
├── users/              # Профиль пользователя: просмотр, редактирование, удаление  
├── access_control/     # Роли, политики доступа, декоратор require_permission  
├── business/           # Mock-эндпоинты бизнес-объектов (магазины, товары, заказы)  
├── data/               # Тестовые данные: load_data.json  
└── tests/              # Тесты


---

## Аутентификация

После успешного `login` сервер возвращает два JWT-токена:

- **access_token** — короткоживущий (15 минут), передаётся в каждом запросе
- **refresh_token** — долгоживущий (7 дней), используется для получения нового access_token

Токен передаётся в заголовке:
```
Authorization: Bearer <access_token>
```

Кастомный `AuthMiddleware` перехватывает каждый запрос, декодирует токен
и записывает пользователя в `request.user`. Если токен невалиден или
пользователь неактивен — `request.user = None`.

Пароли хранятся в БД в виде bcrypt-хэша, исходный пароль нигде не сохраняется.

---

## Система прав доступа

### Схема БД

| **roles** | &nbsp; | **role_policies** |
|-----------|:------:|-------------------|
| id | ──────► | role_id (FK) |
| name |  | resource |
| description |  | action |
|  |  | scope |

| **users** | | | |
|-----------|---|---|---|
| id (UUID) | email | password_hash | role_id (FK) |
| first_name | last_name | patronymic | is_active |


### Как работает проверка прав

При каждом запросе к защищённому эндпоинту декоратор `@require_permission`
ищет в таблице `role_policies` запись для роли пользователя с указанным
**ресурсом** и **действием**. Если запись найдена — запрос выполняется,
в `request.scope` записывается область видимости. Если нет — `403 Forbidden`.



Запрос  
  → AuthMiddleware       — кто ты? → request.user  
  → @require_permission  — что хочешь сделать?  
      ищет (role, resource, action) в role_policies  
          найдено → request.scope = scope → выполняем view → 200  
          не найдено → 403 Forbidden  
          user is None → 401 Unauthorized


### Роли

| Роль    | Описание                               |
|---------|----------------------------------------|
| admin | Полный доступ ко всем ресурсам |
| manager | Управляет своими магазинами и товарами |
| user | Создаёт заказы и отзывы |
| guest | Только чтение публичных данных |

### Ресурсы и действия

| Ресурс   | Доступные действия              |
|----------|---------------------------------|
| users | read, update, delete |
| shops | read, create, update, delete |
| products | read, create, update, delete |
| orders | read, create, update, delete |
| reviews | read, create, delete |

### Области видимости (Scope)

| Scope     | Описание                                      |
|-----------|-----------------------------------------------|
| all | Доступ ко всем объектам |
| own | Только к объектам, созданным самим |
| own_shop | Только к объектам своего магазина |
| published | Только опубликованные объекты |

---

## API эндпоинты

### Аутентификация

| Метод | URL                | Описание              | Доступ |
|-------|--------------------|-----------------------|--------|
| POST | `/auth/register/` | Регистрация | Все |
| POST | `/auth/login/` | Вход | Все |
| POST | `/auth/logout/` | Выход | Auth |
| POST | `/auth/refresh/` | Обновление токена | Все |

### Профиль пользователя

| Метод  | URL                  | Описание              | Доступ |
|--------|----------------------|-----------------------|--------|
| GET | `/users/me/` | Получить свой профиль | Auth |
| PATCH | `/users/me/update/` | Обновить профиль | Auth |
| DELETE | `/users/me/delete/` | Мягкое удаление | Auth |

### Управление политиками (только admin)

| Метод  | URL                      | Описание             | Доступ |
|--------|--------------------------|----------------------|--------|
| GET | `/admin/policies/` | Список всех политик | Admin |
| POST | `/admin/policies/` | Создать политику | Admin |
| DELETE | `/admin/policies/<id>/` | Удалить политику | Admin |

### Бизнес-объекты

| Метод  | URL               | Описание            | Доступ           |
|--------|-------------------|---------------------|------------------|
| GET | `/shops/` | Список магазинов | guest+ |
| GET | `/products/` | Список товаров | guest+ |
| GET | `/orders/` | Мои заказы | user+ |
| POST | `/orders/` | Создать заказ | user+ |
| GET | `/reviews/` | Список отзывов | guest+ |
| POST | `/reviews/` | Создать отзыв | user+ |
| DELETE | `/reviews/<id>/` | Удалить отзыв | user (own)/admin |

---

## Примеры запросов и ответов

### Регистрация

```bash
curl -X POST http://localhost:8000/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "secret123",
    "password2": "secret123"
  }'
```

```json
{
  "user_id": "a1b2c3d4-...",
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci..."
}
```

---

### Вход

```bash
curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@test.com",
    "password": "user123"
  }'
```

```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci..."
}
```

---

### Выход

```bash
curl -X POST http://localhost:8000/auth/logout/ \
  -H "Authorization: Bearer eyJhbGci..."
```

```json
{
  "message": "Logged out successfully"
}
```

---

### Получить свой профиль

```bash
curl http://localhost:8000/users/me/ \
  -H "Authorization: Bearer eyJhbGci..."
```

```json
{
  "id": "a1b2c3d4-...",
  "email": "user@test.com",
  "first_name": "Regular",
  "last_name": "User",
  "patronymic": "",
  "role": "user",
  "created_at": "2025-07-01T12:00:00Z"
}
```

---

### Обновить профиль

```bash
curl -X PATCH http://localhost:8000/users/me/update/ \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Ivan",
    "last_name": "Ivanov"
  }'
```

```json
{
  "message": "Profile updated",
  "updated": ["first_name", "last_name"]
}
```

---

### Смена пароля

```bash
curl -X PATCH http://localhost:8000/users/me/update/ \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "user123",
    "new_password": "newpassword456"
  }'
```

```json
{
  "message": "Profile updated",
  "updated": ["password"]
}
```

---

### Удалить аккаунт (мягкое)

```bash
curl -X DELETE http://localhost:8000/users/me/delete/ \
  -H "Authorization: Bearer eyJhbGci..."
```

```json
{
  "message": "Account deleted"
}
```

После этого токен становится невалидным — пользователь не может войти.

---

### Получить политики (admin only)

```bash
curl http://localhost:8000/admin/policies/ \
  -H "Authorization: Bearer <admin_token>"
```

```json
[
  {
    "id": 1,
    "role": "user",
    "resource": "reviews",
    "action": "create",
    "scope": "own"
  }
]
```

---

### Бизнес-объекты

```bash
curl http://localhost:8000/shops/ \
  -H "Authorization: Bearer <any_token>"
```

```json
[
  {"id": 1, "name": "TechShop",   "owner": "manager@test.com"},
  {"id": 2, "name": "FoodMarket", "owner": "manager@test.com"}
]
```

---

## Как проверить работоспособность сервиса

### Способ 1 — Автотесты

```bash
source venv/bin/activate
pytest -v --tb=short
```

Покрыты: регистрация, логин, логаут, получение/обновление/удаление профиля,
система прав (401/403), мягкое удаление, инвалидация токена после удаления.

---

## Способ 2 — Тестовые данные

Все тестовые данные описаны в `data/load_data.json`.  
Команда создаёт пользователей, магазин, товары, заказы и отзывы:

```bash
docker compose exec web python manage.py seed
```

Вывод:



Users:  
   created admin@test.com    [admin]  
   created manager@test.com  [manager]  
   created user@test.com     [user]  
  
Shops:  
   created TechShop  (owner: manager@test.com)  
  
Products:  
   created Ноутбук Pro          [published]  99999.00 ₽  
   created Беспроводная мышь    [published]   1999.00 ₽  
   created Механическая клавиатура [draft]    7500.00 ₽  
  
Orders:  
   created user@test.com → Ноутбук Pro        x1  [pending]  
   created user@test.com → Беспроводная мышь  x2  [completed]  
  
Reviews:  
   created user@test.com → Ноутбук Pro       ⭐⭐⭐⭐⭐  
   created user@test.com → Беспроводная мышь ⭐⭐⭐⭐  
  
Done. Service is ready for testing.


---

## Демонстрация системы прав

Получи токен нужного пользователя:

```bash
curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@test.com", "password": "user123"}'
```

Используй `access_token` в заголовке `Authorization: Bearer <token>`.

---

### user@test.com — обычный пользователь

```bash
# 200 — свой профиль
GET /users/me/

# 200 — список магазинов (публичное)
GET /shops/

# 200 — только опубликованные товары (draft не видит)
GET /products/
# → [Ноутбук Pro, Беспроводная мышь]  (клавиатура не попадёт — draft)

# 200 — только свои заказы
GET /orders/
# → [заказ на ноутбук, заказ на мышь]

# 200 — все отзывы
GET /reviews/

# 201 — создать заказ
POST /orders/

# 201 — написать отзыв
POST /reviews/

# 403 — нет доступа к политикам
GET /admin/policies/
```

---

### manager@test.com — менеджер

```bash
# 200 — список магазинов
GET /shops/

# 201 — создать магазин
POST /shops/

# 200 — товары своего магазина (включая draft)
GET /products/
# → [Ноутбук Pro, Беспроводная мышь, Механическая клавиатура]

# 201 — добавить товар в свой магазин
POST /products/

# 200 — заказы своего магазина
GET /orders/

# 403 — нет доступа к политикам
GET /admin/policies/
```

---

### admin@test.com — администратор

```bash
# 200 — все политики доступа
GET /admin/policies/

# 201 — добавить новую политику
POST /admin/policies/
# Body: {"role": "user", "resource": "shops", "action": "create", "scope": "own"}

# 204 — удалить политику
DELETE /admin/policies/<id>/

# Полный доступ ко всем остальным ресурсам
```

---

### Инвалидация токена после удаления аккаунта

```bash
# 1. Логинимся
POST /auth/login/  {"email": "user@test.com", "password": "user123"}
# → сохраняем access_token

# 2. Удаляем аккаунт (мягкое — is_active=False)
DELETE /users/me/delete/  # → 200

# 3. Старый токен больше не работает
GET /users/me/  # → 401 Unauthorized
```