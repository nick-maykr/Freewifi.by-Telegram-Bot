from bcrypt import checkpw
from telebot.types import Message

from Objects import bot
from Objects.DbObjects import Clients, Fail2Bans, User, Users
from Objects.Loggers import ErrLog
from Dialogues import menu


@bot.message_handler(commands=['start'],
                     func=lambda m: not User(m.from_user.id).quickstate)
@ErrLog
def start(m):
    user = User(m.from_user.id)
    insert_into_db(user, m)
    try:
        payload = m.text.split(" ")[1]
        authenticate(user, payload)
    except IndexError:
        info(user)


def insert_into_db(user, m: Message):
    first_name = m.from_user.first_name
    last_name = m.from_user.last_name
    tg_name = f"{first_name} {last_name}" if last_name else first_name
    Users(id=user.id, tg_name=tg_name).insert()
    Fail2Bans(id=user.id).insert()


def info(user):
    txt = "👋 Привет!\n" \
          "Этот бот только для клиентов Freewifi.\n" \
          "Попросите ссылку для авторизации у своего менеджера :)"
    bot.send_message(user.id, txt)


def authenticate(user, payload: str):
    try:
        client_id, password = payload.split("_")
        client = Clients(id=client_id).select()[0]
        if checkpw(bytes(password, "utf-8"), bytes(client.password, "utf-8")):
            user.client = client.id
            login(user)
        else:
            raise ValueError
    except (IndexError, ValueError):
        deny(user)


def deny(user):
    user.Fail2Ban.failed_attempts += 1
    remaining = user.Fail2Ban.remaining
    if remaining:
        txt = f"⚠️ Неверная ссылка авторизации. Осталось попыток: {remaining}"
    else:
        user.state = "banned"
        txt = "❌ Доступ заблокирован.\nОбратитесь к своему менеджеру"
    bot.send_message(user.id, txt)


def login(user):
    bot.send_message(user.id, "Добро пожаловать!")
    menu.menu(user)
