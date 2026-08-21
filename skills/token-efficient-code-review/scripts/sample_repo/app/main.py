from app import service, utils


def boot():
    safe = utils.clamp(5, 0, 10)
    print("boot value", safe)
    return service.list_users()
