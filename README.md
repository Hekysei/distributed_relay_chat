## Распределённый чат
Проект по дисциплине "Основы ИТ технологий".

**Для запуска на виндоус требуются дополнительные зависимости из win_requirements.txt**

### Состояние:
- Прототип cli.

## TODO
- Адекватно решить проблему curses и двух потоков
```mermaid

### Не соотвествует реальности, но похоже (нейрослоп)
classDiagram
    %% Группа: Данные
    class Message {
        +str chat
        +str author
        +str text
        +datetime timestamp
        +set_time()
    }

    %% Группа: Логика бота
    class CommandRouter {
        +dict commands_dict
        +route(text)
        +parse_args()
    }
    class Bot {
        +CommandRouter command_router
        +on_text(text)
    }
    class Chat {
        +str name
        +list messages
        +send_message(msg)
    }
    class ChatBot {
        +Bot bot
    }
    Chat <|-- ChatBot
    ChatBot *-- Bot
    Bot *-- CommandRouter

    %% Группа: Сеть
    class NetClient {
        +WebSocket ws
        +connect(ip, port)
        +send(msg)
        +recv_loop()
    }
    class Server {
        +set active_connections
        +run()
    }
    class Relay {
        +Server server
        +start_handler(ws)
    }
    Relay *-- Server

    %% Группа: Приложение (Клиент)
    class Client {
        +NetClient net_client
        +dict chats
        +connect_to_relay()
    }
    class APPClient {
        +ClientChatBot chat_bot
    }
    Client <|-- APPClient
    Client *-- NetClient
    APPClient *-- ClientChatBot

    %% Группа: Интерфейс
    class TUI_Adapter {
        +APPClient client
        +window msg_win
        +window inp_win
        +run()
        +update_messages()
    }
    class APP {
        +APPClient client
        +TUI_Adapter tui_adapter
        +run()
    }
    APP *-- APPClient
    APP *-- TUI_Adapter
    TUI_Adapter o-- APPClient : "управляет"

    %% Связь данных
    Message ..> Chat : "хранится в"
```
