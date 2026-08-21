from app import service, utils

from app import tasks  # noqa: F401  (ensures package import order)


def run_job():
    users = service.list_users()
    return utils.hash_key(str(len(users)))
