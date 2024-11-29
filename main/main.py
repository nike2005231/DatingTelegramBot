import json
import telebot
import sys
import other_files.text as tx
import cv2
import os
import re
import requests
from edit_profile import func_edit_profile
from database import func_database, admin_func
import nudenet
import io
from cordinates_of_cities import city_coords
import threading
from difflib import get_close_matches

data_user = {}
user_states = {}
view_profile = {}
current_chat_id = None

admin_ids = ["6491217944","633986877"]

def func_back_menu(chat_id, text: str):
    markup_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back_menu = telebot.types.KeyboardButton('/menu')
    markup_menu.add(back_menu)
    user_states[chat_id] = "menu"
    bot.send_message(chat_id, text, reply_markup=markup_menu)

with open("/home/nikita_user/dating_telegram_bot/main/other_files/config.json") as f:
    data_json = json.load(f)

bot = telebot.TeleBot(data_json['token'])

@bot.message_handler(commands=["data"])
def start(message):
    text_data = "Информация о пользователе:\n<b>Указанные вами данные</b>\n- Имя\n- Пол\n- Интересы\n- Возраст\n- Описание\n- Фотография\n<b>Данные предоставленные телеграммом</b> \n- Уникальный id пользователя\n- Имя пользователя\n- Фамилия пользователя\n- Имя пользователя в чате\n- Код языка пользователя\n- Фотография профиля пользователя\n- Статус пользователя\n- Разрешения чата пользователя\n- Время последнего онлайна пользователя"
    bot.send_message(message.chat.id, f"{text_data}", parse_mode = "HTML")
    func_back_menu(message.chat.id, "._.")


def is_admin(user_id):
    return str(user_id) in admin_ids

#admin
@bot.message_handler(commands=['admin'])
def admin_handler(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "У вас нет прав для использования этой команды.")
        return

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    item_sql = telebot.types.KeyboardButton('SQL Запрос')
    item_warn = telebot.types.KeyboardButton('Предупредить всех')
    item_stat = telebot.types.KeyboardButton('Статистика')
    markup.row(item_sql, item_warn, item_stat)

    bot.send_message(message.chat.id, "Выберите режим администратора:", reply_markup=markup)
    user_states[message.chat.id] = "admin_mode"


# Обработчик команды /admin для администраторов
def is_admin(user_id):
    return str(user_id) in admin_ids

@bot.message_handler(commands=['admin'])
def admin_handler(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "У вас нет прав для использования этой команды.")
        return

    func_back_admin_menu(message.chat.id, "Выберите режим администратора:")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "admin_mode")
def handle_admin_commands(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "У вас нет прав для использования этой команды.")
        return

    if message.text == 'SQL Запрос':
        bot.send_message(message.chat.id, "Введите SQL запрос:")
        bot.register_next_step_handler(message, handle_sql_query)
    elif message.text == 'Предупредить всех':
        bot.send_message(message.chat.id, "Введите сообщение для всех пользователей:")
        bot.register_next_step_handler(message, handle_warn_all)
    elif message.text == 'Статистика':
        try:
            users_count, user_likes_count = admin_func(select_func="sql_statistic")
            bot.send_message(message.chat.id, f"\nПрофилей создано - {users_count}\nВзаимные симпатии - {user_likes_count}\n")
        except Exception as ex:
            bot.send_message(message.chat.id, f"Произошла ошибка: {ex}")
    elif message.text == 'Выход':
        func_back_menu(message.chat.id, "Вы вышли из администраторского меню.")
    else:
        bot.send_message(message.chat.id, "Неизвестная команда. Попробуйте снова.")

def handle_sql_query(message):
    try:
        sql_query = message.text
        result = admin_func(select_func="sql_request", sql_request=sql_query)
        bot.send_message(message.chat.id, f"Результат запроса:\n{result}")
    except Exception as ex:
        bot.send_message(message.chat.id, f"Произошла ошибка: {ex}")

def handle_warn_all(message):
    try:
        users_id = admin_func(select_func="receive_users_id")
        warning_message = message.text
        for user_id in users_id:
            bot.send_message(user_id[0], f"⚠️Администрация⚠️\n{warning_message}")
        bot.send_message(message.chat.id, "Сообщение отправлено всем пользователям.")
    except Exception as ex:
        bot.send_message(message.chat.id, f"Произошла ошибка: {ex}")
#admin

