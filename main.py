import os
import time
import json
import base64
import httpx
import urllib.parse
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import ipaddress
import ngrok
# import uvicorn


load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
USERNAME = os.getenv('USER_NAME')
PASSWORD = os.getenv('USER_PASSWORD')
ORIGINATOR = os.getenv('ORIGINATOR')
USER_COMPANY = os.getenv('USER_COMPANY')
TEST_PHONE = os.getenv('TEST_PHONE')
DATA_FILE = os.getenv('DATA_FILE')
NGROK_TOKEN = os.getenv('NGROK_TOKEN')
WHITELIST_IP1 = os.getenv('WHITELIST_IP1')
WHITELIST_IP2 = os.getenv('WHITELIST_IP2')
SERVICE_API_URL = os.getenv('SERVICE_API_URL')
TEST_API_URL = os.getenv('TEST_API_URL')
PORT = os.getenv('PORT')
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
BASE_FILE_URL = f"https://api.telegram.org/file/bot{BOT_TOKEN}"
SETWEBHOOK_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/setWebhook'
AUTH_PASS = f"{USERNAME}:{PASSWORD}"
ENCODED_AUTH = base64.b64encode(AUTH_PASS.encode('utf-8')).decode('utf-8')

client = httpx.AsyncClient()


app = FastAPI()


# ngrok setup
listener = ngrok.forward(f'localhost:{PORT}', authtoken=NGROK_TOKEN)
print(f'Ingress established at {listener.url()}')
try:
    response = httpx.get(f'{SETWEBHOOK_URL}?url={listener.url()}/webhook')
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
except Exception as e:
    print(f"Error on setting up webhook: {e}")


# middleware restrictions (safety)
allowed_ips = [
    ipaddress.ip_network(WHITELIST_IP1),   # Telegram IP range
    ipaddress.ip_network(WHITELIST_IP2), # Telegram IP range
    ipaddress.ip_network('127.0.0.1'),
]

@app.middleware('http')
async def ip_address_middleware(request: Request, call_next):
    client_ip = ipaddress.ip_address(request.client.host)
    if not any(client_ip in subnet for subnet in allowed_ips):
        return PlainTextResponse(status_code=400, content='Not allowed')
    else:
        response = await call_next(request)
    return response


# functions to interact with user
async def send(text: str, chat_id: int) -> None:
    encoded_text = urllib.parse.quote(text)
    response = await client.get(f"{BASE_URL}/sendMessage?chat_id={chat_id}&text={encoded_text}")
    print(f'Response from send: {response}')

async def send_button(text: str, chat_id: int, buttons: json) -> None:
    text = f'This is message to be sent:\n***\n{text}\n***'
    encoded_text = urllib.parse.quote(text)
    response = await client.get(f"{BASE_URL}/sendMessage?chat_id={chat_id}&text={encoded_text}&reply_markup={buttons}")
    print(f'Response from send_button: {response}')

async def edit_send_button(chat_id: int, message_id: int, callback_id: int) -> None:
    response = await client.get(f"{BASE_URL}/editMessageReplyMarkup?chat_id={chat_id}&message_id={message_id}")
    print(f'Response from edit_send_button: {response}')
    response = await client.get(f"{BASE_URL}/answerCallbackQuery?callback_query_id={callback_id}")

async def get_confirmation(arg: str, chat_id: int, cmd: str) -> None:
    buttons = {
        'inline_keyboard': [[{'text': 'Ok', 'callback_data': f'/{cmd} {arg}'}],
                            [{'text': 'Cancel', 'callback_data': 'Cancel'}]],
    }
    print(arg)
    await send_button(arg, chat_id, json.dumps(buttons))

async def send_contacts_count(chat_id: int) -> None:
    contacts = get_recipients()
    await send (f'Number of contacts in database: {len(contacts)}', chat_id)

# utility func
def get_recipients() -> list:
    recipients_list = []
    i = 0
    try:
        with open(DATA_FILE, encoding='utf-8') as database_file:
            database = json.load(database_file)
    except FileNotFoundError:
        database = []
    for recipient in database:
        i += 1
        rec = {}
        rec['recipient'] = recipient['phone']
        rec['message-id'] = f"{USER_COMPANY}{i:08}"
        recipients_list.append(rec)
    return recipients_list

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

# command handlers
async def handle_bulk(arg: str, chat_id: int) -> None:
    await send('BULK HANDLED', chat_id)
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': f"Basic {ENCODED_AUTH}"
    }
    body = {
        "priority": 8,
        "sms": {
            "originator": ORIGINATOR,
            "content": {
                "text": arg
            }
        },
        "messages": []
    }
    body['messages'] = get_recipients()
    try:
        response = await client.post(SERVICE_API_URL, data=json.dumps(body), headers=headers)
        # response = await client.post(TEST_API_URL, data=json.dumps(body, ensure_ascii=False), headers=headers)
        await send(f"Status Code: {response.status_code}", chat_id)
        await send(f"Response Text: {response.text}", chat_id)
    except Exception as e:
        await send(f"Error on request to sms service server: {e}", chat_id)

