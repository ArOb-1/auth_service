# 🔐 Auth Service

Бэкенд-сервис собственной системы аутентификации и авторизации.  
Реализован на **Django** без использования встроенных механизмов
аутентификации фреймворка — всё написано вручную: JWT, хэширование
паролей, middleware, система ролей и политик доступа.

---

## 🛠 Стек технологий

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

## 🚀 Запуск локально

### 1. Клонируй репозиторий

```bash
git clone https://github.com/your-username/auth_service.git
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
docker compose up --build
```

### 4. Примени миграции

```bash
docker compose exec web python manage.py migrate
```

### 5. Наполни БД тестовыми данными

Тестовые пользователи описаны в `data/load_data.json`:

```bash
docker compose exec web python manage.py seed
```

После этого в БД появятся три готовых пользователя:

| Email             | Пароль      | Роль    |
|-------------------|-------------|---------|
| admin@test.com | admin123 | admin |
| manager@test.com | manager123 | manager |
| user@test.com | user123 | user |

### 6. Запусти тесты (опционально)

```bash
source venv/bin/activate
pytest -v --tb=short
```

Сервис доступен по адресу: **http://localhost:8000**

---

## 🏗 Архитектура

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

## 🔑 Аутентификация

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

## 🛡 Система прав доступа

### Схема БД



  
| roles |  | role_policies |  
| ----- | --- | ------------- |  
| id | ──────► | role_id (FK) | resource | action | scope |  
| name |  |  |  |  |  |  
  
  
  
| users |  
| --- |  
| id (UUID) \| email \| password_hash \| role_id (FK) |  
  
│first_name│last_name │  patronymic   │    is_active     │  
└──────────┴──────────┴───────────────┴─────────────────┘


### Как работает проверка прав

При каждом запросе к защищённому эндпоинту декоратор `@require_permission`
ищет в таблице `role_policies` запись для роли пользователя с указанным
**ресурсом** и **действием**. Если запись найдена — запрос выполняется,
в `request.scope` записывается область видимости. Если нет — `403 Forbidden`.



Запрос  
  → AuthMiddleware       — кто ты? → request.user  
  → @require_permission  — что хочешь сделать?  
      ищет (role, resource, action) в role_policies  
          ✅ найдено → request.scope = scope → выполняем view → 200  
          ❌ не найдено → 403 Forbidden  
          ❌ user is None → 401 Unauthorized


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

## 📡 API эндпоинты

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

### Бизнес-объекты (Mock)

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

## 📋 Примеры запросов и ответов

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

### Бизнес-объекты (Mock)

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

## ✅ Как проверить работоспособность сервиса

### Способ 1 — Автотесты

```bash
source venv/bin/activate
pytest -v --tb=short
```

Покрыты: регистрация, логин, логаут, получение/обновление/удаление профиля,
система прав (401/403), мягкое удаление, инвалидация токена после удаления.

---

### Способ 2 — Вручную через curl / Postman

**Шаг 1.** Залогинься тестовым пользователем:
```bash
curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@test.com", "password": "user123"}'
```
Скопируй `access_token`.

**Шаг 2.** Запроси свой профиль:
```bash
curl http://localhost:8000/users/me/ \
  -H "Authorization: Bearer <access_token>"
```
→ `200 OK` с данными профиля.

**Шаг 3.** Попробуй получить admin-политики с user-токеном:
```bash
curl http://localhost:8000/admin/policies/ \
  -H "Authorization: Bearer <access_token>"
```
→ `403 Forbidden`.

**Шаг 4.** Залогинься как admin и повтори:
```bash
curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "admin123"}'

curl http://localhost:8000/admin/policies/ \
  -H "Authorization: Bearer <admin_token>"
```
→ `200 OK` со списком политик.

**Шаг 5.** Удали user-аккаунт и убедись что токен инвалидируется:
```bash
curl -X DELETE http://localhost:8000/users/me/delete/ \
  -H "Authorization: Bearer <user_token>"

curl http://localhost:8000/users/me/ \
  -H "Authorization: Bearer <user_token>"
```
→ `401 Unauthorized`.

---

### Способ 3 — Проверить БД напрямую

```bash
docker compose exec db psql -U postgres -d auth_db

-- Пользователи
SELECT id, email, is_active, role_id FROM users;

-- Политики доступа
SELECT r.name AS role, rp.resource, rp.action, rp.scope
FROM role_policies rp
JOIN roles r ON r.id = rp.role_id
ORDER BY r.name, rp.resource;
```