@bot.message_handler(commands=["start", "menu"])
def start(message):
    global current_chat_id
    current_chat_id = message.chat.id

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    item_profile = telebot.types.KeyboardButton('Профиль 👤')
    item_group = telebot.types.KeyboardButton('Группа 💬')
    item_support = telebot.types.KeyboardButton('Поддержка 🛠️')
    item_settings = telebot.types.KeyboardButton('Смотреть анкеты 🥰')
    item_mutual_likes = telebot.types.KeyboardButton('Cимпатии ❤️')
    item_donate = telebot.types.KeyboardButton('Поддержать автора 💸')
    markup.row(item_mutual_likes)
    markup.row(item_settings, item_profile)
    markup.row(item_group, item_support)
    markup.row(item_donate)

    user_states[message.chat.id] = "menu"

    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

def send_profile(chat_id, profile, profile_count, total_profiles):
    text_photo = f"<b>{profile[2]}, {profile[4]}, {profile[5].split(',')[0]}, {profile[7]}</b>\n{profile[8]}\nМожете написать: {profile[1]}"
    markup = telebot.types.InlineKeyboardMarkup()
    if profile_count < total_profiles - 1:
        next_button = telebot.types.InlineKeyboardButton("Следующий", callback_data=f"next_profile_{profile_count + 1}")
        markup.add(next_button)
    bot.send_photo(chat_id, profile[6], caption=text_photo, parse_mode="HTML", reply_markup=markup)


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "menu")
def handle_text(message):
    global user_states, view_profile

    if message.text == 'Поддержать автора 💸':
        token = 'gNUwJTXeNKsF4QXWhDuY'

        support_link = "https://www.donationalerts.com/r/nike1999"
        bot.send_message(message.chat.id, f"Вы можете поддержать автора по следующей ссылке: {support_link}")

    elif message.text == 'Cимпатии ❤️':
        if func_database(message.chat.id, data_user, select_func="check_like_profile"):
            profiles = func_database(message.chat.id, data_user, select_func="viewing_profiles_like")
            if profiles:
                view_profile[message.chat.id] = {"count": 0, "data": profiles}
                func_back_menu(message.chat.id, "Ваши взаимные симпатии:")
                send_profile(message.chat.id, profiles[0], 0, len(profiles))
            else:
                bot.send_message(message.chat.id, "Симпатий пока нет, ожидайте лайков")
        else:
            bot.send_message(message.chat.id, "Симпатий пока нет, ожидайте лайков")


    elif message.text == 'Профиль 👤':
        result = func_database(message.chat.id, data_user, select_func="checking_the_profile")
        if result:
            markup_change = telebot.types.InlineKeyboardMarkup()
            
            button_change = telebot.types.InlineKeyboardButton("Изменить профиль", callback_data="edit_profile")
            button_delete_profile = telebot.types.InlineKeyboardButton("Удалить профиль", callback_data="check_delete_profile")
            markup_change.add(button_change) 
            markup_change.add(button_delete_profile) 
            
            date_bd = func_database(message.chat.id, data_user, select_func="send_profile_user")
            text_photo = f"<b>{date_bd[1]}, {date_bd[2]}, {date_bd[3].split(', ')[0]}, {date_bd[4]}</b>\n{date_bd[5]}" 
            bot.send_photo(message.chat.id, date_bd[0], caption=text_photo, parse_mode="HTML", reply_markup=markup_change)
            
        else:
            user_states[message.chat.id] = "creating_profile"
            start_info(message)


    elif message.text == 'Группа 💬':
        markup_group = telebot.types.InlineKeyboardMarkup()
        button_group = telebot.types.InlineKeyboardButton("Заходи у нас весело!!!", url="https://t.me/Encounter_Circle")
        markup_group.add(button_group)
        bot.send_message(message.chat.id, "<b>Нажмите на кнопку, чтобы присоединиться к группе!</b>", reply_markup=markup_group, parse_mode="HTML")

    elif message.text == 'Поддержка 🛠️':

        markup_support = telebot.types.InlineKeyboardMarkup()
        button_support = telebot.types.InlineKeyboardButton("Did_try", url="https://t.me/Did_try")
        markup_support.add(button_support)
        bot.send_message(message.chat.id, "<b>Нажмите на кнопку, для обращения в техническую поддержку:</b>", reply_markup=markup_support, parse_mode="HTML")

    elif message.text == 'Смотреть анкеты 🥰':
        result = func_database(message.chat.id, data_user, select_func="checking_the_profile")

        if result:
            user_states[message.chat.id] = "view_profiles"

            markup_view_profiles = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            item_dislike = telebot.types.KeyboardButton('👎')
            item_like = telebot.types.KeyboardButton('❤️')
            item_exit = telebot.types.KeyboardButton('❌')
            item_message = telebot.types.KeyboardButton('💬')
            markup_view_profiles.row(item_like, item_message, item_dislike)
            markup_view_profiles.row(item_exit)

            view_profile[message.chat.id] = {"count": 0, "data": func_database(message.chat.id, data_user, select_func="viewing_profiles")}

            def view_profile_func(chat_id, number_profile:int): #view_profile[message.chat.id]['data'][view_profile[message.chat.id]['count']]
                global view_profile, text_photo
                if view_profile[chat_id]['count'] == len(view_profile[chat_id]['data']): #тут -1 въебать если шо то ломанеться
                    func_back_menu(chat_id, "Анкеты закончились, подождите некоторое время для возобновления списка.")

                else:
                    profile_data = view_profile[chat_id]['data'][number_profile]
                    photo = profile_data[1]
                    name = profile_data[2]
                    age = profile_data[3]
                    city = profile_data[4].split(',')[0]
                    purpose = profile_data[5]
                    description = profile_data[6]
                    distance = profile_data[7]

                    text_photo = f"<b>{name}, {age}, {city}, {purpose}</b>\n{description}\n{distance}"
                    bot.send_photo(chat_id, photo, caption=text_photo, parse_mode="HTML", reply_markup=markup_view_profiles)

            
            view_profile_func(message.chat.id, view_profile[message.chat.id]['count'])

            @bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "view_profiles")
            def handle_text(message):
                global user_states, view_profile

                if message.text == '👎':
                    if view_profile[message.chat.id]['count'] < len(view_profile[message.chat.id]['data']):
                        view_profile[message.chat.id]['count'] += 1
                        profile_data = view_profile[message.chat.id]['data'][view_profile[message.chat.id]['count']-1]
                        func_database(message.chat.id, data_user, select_func="viewed_profiles", id_profile=profile_data[0])
                        view_profile_func(message.chat.id, view_profile[message.chat.id]['count'])
                    else:
                        func_back_menu(message.chat.id, "Анкеты закончились, подождите некоторое время для возобновления списка.")


                elif message.text == '💬':
                    bot.send_message(message.chat.id, "Напишите письмо пользователю ;)")
                    user_states[message.chat.id] = "view_profiles_send_message"

                    @bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "view_profiles_send_message")
                    def handle_message(message):
                        global user_states
                        if not message.text:
                            bot.send_message(message.chat.id, "Пожалуйста, напишите письмо.")
                        else:
                            user_message = message.text
                            user_states[message.chat.id] = "view_profiles"

                            if view_profile[message.chat.id]['count'] < len(view_profile[message.chat.id]['data']):
                                view_profile[message.chat.id]['count'] += 1
                                profile_data = view_profile[message.chat.id]['data'][view_profile[message.chat.id]['count'] - 1]
                                view_profile_func(message.chat.id, view_profile[message.chat.id]['count'])
                                func_database(message.chat.id, data_user, select_func="viewed_profiles", id_profile=profile_data[0])

                                markup_like = telebot.types.InlineKeyboardMarkup()
                                button_like = telebot.types.InlineKeyboardButton("❤️", callback_data=f"like_profile_send_database_{message.chat.id}")
                                button_skip = telebot.types.InlineKeyboardButton("👎", callback_data=f"not_like_profile_send_database_{message.chat.id}")

                                markup_like.add(button_like, button_skip)

                                liked_profile_data = func_database(message.chat.id, data_user, select_func="send_profile_user")

                                text_photo = f"<b>Вам письмо!</b>\n💬 {user_message}\n<b>{liked_profile_data[1]}, {liked_profile_data[2]}, {liked_profile_data[3].split(',')[0]}, {liked_profile_data[4]}</b>\n{liked_profile_data[5]}"
                                bot.send_photo(profile_data[0], liked_profile_data[0], caption=text_photo, parse_mode="HTML", reply_markup=markup_like)
                            else:
                                func_back_menu(message.chat.id, "Анкеты закончились, подождите некоторое время для возобновления списка.")

                elif message.text == '❤️':
                    if view_profile[message.chat.id]['count'] < len(view_profile[message.chat.id]['data']):
                        view_profile[message.chat.id]['count'] += 1
                        profile_data = view_profile[message.chat.id]['data'][view_profile[message.chat.id]['count'] - 1]
                        view_profile_func(message.chat.id, view_profile[message.chat.id]['count'])
                        func_database(message.chat.id, data_user, select_func="viewed_profiles", id_profile=profile_data[0])

                        markup_like = telebot.types.InlineKeyboardMarkup()
                        button_like = telebot.types.InlineKeyboardButton("❤️", callback_data=f"like_profile_send_database_{message.chat.id}")
                        button_skip = telebot.types.InlineKeyboardButton("👎", callback_data=f"not_like_profile_send_database_{message.chat.id}")

                        markup_like.add(button_like, button_skip)

                        liked_profile_data = func_database(message.chat.id, data_user, select_func="send_profile_user")

                        text_photo = f"<b>Вам поставили лайк!\n{liked_profile_data[1]}, {liked_profile_data[2]}, {liked_profile_data[3].split(',')[0]}, {liked_profile_data[4]}</b>\n{liked_profile_data[5]}"
                        bot.send_photo(profile_data[0], liked_profile_data[0], caption=text_photo, parse_mode="HTML", reply_markup=markup_like)
                    
                    else:
                        func_back_menu(message.chat.id, "Анкеты закончились, подождите некоторое время для возобновления списка.")

                elif message.text == '❌':
                    markup_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
                    back_menu = telebot.types.KeyboardButton('/menu')
                    markup_menu.add(back_menu)
                    user_states[message.chat.id] = "menu"
                    bot.send_message(message.chat.id, "Действие закончено:", reply_markup=markup_menu)
        else:
            user_states[message.chat.id] = "creating_profile"
            start_info(message)

