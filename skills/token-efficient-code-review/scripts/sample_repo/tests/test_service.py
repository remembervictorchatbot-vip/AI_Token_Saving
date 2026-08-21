from app import service, utils


def test_create_user():
    assert service.create_user("Bob", "bob@example.com")


def test_slugify_used():
    assert utils.slugify("Hello World") == "hello_world"


def test_list_users():
    assert isinstance(service.list_users(), list)
