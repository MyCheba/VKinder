from models import Users, Profiles, Params
import json


def get_user(session, user_id):  # получаем пользователя из бд по user_id
    user = session.query(Users).filter(Users.id == user_id).first()
    if user is not None:
        result = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "bdate": user.bdate,
            "sex": user.sex,
            "city_name": user.city_name
        }
        return result  # возвращаем словарь


def add_user(session, user_info):  # добавляем нового пользователя в бд
    new_user = Users(**{
        "id": user_info['id'],
        "bdate": int(user_info['bdate'][5:10]),
        "sex": user_info['sex'],
        "first_name": user_info['first_name'],
        "last_name": user_info['last_name'],
        "city_id": user_info['city']['id'],
        "city_name": user_info['city']['title'],
    })
    session.add(new_user)
    session.commit()
    print("Инициирована беседа с новым пользователем ", new_user.id)
    return new_user.id


def add_params(session, user_id, search_data):  # добавляем новые параметры поиска для пользователя
    new_param = Params(**{
        "user_id": user_id,
        "sex": search_data['sex'],
        "age_from": search_data['age_from'],
        "age_to": search_data['age_to'],
        "city_id": search_data['city_id']
    })
    session.add(new_param)
    session.commit()
    print("Добавлены параметры поиска для пользователя ", new_param.user_id)
    return new_param.param_id


def get_param(session, param_id=None, user_id=None):  # получаем параметры поиска из бд
    if param_id is None:  # если код параметров неизвестен, выбираем последние заданные параметры
        param = session.query(Params).filter(Params.user_id == user_id).order_by(Params.param_id.desc()).first()
    else:  # выбираем по коду параметров
        param = session.query(Params).filter(Params.param_id == param_id).first()
    if param is not None:
        result = {
            "id": param.param_id,
            "sex": param.sex,
            "age_from": param.age_from,
            "age_to": param.age_to,
            "city_id": param.city_id
        }
        return result  # возвращаем словарь


def add_profiles(session, param_id):  # добавляем новые профайлы в бд
    user_param = session.query(Params).filter(Params.param_id == param_id).first().user_id
    with open('search.json', 'r') as fd:
        data = json.load(fd)
    count_candidate = 0  # подсчет всех найденных кандидатов
    notclosed_candidate = 0  # количество открытых профилей
    new_candidate = 0  # сколько кандидатов добавлено в базу
    for record in data['response']['items']:
        count_candidate += 1
        if record['is_closed'] is False and 'photo_id' in record.keys() is not None:
            notclosed_candidate += 1
            exists = session.query(Profiles.id).join(Params).filter(
                Profiles.id == record['id'],
                Params.user_id == user_param).first()
            if exists is None:
                new_candidate += 1
                record.update({"favorite": False, "blacklist": False, "param_id": param_id})
                session.add(Profiles(**record))
    if new_candidate > 0:
        session.commit()
    print(f"Всего обработано записей: {count_candidate}\n"
          f"Незаблокировано профилей: {notclosed_candidate}\n"
          f"Добавлено профилей в БД: {new_candidate}")
    return new_candidate


def get_profile(session, p_id):  # получаем профайл по id
    result = session.query(Profiles).filter(Profiles.id == p_id).first()
    return result


def get_new_profile(session, param_id):  # получаем профайл еще не просмотренный пользователем
    profile = session.query(Profiles).filter(
                                        Profiles.param_id == param_id,
                                        Profiles.favorite == False,
                                        Profiles.blacklist == False
                                    ).first()
    if profile is not None:
        result = {
            "id": profile.id,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "photo_id": profile.photo_id
        }
        return result  # возвращаем в виде словаря


def set_favorite(session, profile_id, param_id):  # ставим отметку favorite в профайле
    c = session.query(Profiles).filter(Profiles.id == profile_id, Profiles.param_id == param_id).first()
    c.favorite = True
    session.commit()


def set_blacklist(session, profile_id, param_id):  # ставим отметку blacklist в профайле
    c = session.query(Profiles).filter(Profiles.id == profile_id, Profiles.param_id == param_id).first()
    c.blacklist = True
    # c.show = False
    session.commit()
    return c.blacklist
