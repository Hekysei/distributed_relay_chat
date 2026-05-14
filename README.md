## Распределённый релей чат
Проект по дисциплине "Основы ИТ технологий".
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/f6aba8dc-c5b1-47d6-bfe7-25a1da112ffe" />

## Установка и запуск

1. Клонируйте репозиторий и перейдите в папку проекта:
   ```bash
   git clone https://github.com/Hekysei/distributed_relay_chat.git
   cd distributed_relay_chat
   ```

2. Установите зависимости:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # или venv\Scripts\activate для Windows
   pip install -r requirements.txt
   ```

3. Запустите сервер (релей):
   ```bash
   python3 relay.py
   ```

4. В новом терминале запустите TUI-клиент:
   ```bash
   python3 tui_client.py
   ```

## Docker

Нужны установленный [Docker](https://docs.docker.com/engine/install/) и плагин Compose (часто поставляется вместе с Docker Desktop или пакетом `docker-compose`).

Из корня репозитория:

```bash
docker compose up --build
```

Поднимутся два сервиса: **relay** (WebSocket на порту **12021**) и **moderator** (подключается к relay по внутреннему имени сервиса `relay`). Клиенты с вашей машины подключаются к адресу `ws://localhost:12021`.

Запуск в фоне и просмотр логов:

```bash
docker compose up -d --build
docker compose logs -f relay moderator
```

Остановка:

```bash
docker compose down
```

Если порт 12021 занят, измените проброс в `docker-compose.yml` (например `"12022:12021"`) и укажите клиентам внешний порт **12022**.

## TODO
- Адекватно решить проблему curses и двух потоков



### UML
Подробности и паттерны — в [uml-task/README.md](uml-task/README.md).

![Диаграмма классов](uml-task/class-diagram.svg)

- [PDF](uml-task/class-diagram.pdf)
- [PlantUML](uml-task/class-diagram.puml)
