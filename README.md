## VKinder - бот для романтических знакомств в социальной сети VK. 
***
### Для работы бота нужно: 
1. создать открытое сообщество в VK
2. получить токен группы
3. в настройках группы включить бота
4. дать разрешения на работу с сообщениями.
5. база данных *postgressql*

### Для взаимодействия с ботом используются две команды:
- искать
- параметры

Для работы с командами можно использовать встроенную клавиатуру, но она долго обрабатывает ответ и пока адекватного решения проблемы не найдено.
Поэтому в реализации диалог идет через написание команд в чате.

### Работать с ботом могу одновременно несколько пользователей.
Каждый пользователь, начавший диалог, заносится в базу данных.
При команде "искать" у пользователя будут запрошены параметры поиска автоматически:
- пол (мужской, женский, любой (м/ж/л), 
- минимальный возраст для поиска,
- максимальный возраст для поиска,
- город для поиска.

Параметры поиска заносятся в базу данных с ключом пользователя в таблицу *params*.

### В поиске профилей также используются дополнительные параметры:
- *has_photo* (наличие фото профиля обязательно)
- *status* [1, 5, 6] (не женат (не замужем), всё сложно, в активном поиске)
- *photo_id* (дополнительное поле для получения ссылки на фото)

Все найденные по заданным параметрам профили сохраняются в файле .*json*
Далее из файл .*json* профили записываются в БД в таблицу *profiles*, в которой составной ключ (код профиля и код параметров поиска), так как один и тот же профайл может быть отправлен разным пользователям.

Бот считывает одну запись из БД и ответном собщении отправляет фото профиля с описанием кандидата - *имя, фамилия, город, возраст и интересы*, если они заполнены в профайле.
На фото пользователя можно кликнуть и поставить лайк этому фото (это действия по-умолчанию).

Также к сообщению с фото привязана клавиатура с двумя кнопками для реакции пользователя - *"нравится"* и *"не нравится"*. 

Если пользователь нажимает *"нравится"*, клавиатура меняется на ссылку этого профиля.
Если нажимается кнопка *"не нравится"*, то фото профиля скрывается от пользователя.

После реакции пользователя, следующий профиль подгружается автоматически.

### Пользователь может изменить параметры поиска командой "параметры".
Для сокращения обращений к БД используется словарь, в котором хранятся активные пользователи, последние заданные параметры поиска и последний показанный профиль. 

### Имеющиеся проблемы:
1. Несмотря на то, что в метод *users.search* передается параметр *city_id*, в результатах поиска появляются города, не соответствующие городу поиска.
Скорее всего *city_id* ищет по какому-то параметру "родной город" или еще что-то, точного объяснения нет. Использовались параметры: *city* и *hometown*,
результаты поиска сильно сокращались.
2. Не решена проблема точного вычисления возраста по параметру *bdate* для описания профайла.

Используется код:

    bdate = datetime.strptime(profile['bdate'], "%d.%m.%Y")
    today = datetime.today()
    age = round((today - bdate).days/365)
    
В результате, если человеку на сегодняшний день 40 лет, но в этом году будет 41, он корректно попадает в поиск с максимальным возрастом 40,
но в описании bot указывает именно 41.

3. Долгий ответ от встроенной клавиатуры в диалоге. Нет решения.
