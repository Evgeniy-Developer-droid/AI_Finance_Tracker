LOCALES = {
    "en": {
        "start_new": "🔐 You're not registered. Please provide your email:",
        "choose_currency": "💱 Choose your default currency:",
        "registered": "🎉 You're registered and can add transactions.",
        "add_type": "Do you want to add income or expense?",
        "amount": "Enter the amount:",
        "category": "Choose a category:",
        "date": "Pick a date:",
        "saved": "✅ Transaction saved!",
        "date_format_error": "❌ Invalid date format. Use YYYY-MM-DD",
        "report_result": "📊 Report from {start} to {end}\nIncome: {income} | Expense: {expense}",
    },
    "uk": {
        "start_new": "🔐 Ти ще не зареєстрований. Вкажи свій email:",
        "choose_currency": "💱 Обери валюту за замовчуванням:",
        "registered": "🎉 Тебе зареєстровано. Можеш додавати транзакції.",
        "add_type": "Хочеш додати дохід чи витрату?",
        "amount": "Вкажи суму:",
        "category": "Обери категорію:",
        "date": "Обери дату:",
        "saved": "✅ Транзакцію збережено!",
        "date_format_error": "❌ Неправильний формат дати. Використовуй YYYY-MM-DD",
        "report_result": "📊 Звіт з {start} по {end}\nДоходи: {income} | Витрати: {expense}",
    }
}


def _(user_lang: str, key: str) -> str:
    return LOCALES.get(user_lang or "en", LOCALES["en"]).get(key, key)