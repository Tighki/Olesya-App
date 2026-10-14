"""SQLite: люди, заявки, занятия, записи, гардероб, опыт и значки.

Пароли хранятся как хеш. Повторный запуск не дублирует демонстрационные строки.
"""

import hashlib
import os
import re
import sqlite3
import sys
from datetime import datetime

ROLES = ("admin", "teacher", "atelier", "student")
STYLES = ("ballet", "contemporary", "hiphop", "latin", "ballroom", "kids", "other")
BRANCHES = ("center", "north", "river", "park", "loft", "other")
PRIORITIES = ("low", "normal", "high")
REQUEST_STATUSES = ("new", "assigned", "done", "cancelled")
CLASS_STATUSES = ("open", "full", "completed", "cancelled")
ENROLL_STATUSES = ("confirmed", "completed", "cancelled")
ORDER_STATUSES = ("new", "accepted", "ready", "completed", "cancelled")
PRODUCT_CATEGORIES = ("costume", "shoes", "accessory")
REVIEW_KINDS = ("teacher", "class", "product")

ROLE_RU = {
    "admin": "Администратор",
    "teacher": "Педагог",
    "atelier": "Костюмер",
    "student": "Ученик",
}
STYLE_RU = {
    "ballet": "Классика",
    "contemporary": "Контемп",
    "hiphop": "Хип-хоп",
    "latin": "Латина",
    "ballroom": "Бальные",
    "kids": "Дети",
    "other": "Любой стиль",
}
BRANCH_RU = {
    "center": "Центральный зал",
    "north": "Северный зал",
    "river": "Зал у реки",
    "park": "Парковый зал",
    "loft": "Лофт",
    "other": "Любая площадка",
}
PRIORITY_RU = {
    "low": "Низкий",
    "normal": "Обычный",
    "high": "Срочный",
}
REQUEST_STATUS_RU = {
    "new": "Новая",
    "assigned": "У педагога",
    "done": "Проведена",
    "cancelled": "Отменена",
}
CLASS_STATUS_RU = {
    "open": "Есть места",
    "full": "Мест нет",
    "completed": "Прошло",
    "cancelled": "Отменено",
}
ENROLL_STATUS_RU = {
    "confirmed": "В расписании",
    "completed": "Отработано",
    "cancelled": "Снято",
}
ORDER_STATUS_RU = {
    "new": "Новый",
    "accepted": "Принят",
    "ready": "Можно забрать",
    "completed": "Выдан",
    "cancelled": "Отменён",
}
PRODUCT_CATEGORY_RU = {
    "costume": "Костюм",
    "shoes": "Обувь",
    "accessory": "Аксессуар",
}

ORDER_FLOW = {
    "new": {"accepted", "cancelled"},
    "accepted": {"ready", "cancelled"},
    "ready": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}

RANKS = (
    (0, "Зритель"),
    (100, "Новичок"),
    (300, "Кордебалет"),
    (650, "Солист"),
    (1000, "Прима"),
    (1800, "Легенда зала"),
)

BADGES = (
    ("debut", "Дебют", "Первое отработанное занятие", 40),
    ("five", "Пять выходов", "Пять отработанных занятий", 60),
    ("ten", "Десятка", "Десять отработанных занятий", 100),
    ("palette", "Палитра", "Три разных стиля в отработанных занятиях", 80),
    ("solo", "Соло", "Проведённый индивидуальный урок", 50),
    ("voice", "Голос зала", "Первая оценка", 20),
    ("costume", "Гардероб", "Выданный заказ костюмерной", 30),
    ("regular", "Постоянный", "Три записи в расписании или уже отработанные", 40),
)
BADGE_BY = {item[0]: item for item in BADGES}

XP_CLASS_BASE = 80
XP_CLASS_HOUR = 20
XP_LESSON = 120
XP_ORDER = 30
XP_REVIEW = 20


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def db_path():
    override = os.environ.get("OLESYA_DB")
    if override:
        parent = os.path.dirname(os.path.abspath(override))
        if parent:
            os.makedirs(parent, exist_ok=True)
        return override
    root = _app_dir()
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "olesya.db")


def connect():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today():
    return datetime.now().strftime("%Y-%m-%d")


def hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        salt_hex, _digest = stored.split("$", 1)
    except ValueError:
        return False
    return hash_password(password, bytes.fromhex(salt_hex)) == stored


def _public(row):
    if row is None:
        return None
    data = dict(row)
    data.pop("password", None)
    return data


def rank_of(xp):
    xp = int(xp or 0)
    current = RANKS[0]
    nxt = None
    for index, item in enumerate(RANKS):
        if xp >= item[0]:
            current = item
            nxt = RANKS[index + 1] if index + 1 < len(RANKS) else None
        else:
            break
    if nxt is None:
        fraction = 1.0
    else:
        span = nxt[0] - current[0]
        fraction = 0.0 if span <= 0 else (xp - current[0]) / span
    return {
        "name": current[1],
        "floor": current[0],
        "next_name": None if nxt is None else nxt[1],
        "next_at": None if nxt is None else nxt[0],
        "xp": xp,
        "fraction": fraction,
    }


