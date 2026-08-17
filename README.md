# Grok Zero Inbox Bot

Telegram-бот и AI-агент на базе Grok (xAI) для управления почтой **Mail.ru** по методике **Zero Inbox**.

## Возможности
- Подключение к Mail.ru через IMAP/SMTP (требуется подписка Mail Space)
- Анализ писем через Grok
- Автоматическая классификация: To Reply / Archive / Delete / Newsletter / Cold
- Генерация черновиков ответов
- Команды для поддержания пустого инбокса
- Ежедневный summary

## Требования
1. Подписка **Mail Space** (тариф «для работы») — пользователь сообщил, что будет завтра.
2. Пароль приложения Mail.ru.
3. Telegram Bot Token (от @BotFather).
4. xAI API Key (Grok).

## Быстрый старт

### 1. Клонировать
```bash
git clone https://github.com/SatoryKono/grok-zero-inbox-bot.git
cd grok-zero-inbox-bot
```

### 2. Установить зависимости
```bash
pip install -r requirements.txt
```

### 3. Настроить .env
Скопируйте `.env.example` → `.env` и заполните:
```
TELEGRAM_BOT_TOKEN=...
GROK_API_KEY=xai-...
MAIL_EMAIL=your@mail.ru
MAIL_APP_PASSWORD=пароль_приложения
IMAP_HOST=imap.mail.ru
IMAP_PORT=993
SMTP_HOST=smtp.mail.ru
SMTP_PORT=465
```

### 4. Запустить
```bash
python bot.py
```

## Команды бота
- `/start` — приветствие и статус
- `/inbox` — список непрочитанных
- `/summary` — краткий обзор входящих
- `/process` — разобрать письма по Zero Inbox
- `/draft <id>` — сгенерировать черновик ответа
- `/archive <id>` — архивировать
- `/zero` — статус «Inbox Zero»
- `/help` — справка

## System Prompt
Полный системный промпт находится в `prompts/system_prompt.txt`. Его можно использовать отдельно в Grok / Custom Instructions.

## Важно про Mail.ru (август 2026)
С 12 июня 2026 бесплатный IMAP отключён. Нужна подписка Mail Space. После оформления создайте пароль приложения:
Настройки → Безопасность → Пароли для внешних приложений.

---
Создано командой Grok + Harper, Benjamin, Lucas.
