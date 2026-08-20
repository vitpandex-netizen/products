"""
Сетевые утилиты, общие для всех проектов монорепо.

Основная причина существования — Telegram API из этой сети недоступен по
IPv6: DNS отдаёт AAAA-запись (2001:67c:4e8:f004::9), маршрута до неё нет,
и requests/urllib3 падает с `[Errno 65] No route to host`, НЕ пробуя IPv4.
curl в тех же условиях работает, потому что умеет happy-eyeballs-фоллбэк,
а urllib3 — нет.

Проверено вживую 2026-08-05: `curl` → HTTP 200, `requests` → No route to host
на том же URL в ту же секунду.
"""

import socket

_original_getaddrinfo = socket.getaddrinfo
_ipv4_forced = False


def force_ipv4() -> None:
    """Заставить socket резолвить только в IPv4 (AF_INET).

    Вызывать один раз при старте приложения, ДО первых сетевых запросов.
    Идемпотентна — повторные вызовы ничего не ломают.
    """
    global _ipv4_forced
    if _ipv4_forced:
        return

    def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

    socket.getaddrinfo = _ipv4_only_getaddrinfo
    _ipv4_forced = True


def restore_default_dns() -> None:
    """Вернуть штатное поведение резолвера (для тестов)."""
    global _ipv4_forced
    socket.getaddrinfo = _original_getaddrinfo
    _ipv4_forced = False
