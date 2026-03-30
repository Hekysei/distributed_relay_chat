## Распределённый чат
Проект по дисциплине "Основы ИТ технологий".

**Для запуска на виндоус требуются дополнительные зависимости из win_requirements.txt**

### Состояние:
- Прототип cli.

## TODO
- Адекватно решить проблему curses и двух потоков

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/f6aba8dc-c5b1-47d6-bfe7-25a1da112ffe" />


### Не соотвествует реальности, но похоже (нейрослоп)
```mermaid
classDiagram
    direction TB

    %% ==================== Пакеты ====================
    class Package {
        <<abstract>>
        +str type
        +to_json() str
        +from_json(json_str) Package$
    }

    class Message {
        +str chat
        +str sender
        +str text
        +int message_id
        +datetime timestamp
        +set_timestamp_now() Message
    }

    class TimestampResponse {
        +str chat
        +int message_id
        +datetime timestamp
        +from_message(msg) TimestampResponse$
    }

    class SystemMessage {
        +str msg_type
        +str body
    }

    Package <|-- Message
    Package <|-- TimestampResponse
    Package <|-- SystemMessage

    %% ==================== Фабрика пакетов ====================
    class PackageFactory {
        <<abstract>>
        #dict _classes
        #dict _handlers
        +get_handler_and_instance(json_str) tuple
        +process_json(json_str)
        +async_process_json(json_str)
    }

    class RelayPackageFactory {
        +__init__(connection_handler)
    }

    class APPClientPackageFactory {
        +__init__(client)
    }

    PackageFactory <|-- RelayPackageFactory
    PackageFactory <|-- APPClientPackageFactory

    %% ==================== Сервер ====================
    class Relay {
        -Server server
        -Dispatcher dispatcher
        +run()
        +start_handler(connection_handler)
    }

    class Server {
        -set~ServerConnection~ active_connections
        +on_connection_callback
        +handler_factory(ws)
        +run()
        +close_active_connections()
    }

    class ConnectionHandler {
        -WebSocket ws
        -PackageFactory package_factory
        +run()
        +send_message(msg)
        +send_tsr(tsr)
        +send_sys_message(sys_msg)
    }

    class ClientHandler {
        -str username
        -Dispatcher dispatcher
        -ConnectionHandler connection_handler
        -RelayBot bot
        +run()
        +on_msg(msg)
        +on_sys_msg(sys_msg)
        +send_text_to_client(text)
        +set_username(name)
    }

    class Dispatcher {
        -dict channels
        -dict users
        +send_message(msg, sender_func)
        +subscribe(channel, username, send_func)
        +unsubscribe(channel, username)
        +create_channel(channel, username, send_func)
        +call(msg)
    }

    class Channel {
        -dict members_funcs
        +send_message(msg, sender_func)
        +subscribe(username, send_func)
        +unsubscribe(username)
    }

    Dispatcher *-- Channel
    Relay *-- Server
    Relay *-- Dispatcher
    Server o-- ConnectionHandler : creates
    ConnectionHandler o-- PackageFactory : uses
    ClientHandler o-- Dispatcher : uses
    ClientHandler o-- ConnectionHandler : wraps
    ClientHandler o-- RelayBot : creates

    %% ==================== Клиент ====================
    class APP {
        -APPClient client
        -TUI_Adapter tui_adapter
        +run()
    }

    class TUI_Adapter {
        -curses.window stdscr
        -Client client
        -str input_buffer
        -str active_chat
        -int active_chat_idx
        +run()
        +iter()
        +update_messages()
        +update_input()
        +update_bar()
        +enter()
        +step_chat()
        +handle_chat_removed()
    }

    class APPClient {
        -APPClientChatBot chat_bot
        +__init__()
        +send_user_text(chat, text)
        +start_connection_thread(ip, port)
        +connect_to_relay(ip, port)
        +run_net_client()
    }

    class Client {
        #str username
        #dict chats
        #NetClient net_client
        #Thread connection_thread
        +on_message_callback
        +on_chat_added_callback
        +on_chat_removed_callback
        +connect_to_relay(ip, port)
        +run_net_client()
        +start_connection_thread(ip, port)
        +disconnect()
        +add_chat(chat)
        +create_chat(chat_name)
        +remove_chat(chat_name)
        +on_msg(msg)
        +on_ts_response(tsr)
        +on_sys_msg(sys_msg)
        +send_user_text(chat, text)
        +set_username(name)
        +send_username()
    }

    class NetClient {
        -WebSocket ws
        -PackageFactory package_factory
        +connect(ip, port) bool
        +run() Message
        +send_message(msg)
        +send_sys_message(sys_msg)
        +disconnect()
    }

    Client <|-- APPClient
    APPClient *-- APPClientChatBot
    APP *-- APPClient
    APP *-- TUI_Adapter
    TUI_Adapter o-- Client : uses
    Client *-- NetClient
    NetClient o-- PackageFactory : uses
    APPClientPackageFactory -- Client : used by

    %% ==================== Чаты и боты ====================
    class Chat {
        <<abstract>>
        +str name
        +list messages
        +add_message(msg)
        +send_message(msg)
    }

    class RemoteChat {
        -NetClient net_client
        -dict messages_wait_for_sync
        -int messages_sync_count
        +send_message(msg)
        +on_tsr(tsr)
    }

    class ChatBot {
        -Bot bot
        +add_commands(commands)
        +send_message(msg)
    }

    class Bot {
        +str chat_name
        +str bot_name
        -CommandRouter command_router
        -send_message Callable
        +add_command(cmd, func, args)
        +add_commands(commands)
        +send_text(text)
        +async_send_text(text)
        +on_text(text)
        +async_on_text(text)
    }

    class CommandRouter {
        +add_command(cmd, func, args)
        +route(text) bool
        +async_route(text) bool
    }

    class RelayBot {
        +__init__(client_handler)
    }

    class APPClientChatBot {
        +__init__(client)
    }

    Chat <|-- RemoteChat
    Chat <|-- ChatBot
    ChatBot *-- Bot
    Bot *-- CommandRouter
    RelayBot --|> Bot
    APPClientChatBot --|> ChatBot
    Client o-- Chat : manages
```