async def handle_test(arg: str, chat_id: int) -> None:
    await send('TEST HANDLED', chat_id)
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': f"Basic {ENCODED_AUTH}"
    }
    body = {
        "priority": 8,
        "sms": {
            "originator": ORIGINATOR,
            "content": {
                "text": arg
            }
        },
        "messages": [
            {
            "recipient": TEST_PHONE,
            "message-id": USER_COMPANY + '00000001'
            }
        ]
    }
    try:
        response = await client.post(SERVICE_API_URL, data=json.dumps(body), headers=headers)
        # response = await client.post(TEST_API_URL, data=json.dumps(body), headers=headers)
        await send(f"Status Code: {response.status_code}", chat_id)
        await send(f"Response Text: {response.text}", chat_id)
    except Exception as e:
        await send(f"Error on request to sms service server: {e}", chat_id)

async def handle_cmd(text: str, chat_id: int) -> None:
    cmd, arg = await extract_cmd(text, chat_id)
    if cmd == 'error':
        pass
    elif cmd == 'bulk' or cmd == 'test':
        await get_confirmation(arg, chat_id, cmd)
    elif cmd == 'contacts':
        await send_contacts_count(chat_id)
    else:
        await send(f"Command {cmd} not implemented.", chat_id)

async def handle_send(data: str, chat_id: int, message_id: int, callback_id: int) -> None:
    if (data == 'Cancel'):
        await edit_send_button(chat_id, message_id, callback_id)
        await send('Opperation canceled', chat_id)
    else:
        await edit_send_button(chat_id, message_id, callback_id)
        await send('Message(s) sent', chat_id)
        cmd, arg = await extract_cmd(data, chat_id)
        if cmd == 'bulk':
            await handle_bulk(arg, chat_id)
        elif cmd == 'test':
            await handle_test(arg, chat_id)
        else:
            await send("Unexpected error occured", chat_id)

# new contacts
async def phone_already_in_db(database: dict, phone: str, name: str, chat_id: int) -> bool:
    for recipient in database:
        if recipient['phone'] == phone:
            if recipient['name'] != name:
                await send(f'Phone {phone} already has recipient {recipient["name"]} associated with it. Cannot overwrite with new user {name}.', chat_id)
            await send(f'Phone {phone} is already in database associated with {recipient["name"]}', chat_id)
            return True
    return False

async def import_document(document: dict, chat_id: int) -> None:
    file_name = document['file_name']
    file_id = document['file_id']
    resp = await client.get(f'{BASE_URL}/getFile?file_id={file_id}')
    if resp.status_code != 200:
        await send(f"Couldn't save file: {file_name}", chat_id)
        return
    file_meta = resp.json()
    file_path = file_meta['result']['file_path']
    resp = await client.get(f'{BASE_FILE_URL}/{file_path}')
    local_file_path = f'tmpfile_{int(time.time())}.xlsx'
    with open(local_file_path, 'wb') as xlsx:
        xlsx.write(resp.content)
    await send('File saved successfully', chat_id)

    try:
        workbook = pd.read_excel(local_file_path)
    except Exception as e:
        await send(f"Couldn't open file: {file_name}", chat_id)
        await send(f'Reason: {e}', chat_id)
        return

    try:
        with open(DATA_FILE, encoding='utf-8') as database_file:
            database = json.load(database_file)
    except FileNotFoundError as e:
        await send(f"Couldn't open database: {DATA_FILE}", chat_id)
        await send(f'Reason: {e}')
        return
    for index, row in workbook.iterrows():
        name = str(row[0]).strip()
        phone = str(row[1]).strip()
        if not is_valid_phonenumber(phone):
            await send(f'User {name} has invalid phone number: {phone}.', chat_id)
            continue
        if await phone_already_in_db(database, phone, name, chat_id):
            continue
        database.append({'name': name, 'phone': phone})
    os.rename(DATA_FILE, f'{DATA_FILE}_{int(time.time())}.bak')
    with open(DATA_FILE, 'w', encoding='utf-8') as database_file:
        json.dump(database, database_file, indent=2, ensure_ascii=False)
    await send("contacts added successfully", chat_id)

# parsing commands
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
        return cmd, text[0]
    elif cmd == 'test':
        if not text:
            await send('test command requires argument', chat_id)
            return 'error', ''
        return cmd, text[0]
    elif cmd == 'contacts':
        if text:
            await send('contacts command should not have argument(s)', chat_id)
            return 'error', ''
        return cmd, None
    else:
        await send(f'Unknown command: {cmd}', chat_id)
        return 'error', ''

# incoming request handler
@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    print(data)
    try:
        print(f'***\nDebug, recieved command:\n{json.dumps(data, indent=2)}\n***')
        if 'message' in data:
            chat_id = data['message']['chat']['id']
            if data['message'].get('document') is not None:
                await import_document(data['message']['document'], chat_id)
            elif data['message'].get('text') is not None:
                text = data['message']['text']
                await handle_cmd(text, chat_id)
        elif 'callback_query' in data:
            chat_id = data['callback_query']['message']['chat']['id']
            await handle_send(data['callback_query']['data'],
                              chat_id, data['callback_query']['message']['message_id'], data['callback_query']['id'])
    except KeyError as e:
        print(e)
        print(data)

# if __name__ == "__main__":
#     uvicorn.run(app, host="localhost", port=2340)
