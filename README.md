```markdown
# AI Чат Система

Веб-приложение для общения с ИИ через Ollama API.

## Документация и диаграммы

В папке `docs/` находятся диаграммы:

- `User Chat Management Model.pdf` — Диаграмма классов
- `User Interaction Stream.pdf` — Диаграмма последовательности  
- `AI Chat System User.pdf` — Use Case диаграмма

## Функциональность

**Пользователь:**
- Регистрация и вход
- Создание/переименование/удаление чатов
- Отправка сообщений (стриминг ответов)
- Переключение AI моделей
- Остановка генерации
- История сообщений

**Администратор:**
- Просмотр всех пользователей
- Просмотр их чатов и сообщений

## Технологии

Python / Flask / PostgreSQL / SQLAlchemy / Ollama / HTML/CSS/JS

## Установка

### 1. PostgreSQL

```bash
# Arch
sudo pacman -S postgresql
sudo -u postgres initdb -D /var/lib/postgres/data
sudo systemctl enable --now postgresql

# Ubuntu
sudo apt install postgresql postgresql-contrib
sudo systemctl enable --now postgresql
```

### 2. База данных

```bash
sudo -u postgres psql -c "CREATE DATABASE ai_chat_db;"
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_chat_db TO postgres;"
```

### 3. Проект

```bash
git clone https://github.com/your-repo/ai_chat_app.git
cd ai_chat_app
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama run llama2
```

### 5. .env

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

### 6. Запуск

```bash
python app.py
```

Открыть: http://localhost:5000

## API

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | /api/register | Регистрация |
| POST | /api/login | Вход |
| POST | /api/logout | Выход |
| GET | /api/chats | Список чатов |
| POST | /api/chats | Создать чат |
| DELETE | /api/chats/{id} | Удалить чат |
| GET | /api/chats/{id}/messages | История |
| POST | /api/chats/{id}/messages/stream | Отправить |
| GET | /api/models | Список моделей |
| GET | /api/admin/users | Пользователи (админ) |

## Тесты

```bash
python tests/test_app.py
```

## Админ

- Логин: `admin`
- Пароль: `admin123`

## Устранение проблем

```bash
# PostgreSQL
sudo systemctl status postgresql

# Ollama
curl http://127.0.0.1:11434/api/tags

# Порт занят
lsof -i :5000
kill -9 <PID>
```


```
