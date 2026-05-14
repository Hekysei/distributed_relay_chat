#!/usr/bin/env python3
"""Локальный запуск релея и модератора без Docker.

Повторяет сценарий docker-compose.yml: relay слушает сеть, пауза перед
подключением модератора, затем интерактивный moderator (stdin/stdout/stderr
как у `docker compose run` с TTY).

Из корня репозитория:

  python3 scripts/run_relay_and_moderator.py

Требуются зависимости: pip install -r requirements.txt
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Запуск relay.py и moderator.py в одном процессе-оркестраторе."
    )
    parser.add_argument(
        "--relay-host",
        default="0.0.0.0",
        help="Адрес прослушивания релея (как в compose: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=12021,
        help="Порт WebSocket релея",
    )
    parser.add_argument(
        "--moderator-host",
        default="localhost",
        help="Хост для moderator.py (в Docker это имя сервиса relay)",
    )
    parser.add_argument(
        "--startup-delay",
        type=float,
        default=3.0,
        help="Секунды ожидания после старта релея (как sleep 3 в compose)",
    )
    args = parser.parse_args()

    relay_cmd = [
        sys.executable,
        str(ROOT / "relay.py"),
        "--host",
        args.relay_host,
        "--port",
        str(args.port),
    ]
    mod_cmd = [
        sys.executable,
        str(ROOT / "moderator.py"),
        "--host",
        args.moderator_host,
        "--port",
        str(args.port),
    ]

    relay = subprocess.Popen(relay_cmd, cwd=ROOT)
    try:
        time.sleep(args.startup_delay)
        if relay.poll() is not None:
            rc = relay.returncode if relay.returncode is not None else 1
            print(f"relay завершился до старта модератора (код {rc}).", file=sys.stderr)
            return rc
        mod = subprocess.run(mod_cmd, cwd=ROOT)
        return mod.returncode
    except KeyboardInterrupt:
        return 130
    finally:
        if relay.poll() is None:
            relay.terminate()
            try:
                relay.wait(timeout=5)
            except subprocess.TimeoutExpired:
                relay.kill()
                relay.wait()


if __name__ == "__main__":
    sys.exit(main())
