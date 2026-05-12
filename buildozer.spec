[app]

# Название игры
title = Карты

# Внутреннее имя пакета
package.name = cardsmama

# Уникальный идентификатор
package.domain = org.myfamily

# Папка с исходниками
source.dir = .

# Какие файлы включить
source.include_exts = py,png,jpg,kv,atlas,ttf

# Версия
version = 1.0

# Зависимости (стабильная связка для Android)
requirements = python3==3.11.5,kivy==2.3.0

# Ориентация — разрешаем все, переключаем из кода
orientation = all

# Полноэкранный режим
fullscreen = 0

# Разрешения
android.permissions = WAKE_LOCK

# Минимальная версия Android (5.0)
android.minapi = 21

# Целевая версия Android (Android 13)
android.api = 33

# Фиксируем NDK 25b — стабильная и проверенная версия для Kivy 2.3.0
android.ndk = 25b

# SDK
android.sdk = 33

# Архитектура
android.archs = arm64-v8a

# Принять лицензии
android.accept_sdk_license = True

# Версия p4a fork (стабильная для kivy 2.3.0)
p4a.branch = master

[buildozer]

log_level = 2
warn_on_root = 1
