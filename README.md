# homework_bot

### Описание проекта:

Учебный проект. Telegram-бот для оповещения об изменении статуса проверки заданий с функцией логирования.
Реализован на библиотеке telegram.


### Системные требования: 

python 3.7


### Шаблон наполнения env-файла:

Расположение файла: ./.env  

Данный файл используется для передачи в окружение приложения следующих переменных без их явного указания в коде:  

PRACTICUM_TOKEN=<токен API yandex.practicum>  
TELEGRAM_TOKEN=<токен используемого бота Telegram>  
TELEGRAM_CHAT_ID=<идентификатор пользователя для отправки сообщения>  


### Инструкция по запуску:

Создать виртуальное окружение:
```
python -m venv venv
```

Запустить виртуальное окружение:
```
source venv/Scripts/activate
```

Установить используемые библиотеки:
```
pip install -r requirements.txt
```

Запустить бота:
```
python homework.py
```


![example workflow](https://github.com/jd60-perm/homework_bot/actions/workflows/main.yml/badge.svg)
