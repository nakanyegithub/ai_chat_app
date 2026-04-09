```bash
# AI Чат Система

Веб-приложение для общения с искусственным интеллектом через Ollama API. Пользователи могут создавать несколько чатов, переключать модели AI, получать ответы в реальном времени (стриминг), а администратор может просматривать всех пользователей и их чаты.

---

## Документация и диаграммы

В папке `docs/` находятся диаграммы, созданные для отчетности по практике:

### Диаграммы UML

| Файл | Описание |
|------|----------|
| `User Chat Management Model.pdf` | Диаграмма классов UML. Показывает структуру системы: классы User, Chat, Message, ModelStats, UserSession, OllamaClient, ChatController и связи между ними (один-ко-многим). |
| `User Interaction Stream.pdf` | Диаграмма последовательности (Sequence Diagram). Отображает процесс отправки сообщения: от ввода пользователем до получения стримингового ответа от AI, включая взаимодействие с БД и Ollama API. |
| `AI Chat System User.pdf` | Диаграмма вариантов использования (Use Case Diagram). Описывает функциональность системы с точки зрения пользователя и администратора: регистрация, создание чатов, отправка сообщений, управление моделями и администрирование. |

### Где находятся диаграммы

```
ai_chat_app/
└── docs/
    ├── User Chat Management Model.pdf
    ├── User Interaction Stream.pdf
    └── AI Chat System User.pdf
```

### Главный экран чата

- Левая панель: список чатов, кнопка "New Chat", информация о пользователе
- Центральная область: диалог с AI, приветственный экран
- Правая верхняя панель: выбор модели AI, настройки

### Админ-панель

- Список всех пользователей слева
- При выборе пользователя показываются его чаты
- При выборе чата показываются все сообщения

---

## Функциональность

### Пользовательские функции

| Функция | Описание |
|---------|----------|
| Регистрация | Создание аккаунта |
| Вход/Выход | Авторизация |
| Создание чата | Новая беседа |
| Переименование | Изменение названия |
| Удаление | Удаление чата |
| Сообщения | Отправка сообщений |
| Стриминг | Ответ в реальном времени |
| Stop | Остановка генерации |
| Модели | Выбор AI |
| История | Сохранение сообщений |
| Очистка | Очистка чата |

### Административные функции

| Функция | Описание |
|---------|----------|
| Пользователи | Просмотр всех |
| Чаты | Просмотр чатов |
| Сообщения | Просмотр сообщений |

---

## Технологии

- Python 3.11+
- Flask 2.3.3
- PostgreSQL 15+
- SQLAlchemy
- Ollama
- HTML/CSS/JS

---

## Установка

### Требования

- Python 3.11+
- PostgreSQL
- Ollama (обязательно установлен и запущен)

### 1. PostgreSQL

**Arch Linux:**
```bash
sudo pacman -S postgresql
sudo -u postgres initdb -D /var/lib/postgres/data
sudo systemctl enable --now postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl enable --now postgresql
```

### 2. База данных

```bash
sudo -u postgres psql -c "CREATE DATABASE ai_chat_db;"
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_chat_db TO postgres;"
```

### 3.1 Установка проекта

```bash
git clone https://github.com/your-repo/ai_chat_app.git
cd ai_chat_app

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 3.2 Установка Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama run llama2
```

### 4. .env

```env
SECRET_KEY=your-secret-key

DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_chat_db
DB_USER=postgres
DB_PASSWORD=postgres

OLLAMA_HOST=127.0.0.1
OLLAMA_PORT=11434
```

### 5. Запуск

```bash
python app.py
```

Открыть: http://localhost:5000

---

## Структура проекта

```
ai_chat_app/
├── app.py
├── config.py
├── database.py
├── ollama_client.py
├── decorators.py
├── utils.py
├── requirements.txt
├── .env
├── templates/
├── static/
├── docs/
└── tests/
```

---

## API

### Auth
- POST /api/register
- POST /api/login
- POST /api/logout

### Chats
- GET /api/chats
- POST /api/chats
- DELETE /api/chats/{id}

### Messages
- GET /api/chats/{id}/messages
- POST /api/chats/{id}/messages/stream

### Models
- GET /api/models

### Admin
- GET /api/admin/users

---

## Тесты

```bash
python tests/test_app.py
```

---

## Админ

- login: admin
- password: admin123

---

## Устранение проблем

### PostgreSQL
```bash
sudo systemctl status postgresql
```

### Ollama
```bash
curl http://127.0.0.1:11434/api/tags
```

### Порт занят
```bash
lsof -i :5000
kill -9 <PID>
```

---

## Лицензия

Учебный проект


