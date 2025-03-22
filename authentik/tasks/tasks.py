from dramatiq import actor


@actor
def test_actor():
    import time

    time.sleep(5)
    print("done sleeping")