def start_info(message):
    markup = telebot.types.InlineKeyboardMarkup()
    button_start = telebot.types.InlineKeyboardButton("Начать", callback_data="switching_to_profile_editing")
    markup.row(button_start)

    photo_logo = open("/home/nikita_user/dating_telegram_bot/main/other_files/logo.jpg", "rb")
    text_photo = f"Привет <b>{message.chat.first_name}</b>! {tx.date_info['start_info_text']}"
    bot.send_photo(message.chat.id, photo_logo, text_photo, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def switching_to_profile_editing(call):
    global data_user, view_profile
    chat_id = call.message.chat.id
    user_states[call.message.chat.id] = "creating_profile"

    if call.data == "switching_to_profile_editing":
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, "Начнем", reply_markup=telebot.types.ReplyKeyboardRemove())

        data_user[call.from_user.id] = {
            "name": False, "gender": False,  
            "gender_search": False,
            "discription": False, "purpose": False,
            "age": False, "city": False,
            "photo": False, "id_user": False,
            "link_profile": False
        }
        username = call.from_user.username
        if username is None:
            msg = bot.send_message(chat_id, 
                "Ваше <b>имя пользователя</b> в Telegram не установлено.\n"
                "(@ username).\n"
                "Вы не сможете взаимодействовать с другими участниками бота.\n"
                "Пожалуйста, введите ваше имя пользователя в Telegram самостоятельно, чтобы при взаимном лайке человек мог вам написать.\n"
                "<b>Инструкция:</b>\n"
                "1. Нажмите на <b>три точки</b> в левом верхнем углу телеграма.\n"
                "2. Перейдите в <b>Настройки</b>.\n"
                "3. Выберите <b>Имя пользователя</b> и введите его. После этого заново зарегистрируйтесь."
            , parse_mode="HTML")
            func_back_menu(chat_id, "Попробуйте сначало")
        else:
            data_user[call.from_user.id]["link_profile"] = f"@{username}"
            data_user[call.from_user.id]["id_user"] = call.from_user.id
            name_edit(chat_id)

    elif call.data == "record_female":
        if data_user[call.from_user.id]["gender"] == False:
            data_user[call.from_user.id]["gender"] = "женский"
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            gender_search_edit(chat_id)
    
    elif call.data == "record_male":
        if data_user[call.from_user.id]["gender"] == False:
            data_user[call.from_user.id]["gender"] = "мужской"
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            gender_search_edit(chat_id)

    elif call.data == "record_male_search":
        if data_user[call.from_user.id]["gender_search"] == False:
            data_user[call.from_user.id]["gender_search"]  = "мужчин"
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            discription_profile(chat_id)

    elif call.data == "record_female_search":
        if data_user[call.from_user.id]["gender_search"]  == False:
            data_user[call.from_user.id]["gender_search"]  = "женщин"
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            discription_profile(chat_id)

    elif call.data == "record_communication":
        if data_user[call.from_user.id]["purpose"] == False:
            data_user[call.from_user.id]["purpose"] = "общение"
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            age_edit(chat_id)

    elif call.data == "record_friendship":
        if data_user[call.from_user.id]["purpose"] == False:
            data_user[call.from_user.id]["purpose"] = "дружба"
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            age_edit(chat_id)

    elif call.data == "record_relationships":
        if data_user[call.from_user.id]["purpose"] == False:
            data_user[call.from_user.id]["purpose"] = "отношения"
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            age_edit(chat_id)
    
    elif call.data == "everything_is_right":
        everything_is_right(chat_id, data_user)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)

    elif call.data == "fill_it_in_again":
        fill_it_in_again(chat_id)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)


    #Обработчики для удаления профиля
    elif call.data == "check_delete_profile":
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        user_states[call.message.chat.id] = "delete_profile"

        markup_check_delete = telebot.types.InlineKeyboardMarkup()
        button_check_yes = telebot.types.InlineKeyboardButton("Да", callback_data="delete_profile")
        button_check_no = telebot.types.InlineKeyboardButton("Нет", callback_data="not_delete_profile")
        markup_check_delete.row(button_check_yes, button_check_no)
        bot.send_message(call.message.chat.id, "❗<b>Вы уверены что хотите удалить профиль</b>❗", reply_markup=markup_check_delete, parse_mode="HTML")

    elif call.data == "delete_profile":
        func_database(call.message.chat.id, data_user, select_func="clear_viewed_profiles")
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        func_database(call.message.chat.id, data_user, select_func="delete_profile")
        func_back_menu(chat_id, "Профиль успешно удален.")
        
    elif call.data == "not_delete_profile":
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        func_back_menu(chat_id, "Действие закончено:")

    elif call.data == "back_city_edit":
        data_user[call.from_user.id]["city"] = False
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        city_edit(chat_id)

    elif call.data == "gps_send":
        data_user[call.from_user.id]["city"] = 1
        ask_gps_send(call.message.chat.id)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)


    #Шняга для редактирования профиля тут очень обидно не придумал как все перенести в edit_profile
    elif call.data == "edit_profile":
        func_database(call.message.chat.id, data_user, select_func="clear_viewed_profiles")
        func_edit_profile(bot, call.message.chat.id, call, user_states, data_user)

    elif call.data == "record_female_edit":
        if data_user[call.from_user.id]["gender"] == False:
            data_user[call.from_user.id]["gender"] = "женский"
            func_database(chat_id, data_user, select_func="update_profile_field")
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            func_back_menu(chat_id, "Пол успешно обновлен.")
            data_user[call.from_user.id]["gender"] = False

    elif call.data == "record_male_edit":
        if data_user[call.from_user.id]["gender"] == False:
            data_user[call.from_user.id]["gender"] = "мужской"
            func_database(chat_id, data_user, select_func="update_profile_field")
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            func_back_menu(chat_id, "Пол успешно обновлен.")
            data_user[call.from_user.id]["gender"] = False

    elif call.data == "record_communication_edit":
        if data_user[call.from_user.id]["purpose"] == False:
            data_user[call.from_user.id]["purpose"] = "общение"
            func_database(chat_id, data_user, select_func="update_profile_field")
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            func_back_menu(chat_id, "Цель успешно обновлена.")
            data_user[call.from_user.id]["purpose"] = False

    elif call.data == "record_friendship_edit":
        if data_user[call.from_user.id]["purpose"] == False:
            data_user[call.from_user.id]["purpose"] = "дружба"
            func_database(chat_id, data_user, select_func="update_profile_field")
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            func_back_menu(chat_id, "Цель успешно обновлена.")
            data_user[call.from_user.id]["purpose"] = False

    elif call.data == "record_relationships_edit":
        if data_user[call.from_user.id]["purpose"] == False:
            data_user[call.from_user.id]["purpose"] = "отношения"
            func_database(chat_id, data_user, select_func="update_profile_field")
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            func_back_menu(chat_id, "Цель успешно обновлена.")
            data_user[call.from_user.id]["purpose"] = False
    
    elif call.data == "record_male_search_edit":
        if data_user[call.from_user.id]["gender_search"] == False:
            data_user[call.from_user.id]["gender_search"]  = "мужчин"
            func_database(chat_id, data_user, select_func="update_profile_field")
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            func_back_menu(chat_id, "Цель поиска успешно обновлена.")
            data_user[call.from_user.id]["gender_search"] = False

    elif call.data == "record_female_search_edit":
        if data_user[call.from_user.id]["gender_search"]  == False:
            data_user[call.from_user.id]["gender_search"]  = "женщин"
            func_database(chat_id, data_user, select_func="update_profile_field")
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            func_back_menu(chat_id, "Цель поиска успешно обновлена.")
            data_user[call.from_user.id]["gender_search"] = False

    elif call.data.startswith("next_profile_"):
        profile_count = int(call.data.split("_")[-1])
        profiles = view_profile[chat_id]["data"]
        
        if profile_count < len(profiles):
            view_profile[chat_id]["count"] = profile_count
            bot.delete_message(chat_id, call.message.message_id)
            send_profile(chat_id, profiles[profile_count], profile_count, len(profiles))
        else:
            bot.answer_callback_query(call.id, "Это был последний профиль.")
    
    elif call.data.startswith("like_profile_send_database_"):
        sender_chat_id = int(call.data.split("_")[-1])
        profile_id = func_database(sender_chat_id, data_user, select_func="send_profile_user")

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        
        func_database(call.message.chat.id, data_user, select_func="like_profile", id_profile=profile_id[6])
        func_database(profile_id[6], data_user, select_func="like_profile", id_profile=call.message.chat.id)

        func_back_menu(call.message.chat.id, "Поставлен лайк, зайдите в симпатии.")
        bot.send_message(profile_id[6], "Кому-то понравилась твоя анкета!!!\nПерейди в <b>симпатии</b>", parse_mode="HTML")

    elif call.data.startswith("not_like_profile_send_database_"):
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        func_back_menu(chat_id, "Анкета пропущена.")


