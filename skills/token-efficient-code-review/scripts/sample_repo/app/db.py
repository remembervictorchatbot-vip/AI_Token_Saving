"""Low-level data access. Deliberately large so whole-repo review is expensive.

This module is imported by service.py and utils-dependent modules; it exists to
show how a *dependent* module can bloat context if you are not careful about
which symbols you actually pull in.
"""

import sqlite3

from app import utils

CONNECTION = None


def connect(path: str = ":memory:"):
    global CONNECTION
    CONNECTION = sqlite3.connect(path)
    return CONNECTION


def disconnect():
    global CONNECTION
    if CONNECTION is not None:
        CONNECTION.close()
        CONNECTION = None


def _conn():
    if CONNECTION is None:
        raise RuntimeError("not connected; call connect() first")
    return CONNECTION


def execute(sql: str, params=None):
    cur = _conn().execute(sql, params or ())
    _conn().commit()
    return cur


def query(sql: str, params=None):
    cur = _conn().execute(sql, params or ())
    return cur.fetchall()


def insert_user(slug: str, email: str):
    key = utils.slugify(slug)
    return execute(
        "INSERT INTO users (slug, email) VALUES (?, ?)", (key, email)
    )


def update_user(uid: int, email: str):
    return execute("UPDATE users SET email=? WHERE id=?", (email, uid))


def delete_user(uid: int):
    return execute("DELETE FROM users WHERE id=?", (uid,))


def find_user(slug: str):
    return query("SELECT * FROM users WHERE slug=?", (utils.slugify(slug),))


def count_users():
    return query("SELECT COUNT(*) FROM users")[0][0]


def insert_order(user_id: int, total: float):
    amt = utils.format_money(total)
    return execute(
        "INSERT INTO orders (user_id, total) VALUES (?, ?)", (user_id, amt)
    )


def list_orders(user_id: int):
    return query("SELECT * FROM orders WHERE user_id=?", (user_id,))


def migrate():
    execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, slug TEXT, email TEXT)")
    execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, total TEXT)")


def healthcheck():
    return query("SELECT 1")


def backup(target: str):
    with open(target, "w") as fh:
        for row in query("SELECT * FROM users"):
            fh.write(str(row) + "\n")


def restore(source: str):
    with open(source) as fh:
        return [line.strip() for line in fh]


def explain(sql: str):
    return query("EXPLAIN " + sql)


def vacuum():
    return execute("VACUUM")


def raw(sql: str, params=None):
    return query(sql, params)


def last_insert_id():
    return query("SELECT last_insert_rowid()")[0][0]
