import psycopg2
import json
from geopy.distance import geodesic

def extract_coordinates(location):
    parts = location.split(', ')
    city = parts[0]
    coordinates = (float(parts[1]), float(parts[2]))
    return city, coordinates

def calculate_distance(coord1, coord2):
    return geodesic(coord1, coord2).kilometers

def sorted_by_distance(data_bd, user_coords):
    distances = [(entry, calculate_distance(user_coords, extract_coordinates(entry[4])[1])) for entry in data_bd]
    distances.sort(key=lambda x: x[1])
    updated_data = [entry + (f"📍{distance:.0f} км",) for entry, distance in distances]
    return updated_data

def func_database(chat_id, data_user, select_func: str, id_profile: int = None):
    with open("/home/nikita_user/dating_telegram_bot/main/other_files/config.json") as f:
        data_json = json.load(f)

    try:
        connection = psycopg2.connect(
            host = data_json["host"],
            user = data_json["user"],
            password = data_json["password"],
            database = data_json["db_name"],
            client_encoding = data_json["encode"]
        )

        connection.autocommit = True

        if select_func == "send_database_profile": #1
            user_query = f"""
            INSERT INTO "user" (
                id_user, link_profile, name, gender, age, city
            )
            VALUES (                               
                {data_user[chat_id]["id_user"]}, '{data_user[chat_id]["link_profile"]}', '{data_user[chat_id]["name"]}', '{data_user[chat_id]["gender"]}', {data_user[chat_id]["age"]}, '{data_user[chat_id]["city"]}'
            )
            ON CONFLICT (id_user) DO UPDATE
            SET 
                link_profile = EXCLUDED.link_profile, 
                name = EXCLUDED.name, 
                gender = EXCLUDED.gender, 
                age = EXCLUDED.age, 
                city = EXCLUDED.city
            """
            profile_query = f"""
            INSERT INTO "profile" (
                id_user, photo, purpose, discription, gender_search
            )
            VALUES(
                {data_user[chat_id]["id_user"]}, '{data_user[chat_id]["photo"]}', '{data_user[chat_id]["purpose"]}', '{data_user[chat_id]["discription"]}', '{data_user[chat_id]["gender_search"]}'
            )
            ON CONFLICT (id_user) DO UPDATE
            SET
                photo = EXCLUDED.photo,
                purpose = EXCLUDED.purpose,
                discription = EXCLUDED.discription,
                gender_search = EXCLUDED.gender_search
            """

            with connection.cursor() as cursor:
                cursor.execute(user_query)
                cursor.execute(profile_query)
        
        elif select_func == "checking_the_profile": #2
            user_query = f"""
                SELECT EXISTS (
                SELECT 1
                FROM "user"
                WHERE id_user = {chat_id}
                );
            """

            with connection.cursor() as cursor:
                cursor.execute(user_query)
                result = cursor.fetchone()[0]
                return result
        

        elif select_func == "delete_profile":
            delete_profile_query = f"""
                DELETE FROM profile
                WHERE id_user = {chat_id};
            """
            delete_user_query = f"""
                DELETE FROM "user"
                WHERE id_user = {chat_id};
            """
            with connection.cursor() as cursor:
                cursor.execute(delete_profile_query)
                cursor.execute(delete_user_query)
                

        elif select_func == "update_profile_field":
            user_update_queries = []
            profile_update_queries = []
            
            user_fields = ["name", "gender", "age", "city", "link_profile"]
            profile_fields = ["photo", "purpose", "discription", "gender_search"]
            
            for field in user_fields:
                value = data_user[chat_id].get(field)
                if value not in [False, None, ""]:
                    update_query = f"""
                    UPDATE "user"
                    SET {field} = %s
                    WHERE id_user = %s;
                    """
                    user_update_queries.append((update_query, (value, chat_id)))

            for field in profile_fields:
                value = data_user[chat_id].get(field)
                if value not in [False, None, ""]:
                    update_query = f"""
                    UPDATE profile
                    SET {field} = %s
                    WHERE id_user = %s;
                    """
                    profile_update_queries.append((update_query, (value, chat_id)))
            
            with connection.cursor() as cursor:
                for query, params in user_update_queries:
                    cursor.execute(query, params)

                for query, params in profile_update_queries:
                    cursor.execute(query, params)
                
                connection.commit()



        elif select_func == "send_profile_user": #3
            user_query = f"""
                SELECT 
                    profile.photo,
                    "user".name,
                    "user".age,
                    "user".city,
                    profile.purpose,
                    profile.discription,
                    "user".id_user
                FROM 
                    "user"
                JOIN 
                    profile ON "user".id_user = profile.id_user
                WHERE 
                    "user".id_user = {chat_id};
            """

            with connection.cursor() as cursor:
                cursor.execute(user_query)
                data_bd = cursor.fetchone()
                return data_bd

        elif select_func == "viewing_profiles": #4
            my_query = f'select gender_search, purpose, "user".age, "user".city, "user".gender from profile, "user" where "user".id_user = {chat_id} and profile.id_user = {chat_id}'
            with connection.cursor() as cursor:
                cursor.execute(my_query)
                my_data = cursor.fetchone()
            gender_search_where = ""

            if my_data[4] == 'мужской' and my_data[0] == 'мужчин': # Мужик который ищет мужчин ему показываем только мужиков которые ищут мужиков
                gender_search_where = "\"user\".gender = 'мужской' and profile.gender_search = 'мужчин'"
            
            elif my_data[4] == 'мужской' and my_data[0] == 'женщин': # Мужик который ищет женщин ему показываем женщин которые ищут мужиков
                gender_search_where = "\"user\".gender = 'женский' and profile.gender_search = 'мужчин'"

            elif my_data[4] == 'женский' and my_data[0] == 'мужчин': # Женщина которая ищет мужчин ей показываем мужчин которые ищут женщин
                gender_search_where = "\"user\".gender = 'мужской' and profile.gender_search = 'женщин'"
            
            elif my_data[4] == 'женский' and my_data[0] == 'женщин': # Женщина которая ищет женщин ей показываем женщин которые ищут женщин
                gender_search_where = "\"user\".gender = 'женский' and profile.gender_search = 'женщин'"

            user_query = f"""
                SELECT 
                    "user".id_user,
                    profile.photo,
                    "user".name,
                    "user".age,
                    "user".city,
                    profile.purpose,
                    profile.discription
                FROM 
                    "user"
                JOIN
                    profile ON "user".id_user = profile.id_user
                WHERE
                    {gender_search_where} 
                    AND "user".id_user != {chat_id}
                    AND "user".id_user NOT IN (
                        SELECT profile_id
                        FROM viewed_profiles
                        WHERE mu_user_id = {chat_id}
                    )
                    AND "user".id_user NOT IN (
                        SELECT like_user 
                        FROM like_profiles
                        WHERE my_chat_id = {chat_id}
                    )
                """

            def sorted_age(data_bd, age):
                ages = [entry[3] for entry in data_bd]
                sorted_ages = sorted(ages, key=lambda x: abs(x - age))
                sorted_data = sorted(data_bd, key=lambda entry: sorted_ages.index(entry[3]))
                return sorted_data

            with connection.cursor() as cursor:
                cursor.execute(user_query)
                data_bd = cursor.fetchall()
                
                user_city, user_coords = extract_coordinates(my_data[3])
                
                sorted_by_age = sorted_age(data_bd, int(my_data[2]))

                sorted_result_with_distance = sorted_by_distance(sorted_by_age, user_coords)
                return sorted_result_with_distance 

        elif select_func == "viewed_profiles":
            profile_insert = f"""
            INSERT INTO viewed_profiles (mu_user_id, profile_id) VALUES ({int(chat_id)}, {int(id_profile)});
            """
            with connection.cursor() as cursor:
                cursor.execute(profile_insert)
                connection.commit()

        elif select_func == "clear_viewed_profiles":
            profile_clear = f"""
            DELETE FROM viewed_profiles 
            WHERE
            {int(chat_id)} = mu_user_id;
            """
            with connection.cursor() as cursor:
                cursor.execute(profile_clear)
                connection.commit()
            
        elif select_func == "like_profile":
            profile_add_like = f"""
            INSERT INTO like_profiles (my_chat_id, like_user) VALUES ({int(chat_id)}, {int(id_profile)});
            """
            with connection.cursor() as cursor:
                cursor.execute(profile_add_like)
                connection.commit()
        
        elif select_func == "check_like_profile":
            check_query = f"""
            SELECT COUNT(*) FROM like_profiles 
            WHERE like_user = {int(chat_id)};
            """
            
            with connection.cursor() as cursor:
                cursor.execute(check_query)
                count = cursor.fetchone()[0]
                if count > 0:
                    return True
                else:
                    return False
        elif select_func == "viewing_profiles_like":
            viewing_profiles_query = f"""
            SELECT u.id_user, u.link_profile, u.name, u.gender, u.age, u.city, p.photo, p.purpose, p.discription, p.gender_search
            FROM like_profiles lp
            JOIN "user" u ON lp.my_chat_id = u.id_user
            JOIN profile p ON u.id_user = p.id_user
            WHERE lp.like_user = {int(chat_id)};
            """
            
            with connection.cursor() as cursor:
                cursor.execute(viewing_profiles_query)
                profiles = cursor.fetchall()
                return profiles
                
    # except Exception as ex:
    #     print(f"Ошибка при подключении к базе данных:\n{ex}")
        
    finally:
        if connection:
            connection.close()

