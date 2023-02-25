from models import Users, Profiles


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


def add_profiles(session, profile, favorite, user_id):  # добавляет профайл в бд
    profile.update({"favorite": favorite, "id_user": user_id})
    session.add(Profiles(**profile))
    session.commit()