def ask_gps_send(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_geo = telebot.types.KeyboardButton(text="Отправить геолокацию", request_location=True)
    markup.add(button_geo)
    bot.send_message(chat_id, "Пожалуйста, отправьте свою геолокацию, нажав кнопку ниже.", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    if user_states.get(message.chat.id) == "creating_profile" and data_user[message.from_user.id]["city"] == 1:
        user_id = message.from_user.id
        latitude = message.location.latitude
        longitude = message.location.longitude
        
        response = requests.get(f"https://api.opencagedata.com/geocode/v1/json?q={latitude}+{longitude}&key={data_json["OPENCAGE_API_KEY"]}")
        result = response.json()
        
        if result['results']:
            components = result['results'][0]['components']
            city = components.get('city') or components.get('town') or components.get('village') or components.get('hamlet') or 'Unknown'
            full_location = f"{city}, {latitude}, {longitude}"
            data_user[user_id]["city"] = full_location
            full_location = None
            
            bot.send_message(message.chat.id, "Спасибо! Местоположение получено.", reply_markup=telebot.types.ReplyKeyboardRemove())
            
            photo_edit(message.chat.id)
            
        else:
            markup_back_write_coords_send = telebot.types.InlineKeyboardMarkup()
            button_back_write_coords_send = telebot.types.InlineKeyboardButton("Вернуться назад", callback_data="back_city_edit") 
            markup_back_write_coords_send.row(button_back_write_coords_send)
            bot.send_message(message.chat.id, "Не удалось определить название города. Пожалуйста, отправьте его снова, или вернитесь на шаг назад.", reply_markup=markup_back_write_coords_send)


def name_edit(chat_id):
    global data_user
    delete_message_bot = bot.send_message(chat_id, f"{tx.date_info["profile_edit_text"]}\n{tx.date_info["name_text"]}")
    @bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "creating_profile" and (data_user[message.from_user.id]["name"] == False))
    def name_edit(message):
        max_length = message.text
        if 2 <= len(max_length) <= 20: 
            data_user[message.from_user.id]["name"] = max_length
            gender_edit(message.chat.id)
        else:
            data_user[message.from_user.id]["name"] = False
            bot.send_message(message.chat.id, "Имя не ликвидно, <b>попробуйте еще раз.</b> Максимальная длина имени <b>20</b> символов, а минимальная длина имени <b>2</b> символа", parse_mode="HTML")

def gender_edit(chat_id):
    markup_gender = telebot.types.InlineKeyboardMarkup()
    button_male = telebot.types.InlineKeyboardButton("Мужской", callback_data="record_male")
    button_female = telebot.types.InlineKeyboardButton("Женский", callback_data="record_female")
    markup_gender.add(button_male, button_female)

    bot.send_message(chat_id, "Давай определимся с полом", reply_markup=markup_gender)

def gender_search_edit(chat_id):
    markup_gender_search = telebot.types.InlineKeyboardMarkup()
    button_male = telebot.types.InlineKeyboardButton("Мужчин", callback_data="record_male_search")
    button_female = telebot.types.InlineKeyboardButton("Женщин", callback_data="record_female_search")
    markup_gender_search.row(button_male, button_female)

    bot.send_message(chat_id, "Кого ты хочешь найти?", reply_markup=markup_gender_search)

def discription_profile(chat_id):
    bot.send_message(chat_id, "Теперь напиши описание к своей анкете :")
    @bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "creating_profile" and (data_user[message.from_user.id]["discription"] == False))
    def discription_edit(message):
        max_length = message.text
        if len(max_length) <= 1500: 
            data_user[message.from_user.id]["discription"] = message.text
            purpose_edit(message.chat.id)
        else:
            data_user[message.from_user.id]["discription"] = False
            bot.send_message(message.chat.id, "Описание не ликвидно, <b>попробуйте еще раз.</b> Максимальная длина описания <b>1500</b> символов", parse_mode="HTML")


