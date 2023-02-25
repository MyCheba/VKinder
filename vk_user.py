import time
import requests


class VKUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {'access_token': token,
                       'v': version
                       }

    def get_user_info(self, user_id):  # получаем данные из профиля пользователя по заданным полям
        metod_url = self.url + 'users.get'
        params = {
            'user_id': user_id,
            'fields': 'bdate, sex, city, interests, can_send_friend_request'
        }
        while True:
            response = requests.get(metod_url, params={**self.params, **params})
            if response.status_code == 200:  # если данные получены, оформляем в словарь
                result = response.json()
                if "response" in result.keys():
                    user_info = result['response'][0]
                    if "bdate" not in user_info.keys():
                        user_info.update({"bdate": None})
                    if "city" not in user_info.keys():
                        user_info.update({"city": {"id": None, "title": None}})
                    if "first_name" not in user_info.keys():
                        user_info.update({"first_name": None})
                    if "last_name" not in user_info.keys():
                        user_info.update({"last_name": None})
                    if "interests" not in user_info.keys():
                        user_info.update({"interests": None})
                    break
                else:
                    time.sleep(1)  # если блокировка по частоте запросов и нет ответа
        print("Данные пользователя", user_info)
        return user_info

    def get_city_id(self, city):  # получаем id города по названию
        metod_url = self.url + 'database.getCities'
        params = {
            'q': city,
            'count': 1
        }
        response = requests.get(metod_url, params={**self.params, **params}).json()
        if len(response['response']['items']) != 0:
            return response  # ['response']['items'][0]['id']

    def get_profiles(self, search_params):  # поиск профилей по параметрам
        metod_url = self.url + 'users.search'
        params = {
            'has_photo': 1,
            'count': 100,
            # 'city': search_params['city_id'],
            'city_id': search_params['city_id'],
            # 'hometown': search_params['city_name'],
            'sex': search_params['sex'],
            'status': [1, 5, 6],  # не женат (не замужем), всё сложно, в активном поиске
            'age_from': search_params['age_from'],
            'age_to': search_params['age_to'],
            'fields': 'photo_id'
        }
        response = requests.get(metod_url, params={**self.params, **params})
        if response.status_code == 200:
            result = response.json()
            if "response" in result.keys():  # если ответ получен, возвращаем результат
                count_profiles = len(result["response"]["items"])
                print("Найдено профилей:", count_profiles)
                return result

    def friend_add(self, user_id, message):  # отправить заявку в друзья
        metod_url = self.url + 'friends.add'
        params = {
            'user_id': user_id,
            'text': message
        }
        response = requests.get(metod_url, params={**self.params, **params})
        if response.status_code == 200:
            return True

    # def get_photos(self, user_id):
    #     photos_url = self.url + 'photos.get'
    #     photos_params = {
    #         'count': 1000,
    #         'user_id': user_id,
    #         'extended': 1,
    #         'foto_sizes': 1,
    #         'album_id': 'profile'
    #     }
    #     response = requests.get(photos_url, params={**self.params, **photos_params})
    #     if response.status_code == 200:
    #         return response.json()
    #     else:
    #         print(response.json())
