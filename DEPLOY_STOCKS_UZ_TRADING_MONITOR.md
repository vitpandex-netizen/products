# 🚀 Деплой Stocks UZ `trading-monitor` на US Server

**Статус:** SSH через Tailscale заблокирован (snap-конфликт). Требуется ручное выполнение через консоль сервера.

---

## Команды для выполнения на US Server (`100.84.223.96:/home/us/projects/stocks-uz`)

**Только Docker. Контейнеризированное окружение — commercial-grade.**

```bash
# 1. Перейти в директорию проекта
cd /home/us/projects/stocks-uz

# 2. Переключиться на ветку с новыми модулями
git checkout trading-monitor

# 3. Скачать последний код с GitHub
git pull origin trading-monitor

# 4. Пересобрать Docker образ с новым кодом
docker-compose build --no-cache

# 5. Остановить старый контейнер и запустить новый
docker-compose down
docker-compose up -d

# 6. Проверить логи контейнера
docker-compose logs -f stocks-uz

# 7. Убедиться, что порт 8004 прослушивается
netstat -tlnp | grep 8004
```

### Проверки после деплоя

---

## Проверки после деплоя (оба варианта)

```bash
# 8. Проверить API доступность
curl http://localhost:8004/api/summary

# 9. Проверить новые модули через API:
# ML Predictor:
curl http://localhost:8004/api/ml/predict?ticker=UZMT

# Voice Agent:
curl -X POST http://localhost:8004/api/agent/query -d '{"query": "что купить?"}'

# Monte Carlo:
curl http://localhost:8004/api/risk/monte-carlo?ticker=UZMT

# 10. Запустить selfcheck внутри контейнера
docker-compose exec stocks-uz python3 tests/test_stage4_macro.py
docker-compose exec stocks-uz python3 tests/test_sprint5.py
```

✅ **Ожидаемый результат Selfcheck:** `22 PASS / 1 WARN / 0 FAIL`

✅ **Контейнер должен быть:** `Up` (docker-compose ps)

✅ **API должны отвечать на запросы:** 200 OK с данными или ошибкой валидации, но не 500

---

## Откат (если что-то сломалось)

```bash
cd /home/us/projects/stocks-uz
git checkout main
git pull origin main
docker-compose build --no-cache
docker-compose down
docker-compose up -d
```

---

**Дата:** 2026-09-14  
**Коммит:** `ea7431b` (trading-monitor, 6 мажорных коммитов спринта 5)  
**Требуемое действие:** Ручной рун команд на US Server (SSH заблокирован)
