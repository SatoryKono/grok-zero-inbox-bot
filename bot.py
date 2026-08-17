#!/usr/bin/env python3
"""
Grok Zero Inbox Bot
Telegram-бот для управления почтой Mail.ru по методике Zero Inbox.
Использует Grok (xAI) для анализа писем.
"""

import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from openai import OpenAI
import asyncio

load_dotenv()

# Конфиг
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_BASE_URL = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4")
MAIL_EMAIL = os.getenv("MAIL_EMAIL")
MAIL_PASSWORD = os.getenv("MAIL_APP_PASSWORD")
IMAP_HOST = os.getenv("IMAP_HOST", "imap.mail.ru")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Клиент Grok (openai-совместимый)
client = OpenAI(
    api_key=GROK_API_KEY,
    base_url=GROK_BASE_URL,
)

def load_system_prompt() -> str:
    try:
        with open("prompts/system_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Ты — Grok Zero Inbox Manager. Помогай держать Inbox Zero."

SYSTEM_PROMPT = load_system_prompt()

def decode_mime(s):
    if not s:
        return ""
    decoded = decode_header(s)
    result = []
    for part, enc in decoded:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="ignore"))
        else:
            result.append(part)
    return "".join(result)

def get_unread_emails(limit=10):
    """Получить список непрочитанных писем."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(MAIL_EMAIL, MAIL_PASSWORD)
        mail.select("INBOX")
        status, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split()
        emails = []
        for eid in email_ids[-limit:]:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_mime(msg["Subject"])
            from_ = decode_mime(msg["From"])
            date_ = msg["Date"]
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")[:1500]
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")[:1500]
            emails.append({
                "id": eid.decode(),
                "from": from_,
                "subject": subject,
                "date": date_,
                "body": body
            })
        mail.logout()
        return emails
    except Exception as e:
        return [{"error": str(e)}]

async def ask_grok(user_message: str) -> str:
    """Запрос к Grok."""
    try:
        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка Grok API: {e}"

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я **Grok Zero Inbox Manager**.\n\n"
        "Помогаю держать почту Mail.ru в состоянии Inbox Zero.\n"
        "Подписка Mail Space — завтра будет, учтено.\n\n"
        "Команды:\n"
        "/inbox — непрочитанные\n"
        "/summary — обзор\n"
        "/process — разобрать по Zero Inbox\n"
        "/help — справка"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "**Команды:**\n"
        "/inbox — список непрочитанных писем\n"
        "/summary — краткий AI-обзор входящих\n"
        "/process — проанализировать и предложить действия\n"
        "/zero — статус Inbox Zero\n"
        "/help — эта справка\n\n"
        "После получения подписки Mail Space и создания пароля приложения заполни .env и перезапусти бота."
    )

@dp.message(Command("inbox"))
async def cmd_inbox(message: Message):
    await message.answer("Проверяю непрочитанные письма...")
    emails = get_unread_emails(limit=7)
    if not emails:
        await message.answer("✅ Входящие пусты. Inbox Zero!")
        return
    if "error" in emails[0]:
        await message.answer(f"Ошибка подключения: {emails[0]['error']}\n\nПроверь подписку Mail Space и пароль приложения.")
        return
    text = "📥 **Непрочитанные:**\n\n"
    for e in emails:
        text += f"• **{e['subject'][:60]}**\n  от {e['from'][:40]}\n  id: `{e['id']}`\n\n"
    await message.answer(text)

@dp.message(Command("summary"))
async def cmd_summary(message: Message):
    await message.answer("Формирую summary...")
    emails = get_unread_emails(limit=10)
    if not emails or "error" in emails[0]:
        await message.answer("Нет писем или ошибка подключения.")
        return
    prompt = "Сделай краткий summary этих писем и предложи приоритеты:\n\n"
    for e in emails:
        prompt += f"From: {e['from']}\nSubject: {e['subject']}\nBody: {e['body'][:300]}\n---\n"
    answer = await ask_grok(prompt)
    await message.answer(answer)

@dp.message(Command("process"))
async def cmd_process(message: Message):
    await message.answer("Анализирую письма по правилам Zero Inbox...")
    emails = get_unread_emails(limit=5)
    if not emails or "error" in emails[0]:
        await message.answer("Нет писем или ошибка.")
        return
    prompt = "Проанализируй каждое письмо и дай рекомендацию по Zero Inbox (категория + действие + черновик если нужно):\n\n"
    for e in emails:
        prompt += f"ID: {e['id']}\nFrom: {e['from']}\nSubject: {e['subject']}\nBody: {e['body'][:400]}\n===\n"
    answer = await ask_grok(prompt)
    await message.answer(answer)

@dp.message(Command("zero"))
async def cmd_zero(message: Message):
    emails = get_unread_emails(limit=1)
    if not emails:
        await message.answer("✅ **Inbox Zero!** Папка «Входящие» пуста.")
    elif "error" in emails[0]:
        await message.answer(f"Ошибка: {emails[0]['error']}")
    else:
        await message.answer(f"Ещё есть непрочитанные. Используй /process")

async def main():
    print("Grok Zero Inbox Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
