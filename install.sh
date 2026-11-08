#!/bin/bash

# Выход при любой ошибке
set -e

# Цвета для вывода в консоль
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Запуск универсального инсталлятора LinuxLog ===${NC}"

# Проверка запуска с root-правами
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Ошибка: Не запускайте скрипт через sudo ./install.sh.${NC}"
    echo "Запустите как обычный пользователь: ./install.sh"
    exit 1
fi

# 1. Определение дистрибутива через /etc/os-release
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO="$ID"
    ID_LIKE_LIST="${ID_LIKE:-}"
else
    echo -e "${RED}Ошибка: Не удалось определить операционную систему.${NC}"
    exit 1
fi

# Пути установки
USER_HOME="$HOME"
INSTALL_DIR="$USER_HOME/.local/share/linuxlog"
DESKTOP_ENTRY_DIR="$USER_HOME/.local/share/applications"

# Переменные для пакетов
PM=""
PKGS=""
ARCH_SETUP_DB=false

echo -e "Обнаружена система: ${GREEN}${NAME:-$DISTRO}${NC}"

# 2. Настройка под конкретный менеджер пакетов
case "$DISTRO" in
    fedora)
        PM="dnf"
        PKGS="mariadb mariadb-server python3 python3-devel python3-virtualenv qt6-qtbase-devel mesa-libGL rsync"
        ;;

    ubuntu|debian|mint)
        PM="apt"
        PKGS="mariadb-server mariadb-client python3 python3-dev python3-venv qt6-base-dev libgl1 libglx-mesa0 rsync"
        ;;

    arch)
        PM="pacman"
        PKGS="mariadb python python-virtualenv qt6-base mesa rsync"
        ARCH_SETUP_DB=true
        ;;

    *)
        # Проверка по вторичным признакам ID_LIKE
        if [[ "$ID_LIKE_LIST" == *ubuntu* || "$ID_LIKE_LIST" == *debian* ]]; then
            PM="apt"
            PKGS="mariadb-server mariadb-client python3 python3-dev python3-venv qt6-base-dev libgl1-mesa-glx rsync"

        elif [[ "$ID_LIKE_LIST" == *arch* ]]; then
            PM="pacman"
            PKGS="mariadb python python-virtualenv qt6-base mesa rsync"
            ARCH_SETUP_DB=true

        else
            echo -e "${RED}Извините, ваш дистрибутив ($DISTRO) пока не поддерживается автоматически.${NC}"
            exit 1
        fi
        ;;
esac

# 3. Установка системных зависимостей
echo -e "${BLUE}[1/6] Установка MariaDB и системных библиотек через $PM...${NC}"

if [ "$PM" = "apt" ]; then
    sudo apt update
    sudo apt install -y $PKGS

elif [ "$PM" = "dnf" ]; then
    sudo dnf install -y $PKGS

elif [ "$PM" = "pacman" ]; then
    sudo pacman -Syu --needed --noconfirm $PKGS
fi

# 4. Инициализация базы данных (специфика Arch Linux)
if [ "$ARCH_SETUP_DB" = true ]; then
    if [ ! -d "/var/lib/mysql/mysql" ]; then
        echo -e "${BLUE}Инициализация системных таблиц MariaDB (Arch Linux)...${NC}"
        sudo mariadb-install-db \
            --user=mysql \
            --basedir=/usr \
            --datadir=/var/lib/mysql
    fi
fi

echo -e "${BLUE}[2/6] Активация и запуск службы MariaDB...${NC}"

sudo systemctl enable --now mariadb

# Создание базы данных и пользователя
DB_CONFIG_PATH="$INSTALL_DIR/settings.cfg"
if [ ! -f "$DB_CONFIG_PATH" ]; then
    DB_CONFIG_PATH="./settings.cfg"
fi
mapfile -t DB_CONFIG < <(python3 - "$DB_CONFIG_PATH" <<'PY'
from pathlib import Path
import sys

values = {}
for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
print(values.get("db-name") or "linuxlog")
print(values.get("db-user") or "linuxlog")
PY
)
DB_NAME="${DB_CONFIG[0]}"
DB_USER="${DB_CONFIG[1]}"
if [[ ! "$DB_NAME" =~ ^[A-Za-z0-9_]+$ || ! "$DB_USER" =~ ^[A-Za-z0-9_]+$ ]]; then
    echo -e "${RED}Ошибка: имя базы и пользователя могут содержать только латинские буквы, цифры и _.${NC}"
    exit 1
fi

# One stable password across reinstalls.  Precedence:
#   1. LINUXLOG_DB_PASS exported by the user;
#   2. the password already stored in the application's .env;
#   3. the well-known default.
# This keeps access to an existing database after an upgrade while still
# letting the user choose their own password (or change it in Settings).
DEFAULT_DB_PASS='Linuxlog12#'
DB_PASS="${LINUXLOG_DB_PASS:-}"
if [ -z "$DB_PASS" ] && [ -f "$INSTALL_DIR/.env" ]; then
    DB_PASS="$(python3 - "$INSTALL_DIR/.env" <<'PY'
from pathlib import Path
import sys

for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    if line.lstrip().startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    if key.strip() == "LINUXLOG_DB_PASS":
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        print(value)
        break
PY
)"
fi
if [ -z "$DB_PASS" ]; then
    DB_PASS="$DEFAULT_DB_PASS"
fi
DB_PASS_SQL="${DB_PASS//\'/\'\'}"

