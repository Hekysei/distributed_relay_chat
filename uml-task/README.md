# UML: distributed_relay_chat

Диаграмма классов отражает структуру репозитория [Hekysei/distributed_relay_chat](https://github.com/Hekysei/distributed_relay_chat) (Python, WebSocket-релей и TUI-клиент).

## Проект

**Распределённый чат через релей:** сервер принимает WebSocket-подключения, маршрутизирует сообщения по именованным каналам (`Dispatcher` + `Channel`), клиент с curses-TUI подключается к релею, ведёт локальные представления чатов (`RemoteChat`, синхронизация `message_id` / `TimestampResponse`), служебный чат с ботом для команд (`/connect`, `/create`, `/join` и т.д.).

## Архитектурные решения

1. **Слой пакетов (`Package`, `Message`, …)** — единый JSON-протокол; сериализация через dataclass + `to_json` / `from_json`, поле `type` выбирает класс при разборе.

2. **Фабрика пакетов (`PackageFactory`)** — таблица типов → классы плюс таблица типов → обработчики. На релее подставляется `RelayPackageFactory` (вход в `ClientHandler`), у клиента — `APPClientPackageFactory`. Так входящий JSON не размазывается по `if/else` по всему коду.

3. **Pub/Sub на релее** — `Dispatcher` владеет `Channel`; в канале словарь «имя пользователя → функция отправки сообщения этому сокету». Это соответствует комментариям в коде про DI и pub/sub.

4. **Разделение синхронного клиента и асинхронного релея** — `NetClient` блокирует поток в `recv`; TUI обновляется колбэками. Это осознанный компромисс для CLI-прототипа (в README проекта отмечена проблема curses + два потока).

5. **Бот и маршрутизация команд** — `Bot` + `CommandRouter` + `FuncArgsPair`: текст парсится в команду и именованные аргументы; на релее `RelayBot` регистрирует async-команды создания/входа в канал.

## Ответственности классов (кратко)

| Компонент | Роль |
|-----------|------|
| `Package` / `Message` / `TimestampResponse` / `SystemMessage` | Модель сообщений протокола. |
| `PackageFactory` (+ `Relay*`, `APPClient*`) | Разбор JSON и вызов нужного обработчика. |
| `Relay`, `Server`, `ConnectionHandler` | Жизненный цикл WebSocket на стороне релея. |
| `Dispatcher`, `Channel` | Каналы чата и рассылка подписчикам. |
| `ClientHandler`, `RelayBot` | Логика одного подключения к релею и сервисный бот `r/relay`. |
| `NetClient`, `Client`, `APPClient` | Сеть, чаты, специализация под приложение. |
| `Chat`, `RemoteChat`, `ChatBot` | Абстракция чата; удалённый чат с отложенной подстановкой timestamp. |
| `Bot`, `CommandRouter` | Команды в локальном/служебном чате. |
| `APP`, `TUI_Adapter` | Точка входа и curses-интерфейс. |

## Паттерны

| Паттерн | Где проявляется |
|---------|-----------------|
| **Template Method** | `PackageFactory.process_json` / `async_process_json`: общий алгоритм «определить тип → `from_json` → вызвать handler». |
| **Factory Method / абстрактная фабрика** | Подстановка `_handlers` в `RelayPackageFactory` и `APPClientPackageFactory`. |
| **Strategy / Callable** | Отправка сообщения подписчику через `Callable[[Message]]` без жёсткой привязки к WebSocket-классу. |
| **Adapter** | `TUI_Adapter` — интерфейс curses к `Client`. |
| **Observer (упрощённо)** | Колбэки `on_message_callback`, `on_chat_added_callback` на `Client` для обновления UI. |

## Файлы

- `class-diagram.pdf` — экспорт диаграммы.
- `class-diagram.puml` — исходник PlantUML (`!pragma layout smetana`, без Graphviz).

Пересборка PDF (при наличии `plantuml.jar` и venv с `img2pdf`):

```bash
java -jar plantuml.jar -tpng class-diagram.puml && img2pdf -o class-diagram.pdf class-diagram.png
```
