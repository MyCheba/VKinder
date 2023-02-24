keyboard_candidate = {"inline": True, "buttons": [[{"action": {"type": "callback", "label": "Нравится", "payload": {"type": "add_favorite"}}, "color": "positive"}, {"action": {"type": "callback", "label": "Не нравится", "payload": {"type": "add_blacklist"}}, "color": "negative"}]]}
keyboard_favorite = {"inline": True, "buttons": [[{"action": {"type": "open_link", "link": "", "label": "Открыть профиль"}}]]}
keyboard_gender = {"inline": False, "buttons": [[{"action": {"type": "text", "label": "мужчина"}},{"action": {"type": "text","label": "женщина"}}]]}
keyboard_main = {"one_time": False, "buttons": [[{"action": {"type": "callback", "label": "Параметры", "payload": {"type": "change_search_param"}}}], [{"action": {"type": "callback", "label": "Искать", "payload": {"type": "run_search"}}}]]}
# {"action": {"type": "callback", "label": "Добавить в друзья", "payload": {"type": "add_friend"}

