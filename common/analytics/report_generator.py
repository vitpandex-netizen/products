import json
import logging
from datetime import datetime

logger = logging.getLogger("CrossProjectReport")
logging.basicConfig(level=logging.INFO)

class SynergyReportGenerator:
    """
    Генерирует сводные отчёты, объединяющие данные нескольких сервисов Триады.
    Например:
    - Изменение зарплат IT-специалистов (HH Jobs)
    - Оценка стоимости IT-компаний на бирже (UZ Stock)
    - Генерация контента для публикации (LinkID)
    """
    def __init__(self, s3_client=None):
        self.s3 = s3_client  # Boto3 client

    def fetch_latest_data(self):
        # В реальной реализации - чтение из MinIO s3://cross-project-analytics/
        logger.info("Скачивание данных из Data Lake...")
        return {
            "tech_stocks_index": 125.4,
            "avg_devops_salary": 2500,
            "market_sentiment": "positive"
        }

    def generate_report(self):
        data = self.fetch_latest_data()
        
        report = f"""
        === СВОДНЫЙ АНАЛИТИЧЕСКИЙ ОТЧЕТ ТРИАДЫ ===
        Дата: {datetime.now().strftime('%Y-%m-%d')}
        
        [1] Финансовый сектор (UZ Stock)
        Индекс IT/Телеком: {data['tech_stocks_index']} пунктов
        Сентимент: {data['market_sentiment'].upper()}
        
        [2] Кадровый рынок (HH Jobs)
        Средняя ЗП DevOps/Инфра-инженеров: ${data['avg_devops_salary']}
        Тенденция: Дефицит квалифицированных кадров сохраняется.
        
        [3] PR Идеи (для LinkID)
        "Почему рост IT-сектора на UZSE напрямую коррелирует с кадровым голодом"
        "DevOps за $2500: инвестируем в инфраструктуру или нанимаем дорогих спецов?"
        ==========================================
        """
        return report

def send_telegram_alert(message: str):
    import os
    import urllib.request
    import urllib.parse
    
    # Читаем токен и ID чата из окружения (или Vault)
    # Master PM / Owner chat ID
    token = os.getenv("MASTER_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_USER_ID")
    
    if not token or not chat_id:
        logger.warning("Telegram токен или Chat ID не настроены. Отправка пропущена.")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=payload)
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info("Отчёт успешно отправлен в Telegram.")
    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")

if __name__ == "__main__":
    generator = SynergyReportGenerator()
    report = generator.generate_report()
    print(report)
    # Пытаемся отправить в Telegram (если настроены ключи)
    send_telegram_alert(f"<pre>{report}</pre>")