def purpose_edit(chat_id):
    global data_user

    if data_user[chat_id]["gender"][0:3] == data_user[chat_id]["gender_search"][0:3]:
        markup_purpose = telebot.types.InlineKeyboardMarkup()
        button_communication = telebot.types.InlineKeyboardButton("Общение", callback_data="record_communication")
        button_friendship = telebot.types.InlineKeyboardButton("Дружба", callback_data="record_friendship")
        markup_purpose.row(button_communication, button_friendship)

    else:
        markup_purpose = telebot.types.InlineKeyboardMarkup()
        button_communication = telebot.types.InlineKeyboardButton("Общение", callback_data="record_communication")
        button_friendship = telebot.types.InlineKeyboardButton("Дружба", callback_data="record_friendship")
        button_relationships = telebot.types.InlineKeyboardButton("Отношения", callback_data="record_relationships")
        markup_purpose.row(button_communication, button_friendship)
        markup_purpose.row(button_relationships)

    bot.send_message(chat_id, "Выберите цель знакомства :", reply_markup=markup_purpose)
        
def age_edit(chat_id):
    bot.send_message(chat_id, "Сколько вам полных лет?")
    @bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "creating_profile" and (data_user[message.from_user.id]["age"] == False))
    def age_edit(message):
        try:
            type_int = int(message.text)
            if type_int <= 15:
                data_user[message.from_user.id]["age"] = False  
                bot.send_message(message.chat.id, "Возраст слишком <b>маленький</b>, попробуйте повторно.", parse_mode="HTML")

            elif type_int > 100:
                data_user[message.from_user.id]["age"] = False  
                bot.send_message(message.chat.id, "Возраст слишком <b>большой</b>, попробуйте повторно.", parse_mode="HTML")

            else:
                data_user[message.from_user.id]["age"] = message.text
                city_edit(message.chat.id)

        except:  
            data_user[message.from_user.id]["age"] = False  
            bot.send_message(message.chat.id, "Произошла ошибка, попробуйте повторно указать ваш возраст, введя <b>число</b> от <b>10 до 99.</b>", parse_mode="HTML")