def admin_func(select_func:str, sql_request:str="1=1"):
    with open("/home/nikita_user/dating_telegram_bot/main/other_files/config.json") as f:
        data_json = json.load(f)

    try:
        connection = psycopg2.connect(
            host = data_json["host"],
            user = data_json["user"],
            password = data_json["password"],
            database = data_json["db_name"],
            client_encoding = data_json["encode"]
        )

        connection.autocommit = True

        if select_func == "receive_users_id":
            receive_id = 'select id_user from "user"'
            with connection.cursor() as cursor:
                cursor.execute(receive_id)
                users_id = cursor.fetchall()
                return users_id

        elif select_func == "sql_request":
            request = f"""
                    {sql_request}
                """
            with connection.cursor() as cursor:
                cursor.execute(request)
                users_id = cursor.fetchall()
                return users_id
        
        elif select_func == "sql_statistic":
            with connection.cursor() as cursor:
                user_count_query = 'SELECT COUNT(id_user) FROM "user"'
                cursor.execute(user_count_query)
                user_count = cursor.fetchone()[0]

                mutual_likes_query = 'SELECT COUNT(like_profiles_id) / 2 AS mutual_likes FROM like_profiles'
                cursor.execute(mutual_likes_query)
                mutual_likes_count = cursor.fetchone()[0]

                return user_count, mutual_likes_count

    finally:
        if connection:
            connection.close()