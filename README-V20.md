# Varamin Secure V20

این نسخه بر پایه V19 ساخته شده و برای اجرای روان‌تر و امنیت بهتر تنظیم شده است.

## تنظیمات Railway
Environment Variables:
- BOT_TOKEN
- TELEGRAM_CHANNEL_USERNAME=@ROVKQPKC
- ADMIN_USERNAME=admin
- ADMIN_PASSWORD=یک رمز قوی و اختصاصی
- FLASK_SECRET_KEY=رشته تصادفی طولانی
- VISITOR_HASH_SALT=رشته تصادفی دیگر
- COOKIE_SECURE=true

اگر کانال خصوصی است، حتماً TELEGRAM_CHAT_ID عددی را هم تنظیم کنید.
ربات باید داخل کانال ادمین باشد و اجازه ارسال پیام داشته باشد.

## رمز پیشنهادی پنل
نام کاربری: admin
رمز اولیه: V20-ChangeMe-9fQ7!xK2
بعد از اولین ورود، مقدار ADMIN_PASSWORD را در Railway تغییر دهید.

## بهینه‌سازی
- Gunicorn با preload، دو worker و چهار thread
- SQLite WAL
- محدودیت نرخ درخواست
- هدرهای امنیتی
- کوکی HttpOnly/SameSite/Secure
- ثبت گزارش قبل از ارسال تلگرام و امکان Retry
- عدم ذخیره IP خام بازدیدکنندگان
- ورودی‌های محدودشده و پاک‌سازی‌شده