echo -e "${BLUE}Настройка базы данных проекта в MariaDB...${NC}"

# UNIX-сокет позволяет root выполнять команды без пароля через sudo
sudo mariadb -u root <<EOF
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost'
    IDENTIFIED BY '${DB_PASS_SQL}';

ALTER USER '${DB_USER}'@'localhost'
    IDENTIFIED BY '${DB_PASS_SQL}';

GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.*
    TO '${DB_USER}'@'localhost';

FLUSH PRIVILEGES;
EOF

# 5. Копирование файлов приложения
echo -e "${BLUE}[3/6] Развёртывание файлов логгера...${NC}"

mkdir -p "$INSTALL_DIR"

rsync -av \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='.idea' \
    --exclude='settings.cfg' \
    --exclude='.env' \
    --exclude='country' \
    --exclude='*.adi' \
    --exclude='*.rules' \
    --exclude='image/***' \
    --exclude='eqsl/***' \
    ./ "$INSTALL_DIR/"

# Seed user data on a new install, but keep existing files on upgrades.
rsync -av --ignore-existing settings.cfg country "$INSTALL_DIR/"
find . -maxdepth 1 -type f \( -name '*.adi' -o -name '*.rules' \) \
    -exec rsync -av --ignore-existing {} "$INSTALL_DIR/" \;
for user_data_dir in image eqsl; do
    mkdir -p "$INSTALL_DIR/$user_data_dir"
    rsync -av --ignore-existing "$user_data_dir/" "$INSTALL_DIR/$user_data_dir/"
done

# Keep the application's database credentials in sync with the configured DB user.
# The password is stored in a 0600 .env file instead of settings.cfg.
python3 - "$INSTALL_DIR/settings.cfg" "$INSTALL_DIR/.env" "$DB_NAME" "$DB_USER" "$DB_PASS" <<'PY'
import sys
from pathlib import Path

install_dir = Path(sys.argv[1]).parent
sys.path.insert(0, str(install_dir))
from config_store import (
    ENV_MANAGED_SETTING_KEYS,
    blank_settings,
    env_file_values,
    load_settings,
    update_settings,
    write_env_file,
)

settings_path = sys.argv[1]
env_path = sys.argv[2]
settings = load_settings(path=settings_path, env_file=env_path, use_env=False)
env_values = env_file_values(settings)
env_values["LINUXLOG_DB_PASS"] = sys.argv[5]
write_env_file(env_values, path=env_path)
blank_settings(ENV_MANAGED_SETTING_KEYS, path=settings_path)
update_settings(
    {"db-name": sys.argv[3], "db-user": sys.argv[4]},
    path=settings_path,
    env_file=env_path,
)
PY
chmod 600 "$INSTALL_DIR/settings.cfg" "$INSTALL_DIR/.env"

# 6. Создание виртуального окружения Python
echo -e "${BLUE}[4/6] Настройка виртуального окружения (venv)...${NC}"

cd "$INSTALL_DIR"

python3 -m venv .venv

source .venv/bin/activate

# Обновление инструментов установки пакетов
python -m pip install --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
    python -m pip install -r requirements.txt
else
    # Запасной вариант, если файла зависимостей нет
    python -m pip install PyQt6 pyserial requests beautifulsoup4 PyMySQL websocket-client websockets
fi

deactivate

# 7. Создание стартового скрипта
echo -e "${BLUE}[5/6] Создание исполняемого скрипта запуска...${NC}"

cat <<EOF > "$INSTALL_DIR/linuxlog-run.sh"
#!/bin/bash
set -e

cd "$INSTALL_DIR"
source .venv/bin/activate
exec python main.py "\$@"
EOF

chmod +x "$INSTALL_DIR/linuxlog-run.sh"

# 8. Создание ярлыка в меню приложений
echo -e "${BLUE}[6/6] Создание ярлыка в меню приложений...${NC}"

mkdir -p "$DESKTOP_ENTRY_DIR"

ICON_PATH="$INSTALL_DIR/logo.png"

if [ ! -f "$ICON_PATH" ] && [ -f "$INSTALL_DIR/icon.svg" ]; then
    ICON_PATH="$INSTALL_DIR/icon.svg"
fi

cat <<EOF > "$DESKTOP_ENTRY_DIR/linuxlog.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=LinuxLog Ham Radio
Comment=Логгер для радиолюбителей (CAT, TCI, eQSL)
Exec=$INSTALL_DIR/linuxlog-run.sh
Icon=$ICON_PATH
Terminal=false
Categories=Utility;Development;HamRadio;
StartupNotify=true
Path=$INSTALL_DIR
EOF

# Обновление системного меню
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$DESKTOP_ENTRY_DIR"
fi

echo -e "${GREEN}=== Установка успешно завершена в системе ${NAME:-$DISTRO}! ===${NC}"

echo "Данные для подключения Python-приложения к MariaDB:"
echo -e "База данных: ${BLUE}${DB_NAME}${NC}"
echo -e "Пользователь: ${BLUE}${DB_USER}${NC}"
if [ "$DB_PASS" = "$DEFAULT_DB_PASS" ]; then
    echo "Пароль MariaDB: стандартный (${DEFAULT_DB_PASS}), сохранён в .env."
else
    echo "Пароль MariaDB сохранён в .env (значение не выводится)."
fi
echo "Пароль можно изменить в окне Settings или через переменную LINUXLOG_DB_PASS."
