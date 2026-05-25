#!/bin/sh
set -e

# Чиним владельца смонтированных директорий (bind-mounts перекрывают chown из Dockerfile)
for dir in /app/data /app/logs /app/uploads /app/themes; do
    if [ -d "$dir" ]; then
        chown -R appuser:appuser "$dir"
    fi
done

# Запускаем процесс от непривилегированного пользователя
exec gosu appuser "$@"
