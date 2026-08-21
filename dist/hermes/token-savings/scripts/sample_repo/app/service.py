from app import db, utils


def create_user(name: str, email: str):
    slug = utils.slugify(name)
    return db.insert_user(slug, email)


def list_users():
    return db.query("SELECT * FROM users")


def get_user(name: str):
    return db.find_user(name)


def charge_user(uid: int, amount: float):
    amt = utils.format_money(amount)
    return db.execute("UPDATE users SET balance=? WHERE id=?", (amt, uid))


def delete_user(uid: int):
    return db.delete_user(uid)


def user_count():
    return db.count_users()
