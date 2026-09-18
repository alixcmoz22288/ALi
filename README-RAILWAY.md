# نسخه امن V19 — سامانه ورامین

## راه‌اندازی Railway
1. کل فایل‌های این پوشه را داخل GitHub بگذارید.
2. پروژه را در Railway از GitHub Deploy کنید.
3. Variables را بسازید:
   - `BOT_TOKEN` = توکن BotFather
   - `TELEGRAM_CHANNEL_USERNAME / TELEGRAM_CHAT_ID` = شناسه عددی کانال خصوصی، مثل `-100123...`
   - `ADMIN_USERNAME`
   - `ADMIN_PASSWORD`
   - `FLASK_SECRET_KEY`
   - `VISITOR_HASH_SALT`
4. Railway به‌صورت خودکار با Procfile اجرا می‌شود.

## کانال تلگرام
ربات را در کانال خصوصی به‌عنوان Administrator اضافه کنید و اجازه ارسال پیام بدهید.
لینک دعوت کانال شما:
https://t.me/+KbtIMoi-oIM0ZWRk

نکته: لینک دعوت (`t.me/+...`) خودش `chat_id` نیست. برای ارسال مستقیم Bot API باید `TELEGRAM_CHANNEL_USERNAME / TELEGRAM_CHAT_ID` عددی کانال را وارد کنید.

## نکات امنیتی
- توکن ربات و رمز مدیر داخل HTML نیستند.
- SQLite با WAL و query پارامتری استفاده می‌شود.
- rate limit برای endpointهای عمومی وجود دارد.
- هانی‌پات ضد ربات، محدودیت طول ورودی و پاک‌سازی کاراکترهای کنترل فعال است.
- session مدیر HttpOnly/SameSite است.
- هدرهای امنیتی و CSP تنظیم شده‌اند.
- IP خام ذخیره نمی‌شود و برای آمار، hash سمت سرور نگهداری می‌شود.
- برای امنیت واقعی، HTTPS Railway را نگه دارید و رمز قوی استفاده کنید.


## V21 Telegram
کانال مقصد گزارش‌ها: `@ROVKQPKC` — در صورت عمومی بودن کانال، شناسه عددی لازم نیست. ربات باید ادمین کانال و دارای اجازه ارسال پیام باشد.
