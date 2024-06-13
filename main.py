import os
import time
import json

import httpx
import requests
import pandas as pd
from fastapi import FastAPI, Request
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.environ.get('BOT_TOKEN')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
BASE_FILE_URL = f"https://api.telegram.org/file/bot{TOKEN}"

client = httpx.AsyncClient()

app = FastAPI()

async def send(text: str, chat_id: int) -> None:
    await client.get(f"{BASE_URL}/sendMessage?chat_id={chat_id}&text={text}")

async def extract_cmd(text: str, chat_id: int) -> tuple[str, str]:
    orig_text = text
    cmd, *text = text.strip().split(maxsplit=1)
    if cmd[0] != '/':
        await send(f'Invalid command: {orig_text}', chat_id)
        return 'error', ''
    cmd = cmd[1:]
    if cmd == 'bulk':
        if not text:
            await send('bulk command requires argument', chat_id)
            return 'error', ''
        return cmd, text
    elif cmd == 'test':
        if not text:
            await send('test command requires argument', chat_id)
            return 'error', ''
        return cmd, text
    else:
        await send(f'Unknown command: {cmd}', chat_id)
        return 'error', ''

async def handle_bulk(arg: str, chat_id: int) -> None:
    await send('BULK HANDLED', chat_id)

async def handle_test(arg: str, chat_id: int) -> None:
    await send('TEST HANDLED', chat_id)

async def handle_cmd(text: str, chat_id: int) -> None:
    cmd, arg = await extract_cmd(text, chat_id)
    if cmd == 'error':
        pass
    elif cmd == 'bulk':
        await handle_bulk(arg, chat_id)
    elif cmd == 'test':
        await handle_test(arg, chat_id)
    else:
        await send(f"Command {cmd} not implemented.", chat_id)

def is_valid_phonenumber(phone: str) -> bool:
    phone = phone.strip()
    if phone[0] == '+':
        phone = phone[1:]
    if not phone.startswith('998'):
        return False
    if len(phone) != 12:
        return False
    if not phone.isascii() or not phone.isdecimal():
        return False
    return True

async def phone_already_in_db(users: dict, phone: str, name: str, chat_id: int) -> bool:
    for user in users:
        if user['phone'] == phone:
            if user['name'] != name:
                await send(f'Phone {phone} already has user {user["name"]} associated with it. Cannot overwrite with new user {name}.', chat_id)
            return True
    return False

async def import_document(document: dict, chat_id: int) -> None:
    file_name = document['file_name']
    file_id = document['file_id']
    resp = requests.get(f'{BASE_URL}/getFile?file_id={file_id}')
    if resp.status_code != 200:
        await send(f"Couldn't save file: {file_name}", chat_id)
        return
    file_meta = resp.json()
    file_path = file_meta['result']['file_path']
    resp = requests.get(f'{BASE_FILE_URL}/{file_path}')
    local_file_path = f'tmpfile_{int(time.time())}.xlsx'
    with open(local_file_path, 'wb') as xlsx:
        xlsx.write(resp.content)
    await send('File saved successfully', chat_id)

    try:
        workbook = pd.read_excel(local_file_path)
    except Exception as e:
        await send(f"Couldn't open file: {file_name}", chat_id)
        return

    try:
        with open('users.json', encoding='utf-8') as users_file:
            users = json.load(users_file)
    except FileNotFoundError:
        users = []

    for index, row in workbook.iterrows():
        name = str(row[0]).strip()
        phone = str(row[1]).strip()
        if not is_valid_phonenumber(phone):
            await send(f'User {name} has invalid phone number: {phone}.', chat_id)
            continue
        if await phone_already_in_db(users, phone, name, chat_id):
            continue
        users.append({'name': name, 'phone': phone})

    os.rename('users.json', 'users.bak.json')
    with open('users.json', 'w', encoding='utf-8') as users_file:
        json.dump(users, users_file, indent=2, ensure_ascii=False)

@app.post("/webhook/")
async def webhook(req: Request):
    data = await req.json()
    try:
        chat_id = data['message']['chat']['id']
        if data['message'].get('document') is not None:
            await import_document(data['message']['document'], chat_id)
        elif data['message'].get('text') is not None:
            text = data['message']['text']
            await handle_cmd(text, chat_id)
        else:
            await send('Unknown message type.', chat_id)
    except KeyError as e:
        print(e)
        print(data)
