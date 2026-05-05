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

# Зависимости
requirements = python3,kivy==2.3.0

# ВЕРТИКАЛЬНАЯ ОРИЕНТАЦИЯ
orientation = landscape

# Полноэкранный режим
fullscreen = 0

# Разрешения
android.permissions = WAKE_LOCK

# Минимальная версия Android (5.0)
android.minapi = 21

# Целевая версия
android.api = 33

# Архитектура
android.archs = arm64-v8a

# Принять лицензии
android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1
