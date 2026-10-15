"""Engine shutdown must not block the loop or lose cleanup on cancellation."""
import asyncio
import threading

import pytest

from dspy.clients.engines.lm15_engine import AsyncLM15Engine


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel", [False, True])
async def test_close_waits_for_engine_lock_off_loop(monkeypatch, cancel):
    engine = AsyncLM15Engine()
    entered, release = threading.Event(), threading.Event()
    closed = []
    loop_thread = threading.get_ident()

    async def close_router():
        closed.append(threading.get_ident())

    monkeypatch.setattr(engine.router, "aclose", close_router)

    def construct():
        with engine._lock:
            entered.set()
            assert release.wait(3), "engine shutdown blocked the event loop"
            engine._providers["test"] = object()

    construction = asyncio.create_task(asyncio.to_thread(construct))
    closing = None
    try:
        assert await asyncio.to_thread(entered.wait, 1)
        closing = asyncio.create_task(engine.aclose())
        await asyncio.sleep(0.02)
        if cancel:
            closing.cancel()
            await asyncio.sleep(0.02)
            closing.cancel()
            await asyncio.sleep(0.02)
        assert not closing.done()
        release.set()
        await construction
        if cancel:
            with pytest.raises(asyncio.CancelledError):
                await closing
        else:
            await closing
        assert closed == [loop_thread]
        assert engine._closed is True
        assert engine._providers == {}
    finally:
        release.set()
        await construction
        if closing is not None:
            try:
                await closing
            except asyncio.CancelledError:
                pass


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [False, True])
async def test_engine_construction_is_drained_on_cancellation(monkeypatch, failure):
    engine = AsyncLM15Engine()
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()

    def target(request, *, streaming=False):
        entered.set()
        assert release.wait(3)
        finished.set()
        if failure:
            raise ValueError("construction failed")
        return object(), request

    monkeypatch.setattr(engine, "_target", target)
    operation = asyncio.create_task(engine.complete(object()))
    try:
        assert await asyncio.to_thread(entered.wait, 1)
        operation.cancel()
        await asyncio.sleep(0.02)
        operation.cancel()
        await asyncio.sleep(0.02)
        assert not operation.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await operation
        assert finished.is_set()
    finally:
        release.set()
        try:
            await operation
        except asyncio.CancelledError:
            pass