def city_edit(chat_id):
    bot.send_message(chat_id, "Введи свой город :")
    @bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "creating_profile" and (data_user[message.from_user.id]["city"] == False))
    def city_edit(message):
        max_length = message.text
        if len(max_length) <= 60: 
            if str(max_length).capitalize() in city_coords:
                coords = city_coords[message.text.capitalize()]
                city_with_coords = f"{message.text.capitalize()}, {coords[0]}, {coords[1]}"
                data_user[message.from_user.id]["city"] = city_with_coords
                photo_edit(message.chat.id)

            else:
                possible_cities = get_close_matches(str(max_length).capitalize(), city_coords.keys(), n=1, cutoff=0.6)

                if possible_cities:
                    markup_option = telebot.types.InlineKeyboardMarkup()
                    button_gps = telebot.types.InlineKeyboardButton("Отправить gps кординаты", callback_data="gps_send")
                    markup_option.row(button_gps)

                    bot.send_message(message.chat.id, f"Возможно, вы имели в виду: <b>{possible_cities[0]}</b> \nМожете ввести название города еще раз, не нажимая на кнопку:", reply_markup = markup_option, parse_mode="HTML")

                else:
                    markup_input_selection = telebot.types.InlineKeyboardMarkup()
                    button_gps = telebot.types.InlineKeyboardButton("Отправить gps кординаты", callback_data="gps_send")
                    markup_input_selection.add(button_gps)

                    bot.send_message(message.chat.id, 
                                    "Такого <b>города</b> в нашей базе данных нет.\n"
                                    "<b>Пожалуйста, убедитесь, что вы правильно ввели название города.</b>\n"
                                    "Если вы ошиблись, не жмите на кнопку и введите название еще раз\n"
                                    "Если всё правильно, то можете:\n"
                                    "Предоставить свои GPS координаты, нажав на кнопку ниже.\n",
                                    parse_mode="HTML", reply_markup=markup_input_selection)
        else:
            bot.send_message(message.chat.id, "Название вашего города слишком большое, попробуйте еще раз")