def init_db():
    conn = connect()
    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                login       TEXT NOT NULL UNIQUE,
                password    TEXT NOT NULL,
                full_name   TEXT NOT NULL,
                role        TEXT NOT NULL DEFAULT 'student'
                                CHECK (role IN ('admin', 'teacher', 'atelier', 'student')),
                style       TEXT NOT NULL DEFAULT 'other',
                branch      TEXT NOT NULL DEFAULT 'other',
                about       TEXT NOT NULL DEFAULT '',
                is_active   INTEGER NOT NULL DEFAULT 1,
                xp          INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS requests (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT NOT NULL,
                description     TEXT NOT NULL DEFAULT '',
                style           TEXT NOT NULL DEFAULT 'other',
                branch          TEXT NOT NULL DEFAULT 'other',
                people          INTEGER NOT NULL DEFAULT 1 CHECK (people > 0),
                preferred_date  TEXT NOT NULL DEFAULT '',
                priority        TEXT NOT NULL DEFAULT 'normal',
                status          TEXT NOT NULL DEFAULT 'new',
                student_id      INTEGER NOT NULL REFERENCES users(id),
                teacher_id      INTEGER REFERENCES users(id),
                created_at      TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ux_open_request
            ON requests(student_id, title)
            WHERE status IN ('new', 'assigned');

            CREATE TABLE IF NOT EXISTS classes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT NOT NULL,
                description     TEXT NOT NULL DEFAULT '',
                style           TEXT NOT NULL,
                branch          TEXT NOT NULL,
                class_date      TEXT NOT NULL,
                duration_hours  INTEGER NOT NULL CHECK (duration_hours > 0),
                price           INTEGER NOT NULL CHECK (price > 0),
                capacity        INTEGER NOT NULL CHECK (capacity > 0),
                teacher_id      INTEGER NOT NULL REFERENCES users(id),
                status          TEXT NOT NULL DEFAULT 'open',
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS enrollments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id    INTEGER NOT NULL REFERENCES classes(id),
                student_id  INTEGER NOT NULL REFERENCES users(id),
                people      INTEGER NOT NULL CHECK (people > 0),
                status      TEXT NOT NULL DEFAULT 'confirmed',
                created_at  TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ux_enrollment_active
            ON enrollments(class_id, student_id)
            WHERE status = 'confirmed';

            CREATE TABLE IF NOT EXISTS products (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                atelier_id   INTEGER NOT NULL REFERENCES users(id),
                name         TEXT NOT NULL,
                description  TEXT NOT NULL DEFAULT '',
                category     TEXT NOT NULL,
                price        INTEGER NOT NULL CHECK (price > 0),
                stock        INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
                is_active    INTEGER NOT NULL DEFAULT 1,
                created_at   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id   INTEGER NOT NULL REFERENCES users(id),
                atelier_id   INTEGER NOT NULL REFERENCES users(id),
                status       TEXT NOT NULL DEFAULT 'new',
                total        INTEGER NOT NULL CHECK (total >= 0),
                created_at   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id    INTEGER NOT NULL REFERENCES orders(id),
                product_id  INTEGER NOT NULL REFERENCES products(id),
                name        TEXT NOT NULL,
                qty         INTEGER NOT NULL CHECK (qty > 0),
                price       INTEGER NOT NULL CHECK (price > 0)
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id   INTEGER NOT NULL REFERENCES users(id),
                target_kind TEXT NOT NULL,
                target_id   INTEGER NOT NULL,
                rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                body        TEXT NOT NULL DEFAULT '',
                created_at  TEXT NOT NULL,
                UNIQUE (author_id, target_kind, target_id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id  INTEGER NOT NULL REFERENCES requests(id),
                user_id     INTEGER NOT NULL REFERENCES users(id),
                body        TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_kind TEXT NOT NULL,
                entity_id   INTEGER NOT NULL,
                user_id     INTEGER,
                action      TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS xp_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                source      TEXT NOT NULL,
                amount      INTEGER NOT NULL,
                reason      TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                UNIQUE (user_id, source)
            );

            CREATE TABLE IF NOT EXISTS user_badges (
                user_id     INTEGER NOT NULL REFERENCES users(id),
                code        TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                PRIMARY KEY (user_id, code)
            );

            CREATE INDEX IF NOT EXISTS ix_requests_student ON requests(student_id);
            CREATE INDEX IF NOT EXISTS ix_requests_teacher ON requests(teacher_id);
            CREATE INDEX IF NOT EXISTS ix_classes_teacher ON classes(teacher_id);
            CREATE INDEX IF NOT EXISTS ix_enroll_class ON enrollments(class_id);
            CREATE INDEX IF NOT EXISTS ix_enroll_student ON enrollments(student_id);
            CREATE INDEX IF NOT EXISTS ix_products_atelier ON products(atelier_id);
            CREATE INDEX IF NOT EXISTS ix_orders_student ON orders(student_id);
            CREATE INDEX IF NOT EXISTS ix_orders_atelier ON orders(atelier_id);
            CREATE INDEX IF NOT EXISTS ix_messages_request ON messages(request_id);
            CREATE INDEX IF NOT EXISTS ix_history_entity ON history(entity_kind, entity_id);
            CREATE INDEX IF NOT EXISTS ix_xp_user ON xp_log(user_id);
            """
        )
    _seed(conn)
    conn.close()


def _seed(conn):
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        with conn:
            conn.execute(
                "INSERT INTO users (login, password, full_name, role, style, branch, about, created_at)"
                " VALUES (?, ?, ?, 'admin', 'other', 'other', ?, ?)",
                (
                    "admin",
                    hash_password("admin"),
                    "Администратор студии «Олеся»",
                    "Ведёт зал, людей, расписание и доску опыта.",
                    "2026-08-01 09:00:00",
                ),
            )
    _seed_demo(conn)


def _seed_demo(conn):
    people = (
        ("orlova", "teacher", "Мария Орлова", "teacher", "ballet", "center", "Классический станок, центр зала."),
        ("gromov", "teacher", "Кирилл Громов", "teacher", "hiphop", "north", "Хип-хоп и баттл, северный зал."),
        ("danilova", "teacher", "Алина Данилова", "teacher", "contemporary", "loft", "Контемп и импровизация в лофте."),
        ("petrova", "teacher", "Елена Петрова", "teacher", "latin", "river", "Латина у реки, связки под показ."),
        ("sokol", "teacher", "Андрей Сокол", "teacher", "ballroom", "park", "Европейская программа, парковый зал."),
        ("mironova", "teacher", "Вера Миронова", "teacher", "other", "other", "Беру разные стили, если коллеги заняты."),
        ("lisina", "atelier", "Нина Лисина", "atelier", "other", "center", "Купальники и сценические костюмы."),
        ("kravtsov", "atelier", "Олег Кравцов", "atelier", "other", "north", "Обувь для зала и сцены."),
        ("shirokova", "atelier", "Дарья Широкова", "atelier", "other", "loft", "Гетры, резинки и сумки."),
        ("volkova", "student", "Софья Волкова", "student", "other", "center", ""),
        ("egorov", "student", "Максим Егоров", "student", "other", "north", ""),
        ("kim", "student", "Арина Ким", "student", "other", "loft", ""),
        ("zaitseva", "student", "Полина Зайцева", "student", "other", "park", ""),
    )
    with conn:
        for login, password, full_name, role, style, branch, about in people:
            if conn.execute("SELECT 1 FROM users WHERE login = ?", (login,)).fetchone():
                continue
            conn.execute(
                "INSERT INTO users (login, password, full_name, role, style, branch, about, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (login, hash_password(password), full_name, role, style, branch, about, "2026-08-15 10:00:00"),
            )
    if conn.execute("SELECT COUNT(*) FROM classes").fetchone()[0]:
        return

    ids = {row["login"]: row["id"] for row in conn.execute("SELECT id, login FROM users").fetchall()}

    def add_class(key, title, description, style, branch, class_date, hours, price, capacity, teacher, status, created):
        cur = conn.execute(
            "INSERT INTO classes (title, description, style, branch, class_date, duration_hours, price, capacity, teacher_id, status, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (title, description, style, branch, class_date, hours, price, capacity, ids[teacher], status, created),
        )
        class_id = cur.lastrowid
        _log(conn, "class", class_id, ids[teacher], "Занятие опубликовано", created)
        if status == "completed":
            _log(conn, "class", class_id, ids[teacher], "Статус: Прошло", class_date + " 21:00:00")
        if status == "full":
            _log(conn, "class", class_id, None, "Свободных мест не осталось", created)
        classes[key] = class_id

    def add_enrollment(class_key, student, people_count, status, created):
        cur = conn.execute(
            "INSERT INTO enrollments (class_id, student_id, people, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (classes[class_key], ids[student], people_count, status, created),
        )
        action = "Запись оформлена" if status == "confirmed" else "Запись закрыта вместе с занятием"
        _log(conn, "enrollment", cur.lastrowid, ids[student], action, created)
        return cur.lastrowid

    def add_request(title, description, style, branch, people_count, preferred, priority, student, teacher, status, created):
        cur = conn.execute(
            "INSERT INTO requests (title, description, style, branch, people, preferred_date, priority, status, student_id, teacher_id, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                title,
                description,
                style,
                branch,
                people_count,
                preferred,
                priority,
                status,
                ids[student],
                ids[teacher] if teacher else None,
                created,
            ),
        )
        request_id = cur.lastrowid
        _log(conn, "request", request_id, ids[student], "Заявка создана", created)
        if teacher:
            name = conn.execute("SELECT full_name FROM users WHERE id = ?", (ids[teacher],)).fetchone()["full_name"]
            _log(conn, "request", request_id, None, f"Назначен педагог: {name}", created)
        if status == "done":
            _log(conn, "request", request_id, ids[teacher], "Статус: Проведена", created)
        return request_id

    def add_product(key, atelier, name, description, category, price, stock):
        cur = conn.execute(
            "INSERT INTO products (atelier_id, name, description, category, price, stock, is_active, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
            (ids[atelier], name, description, category, price, stock, "2026-09-01 11:00:00"),
        )
        products[key] = {"id": cur.lastrowid, "atelier": atelier, "name": name, "price": price}

    def add_order(student, product_key, qty, status, created):
        product = products[product_key]
        total = product["price"] * qty
        cur = conn.execute(
            "INSERT INTO orders (student_id, atelier_id, status, total, created_at) VALUES (?, ?, ?, ?, ?)",
            (ids[student], ids[product["atelier"]], status, total, created),
        )
        order_id = cur.lastrowid
        conn.execute(
            "INSERT INTO order_items (order_id, product_id, name, qty, price) VALUES (?, ?, ?, ?, ?)",
            (order_id, product["id"], product["name"], qty, product["price"]),
        )
        _log(conn, "order", order_id, ids[student], "Заказ оформлен", created)
        if status != "new":
            _log(conn, "order", order_id, ids[product["atelier"]], f"Статус: {ORDER_STATUS_RU[status]}", created)
        return order_id

    def add_review(author, kind, target_id, rating, body, created):
        cur = conn.execute(
            "INSERT INTO reviews (author_id, target_kind, target_id, rating, body, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (ids[author], kind, target_id, rating, body, created),
        )
        return cur.lastrowid

    classes = {}
    products = {}
    with conn:
        add_class(
            "barre",
            "Станок: адажио",
            "Работа у станка и короткое адажио в центр. Форма: купальник, мягкая обувь.",
            "ballet", "center", "2026-10-18", 2, 1200, 10, "orlova", "open", "2026-09-20 12:00:00",
        )
        add_class(
            "battle",
            "Баттл-лаборатория",
            "Фристайл кругами по 30 секунд. Кроссовки с ровной подошвой.",
            "hiphop", "north", "2026-10-19", 2, 900, 12, "gromov", "open", "2026-09-21 12:00:00",
        )
        add_class(
            "floor",
            "Пол и дыхание",
            "Партер, падения и фраза на 32 счёта. Коврик студии выдаём.",
            "contemporary", "loft", "2026-10-21", 2, 1100, 8, "danilova", "open", "2026-09-22 12:00:00",
        )
        add_class(
            "samba",
            "Самба-связка",
            "Базовый ход и одна конкурсная связка. Каблук не обязателен.",
            "latin", "river", "2026-10-22", 2, 1300, 10, "petrova", "open", "2026-09-18 12:00:00",
        )
        add_class(
            "waltz",
            "Медленный вальс",
            "Подъём, снижение и один квадрат. Можно прийти парой или одному.",
            "ballroom", "park", "2026-10-25", 2, 1400, 8, "sokol", "open", "2026-09-19 12:00:00",
        )
        add_class(
            "warmup",
            "Общий разогрев",
            "Короткий класс для любого стиля. Мест мало, темп спокойный.",
            "kids", "center", "2026-10-20", 1, 600, 2, "mironova", "full", "2026-09-25 12:00:00",
        )
        add_class(
            "exersis",
            "Экзерсис у станка",
            "Прошедший класс: плие, батман, растяжка.",
            "ballet", "center", "2026-09-08", 2, 1200, 12, "orlova", "completed", "2026-08-20 12:00:00",
        )
        add_class(
            "toprock",
            "Основы топрока",
            "Прошедший класс: стойка, шаги, выход в круг.",
            "hiphop", "north", "2026-09-10", 2, 900, 12, "gromov", "completed", "2026-08-22 12:00:00",
        )
        add_class(
            "improv",
            "Импровизация",
            "Прошедший класс: задание на вес и взгляд.",
            "contemporary", "loft", "2026-09-14", 2, 1100, 8, "danilova", "completed", "2026-08-24 12:00:00",
        )
        add_class(
            "chacha",
            "Ча-ча-ча",
            "Прошедший класс: шассе и поворот.",
            "latin", "river", "2026-09-16", 2, 1300, 10, "petrova", "completed", "2026-08-26 12:00:00",
        )
        add_class(
            "waltz_past",
            "Вальс: первый квадрат",
            "Прошедший класс: рама и квадрат.",
            "ballroom", "park", "2026-09-18", 2, 1400, 8, "sokol", "completed", "2026-08-28 12:00:00",
        )

        add_enrollment("barre", "volkova", 1, "confirmed", "2026-10-02 14:10:00")
        add_enrollment("battle", "egorov", 1, "confirmed", "2026-10-03 11:20:00")
        add_enrollment("samba", "zaitseva", 1, "confirmed", "2026-10-04 16:05:00")
        add_enrollment("warmup", "kim", 1, "confirmed", "2026-10-01 10:00:00")
        add_enrollment("warmup", "egorov", 1, "confirmed", "2026-10-01 10:20:00")

        for class_key, student, stamp in (
            ("exersis", "volkova", "2026-09-01 10:00:00"),
            ("exersis", "egorov", "2026-09-01 10:05:00"),
            ("exersis", "zaitseva", "2026-09-01 10:08:00"),
            ("toprock", "volkova", "2026-09-02 10:00:00"),
            ("toprock", "egorov", "2026-09-02 10:05:00"),
            ("improv", "volkova", "2026-09-03 10:00:00"),
            ("improv", "kim", "2026-09-03 10:05:00"),
            ("chacha", "volkova", "2026-09-04 10:00:00"),
            ("chacha", "zaitseva", "2026-09-04 10:05:00"),
            ("waltz_past", "volkova", "2026-09-05 10:00:00"),
            ("waltz_past", "zaitseva", "2026-09-05 10:05:00"),
        ):
            _grant_enrollment(conn, add_enrollment(class_key, student, 1, "completed", stamp), stamp)

        done_id = add_request(
            "Индивидуальный экзерсис",
            "Нужен час у станка перед отчётником, без группы.",
            "ballet", "center", 1, "2026-09-12", "high", "volkova", "orlova", "done", "2026-09-06 09:00:00",
        )
        conn.execute(
            "INSERT INTO messages (request_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
            (done_id, ids["volkova"], "Можно без пуантов, только мягкие?", "2026-09-06 12:00:00"),
        )
        conn.execute(
            "INSERT INTO messages (request_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
            (done_id, ids["orlova"], "Да. Час у станка, пуанты не берём.", "2026-09-06 15:00:00"),
        )
        _grant_request(conn, done_id, "2026-09-12 20:00:00")

        battle_id = add_request(
            "Баттл к отчётнику",
            "Нужен сольник на 40 секунд, хип-хоп, северный зал.",
            "hiphop", "north", 1, "2026-10-24", "high", "egorov", None, "new", "2026-10-10 09:30:00",
        )
        floor_id = add_request(
            "Связка на показ",
            "Первый показ. Хочу короткую фразу в контемпе, без акробатики.",
            "contemporary", "loft", 1, "2026-10-28", "normal", "kim", None, "new", "2026-10-10 11:00:00",
        )
        add_request(
            "Первый вальс в паре",
            "Идём вдвоём. Нужен педагог по бальной, парковый зал.",
            "ballroom", "park", 2, "2026-11-02", "normal", "zaitseva", None, "new", "2026-10-11 08:40:00",
        )
        add_request(
            "Спокойный разогрев",
            "Стиль не важен. Нужен неспешный час перед прогоном.",
            "other", "other", 1, "2026-10-30", "low", "volkova", None, "new", "2026-10-11 09:10:00",
        )
        add_request(
            "Латина для сцены",
            "Хочу самбу под конкретный трек, зал у реки.",
            "latin", "river", 1, "2026-11-06", "high", "zaitseva", None, "new", "2026-10-11 09:20:00",
        )

        add_product("leo", "lisina", "Купальник", "Чёрный, рукав 3/4, хлопок с эластаном.", "costume", 2400, 7)
        add_product("skirt", "lisina", "Шифоновая юбка", "Репетиционная, длина миди.", "costume", 1800, 5)
        add_product("tights", "lisina", "Трико", "Телесные, плотность 80 den.", "costume", 700, 14)
        add_product("pointe", "kravtsov", "Мягкие балетки", "Кожа, чёрные, несколько размеров.", "shoes", 2200, 6)
        add_product("sneaker", "kravtsov", "Кроссовки для зала", "Ровная подошва, не оставляют след.", "shoes", 4600, 4)
        add_product("latin_shoe", "kravtsov", "Туфли латина", "Каблук 5 см, телесные.", "shoes", 3900, 3)
        add_product("warmers", "shirokova", "Гетры", "Вязаные, серые.", "accessory", 650, 12)
        add_product("bag", "shirokova", "Сумка для формы", "Отделение под обувь.", "accessory", 2100, 8)

        costume_order = add_order("volkova", "leo", 1, "completed", "2026-09-15 13:00:00")
        add_order("egorov", "sneaker", 1, "accepted", "2026-10-08 17:20:00")
        add_order("kim", "warmers", 2, "new", "2026-10-11 10:05:00")
        _log(conn, "order", costume_order, ids["volkova"], "Ученик забрал заказ", "2026-09-16 12:00:00")
        _grant_order(conn, costume_order, "2026-09-16 12:00:00")

        review_specs = (
            ("volkova", "teacher", ids["orlova"], 5, "Станок собран по делу, без лишней паузы.", "2026-09-09 19:00:00"),
            ("egorov", "teacher", ids["orlova"], 4, "Понятно, темп для хип-хопа непривычный.", "2026-09-09 19:20:00"),
            ("volkova", "class", classes["exersis"], 5, "Адажио в конце как раз по силам.", "2026-09-09 19:05:00"),
            ("egorov", "teacher", ids["gromov"], 5, "Круг не развалился, поправил стойку.", "2026-09-11 18:00:00"),
            ("kim", "teacher", ids["danilova"], 5, "Первый контемп, не было страшно лечь на пол.", "2026-09-15 18:10:00"),
            ("zaitseva", "teacher", ids["petrova"], 4, "Связка села, каблук ещё мешает.", "2026-09-17 18:00:00"),
            ("volkova", "teacher", ids["sokol"], 5, "Квадрат наконец ровный.", "2026-09-19 18:00:00"),
            ("volkova", "product", products["leo"]["id"], 5, "Сел по фигуре, на станке не сползает.", "2026-09-20 12:00:00"),
        )
        for author, kind, target_id, rating, body, created in review_specs:
            review_id = add_review(author, kind, target_id, rating, body, created)
            _grant_source(conn, ids[author], f"review:{review_id}", XP_REVIEW, "Оценка", created)

    from olesya import matching

    matching.distribute(battle_id, None)
    matching.distribute(floor_id, None)


def _log(conn, kind, entity_id, user_id, action, created_at=None):
    conn.execute(
        "INSERT INTO history (entity_kind, entity_id, user_id, action, created_at) VALUES (?, ?, ?, ?, ?)",
        (kind, entity_id, user_id, action, created_at or now()),
    )


def list_history(kind, entity_id):
    conn = connect()
    rows = conn.execute(
        "SELECT h.*, u.full_name AS user_name FROM history h"
        " LEFT JOIN users u ON u.id = h.user_id"
        " WHERE h.entity_kind = ? AND h.entity_id = ? ORDER BY h.id",
        (kind, entity_id),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _as_int(value, minimum, maximum, label):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None, f"{label}: нужно целое число"
    if number < minimum or number > maximum:
        return None, f"{label}: от {minimum} до {maximum}"
    return number, None


def _parse_date(text, allow_empty=False, not_past=False):
    text = (text or "").strip()
    if not text and allow_empty:
        return "", None
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        return None, "Дата в формате ГГГГ-ММ-ДД"
    if not_past and text < today():
        return None, "Дата уже прошла"
    return text, None


def _open_request_duplicate(conn, student_id, title, exclude_id=None):
    key = title.strip().casefold()
    rows = conn.execute(
        "SELECT id, title FROM requests WHERE student_id = ? AND status IN ('new', 'assigned')",
        (student_id,),
    ).fetchall()
    for row in rows:
        if exclude_id is not None and row["id"] == exclude_id:
            continue
        if row["title"].strip().casefold() == key:
            return row["id"]
    return None


def _grant_source(conn, user_id, source, amount, reason, created_at=None):
    if amount <= 0:
        return 0
    user = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user or user["role"] != "student":
        return 0
    exists = conn.execute(
        "SELECT 1 FROM xp_log WHERE user_id = ? AND source = ?",
        (user_id, source),
    ).fetchone()
    if exists:
        return 0
    stamp = created_at or now()
    conn.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (amount, user_id))
    conn.execute(
        "INSERT INTO xp_log (user_id, source, amount, reason, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, source, amount, reason, stamp),
    )
    return amount + _sync_badges(conn, user_id, stamp)


def _sync_badges(conn, user_id, created_at=None):
    owned = {
        row["code"]
        for row in conn.execute("SELECT code FROM user_badges WHERE user_id = ?", (user_id,)).fetchall()
    }
    earned = _eligible_badges(conn, user_id)
    bonus = 0
    stamp = created_at or now()
    for code in earned:
        if code in owned:
            continue
        _code, title, _detail, amount = BADGE_BY[code]
        source = f"badge:{code}"
        if conn.execute(
            "SELECT 1 FROM xp_log WHERE user_id = ? AND source = ?",
            (user_id, source),
        ).fetchone():
            continue
        conn.execute(
            "INSERT INTO user_badges (user_id, code, created_at) VALUES (?, ?, ?)",
            (user_id, code, stamp),
        )
        conn.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (amount, user_id))
        conn.execute(
            "INSERT INTO xp_log (user_id, source, amount, reason, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, source, amount, f"Значок «{title}»", stamp),
        )
        bonus += amount
        owned.add(code)
    return bonus


def _eligible_badges(conn, user_id):
    done_classes = conn.execute(
        "SELECT COUNT(*) FROM enrollments WHERE student_id = ? AND status = 'completed'",
        (user_id,),
    ).fetchone()[0]
    styles = conn.execute(
        "SELECT COUNT(DISTINCT c.style) FROM enrollments e"
        " JOIN classes c ON c.id = e.class_id"
        " WHERE e.student_id = ? AND e.status = 'completed'",
        (user_id,),
    ).fetchone()[0]
    lessons = conn.execute(
        "SELECT COUNT(*) FROM requests WHERE student_id = ? AND status = 'done'",
        (user_id,),
    ).fetchone()[0]
    reviews = conn.execute(
        "SELECT COUNT(*) FROM reviews WHERE author_id = ?",
        (user_id,),
    ).fetchone()[0]
    orders = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE student_id = ? AND status = 'completed'",
        (user_id,),
    ).fetchone()[0]
    visits = conn.execute(
        "SELECT COUNT(*) FROM enrollments WHERE student_id = ? AND status IN ('confirmed', 'completed')",
        (user_id,),
    ).fetchone()[0]
    codes = []
    if done_classes >= 1:
        codes.append("debut")
    if done_classes >= 5:
        codes.append("five")
    if done_classes >= 10:
        codes.append("ten")
    if styles >= 3:
        codes.append("palette")
    if lessons >= 1:
        codes.append("solo")
    if reviews >= 1:
        codes.append("voice")
    if orders >= 1:
        codes.append("costume")
    if visits >= 3:
        codes.append("regular")
    return codes


def _class_xp(hours):
    return XP_CLASS_BASE + XP_CLASS_HOUR * int(hours)


def _grant_enrollment(conn, enrollment_id, created_at=None):
    row = conn.execute(
        "SELECT e.student_id, e.status, c.duration_hours, c.title"
        " FROM enrollments e JOIN classes c ON c.id = e.class_id WHERE e.id = ?",
        (enrollment_id,),
    ).fetchone()
    if not row or row["status"] != "completed":
        return 0
    return _grant_source(
        conn,
        row["student_id"],
        f"enroll:{enrollment_id}",
        _class_xp(row["duration_hours"]),
        f"Занятие «{row['title']}»",
        created_at,
    )


def _grant_request(conn, request_id, created_at=None):
    row = conn.execute(
        "SELECT student_id, status, title FROM requests WHERE id = ?",
        (request_id,),
    ).fetchone()
    if not row or row["status"] != "done":
        return 0
    return _grant_source(
        conn,
        row["student_id"],
        f"request:{request_id}",
        XP_LESSON,
        f"Урок «{row['title']}»",
        created_at,
    )


def _grant_order(conn, order_id, created_at=None):
    row = conn.execute(
        "SELECT student_id, status FROM orders WHERE id = ?",
        (order_id,),
    ).fetchone()
    if not row or row["status"] != "completed":
        return 0
    return _grant_source(
        conn,
        row["student_id"],
        f"order:{order_id}",
        XP_ORDER,
        "Заказ из гардероба",
        created_at,
    )


def leaderboard(limit=10):
    conn = connect()
    rows = conn.execute(
        "SELECT id, full_name, xp FROM users WHERE role = 'student' AND is_active = 1"
        " ORDER BY xp DESC, full_name LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    board = []
    for row in rows:
        item = dict(row)
        item["rank_name"] = rank_of(item["xp"])["name"]
        board.append(item)
    return board


def badge_board(user_id):
    conn = connect()
    owned = {
        row["code"]: row["created_at"]
        for row in conn.execute(
            "SELECT code, created_at FROM user_badges WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    }
    conn.close()
    board = []
    for code, title, detail, bonus in BADGES:
        board.append(
            {
                "code": code,
                "title": title,
                "detail": detail,
                "bonus": bonus,
                "unlocked": code in owned,
                "unlocked_at": owned.get(code, ""),
            }
        )
    return board


def list_xp(user_id, limit=8):
    conn = connect()
    rows = conn.execute(
        "SELECT amount, reason, created_at FROM xp_log WHERE user_id = ?"
        " ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_user(login, password, full_name, role="student", style="other", branch="other", about="", is_active=1):
    login = login.strip().lower()
    full_name = full_name.strip()
    about = about.strip()
    if not re.fullmatch(r"[a-z0-9_]{3,32}", login):
        return False, "Логин: 3–32 символа, латиница, цифры и _"
    if not full_name or len(full_name) > 80:
        return False, "Укажите ФИО, не длиннее 80 символов"
    if len(password) < 4 or len(password) > 64:
        return False, "Пароль от 4 до 64 символов"
    if role not in ROLES:
        return False, "Неизвестная роль"
    if style not in STYLES:
        return False, "Неизвестный стиль"
    if branch not in BRANCHES:
        return False, "Неизвестная площадка"
    if len(about) > 300:
        return False, "Текст «о себе» слишком длинный"
    conn = connect()
    try:
        with conn:
            conn.execute(
                "INSERT INTO users (login, password, full_name, role, style, branch, about, is_active, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (login, hash_password(password), full_name, role, style, branch, about, int(is_active), now()),
            )
        return True, "Пользователь создан"
    except sqlite3.IntegrityError:
        return False, "Логин уже занят"
    finally:
        conn.close()


def authenticate(login, password):
    conn = connect()
    row = conn.execute(
        "SELECT * FROM users WHERE login = ?",
        (login.strip().lower(),),
    ).fetchone()
    conn.close()
    if not row or not verify_password(password, row["password"]):
        return None, "Неверный логин или пароль"
    if not row["is_active"]:
        return None, "Учётная запись отключена"
    return _public(row), None


def get_user(user_id):
    conn = connect()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return _public(row)


def list_users(role=None):
    conn = connect()
    if role:
        rows = conn.execute("SELECT * FROM users WHERE role = ? ORDER BY id", (role,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    conn.close()
    return [_public(row) for row in rows]


def list_teachers(only_active=True):
    conn = connect()
    sql = (
        "SELECT u.*,"
        " (SELECT COUNT(*) FROM reviews r WHERE r.target_kind = 'teacher' AND r.target_id = u.id) AS review_count,"
        " (SELECT AVG(r.rating) FROM reviews r WHERE r.target_kind = 'teacher' AND r.target_id = u.id) AS review_avg"
        " FROM users u WHERE u.role = 'teacher'"
    )
    if only_active:
        sql += " AND u.is_active = 1"
    sql += " ORDER BY u.id"
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [_public(row) for row in rows]


def teacher_rating(teacher):
    count = int(teacher.get("review_count") or 0)
    if count <= 0 or teacher.get("review_avg") is None:
        return None
    return float(teacher["review_avg"])


def update_user(user_id, **fields):
    allowed = {"full_name", "role", "style", "branch", "about", "is_active", "password"}
    values = {key: value for key, value in fields.items() if key in allowed and value is not None}
    if "password" in values:
        if not str(values["password"]):
            values.pop("password")
        elif len(values["password"]) < 4 or len(values["password"]) > 64:
            return False, "Пароль от 4 до 64 символов"
        else:
            values["password"] = hash_password(values["password"])
    if "full_name" in values:
        values["full_name"] = values["full_name"].strip()
        if not values["full_name"] or len(values["full_name"]) > 80:
            return False, "Укажите ФИО, не длиннее 80 символов"
    if "about" in values:
        values["about"] = values["about"].strip()
        if len(values["about"]) > 300:
            return False, "Текст «о себе» слишком длинный"
    if "role" in values and values["role"] not in ROLES:
        return False, "Неизвестная роль"
    if "style" in values and values["style"] not in STYLES:
        return False, "Неизвестный стиль"
    if "branch" in values and values["branch"] not in BRANCHES:
        return False, "Неизвестная площадка"
    if "is_active" in values:
        values["is_active"] = int(values["is_active"])
    if not values:
        return False, "Нет изменений"

    conn = connect()
    try:
        with conn:
            current = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if not current:
                return False, "Пользователь не найден"
            new_role = values.get("role", current["role"])
            new_active = int(values.get("is_active", current["is_active"]))
            loses_admin = (
                current["role"] == "admin"
                and current["is_active"]
                and not (new_role == "admin" and new_active == 1)
            )
            if loses_admin:
                others = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1 AND id != ?",
                    (user_id,),
                ).fetchone()[0]
                if others == 0:
                    return False, "Нельзя снять последнего активного администратора"
            assignments = ", ".join(f"{key} = ?" for key in values)
            conn.execute(
                f"UPDATE users SET {assignments} WHERE id = ?",
                (*values.values(), user_id),
            )
            released = 0
            was_teacher = current["role"] == "teacher" and current["is_active"]
            stays_teacher = new_role == "teacher" and new_active == 1
            if was_teacher and not stays_teacher:
                released = _release_teacher_requests(conn, user_id, user_id)
        if released:
            return True, f"Сохранено. В очередь возвращено заявок: {released}"
        return True, "Сохранено"
    finally:
        conn.close()


def _release_teacher_requests(conn, teacher_id, actor_id):
    rows = conn.execute(
        "SELECT id, student_id, title FROM requests WHERE teacher_id = ? AND status = 'assigned'",
        (teacher_id,),
    ).fetchall()
    released = 0
    for row in rows:
        if _open_request_duplicate(conn, row["student_id"], row["title"], row["id"]):
            conn.execute("UPDATE requests SET status = 'cancelled' WHERE id = ?", (row["id"],))
            _log(conn, "request", row["id"], actor_id, "Заявка отменена: у ученика уже есть такая открытая")
            continue
        conn.execute(
            "UPDATE requests SET teacher_id = NULL, status = 'new' WHERE id = ?",
            (row["id"],),
        )
        _log(conn, "request", row["id"], actor_id, "Педагог снят, заявка возвращена в очередь")
        released += 1
    return released


def create_request(title, description, style, branch, people, preferred_date, priority, student_id):
    title = title.strip()
    description = description.strip()
    if not title:
        return None, "Укажите тему"
    if len(title) > 120:
        return None, "Тема слишком длинная"
    if len(description) > 2000:
        return None, "Описание слишком длинное"
    if style not in STYLES:
        return None, "Неизвестный стиль"
    if branch not in BRANCHES:
        return None, "Неизвестная площадка"
    if priority not in PRIORITIES:
        return None, "Неизвестный приоритет"
    people_count, error = _as_int(people, 1, 12, "Число людей")
    if error:
        return None, error
    preferred, error = _parse_date(preferred_date, allow_empty=True, not_past=True)
    if error:
        return None, error
    conn = connect()
    try:
        with conn:
            student = conn.execute(
                "SELECT role, is_active FROM users WHERE id = ?",
                (student_id,),
            ).fetchone()
            if not student or student["role"] != "student" or not student["is_active"]:
                return None, "Заявку создаёт активный ученик"
            if _open_request_duplicate(conn, student_id, title):
                return None, "Такая заявка уже открыта"
            cur = conn.execute(
                "INSERT INTO requests (title, description, style, branch, people, preferred_date, priority, status, student_id, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)",
                (title, description, style, branch, people_count, preferred, priority, student_id, now()),
            )
            request_id = cur.lastrowid
            _log(conn, "request", request_id, student_id, "Заявка создана")
        return request_id, None
    except sqlite3.IntegrityError:
        return None, "Такая заявка уже открыта"
    finally:
        conn.close()


_REQUEST_SQL = (
    "SELECT r.*, s.full_name AS student_name, t.full_name AS teacher_name"
    " FROM requests r"
    " JOIN users s ON s.id = r.student_id"
    " LEFT JOIN users t ON t.id = r.teacher_id"
)


def list_requests(student_id=None, teacher_id=None, status=None):
    conn = connect()
    sql = _REQUEST_SQL + " WHERE 1=1"
    params = []
    if student_id is not None:
        sql += " AND r.student_id = ?"
        params.append(student_id)
    if teacher_id is not None:
        sql += " AND r.teacher_id = ?"
        params.append(teacher_id)
    if status:
        sql += " AND r.status = ?"
        params.append(status)
    sql += " ORDER BY r.id DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_request(request_id):
    conn = connect()
    row = conn.execute(_REQUEST_SQL + " WHERE r.id = ?", (request_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def assign_request(request_id, teacher_id, actor_id=None, note=""):
    conn = connect()
    try:
        with conn:
            current = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
            if not current:
                return False, "Заявка не найдена"
            if current["status"] not in ("new", "assigned"):
                return False, "Заявка уже закрыта"
            if current["teacher_id"] == teacher_id and current["status"] == "assigned":
                return True, "Уже назначено"
            teacher = conn.execute(
                "SELECT full_name, role, is_active FROM users WHERE id = ?",
                (teacher_id,),
            ).fetchone()
            if not teacher or teacher["role"] != "teacher" or not teacher["is_active"]:
                return False, "Нужен активный педагог"
            conn.execute(
                "UPDATE requests SET teacher_id = ?, status = 'assigned' WHERE id = ?",
                (teacher_id, request_id),
            )
            action = f"Назначен педагог: {teacher['full_name']}"
            if note:
                action += f" ({note})"
            _log(conn, "request", request_id, actor_id, action)
        return True, "Педагог назначен"
    finally:
        conn.close()


def take_request(request_id, teacher_id):
    conn = connect()
    try:
        row = conn.execute(
            "SELECT teacher_id, status FROM requests WHERE id = ?",
            (request_id,),
        ).fetchone()
        teacher = conn.execute(
            "SELECT role, is_active FROM users WHERE id = ?",
            (teacher_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return False, "Заявка не найдена"
    if not teacher or teacher["role"] != "teacher" or not teacher["is_active"]:
        return False, "Взять заявку может только активный педагог"
    if row["status"] != "new" or row["teacher_id"] is not None:
        return False, "Заявка уже назначена"
    ok, message = assign_request(request_id, teacher_id, teacher_id, note="педагог взял сам")
    if ok:
        return True, "Заявка у вас"
    return False, message


def set_request_status(request_id, status, actor_id):
    if status not in ("done", "cancelled"):
        return False, "Неизвестный статус"
    conn = connect()
    try:
        with conn:
            current = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
            actor = conn.execute("SELECT * FROM users WHERE id = ?", (actor_id,)).fetchone()
            if not current:
                return False, "Заявка не найдена"
            if not actor or not actor["is_active"]:
                return False, "Недостаточно прав"
            if current["status"] in ("done", "cancelled"):
                return False, "Заявка уже закрыта"
            is_admin = actor["role"] == "admin"
            is_author = actor["id"] == current["student_id"]
            is_teacher = actor["role"] == "teacher" and actor["id"] == current["teacher_id"]
            if status == "done":
                if current["status"] != "assigned" or not current["teacher_id"]:
                    return False, "Завершить можно только назначенную заявку"
                if not (is_admin or is_teacher):
                    return False, "Недостаточно прав"
            else:
                if not (is_admin or is_author or is_teacher):
                    return False, "Недостаточно прав"
            conn.execute("UPDATE requests SET status = ? WHERE id = ?", (status, request_id))
            _log(conn, "request", request_id, actor_id, f"Статус: {REQUEST_STATUS_RU[status]}")
            gained = _grant_request(conn, request_id) if status == "done" else 0
        if gained:
            return True, f"Урок проведён. Ученику +{gained} XP"
        return True, "Статус обновлён"
    finally:
        conn.close()


def add_message(request_id, user_id, body):
    body = body.strip()
    if not body:
        return False, "Введите текст"
    if len(body) > 1000:
        return False, "Сообщение слишком длинное"
    conn = connect()
    try:
        with conn:
            request = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if not request:
                return False, "Заявка не найдена"
            if not user or not user["is_active"]:
                return False, "Недостаточно прав"
            allowed = (
                user["role"] == "admin"
                or user["id"] == request["student_id"]
                or (user["role"] == "teacher" and user["id"] == request["teacher_id"])
            )
            if not allowed:
                return False, "Писать могут ученик, назначенный педагог и администратор"
            if request["status"] in ("done", "cancelled"):
                return False, "Переписка по закрытой заявке завершена"
            conn.execute(
                "INSERT INTO messages (request_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
                (request_id, user_id, body, now()),
            )
            _log(conn, "request", request_id, user_id, "Добавлено сообщение")
        return True, "Сообщение отправлено"
    finally:
        conn.close()


def list_messages(request_id):
    conn = connect()
    rows = conn.execute(
        "SELECT m.*, u.full_name AS user_name FROM messages m"
        " JOIN users u ON u.id = m.user_id WHERE m.request_id = ? ORDER BY m.id",
        (request_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def active_load(teacher_id):
    conn = connect()
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM requests WHERE teacher_id = ? AND status = 'assigned'",
        (teacher_id,),
    ).fetchone()
    conn.close()
    return row["c"]


_CLASS_SQL = (
    "SELECT c.*, t.full_name AS teacher_name, t.style AS teacher_style,"
    " t.branch AS teacher_branch,"
    " (SELECT COUNT(*) FROM reviews r WHERE r.target_kind = 'teacher' AND r.target_id = t.id) AS review_count,"
    " (SELECT AVG(r.rating) FROM reviews r WHERE r.target_kind = 'teacher' AND r.target_id = t.id) AS review_avg,"
    " c.capacity - COALESCE(("
    "     SELECT SUM(e.people) FROM enrollments e"
    "     WHERE e.class_id = c.id AND e.status = 'confirmed'"
    " ), 0) AS seats_left"
    " FROM classes c JOIN users t ON t.id = c.teacher_id"
)


def create_class(title, description, style, branch, class_date, duration_hours, price, capacity, teacher_id):
    title = title.strip()
    description = description.strip()
    if not title or len(title) > 120:
        return None, "Укажите название, не длиннее 120 символов"
    if len(description) > 2000:
        return None, "Описание слишком длинное"
    if style not in STYLES or style == "other":
        return None, "Выберите стиль занятия"
    if branch not in BRANCHES or branch == "other":
        return None, "Выберите площадку"
    parsed_date, error = _parse_date(class_date, not_past=True)
    if error:
        return None, error
    hours, error = _as_int(duration_hours, 1, 6, "Длительность, часы")
    if error:
        return None, error
    amount, error = _as_int(price, 100, 100_000, "Цена")
    if error:
        return None, error
    seats, error = _as_int(capacity, 1, 30, "Число мест")
    if error:
        return None, error
    conn = connect()
    try:
        with conn:
            teacher = conn.execute(
                "SELECT role, is_active FROM users WHERE id = ?",
                (teacher_id,),
            ).fetchone()
            if not teacher or teacher["role"] != "teacher" or not teacher["is_active"]:
                return None, "Занятие публикует активный педагог"
            cur = conn.execute(
                "INSERT INTO classes (title, description, style, branch, class_date, duration_hours, price, capacity, teacher_id, status, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)",
                (title, description, style, branch, parsed_date, hours, amount, seats, teacher_id, now()),
            )
            class_id = cur.lastrowid
            _log(conn, "class", class_id, teacher_id, "Занятие опубликовано")
        return class_id, None
    finally:
        conn.close()


def list_classes(teacher_id=None, status=None):
    conn = connect()
    sql = _CLASS_SQL + " WHERE 1=1"
    params = []
    if teacher_id is not None:
        sql += " AND c.teacher_id = ?"
        params.append(teacher_id)
    if status:
        sql += " AND c.status = ?"
        params.append(status)
    sql += " ORDER BY c.class_date, c.id"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_class(class_id):
    conn = connect()
    row = conn.execute(_CLASS_SQL + " WHERE c.id = ?", (class_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def _taken_seats(conn, class_id):
    return conn.execute(
        "SELECT COALESCE(SUM(people), 0) FROM enrollments WHERE class_id = ? AND status = 'confirmed'",
        (class_id,),
    ).fetchone()[0]


def _sync_class_capacity(conn, class_id, actor_id):
    lesson = conn.execute("SELECT status, capacity FROM classes WHERE id = ?", (class_id,)).fetchone()
    if not lesson or lesson["status"] in ("completed", "cancelled"):
        return
    taken = _taken_seats(conn, class_id)
    new_status = "full" if taken >= lesson["capacity"] else "open"
    if new_status == lesson["status"]:
        return
    conn.execute("UPDATE classes SET status = ? WHERE id = ?", (new_status, class_id))
    if new_status == "full":
        _log(conn, "class", class_id, actor_id, "Свободных мест не осталось")
    else:
        _log(conn, "class", class_id, actor_id, "Снова есть свободные места")


def set_class_status(class_id, status, actor_id):
    if status not in ("completed", "cancelled"):
        return False, "Неизвестный статус"
    conn = connect()
    try:
        with conn:
            lesson = conn.execute("SELECT * FROM classes WHERE id = ?", (class_id,)).fetchone()
            actor = conn.execute("SELECT * FROM users WHERE id = ?", (actor_id,)).fetchone()
            if not lesson:
                return False, "Занятие не найдено"
            if not actor or not actor["is_active"]:
                return False, "Недостаточно прав"
            if lesson["status"] in ("completed", "cancelled"):
                return False, "Занятие уже закрыто"
            is_owner = actor["role"] == "teacher" and actor["id"] == lesson["teacher_id"]
            if not (actor["role"] == "admin" or is_owner):
                return False, "Недостаточно прав"
            rows = conn.execute(
                "SELECT id FROM enrollments WHERE class_id = ? AND status = 'confirmed'",
                (class_id,),
            ).fetchall()
            gained = 0
            if status == "completed":
                for row in rows:
                    conn.execute("UPDATE enrollments SET status = 'completed' WHERE id = ?", (row["id"],))
                    _log(conn, "enrollment", row["id"], actor_id, "Запись закрыта вместе с занятием")
                    gained += _grant_enrollment(conn, row["id"])
            else:
                for row in rows:
                    conn.execute("UPDATE enrollments SET status = 'cancelled' WHERE id = ?", (row["id"],))
                    _log(conn, "enrollment", row["id"], actor_id, "Запись снята: занятие отменено")
            conn.execute("UPDATE classes SET status = ? WHERE id = ?", (status, class_id))
            _log(conn, "class", class_id, actor_id, f"Статус: {CLASS_STATUS_RU[status]}")
        if status == "cancelled":
            return True, f"Занятие отменено. Снято записей: {len(rows)}"
        if gained:
            return True, f"Занятие прошло. Ученикам начислено {gained} XP"
        return True, "Занятие завершено"
    finally:
        conn.close()


def enroll(class_id, student_id, people):
    people_count, error = _as_int(people, 1, 8, "Число людей")
    if error:
        return None, error
    conn = connect()
    try:
        with conn:
            lesson = conn.execute("SELECT * FROM classes WHERE id = ?", (class_id,)).fetchone()
            student = conn.execute("SELECT * FROM users WHERE id = ?", (student_id,)).fetchone()
            if not lesson:
                return None, "Занятие не найдено"
            if not student or student["role"] != "student" or not student["is_active"]:
                return None, "Запись оформляет активный ученик"
            if lesson["status"] != "open":
                return None, "На это занятие сейчас нельзя записаться"
            existing = conn.execute(
                "SELECT id FROM enrollments WHERE class_id = ? AND student_id = ? AND status = 'confirmed'",
                (class_id, student_id),
            ).fetchone()
            if existing:
                return None, "Вы уже записаны на это занятие"
            left = lesson["capacity"] - _taken_seats(conn, class_id)
            if people_count > left:
                return None, f"Свободно мест: {left}"
            cur = conn.execute(
                "INSERT INTO enrollments (class_id, student_id, people, status, created_at) VALUES (?, ?, ?, 'confirmed', ?)",
                (class_id, student_id, people_count, now()),
            )
            enrollment_id = cur.lastrowid
            _log(conn, "enrollment", enrollment_id, student_id, "Запись оформлена")
            _log(conn, "class", class_id, student_id, f"Новая запись: {people_count} чел.")
            _sync_class_capacity(conn, class_id, student_id)
            _sync_badges(conn, student_id)
        return enrollment_id, None
    except sqlite3.IntegrityError:
        return None, "Вы уже записаны на это занятие"
    finally:
        conn.close()


def cancel_enrollment(enrollment_id, actor_id):
    conn = connect()
    try:
        with conn:
            enrollment = conn.execute("SELECT * FROM enrollments WHERE id = ?", (enrollment_id,)).fetchone()
            actor = conn.execute("SELECT * FROM users WHERE id = ?", (actor_id,)).fetchone()
            if not enrollment:
                return False, "Запись не найдена"
            if not actor or not actor["is_active"]:
                return False, "Недостаточно прав"
            if enrollment["status"] != "confirmed":
                return False, "Снять можно только действующую запись"
            lesson = conn.execute("SELECT * FROM classes WHERE id = ?", (enrollment["class_id"],)).fetchone()
            is_owner = actor["id"] == enrollment["student_id"]
            is_teacher = actor["role"] == "teacher" and lesson and actor["id"] == lesson["teacher_id"]
            if not (is_owner or is_teacher or actor["role"] == "admin"):
                return False, "Недостаточно прав"
            conn.execute("UPDATE enrollments SET status = 'cancelled' WHERE id = ?", (enrollment_id,))
            _log(conn, "enrollment", enrollment_id, actor_id, "Запись снята")
            _sync_class_capacity(conn, enrollment["class_id"], actor_id)
        return True, "Запись снята"
    finally:
        conn.close()


_ENROLL_SQL = (
    "SELECT e.*, c.title AS class_title, c.class_date AS class_date, c.price AS price,"
    " c.status AS class_status, c.teacher_id AS teacher_id, c.style AS style,"
    " teacher.full_name AS teacher_name, student.full_name AS student_name"
    " FROM enrollments e"
    " JOIN classes c ON c.id = e.class_id"
    " JOIN users teacher ON teacher.id = c.teacher_id"
    " JOIN users student ON student.id = e.student_id"
)


def list_enrollments(student_id=None, teacher_id=None, class_id=None):
    conn = connect()
    sql = _ENROLL_SQL + " WHERE 1=1"
    params = []
    if student_id is not None:
        sql += " AND e.student_id = ?"
        params.append(student_id)
    if teacher_id is not None:
        sql += " AND c.teacher_id = ?"
        params.append(teacher_id)
    if class_id is not None:
        sql += " AND e.class_id = ?"
        params.append(class_id)
    sql += " ORDER BY e.id DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_enrollment(enrollment_id):
    conn = connect()
    row = conn.execute(_ENROLL_SQL + " WHERE e.id = ?", (enrollment_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def confirmed_enrollment(class_id, student_id):
    conn = connect()
    row = conn.execute(
        "SELECT * FROM enrollments WHERE class_id = ? AND student_id = ? AND status = 'confirmed'",
        (class_id, student_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_product(atelier_id, name, description, category, price, stock):
    name = name.strip()
    description = description.strip()
    if not name or len(name) > 80:
        return None, "Укажите название, не длиннее 80 символов"
    if len(description) > 1000:
        return None, "Описание слишком длинное"
    if category not in PRODUCT_CATEGORIES:
        return None, "Неизвестная категория"
    amount, error = _as_int(price, 1, 200_000, "Цена")
    if error:
        return None, error
    qty, error = _as_int(stock, 0, 10_000, "Остаток")
    if error:
        return None, error
    conn = connect()
    try:
        with conn:
            atelier = conn.execute("SELECT * FROM users WHERE id = ?", (atelier_id,)).fetchone()
            if not atelier or atelier["role"] != "atelier" or not atelier["is_active"]:
                return None, "Вещь добавляет активный костюмер"
            if _product_name_taken(conn, atelier_id, name):
                return None, "Такая вещь уже есть"
            cur = conn.execute(
                "INSERT INTO products (atelier_id, name, description, category, price, stock, is_active, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
                (atelier_id, name, description, category, amount, qty, now()),
            )
        return cur.lastrowid, None
    finally:
        conn.close()


def _product_name_taken(conn, atelier_id, name, exclude_id=None):
    key = name.strip().casefold()
    rows = conn.execute(
        "SELECT id, name FROM products WHERE atelier_id = ?",
        (atelier_id,),
    ).fetchall()
    for row in rows:
        if exclude_id is not None and row["id"] == exclude_id:
            continue
        if row["name"].strip().casefold() == key:
            return True
    return False


def update_product(product_id, actor_id, **fields):
    allowed = {"name", "description", "category", "price", "stock", "is_active"}
    values = {key: value for key, value in fields.items() if key in allowed and value is not None}
    conn = connect()
    try:
        with conn:
            product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            actor = conn.execute("SELECT * FROM users WHERE id = ?", (actor_id,)).fetchone()
            if not product:
                return False, "Вещь не найдена"
            if not actor or not actor["is_active"]:
                return False, "Недостаточно прав"
            if actor["role"] != "admin" and actor["id"] != product["atelier_id"]:
                return False, "Недостаточно прав"
            if "name" in values:
                values["name"] = values["name"].strip()
                if not values["name"] or len(values["name"]) > 80:
                    return False, "Укажите название, не длиннее 80 символов"
                if _product_name_taken(conn, product["atelier_id"], values["name"], product_id):
                    return False, "Такая вещь уже есть"
            if "description" in values:
                values["description"] = values["description"].strip()
                if len(values["description"]) > 1000:
                    return False, "Описание слишком длинное"
            if "category" in values and values["category"] not in PRODUCT_CATEGORIES:
                return False, "Неизвестная категория"
            if "price" in values:
                amount, error = _as_int(values["price"], 1, 200_000, "Цена")
                if error:
                    return False, error
                values["price"] = amount
            if "stock" in values:
                qty, error = _as_int(values["stock"], 0, 10_000, "Остаток")
                if error:
                    return False, error
                values["stock"] = qty
            if "is_active" in values:
                values["is_active"] = 1 if values["is_active"] else 0
            if not values:
                return False, "Нет изменений"
            assignments = ", ".join(f"{key} = ?" for key in values)
            conn.execute(
                f"UPDATE products SET {assignments} WHERE id = ?",
                (*values.values(), product_id),
            )
        return True, "Вещь сохранена"
    finally:
        conn.close()


_PRODUCT_SQL = (
    "SELECT p.*, u.full_name AS atelier_name, u.branch AS branch, u.is_active AS atelier_active"
    " FROM products p JOIN users u ON u.id = p.atelier_id"
)


def list_products(atelier_id=None, branch=None, only_market=False):
    conn = connect()
    sql = _PRODUCT_SQL + " WHERE 1=1"
    params = []
    if atelier_id is not None:
        sql += " AND p.atelier_id = ?"
        params.append(atelier_id)
    if branch:
        sql += " AND u.branch = ?"
        params.append(branch)
    if only_market:
        sql += " AND p.is_active = 1 AND u.is_active = 1 AND u.role = 'atelier'"
    sql += " ORDER BY p.name"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_product(product_id):
    conn = connect()
    row = conn.execute(_PRODUCT_SQL + " WHERE p.id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_order(student_id, product_id, qty):
    amount, error = _as_int(qty, 1, 12, "Количество")
    if error:
        return None, error
    conn = connect()
    try:
        with conn:
            student = conn.execute("SELECT * FROM users WHERE id = ?", (student_id,)).fetchone()
            product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if not student or student["role"] != "student" or not student["is_active"]:
                return None, "Заказ оформляет активный ученик"
            if not product or not product["is_active"]:
                return None, "Вещь недоступна"
            atelier = conn.execute("SELECT * FROM users WHERE id = ?", (product["atelier_id"],)).fetchone()
            if not atelier or atelier["role"] != "atelier" or not atelier["is_active"]:
                return None, "Костюмер сейчас недоступен"
            if amount > product["stock"]:
                return None, f"На складе осталось: {product['stock']}"
            updated = conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
                (amount, product_id, amount),
            )
            if updated.rowcount != 1:
                return None, "На складе уже не хватает"
            total = product["price"] * amount
            cur = conn.execute(
                "INSERT INTO orders (student_id, atelier_id, status, total, created_at) VALUES (?, ?, 'new', ?, ?)",
                (student_id, product["atelier_id"], total, now()),
            )
            order_id = cur.lastrowid
            conn.execute(
                "INSERT INTO order_items (order_id, product_id, name, qty, price) VALUES (?, ?, ?, ?, ?)",
                (order_id, product_id, product["name"], amount, product["price"]),
            )
            _log(conn, "order", order_id, student_id, "Заказ оформлен")
        return order_id, None
    finally:
        conn.close()


_ORDER_SQL = (
    "SELECT o.*, s.full_name AS student_name, a.full_name AS atelier_name,"
    " (SELECT group_concat(oi.name || ' × ' || oi.qty, ', ') FROM order_items oi WHERE oi.order_id = o.id) AS items_label"
    " FROM orders o"
    " JOIN users s ON s.id = o.student_id"
    " JOIN users a ON a.id = o.atelier_id"
)


def list_orders(student_id=None, atelier_id=None):
    conn = connect()
    sql = _ORDER_SQL + " WHERE 1=1"
    params = []
    if student_id is not None:
        sql += " AND o.student_id = ?"
        params.append(student_id)
    if atelier_id is not None:
        sql += " AND o.atelier_id = ?"
        params.append(atelier_id)
    sql += " ORDER BY o.id DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_order(order_id):
    conn = connect()
    row = conn.execute(_ORDER_SQL + " WHERE o.id = ?", (order_id,)).fetchone()
    items = []
    if row:
        items = [
            dict(item)
            for item in conn.execute(
                "SELECT * FROM order_items WHERE order_id = ? ORDER BY id",
                (order_id,),
            ).fetchall()
        ]
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["items"] = items
    return data


def set_order_status(order_id, status, actor_id):
    if status not in ORDER_STATUSES:
        return False, "Неизвестный статус"
    conn = connect()
    try:
        with conn:
            order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            actor = conn.execute("SELECT * FROM users WHERE id = ?", (actor_id,)).fetchone()
            if not order:
                return False, "Заказ не найден"
            if not actor or not actor["is_active"]:
                return False, "Недостаточно прав"
            if status not in ORDER_FLOW[order["status"]]:
                return False, "Так статус сменить нельзя"
            is_atelier = actor["role"] == "atelier" and actor["id"] == order["atelier_id"]
            is_student = actor["id"] == order["student_id"]
            is_admin = actor["role"] == "admin"
            if status == "cancelled":
                student_can = is_student and order["status"] == "new"
                if not (is_admin or is_atelier or student_can):
                    return False, "Отменить заказ может костюмер, администратор или ученик, пока заказ новый"
            elif not (is_admin or is_atelier):
                return False, "Статус заказа меняет костюмер"
            if status == "cancelled":
                for item in conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)):
                    conn.execute(
                        "UPDATE products SET stock = stock + ? WHERE id = ?",
                        (item["qty"], item["product_id"]),
                    )
            conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
            _log(conn, "order", order_id, actor_id, f"Статус: {ORDER_STATUS_RU[status]}")
            gained = _grant_order(conn, order_id) if status == "completed" else 0
        if gained:
            return True, f"Заказ выдан. Ученику +{gained} XP"
        return True, "Статус заказа обновлён"
    finally:
        conn.close()


def can_review(author_id, kind, target_id):
    if find_review(author_id, kind, target_id):
        return False
    conn = connect()
    try:
        return _review_eligible(conn, author_id, kind, target_id)
    finally:
        conn.close()


def find_review(author_id, kind, target_id):
    conn = connect()
    row = conn.execute(
        "SELECT r.*, u.full_name AS author_name FROM reviews r"
        " JOIN users u ON u.id = r.author_id"
        " WHERE r.author_id = ? AND r.target_kind = ? AND r.target_id = ?",
        (author_id, kind, target_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def _review_eligible(conn, author_id, kind, target_id):
    author = conn.execute("SELECT role FROM users WHERE id = ?", (author_id,)).fetchone()
    if not author or author["role"] != "student":
        return False
    if kind == "teacher":
        request = conn.execute(
            "SELECT 1 FROM requests WHERE student_id = ? AND teacher_id = ? AND status = 'done'",
            (author_id, target_id),
        ).fetchone()
        enrollment = conn.execute(
            "SELECT 1 FROM enrollments e JOIN classes c ON c.id = e.class_id"
            " WHERE e.student_id = ? AND c.teacher_id = ? AND e.status = 'completed'",
            (author_id, target_id),
        ).fetchone()
        return bool(request or enrollment)
    if kind == "class":
        return bool(conn.execute(
            "SELECT 1 FROM enrollments WHERE student_id = ? AND class_id = ? AND status = 'completed'",
            (author_id, target_id),
        ).fetchone())
    if kind == "product":
        return bool(conn.execute(
            "SELECT 1 FROM orders o JOIN order_items i ON i.order_id = o.id"
            " WHERE o.student_id = ? AND i.product_id = ? AND o.status = 'completed'",
            (author_id, target_id),
        ).fetchone())
    return False


def add_review(author_id, kind, target_id, rating, body):
    if kind not in REVIEW_KINDS:
        return False, "Неизвестный тип оценки"
    stars, error = _as_int(rating, 1, 5, "Оценка")
    if error:
        return False, error
    body = (body or "").strip()
    if len(body) > 500:
        return False, "Текст оценки слишком длинный"
    conn = connect()
    try:
        with conn:
            existing = conn.execute(
                "SELECT 1 FROM reviews WHERE author_id = ? AND target_kind = ? AND target_id = ?",
                (author_id, kind, target_id),
            ).fetchone()
            if existing:
                return False, "Вы уже оставляли оценку"
            if not _review_eligible(conn, author_id, kind, target_id):
                return False, "Оценку можно поставить после завершения"
            cur = conn.execute(
                "INSERT INTO reviews (author_id, target_kind, target_id, rating, body, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (author_id, kind, target_id, stars, body, now()),
            )
            gained = _grant_source(
                conn,
                author_id,
                f"review:{cur.lastrowid}",
                XP_REVIEW,
                "Оценка",
            )
        if gained:
            return True, f"Оценка сохранена. +{gained} XP"
        return True, "Оценка сохранена"
    except sqlite3.IntegrityError:
        return False, "Вы уже оставляли оценку"
    finally:
        conn.close()


def stats():
    conn = connect()

    def scalar(sql, params=()):
        return conn.execute(sql, params).fetchone()[0]

    data = {
        "users": scalar("SELECT COUNT(*) FROM users"),
        "teachers": scalar("SELECT COUNT(*) FROM users WHERE role = 'teacher' AND is_active = 1"),
        "ateliers": scalar("SELECT COUNT(*) FROM users WHERE role = 'atelier' AND is_active = 1"),
        "students": scalar("SELECT COUNT(*) FROM users WHERE role = 'student' AND is_active = 1"),
        "unassigned": scalar(
            "SELECT COUNT(*) FROM requests WHERE teacher_id IS NULL AND status = 'new'"
        ),
        "open_classes": scalar("SELECT COUNT(*) FROM classes WHERE status IN ('open', 'full')"),
        "active_enrollments": scalar("SELECT COUNT(*) FROM enrollments WHERE status = 'confirmed'"),
        "new_orders": scalar("SELECT COUNT(*) FROM orders WHERE status = 'new'"),
        "products": scalar(
            "SELECT COUNT(*) FROM products p JOIN users u ON u.id = p.atelier_id"
            " WHERE p.is_active = 1 AND u.is_active = 1 AND u.role = 'atelier'"
        ),
    }
    conn.close()
    return data
