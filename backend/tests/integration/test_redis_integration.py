

def test_redis_client_connection(integration_redis_client):
    assert integration_redis_client.ping()


def test_redis_client_set_get(integration_redis_client):
    integration_redis_client.set("test_key", "test_value")
    value = integration_redis_client.get("test_key")
    assert value == "test_value"


def test_redis_client_delete(integration_redis_client):
    integration_redis_client.set("test_key", "test_value")
    integration_redis_client.delete("test_key")
    value = integration_redis_client.get("test_key")
    assert value is None


def test_redis_client_expire(integration_redis_client):
    integration_redis_client.set("test_key", "test_value")
    integration_redis_client.expire("test_key", 1)
    import time
    time.sleep(1.5)
    value = integration_redis_client.get("test_key")
    assert value is None