# Создание временного файла фото для развертки в нейронку
def save_photo_from_telegram(bot, file_id, user_id):
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    temp_file_path = f"temp_image_{user_id}.jpg"  # Уникальное имя файла
    with open(temp_file_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    return temp_file_path

def photo_edit(chat_id):
    bot.send_message(chat_id, "Отправь свою фотографию")
    bot.send_message(chat_id, "<b>Важно!</b> На фотографии отчетливо должно быть видно лицо.", parse_mode="HTML")

    @bot.message_handler(content_types=['photo'], func=lambda message: data_user[message.from_user.id]["photo"] == False) # @bot.message_handler(content_types=['photo'])
    def handle_photo(message):
        file_id = message.photo[-1].file_id
        photo_path = save_photo_from_telegram(bot, file_id, message.from_user.id)

        nude_detector = nudenet.NudeDetector()
        result = nude_detector.detect(photo_path)
        if (len(result) == 0 or
            all(entry["class"] not in {'MALE_GENITALIA_EXPOSED', 'FEMALE_BREAST_EXPOSED',
                                        'MALE_GENITALIA_COVERED', 'FEMALE_GENITALIA_EXPOSED',
                                        'MALE_GENITALIA_PARTLY_EXPOSED', 'FEMALE_GENITALIA_PARTLY_EXPOSED',
                                        'MALE_ANUS', 'FEMALE_ANUS'} for entry in result)):
            if any(entry['class'] == 'FACE_FEMALE' for entry in result):
                data_user[message.from_user.id]["photo"] = file_id
                check_profile(message.from_user.id) 
            else:
                bot.send_message(message.chat.id, "Лицо на фото не обнаружено, попробуйте повторно.")
        else:
            bot.send_message(message.chat.id, "На фото обнаружены недопустимые материалы, просьба отправить фотографию без наготы.")

        os.remove(photo_path)

def check_profile(user_id):  
    markup = telebot.types.InlineKeyboardMarkup()
    button_good = telebot.types.InlineKeyboardButton("Все правильно", callback_data="everything_is_right")
    button_again = telebot.types.InlineKeyboardButton("Заполнить заново", callback_data="switching_to_profile_editing")
    markup.row(button_good)
    markup.row(button_again)

    text_photo = f"<b>{data_user[user_id]['name']}, {data_user[user_id]['age']}, {data_user[user_id]['city'].split(', ')[0]}, {data_user[user_id]['purpose']}</b>\n{data_user[user_id]['discription']}"  # Исправлено здесь

    bot.send_photo(user_id, data_user[user_id]["photo"], caption=text_photo, parse_mode="HTML", reply_markup=markup) 
        
def everything_is_right(chat_id, data_user):
    global user_states

    func_database(chat_id, data_user, select_func="send_database_profile")
    data_user[chat_id] = {}
    del data_user[chat_id]
    func_back_menu(chat_id, "Отлично!")

# bot.polling(none_stop=True)
if __name__ == "__main__":
    bot.send_message(6491217944, "Бот был перезапущен, пожалуйста, введите /start или /menu для продолжения взаимодействия.")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            func_back_menu(current_chat_id, f"Произошла ошибка, вернитесь в меню и при желании сообщите в поддержку.")
            bot.send_message(6491217944, f"Произошла ошибка у {current_chat_id}: {e}")
