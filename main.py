import os
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from mydata import BOT_TOKEN, VK_TOKEN
import vk_user
from models import create_tables
import database as db
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from keyboards import keyboard_main, keyboard_candidate, keyboard_favorite
import json
from datetime import datetime


vk = vk_user.VKUser(VK_TOKEN, '5.131')

group_id = 218248035
bot = vk_api.VkApi(token=BOT_TOKEN)
botlongpoll = VkBotLongPoll(bot, group_id)

passw = os.getenv('postgres_passw')
DSN = f"postgresql://postgres:{passw}@localhost:5432/search_users"

engine = sqlalchemy.create_engine(DSN)
Session = sessionmaker(bind=engine)
session = Session()

create_tables(engine)  # создаем таблицы в БД


def saved_user(db_session, new_user):
    while True:
        exists_user = db.get_user(session, new_user)  # проверяем пользователя в БД
        if exists_user is None:
            db.add_user(db_session, vk.get_user_info(new_user))  # добавляем пользователя в БД
        else:
            break
    return exists_user


def write_msg(to_user, message, attach=None, keyboard=None):  # отправить сообщение пользователю
    if keyboard is not None:
        keyboard = json.dumps(keyboard)
    response = bot.method(
        'messages.send', {
            'user_id': to_user,
            'message': message,
            'random_id': 0,
            'attachment': attach,
            'keyboard': keyboard
        })
    return response


def get_request(botevent):  # перехватываем сообщения пользователя по параметрам поиска
    for item in botevent.listen():
        if item.type == VkBotEventType.MESSAGE_NEW:
            if item.obj.message['text'] != '':
                if item.from_user:
                    return item.obj.message['text'].lower()


def text_param(search_param):  # формируем ответ для пользователя по параметрам поиска
    param_mes = f"Параметры поиска:\n"
    if search_param['sex'] == 1:
        param_mes = param_mes + f"Пол: женский\n"
    elif search_param['sex'] == 2:
        param_mes = param_mes + f"Пол: мужской\n"
    else:
        param_mes = param_mes + f"Пол: любой\n"
    if search_param['age_from'] is not None:
        param_mes = param_mes + f"Возраст: {search_param['age_from']}-{search_param['age_to']}\n"
    if search_param['city_name'] is not None:
        param_mes = param_mes + f"Город: {search_param['city_name']}\n"
    else:
        param_mes = param_mes + f"Город: любой\n"
    return param_mes


def set_search_param(to_user):  # определяем параметры для поиска
    default_params = vk.get_user_info(to_user)
    search_param = {}
    user_sex = default_params['sex']
    if user_sex is None or user_sex == 0:
        write_msg(to_user, "Укажите пол(гендер) для поиска - мужской, женский, любой (м/ж/л)?")
        response = get_request(botlongpoll)  # получаем ответ от пользователя
        if response == 'ж':
            param_sex = 1
        elif user_sex == 'м':
            param_sex = 2
        else:
            param_sex = 0
    else:
        if user_sex == 1:
            param_sex = 2
        elif user_sex == 2:
            param_sex = 1
    search_param.update({"sex": param_sex})  # обновляем словарь параметров
    user_bdate = default_params['bdate']
    if user_bdate is not None:
        today = datetime.today().year
        user_age = today - int(user_bdate[-4:])
        age_from = user_age - 5
        age_to = user_age + 5
    else:
        write_msg(to_user, "Минимальный возраст для поиска (2-х значное число)?")
        while True:
            try:
                age_from = int(get_request(botlongpoll))
                break
            except Exception:
                write_msg(to_user, "Нверный ответ, попробуйте еще раз.")
        write_msg(to_user, "Максимальный возраст для поиска (2-х значное число)?")
        while True:
            try:
                age_to = int(get_request(botlongpoll))
                break
            except Exception:  # введено не число
                write_msg(to_user, "Неверный ответ, попробуйте еще раз")
    search_param.update({"age_from": age_from, "age_to": age_to})
    user_city = default_params['city']
    if user_city['id'] is None:
        write_msg(to_user, 'Укажите город для поиска')
        while True:
            response = get_request(botlongpoll)
            result = vk.get_city_id(response)
            if result is None:
                write_msg(to_user, 'Город не найден, попробуйте еще раз.')
            else:
                user_city = result['response']['items'][0]
                break
    search_param.update({
        "city_id": user_city['id'],
        "city_name": user_city['title']
    })
    mes_param = text_param(search_param)
    write_msg(user_id, mes_param, keyboard=keyboard_main)  # отправляем параметры поиска пользователю
    return search_param


