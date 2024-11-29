import telebot
from database import func_database
import nudenet
import os
import sys
from cordinates_of_cities import city_coords
import nudenet
from difflib import get_close_matches
import requests

def func_edit_profile(bot, chat_id, call, user_states, data_user):

    def func_back_menu(chat_id, text: str):
        markup_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back_menu = telebot.types.KeyboardButton('/menu')
        markup_menu.add(back_menu)
        user_states[chat_id] = "menu"
        bot.send_message(chat_id, text, reply_markup=markup_menu)


    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    user_states[call.message.chat.id] = "edit_prodile"
    markup_edit_profile = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    edit_name = telebot.types.KeyboardButton('/имя') #name age gender city photo purpose discription gender_search
    edit_age = telebot.types.KeyboardButton('/возраст')
    edit_gender = telebot.types.KeyboardButton('/пол')
    edit_purpose = telebot.types.KeyboardButton('/цель')
    edit_discription = telebot.types.KeyboardButton('/описание')
    edit_gender_search = telebot.types.KeyboardButton('/цель поиска')
    edit_photo = telebot.types.KeyboardButton('/фото')
    edit_city = telebot.types.KeyboardButton('/город')
    back_menu = telebot.types.KeyboardButton('/menu')

    markup_edit_profile.row(back_menu)
    markup_edit_profile.row(edit_name, edit_age)
    markup_edit_profile.row(edit_gender, edit_purpose)
    markup_edit_profile.row(edit_discription, edit_gender_search)
    markup_edit_profile.row(edit_photo, edit_city)

    bot.send_message(call.message.chat.id, "<b>Что хотите поменять?</b>", reply_markup=markup_edit_profile, parse_mode="HTML")


    data_user[call.from_user.id] = {
        "name": False, "gender": False,  
        "gender_search": False,
        "discription": False, "purpose": False,
        "age": False, "city": False,
        "photo": False, "id_user": False,
        "link_profile": False
    }

    @bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "edit_prodile")
    def handle_text(message):
        if message.text == '/имя':
            user_states[message.chat.id] = "edit_profile_name"
            bot.send_message(message.chat.id, "Введите новое имя:", reply_markup=telebot.types.ReplyKeyboardRemove())
            @bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "edit_profile_name")
            def name_edit(message):
                new_name = message.text
                if 2 <= len(new_name) <= 20: 
                    data_user[message.from_user.id]["name"] = new_name
                    func_database(message.chat.id, data_user, select_func="update_profile_field")
                    data_user[message.from_user.id]["name"] = False 
                    func_back_menu(message.chat.id, "Имя успешно обновлено.")

                else:
                    data_user[message.from_user.id]["name"] = False
                    bot.send_message(message.chat.id, "Имя не ликвидно, <b>попробуйте еще раз.</b> Максимальная длина имени <b>20</b> символов, а минимальная длина имени <b>2</b> символа", parse_mode="HTML")

        elif message.text == '/возраст':
            user_states[message.chat.id] = "edit_profile_age"
            bot.send_message(message.chat.id, "Сколько вам полных лет?", reply_markup=telebot.types.ReplyKeyboardRemove())
            @bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "edit_profile_age")
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
                        func_database(message.chat.id, data_user, select_func="update_profile_field")
                        data_user[message.from_user.id]["age"] = False 
                        func_back_menu(message.chat.id, "Возраст успешно обновлен.")

                except:  
                    data_user[message.from_user.id]["age"] = False  
                    bot.send_message(message.chat.id, "Произошла ошибка, попробуйте повторно указать ваш возраст, введя <b>число</b> от <b>10 до 99.</b>", parse_mode="HTML")

        elif message.text == '/пол':
                markup_gender_edit = telebot.types.InlineKeyboardMarkup()
                button_male_edit = telebot.types.InlineKeyboardButton("Мужской", callback_data="record_male_edit")
                button_female_edit = telebot.types.InlineKeyboardButton("Женский", callback_data="record_female_edit")
                markup_gender_edit.add(button_male_edit, button_female_edit)

                bot.send_message(message.chat.id, "Выбери пол", reply_markup=markup_gender_edit, parse_mode="HTML")

        elif message.text == '/цель':
            markup_purpose_edit = telebot.types.InlineKeyboardMarkup()
            button_communication_edit = telebot.types.InlineKeyboardButton("Общение", callback_data="record_communication_edit")
            button_friendship_edit = telebot.types.InlineKeyboardButton("Дружба", callback_data="record_friendship_edit")
            button_relationships_edit = telebot.types.InlineKeyboardButton("Отношения", callback_data="record_relationships_edit")
            markup_purpose_edit.row(button_communication_edit, button_friendship_edit)
            markup_purpose_edit.row(button_relationships_edit)

            bot.send_message(message.chat.id, "Выберите цель знакомства :", reply_markup=markup_purpose_edit)

        elif message.text == '/описание':
            user_states[message.chat.id] = "edit_profile_discription"
            bot.send_message(message.chat.id, "Напиши описание к своей анкете :", reply_markup=telebot.types.ReplyKeyboardRemove())
            @bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "edit_profile_discription")
            def discription_edit(message):
                max_length = message.text
                if len(max_length) <= 1500: 
                    data_user[message.from_user.id]["discription"] = message.text
                    func_database(message.chat.id, data_user, select_func="update_profile_field")
                    data_user[message.from_user.id]["discription"] = False 
                    func_back_menu(message.chat.id, "Описание успешно обновлено.")
                else:
                    data_user[message.from_user.id]["discription"] = False
                    bot.send_message(message.chat.id, "Описание не ликвидно, <b>попробуйте еще раз.</b> Максимальная длина описания <b>1500</b> символов", parse_mode="HTML")


        elif message.text == '/цель поиска':
            markup_gender_search_edit = telebot.types.InlineKeyboardMarkup()
            button_male_edit = telebot.types.InlineKeyboardButton("Мужчин", callback_data="record_male_search_edit")
            button_female_edit = telebot.types.InlineKeyboardButton("Женщин", callback_data="record_female_search_edit")
            markup_gender_search_edit.row(button_male_edit, button_female_edit)

            bot.send_message(message.chat.id, "Кого ты хочешь найти?", reply_markup=markup_gender_search_edit)

        elif message.text == '/menu':
            user_states[message.chat.id] = "menu"

        elif message.text == '/город':
            
            def city_edit(chat_id):
                bot.send_message(message.chat.id, "Введи свой город :")
                user_states[message.chat.id] = "edit_prodile_city"

                @bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "edit_prodile_city" and (data_user[message.from_user.id]["city"] == False))
                def city_edit(message):
                    max_length = message.text
                    if len(max_length) <= 60: 
                        if str(max_length).capitalize() in city_coords:
                            coords = city_coords[message.text.capitalize()]
                            city_with_coords = f"{message.text.capitalize()}, {coords[0]}, {coords[1]}"
                            data_user[message.from_user.id]["city"] = city_with_coords
                            func_database(message.chat.id, data_user, select_func="update_profile_field")
                            func_back_menu(message.chat.id, "Город успешно обновлен.")

                        else:
                            possible_cities = get_close_matches(str(max_length).capitalize(), city_coords.keys(), n=1, cutoff=0.6)

                            if possible_cities:
                                bot.send_message(message.chat.id, f"Возможно, вы имели в виду: <b>{possible_cities[0]}</b> \nМожете ввести название города еще раз, или выйти /menu:", parse_mode="HTML")

                            else:
                                bot.send_message(message.chat.id, 
                                                "Такого <b>города</b> в нашей базе данных нет.\n"
                                                "<b>Пожалуйста, убедитесь, что вы правильно ввели название города.</b>\n"
                                                "Если вы ошиблись, введите название еще раз, если хотите отправить gps\n"
                                                "Удалите профиль и создайте заново /menu",
                                                parse_mode="HTML")
                    else:
                        bot.send_message(message.chat.id, "Название вашего города слишком большое, попробуйте еще раз")

            city_edit(chat_id)

        elif message.text == '/фото':
            def save_photo_from_telegram(bot, file_id, user_id):
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                temp_file_path = f"temp_image_{user_id}.jpg"  # Уникальное имя файла
                with open(temp_file_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                return temp_file_path

            def photo_edit(chat_id):
                bot.send_message(message.chat.id, "Отправь свою фотографию", reply_markup=telebot.types.ReplyKeyboardRemove())
                bot.send_message(message.chat.id, "<b>Важно!</b> На фотографии отчетливо должно быть видно лицо.", parse_mode="HTML")

                @bot.message_handler(content_types=['photo'], func=lambda message: data_user[message.from_user.id]["photo"] is not None and user_states.get(message.chat.id) == "edit_profile") 
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
                            func_database(message.chat.id, data_user, select_func="update_profile_field")
                            func_back_menu(message.chat.id, "Фотография успешно обновлена.")
                        else:
                            bot.send_message(message.chat.id, "Лицо на фото не обнаружено, попробуйте повторно.")
                    else:
                        bot.send_message(message.chat.id, "На фото обнаружены недопустимые материалы, просьба отправить фотографию без наготы.")

                    os.remove(photo_path)

            photo_edit(chat_id)