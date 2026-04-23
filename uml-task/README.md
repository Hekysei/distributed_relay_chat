# UML: distributed_relay_chat

Диаграмма классов описывает проект [Hekysei/distributed_relay_chat](https://github.com/Hekysei/distributed_relay_chat): распределенный чат с WebSocket-релеем, комнатами, direct-чатами, модерацией и TUI-клиентом.

## Проект

**Распределенный relay-chat**:
- сервер принимает подключения и создает сессию пользователя (`Server` + `ClientHandler`);
- диспетчер маршрутизирует сообщения по комнатам и direct-каналам (`Dispatcher`, `Channel`);
- прокси-диспетчер добавляет ролевой доступ и модерацию (`ProxyDispatcher`);
- клиент хранит локальные чаты и синхронизирует timestamp сообщений (`UserClient`, `RemoteChat`, `TimestampResponse`);
- команды пользователя обрабатываются через ботов (`ClientChatBot`, `RelayBot`).

## Принятые архитектурные решения

1. **Единый протокол пакетов**  
   Все сетевые события сведены к пакетам (`Message`, `TimestampResponse`, `SystemMessage`) с базой `Package`. Это упрощает расширение протокола.

2. **Центральная фабрика разбора пакетов**  
   `PackageFactory` выбирает тип входного пакета и передает его в соответствующий handler (`PackageHandler`). Разбор JSON не размазан по бизнес-логике.

3. **Разделение транспортного слоя и доменной логики**  
   `ConnectionHandler` отвечает только за соединение/передачу, а вся логика маршрутизации и прав доступа находится в `Dispatcher`/`ProxyDispatcher`/`ClientHandler`.

4. **Proxy-слой для авторизации и модерации**  
   `ProxyDispatcher` оборачивает `Dispatcher` и проверяет роли (`GUEST`/`VERIFIED`/`MODERATOR`) для операций создания комнат, подписки, отправки и верификации.

5. **Двухконтурная клиентская модель**  
   Отдельно выделены: сетевой клиентский обработчик (`Client`, `ConnectionHandler`) и доменная модель чатов (`Chat`, `RemoteChat`, `UserClient`), что упрощает поддержку UI.

6. **Командный интерфейс поверх чатов**  
   `Bot` + `CommandRouter` позволяют использовать единый механизм текстовых команд как на клиенте, так и на стороне relay.

## Ответственности ключевых классов

| Компонент | Ответственность |
|-----------|-----------------|
| `Package`, `Message`, `TimestampResponse`, `SystemMessage` | Транспортная модель пакетов протокола. |
| `PackageFactory`, `PackageHandler`, `ActivePackageHandler` | Десериализация пакета и маршрутизация в обработчик. |
| `ConnectionHandler`, `Server` | Управление соединением и серверным циклом. |
| `DispatcherInterface`, `Dispatcher`, `Channel` | Маршрутизация сообщений, комнаты и подписки. |
| `ProxyDispatcher`, `AccessRule`, `UserRole` | Роли, права доступа, модерация. |
| `ClientHandler`, `RelayBot` | Логика сессии пользователя и relay-команд. |
| `Client`, `UserClient`, `APPClient` | Клиентская сетевая и прикладная логика, callbacks для UI. |
| `Chat`, `RemoteChat`, `ChatBot`, `ClientChatBot` | Хранение истории, отправка и командные чаты. |
| `Bot`, `CommandRouter`, `FuncArgsPair` | Регистрация и выполнение команд. |
| `TUI_Adapter`, `APP` | Адаптация клиентской логики к curses-интерфейсу и точка входа. |

## Использованные паттерны

| Паттерн | Где используется | Почему |
|--------|-------------------|--------|
| **Template Method** | `PackageFactory.process_json` | Общий алгоритм обработки входного пакета: определить тип -> создать объект -> вызвать handler. |
| **Factory Method** | `Package.from_json`, `TimestampResponse.from_message`, `make_system_message` | Централизованное создание объектов сообщений и ответов. |
| **Command** | `CommandRouter`, `FuncArgsPair`, `Bot`, `RelayBot`, `ClientChatBot` | Текстовая команда преобразуется в вызов конкретной функции с аргументами. |
| **Decorator / Proxy** | `ProxyDispatcher` вокруг `DispatcherInterface` | Добавляет проверки прав и модерацию без изменения базового диспетчера. |
| **Strategy** | `Dispatcher.users_funs` и callback-отправки (`Callable`) | Способ доставки сообщения инкапсулирован в передаваемую функцию. |
| **Observer (упрощенный)** | `APPClient.on_message_callback`, `on_chat_added_callback`, `on_chat_removed_callback` | UI подписывается на события клиентской модели. |
| **Adapter** | `TUI_Adapter` | Адаптирует модель клиента к интерфейсу curses. |
| **Facade (легковесный)** | `Relay`, `APP` | Упрощенные точки входа, скрывающие внутреннюю композицию подсистем. |

## Артефакты

- UML-диаграмма: `uml-task/class-diagram.puml`
- Описание объектов: `uml-task/objects-overview.md`
- Скрипт пересборки PDF: `uml-task/build-uml-pdf.sh`

Пересборка PDF:

```bash
./uml-task/build-uml-pdf.sh
```
