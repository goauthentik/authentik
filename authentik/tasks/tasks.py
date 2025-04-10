from dramatiq import actor


@actor
def test_actor():
    import time

    time.sleep(2)
    print("done sleeping")
