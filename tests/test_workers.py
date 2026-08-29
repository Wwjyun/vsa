def test_background_worker_returns_result(qtbot):
    from vsa.workers import FunctionWorker

    worker = FunctionWorker(lambda: 42)
    with qtbot.waitSignal(worker.signals.succeeded, timeout=2000) as result:
        worker.run()
    assert result.args == [42]


def test_background_worker_forwards_failure(qtbot):
    from vsa.workers import FunctionWorker

    def fail():
        raise ValueError("synthetic failure")

    worker = FunctionWorker(fail)
    with qtbot.waitSignal(worker.signals.failed, timeout=2000) as failure:
        worker.run()
    assert isinstance(failure.args[0], ValueError)
