# Varamin Secure V21 — Railway

این نسخه با اطلاعاتی که در اختیار داری آماده شده و برای اجرای اصلی سایت روی Railway طراحی شده است.

## Telegram
کانال:
`@ROVKQPKC`

نیازی نیست `TELEGRAM_CHAT_ID` عددی داشته باشی، به شرطی که کانال عمومی باشد و ربات داخل کانال Admin باشد و اجازه Post Messages داشته باشد.
برنامه به صورت پیش‌فرض از `@ROVKQPKC` استفاده می‌کند.

اگر کانال خصوصی باشد، Bot API معمولاً به شناسه عددی کانال نیاز دارد؛ بدون آن نمی‌توان تضمین کرد که ارسال مستقیم به کانال خصوصی انجام شود.

## Railway Variables
حتماً این‌ها را تنظیم کن:
- `BOT_TOKEN` = توکن ربات
- `TELEGRAM_CHANNEL_USERNAME` = `@ROVKQPKC`
- `ADMIN_USERNAME` = `admin`
- `ADMIN_PASSWORD` = رمز قوی اختصاصی
- `FLASK_SECRET_KEY` = یک مقدار تصادفی طولانی
- `VISITOR_HASH_SALT` = یک مقدار تصادفی طولانی
- `COOKIE_SECURE` = `true`

`TELEGRAM_CHAT_ID` اختیاری است و می‌تواند خالی بماند.

## Admin
Username: `admin`
Password اولیه: `V21-R0VK!QPKC-Admin-9f7X`

بعد از راه‌اندازی، رمز را در Railway تغییر بده.

## رفتار گزارش
گزارش ابتدا در SQLite ذخیره می‌شود. سپس ارسال Telegram انجام می‌شود.
اگر Telegram موقتاً در دسترس نباشد، گزارش از بین نمی‌رود و در پنل مدیریت وضعیت ارسال و امکان Retry وجود دارد.
بنابراین خطای تلگرام باعث از کار افتادن سایت اصلی نمی‌شود.

## Railway Start
Procfile:
`web: gunicorn --preload --workers 2 --threads 4 --worker-tmp-dir /dev/shm --timeout 30 --keep-alive 5 app:app`
