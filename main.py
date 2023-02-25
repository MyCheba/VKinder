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


def saved_user(db_session, new_user):  # сохраняем активного пользователя в базе
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


def get_request(botevent):  # перехватываем сообщения пользователя по новым параметрам поиска
    for item in botevent.listen():
        if item.type == VkBotEventType.MESSAGE_NEW:
            if item.obj.message['text'] != '':
                if item.from_user:
                    return item.obj.message['text'].lower()


def get_search_param(for_user):  # получаем параметры поиска из словаря
    while True:
        params = user_dict[for_user].get("params")
        if params is None:  # если параметры не заданы, запрашиваем новые параметры
            user_dict[for_user].update({"params": set_search_param(for_user)})
        else:
            break
    return params


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


def set_search_param(to_user):  # запрашиваем новые параметры для поиска
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
    print("Параметры поиска ", search_param)
    params_id = db.add_params(session, user_id, search_param)  # записываем параметры в базу
    search_param.update({"id": params_id})  # добавляем в словарь id параметров из БД
    mes_param = text_param(search_param)
    write_msg(user_id, mes_param, keyboard=keyboard_main)  # отправляем параметры поиска пользователю
    return search_param


def new_search(params):  # новый поиск по параметрам
    if len(profile_list) == 0:
        while True:
            result = vk.get_profiles(params)
            if result is not None:  # если есть результаты
                break
        with open('search.json', 'w') as file_json:
            json.dump(result, file_json)  # записываем в файл
    # count = db.add_profiles(session, params['id'])  # записываем в базу новые профайлы

        for item in result['response']['items']:
            if item not in profile_list and item['is_closed'] is False and 'photo_id' in item.keys():
                profile_list.append(item)
    return len(profile_list)  # count


def get_candidate(params):  # получить профайл
    while True:
        new_profile = db.get_new_profile(session, params['id'])  # читаем один профайл из базы
        if new_profile is None:  # если профайл в БД не найден, выполняем новый поиск по параметрам
            if new_search(params) == 0:
                break
        else:
            break
    return new_profile


def candidate_description(profile):  # описание кандидата для сообщения
    msg = f"Кандидат {profile['first_name']} {profile['last_name']}\n"  # фамилия, имя
    if profile['city']['title'] is not None:
        msg = msg + f"г.{profile['city']['title']}"  # город, если есть
    # age = datetime.today().year - int(profile['bdate'][-4:])
    if len(profile['bdate']) > 7:
        bdate = datetime.strptime(profile['bdate'], "%d.%m.%Y")
        today = datetime.today()
        age = round((today - bdate).days/365)  # вычисляем возвраст
        msg = msg + f" возраст {age}\n"
    interests = profile['interests']
    if interests is not None and len(interests) > 0:  # если в профиле заполнены интересы, выводим их
        if len(interests) > 100:
            dot = interests.find(".")
            interests = interests[:dot + 1]
        msg = msg + f"Интересы: {interests}"
    return msg


def run_search(to_user):  # команда поиск
    params = get_search_param(to_user)  # получаем параметры
    # profile = get_candidate(params)  # получаем один profile из таблицы
    if new_search(params) > 0:
        profile = profile_list[0]
        if profile is not None:
            profile_more = vk.get_user_info(profile['id'])  # получаем больше информации для профайла
            profile.update({
                "city": profile_more['city'],
                "bdate": profile_more['bdate'],
                "interests": profile_more['interests']  # обновляем словарь
            })
        user_dict[user_id].update({"profile": profile})  # запоминаем активный profile в словаре
        msg = candidate_description(profile)
        attachment = 'photo' + profile['photo_id']
        # отправляем пользователю фото кандидата с кнопками для реакции
        write_msg(to_user, msg, attachment, keyboard_candidate)
        print(user_dict)
    else:
        write_msg(to_user, "Профили не найдены, измените параметры.")


user_dict = {}  # словарь активных пользователей в сообществе
profile_list = []  # список профайлов
favorite_list = []  # белый список
black_list = []  # черный список