def run_search(params):  # команда поиск
    if len(profile_list) == 0:
        result = vk.get_profiles(params)
        if result is not None:  # если есть результаты
            for item in result['response']['items']:  # заносим результаты в список
                if item not in profile_list and item['is_closed'] is False and 'photo_id' in item.keys():
                    profile_list.append(item)
        else:
            write_msg(user_id, "Поиск не дал результатов")
            exit()
    profile = profile_list[0]  # берем первый профайл из списка
    msg = f"Кандидат {profile['first_name']} {profile['last_name']}"
    attachment = 'photo' + profile['photo_id']
    # отправляем пользователю фото кандидата с кнопками для реакции
    write_msg(user_id, msg, attachment, keyboard_candidate)


for event in botlongpoll.listen():  # получаем события от бота
    if event.type == VkBotEventType.MESSAGE_NEW:  # если сообщение
        if event.obj.message['text'] != '':  # не пустое
            if event.from_user:  # от пользователя

                user_id = event.obj.message['from_id']  # запоминаем id пользователя, от которого пришло сообщение
                user_info = db.get_user(session, user_id)  # получаем информацию о пользователе
                if user_info is None:  # если пользователь новый, то сохраняем в базу
                    user_info = saved_user(session, user_id)
                    profile_list = []  # список профайлов
                request = event.obj.message['text'].lower()  # получаем текст сообщения пользователя
                if request == "искать":
                    params = set_search_param(user_id)
                    run_search(params)
                else:  # на любое другое сообщение отправляем пользователю приветствие
                    mes_hello = f"Привет {user_info['first_name']}!\n" \
                                f"Напиши искать для начала работы."
                    write_msg(user_id, mes_hello)

    elif event.type == VkBotEventType.MESSAGE_EVENT:  # событие по кнопке
        user_id = event.object.user_id  # определяем пользователя
        if event.object.payload.get('type') == 'open_link':  # встроенное действие:
            r = bot.method('messages.sendMessageEventAnswer', {
                "event_id": event.object.event_id,
                "user_id": event.object.user_id,
                "peer_id": event.object.peer_id,
                "event_data": json.dumps(event.object.payload)})

        # elif event.object.payload.get('type') == 'run_search':  # кнопка Искать
        #     run_search(user_id)
        elif event.object.payload.get('type') == 'add_favorite':  # кнопка Нравится
            actual_profile = profile_list[0]  # активный профайл
            mes_text = f"Кандидат {actual_profile['first_name']} {actual_profile['last_name']}"
            mes_attach = 'photo' + actual_profile['photo_id']  # фото из профайла
            db.add_profiles(session, profile_list[0], True, user_id)  # записываем профайл в бд
            profile_list.pop(0)  # удаляем профайл из списка
            # редактируем сообщение и отправляем пользователю новую клавиатуру
            keyboard_favorite['buttons'][0][0]['action']['link'] = 'https://vk.com/id' + str(actual_profile['id'])
            edit_keyboard = json.dumps(keyboard_favorite)
            r = bot.method('messages.edit', {
                "peer_id": event.obj.peer_id,
                "message": mes_text,
                "attachment": mes_attach,
                "conversation_message_id": event.obj.conversation_message_id,
                "keyboard": edit_keyboard})
            run_search(user_id)  # предлагаем новую кандидатуру

        elif event.object.payload.get('type') == 'add_blacklist':  # кнопка Не нравится
            actual_profile = profile_list[0]  # актуальный профайл
            db.add_profiles(session, profile_list[0], False, user_id)  # сохраняем в бд
            profile_list.pop(0)  # удаляем из списка
            # скрываем профайл в беседе
            r = bot.method('messages.edit', {
                "peer_id": event.obj.peer_id,
                "message": f"Пользователь {actual_profile['first_name']} {actual_profile['last_name']} скрыт",
                "conversation_message_id": event.obj.conversation_message_id})
            run_search(user_id)

        elif event.object.payload.get('type') == "add_friend":  # кнопка <добавить в друзья>
            actual_profile = profile_list[0]
            mes_attach = 'photo' + actual_profile['photo_id']
            mes_text = f"Кандидат {actual_profile['first_name']} {actual_profile['last_name']}"
            # отправляем запрос на добавление в друзья
            if vk.friend_add(actual_profile['id'], "Давай знакомиться?") is True:
                r = bot.method('messages.edit', {
                    "peer_id": event.obj.peer_id,
                    "attachment": mes_attach,
                    "conversation_message_id": event.obj.conversation_message_id})
                write_msg(user_id, mes_text + " получил вашу заявку в друзья!")
