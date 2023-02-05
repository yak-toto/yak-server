#!/bin/bash
. .flaskenv

current_date=$(date +"%d-%m-%Y")
current_time=$(date +"%H:%M")
current_datetime=${current_date}T${current_time}
file_name=util/backup_files/yak_toto_backup_$current_datetime.sql

mysqldump yak_toto -u $MYSQL_USER_NAME --password=$MYSQL_PASSWORD > $file_name

if [ -f $file_name ]; then
    curl --location --request GET 'https://api.telegram.org/bot'$BOT_TOKEN'/sendMessage' \
    -s -o /dev/null \
    --header 'Content-Type: application/json' \
    --data-raw '{
        "chat_id": '$CHAT_ID',
        "text": "Backup done on '$current_date' at '$current_time'"
    }'
else
    curl --location --request GET 'https://api.telegram.org/bot'$BOT_TOKEN'/sendMessage' \
    -s -o /dev/null \
    --header 'Content-Type: application/json' \
    --data-raw '{
        "chat_id": '$CHAT_ID',
        "text": "Something went wrong when backup on '$current_date' at '$current_time'"
    }'
fi