for event in botlongpoll.listen():  # получаем события от бота
    if event.type == VkBotEventType.MESSAGE_NEW:  # если сообщение
        if event.obj.message['text'] != '':  # не пустое
            if event.from_user:  # от пользователя

                user_id = event.obj.message['from_id']  # запоминаем id пользователя, от которого пришло сообщение
                user_info = db.get_user(session, user_id)  # получаем информацию о пользователе
                if user_info is None:  # если пользователь новый, то сохраняем в базу
                    user_info = saved_user(session, user_id)
                    user_dict.update({user_id: {}})  # добавляем юзера в словарь
                request = event.obj.message['text'].lower()  # получаем текст сообщения пользователя

                if request == "параметры":
                    user_dict[user_id].update({"params": set_search_param(user_id)})
                    run_search(user_id)
                elif request == "искать":
                    run_search(user_id)
                else:
                    # на любое другое сообщение отправляем пользователю приветствие
                    mes_hello = f"Привет {user_info['first_name']}!\n" \
                                f"Мне можно писать команды:\n" \
                                f"-искать (начать или продолжить поиск)\n" \
                                f"-параметры (задать или изменить параметры поиска)"
                    write_msg(user_id, mes_hello)

    elif event.type == VkBotEventType.MESSAGE_EVENT:  # событие по кнопке
        user_id = event.object.user_id  # определяем пользователя
        if event.object.payload.get('type') == 'open_link':  # встроенное действие:
            r = bot.method('messages.sendMessageEventAnswer', {
                "event_id": event.object.event_id,
                "user_id": event.object.user_id,
                "peer_id": event.object.peer_id,
                "event_data": json.dumps(event.object.payload)})

        elif event.object.payload.get('type') == 'change_search_param':  # кнопка Параметры
            user_dict[user_id].update({"params": set_search_param(user_id)})

        elif event.object.payload.get('type') == 'run_search':  # кнопка Искать
            run_search(user_id)

        elif event.object.payload.get('type') == 'add_favorite':  # кнопка Нравится
            # получаем активный профайл из словаря
            actual_profile = user_dict[user_id].get("profile")
            mes_text = candidate_description(actual_profile)
            mes_attach = 'photo' + actual_profile['photo_id']  # фото из профайла
            param = user_dict[user_id].get("params")
            # db.set_favorite(session, actual_profile['id'], param['id'])  # сохраняем в profile отметку favorite
            favorite_list.append(profile_list[0])
            profile_list.pop(0)
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
            # получаем активный профайл из словаря
            actual_profile = user_dict[user_id].get("profile")
            param = user_dict[user_id].get("params")  # получаем код параметров поиска из словаря
            # db.set_blacklist(session, actual_profile['id'], param['id'])  # сохраняем в бд отметку blacklist
            black_list.append(profile_list[0])
            profile_list.pop(0)
            # скрываем профайл в беседе и удаляем из словаря
            r = bot.method('messages.edit', {
                "peer_id": event.obj.peer_id,
                "message": f"Пользователь {actual_profile['first_name']} {actual_profile['last_name']} скрыт",
                "conversation_message_id": event.obj.conversation_message_id})
            user_dict[user_id].pop("profile")
            run_search(user_id)

        elif event.object.payload.get('type') == "add_friend":  # кнопка <добавить в друзья>
            actual_profile = user_dict[user_id].get("profile")
            mes_attach = 'photo' + actual_profile['photo_id']
            mes_text = f"Кандидат {actual_profile['first_name']} {actual_profile['last_name']}"
            # отправляем запрос на добавление в друзья
            if vk.friend_add(actual_profile['id'], "Давай знакомиться?") is True:
                r = bot.method('messages.edit', {
                    "peer_id": event.obj.peer_id,
                    "attachment": mes_attach,
                    "conversation_message_id": event.obj.conversation_message_id})
                write_msg(user_id, mes_text + " получил вашу заявку в друзья!")
                user_dict[user_id].pop("profile")  # удаляем из словаря актуальных профайлов
