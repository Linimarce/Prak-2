from dotenv import load_dotenv
import os
import requests
import csv
import time
from pathlib import Path

load_dotenv()

TOKEN = os.environ.get("TOKEN")
API_VERSION = '5.199'

output_dir = Path(__file__).parent / "friends"
output_dir.mkdir(parents=True, exist_ok=True)

def main():
    print('Начало работы программы')
    group_list = get_group_list()
    for user_id in group_list:
        create_file_with_friends(user_id)

def get_group_list():
    file_path = "input.csv"
    group_list = []
    
    try:
        with open(file_path, encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]
            
            for line in lines:
                if line:
                    group_list.append(line)
                    
    except FileNotFoundError:
        print(f"Ошибка: файл {file_path} не найден.")
        exit(1)
    except Exception as e:
        print(f"Произошла ошибка при чтении файла: {e}")
        exit(1)
        
    if not group_list:
        print("Предупреждение: файл input.csv пустой или содержит только пустые строки.")
        
    return group_list


# Преобразует короткое имя (screen_name) в числовой ID
def get_numeric_id(token, screen_name):
    
    resolve_url = 'https://api.vk.com/method/utils.resolveScreenName'
    params = {
        'access_token': token,
        'screen_name': screen_name,
        'v': API_VERSION
    }
    response = requests.get(resolve_url, params=params).json()
    
    if 'response' in response and response['response']['type'] == 'user':
        return response['response']['object_id']
    else:
        raise ValueError(f"Не удалось найти пользователя с именем {screen_name}")

# Создаёт файл друзе пользователя
def create_file_with_friends(user_id):
    if user_id.isdigit():
        user_id = int(user_id)
    else:
        user_id = get_numeric_id(TOKEN, user_id)

    friends_url = 'https://api.vk.com/method/friends.get'
    params = {
        'access_token': TOKEN,
        'user_id': user_id,
        'fields': '',
        'v': API_VERSION
    }

    response = requests.get(friends_url, params=params).json()

    if 'error' in response:
        print(f"Ошибка API: {response['error']['error_msg']}")
    else:
        friends_list = response['response']['items']
    
    if not friends_list:
        print("Список друзей пуст.")
    else:
        all_friends_info = []
        
        for i in range(0, len(friends_list), 100):
            batch_ids = friends_list[i:i + 100]
            
            users_url = 'https://api.vk.com/method/users.get'
            user_params = {
                'access_token': TOKEN,
                'user_ids': ','.join(map(str, batch_ids)),
                'fields': 'first_name,last_name',
                'v': API_VERSION
            }
            
            user_response = requests.get(users_url, params=user_params).json()
            
            if 'error' in user_response:
                print(f"Ошибка при получении имен: {user_response['error']['error_msg']}")
                continue
                
            all_friends_info.extend(user_response['response'])
            
            time.sleep(0.35) # Не более 3 запросов в секунду

        output_file = output_dir / f'{user_id}.csv'
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Имя', 'Фамилия'])
            for friend in all_friends_info:
                writer.writerow([
                    friend['id'],
                    friend['first_name'],
                    friend['last_name']
                ])
        
        print(f"✅ Файл успешно сохранен: {output_file} ({len(all_friends_info)} друзей)")

main()