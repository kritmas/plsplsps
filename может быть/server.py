from flask import Flask, request, send_from_directory
import requests
import uuid

app = Flask(__name__)

# ⚠️ ВСТАВЬ СВОИ КЛЮЧИ ИЗ ТЕСТОВОГО МАГАЗИНА ЮKASSA
SHOP_ID = "1498187"
SECRET_KEY = "test_NOUQm02pcGC_2QmGesA5d0uXnGm02GiG2QLP7GTImpA"


# Разрешаем всё для учебного проекта (чтобы CSP не блокировал)
@app.after_request
def add_csp_header(response):
    response.headers['Content-Security-Policy'] = (
        "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; "
        "script-src * 'unsafe-inline' 'unsafe-eval'; "
        "style-src * 'unsafe-inline';"
    )
    return response


# Главная страница с формой
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# Создание платежа
@app.route('/create-payment', methods=['POST'])
def create_payment():
    try:
        data = request.get_json()
        amount_value = f"{float(data.get('amount', '100.00')):.2f}"
        idempotence_key = str(uuid.uuid4())

        payload = {
            "amount": {"value": amount_value, "currency": "RUB"},
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": "http://localhost:5000/return"
            },
            "description": "Тестовый заказ"
        }

        response = requests.post(
            'https://api.yookassa.ru/v3/payments',
            auth=(SHOP_ID, SECRET_KEY),
            headers={
                'Idempotence-Key': idempotence_key,
                'Content-Type': 'application/json'
            },
            json=payload
        )

        # Если ЮKassa вернула ошибку — показываем её
        if response.status_code != 200:
            return f"<h1>Ошибка ЮKassa</h1><pre>{response.text}</pre>"

        payment_data = response.json()
        redirect_url = payment_data.get('confirmation', {}).get('confirmation_url')

        if not redirect_url:
            return "<h1>Ошибка: нет ссылки для перенаправления</h1>"

        # Возвращаем HTML-страницу с автоматическим перенаправлением
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Перенаправление...</title></head>
        <body>
            <p>Перенаправление на страницу оплаты...</p>
            <script>window.location.href = "{redirect_url}";</script>
        </body>
        </html>
        """

    except Exception as e:
        return f"<h1>Ошибка сервера</h1><pre>{e}</pre>"


# Заглушка для страницы "Спасибо"
@app.route('/return')
def return_page():
    return "<h1>Оплата прошла! (или не прошла)</h1><a href='/'>Вернуться</a>"


# Убираем 404 на favicon
@app.route('/favicon.ico')
def favicon():
    return '', 204


if __name__ == '__main__':
    app.run(debug=True, port=5000)
