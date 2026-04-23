**dev**
## Распределённый релей чат
Проект по дисциплине "Основы ИТ технологий".

## TODO
- Адекватно решить проблему curses и двух потоков

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/f6aba8dc-c5b1-47d6-bfe7-25a1da112ffe" />


### UML

Диаграмма соответствует текущей структуре кода (пакеты протокола, релей, клиент, чаты/бот, TUI). Подробности и паттерны — в [uml-task/README.md](uml-task/README.md).

![Диаграмма классов](uml-task/class-diagram.svg)

- [PDF](uml-task/class-diagram.pdf)
- [PlantUML](uml-task/class-diagram.puml)

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
   **Если вы используете Windows, убедитесь, что пакет windows-curses был установлен (он добавлен в requirements.txt).**

3. Запустите сервер (релей):
   ```bash
   python3 relay.py
   ```

4. В новом терминале запустите TUI-клиент:
   ```bash
   python3 tui_client.py
   ```

