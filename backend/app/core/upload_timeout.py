"""Bounded execution and deadlines for synchronous upload dependencies."""

from concurrent.futures import (
    CancelledError,
    ThreadPoolExecutor,
    TimeoutError as FutureTimeoutError,
)
import threading
import time
from typing import Callable, TypeVar

T = TypeVar("T")

MAX_UPLOAD_OPERATIONS = 4


class UploadDependencyTimeout(TimeoutError):
    """Raised when an upload dependency cannot complete within the shared deadline."""


class UploadOperationRunner:
    """Runs synchronous upload dependencies with bounded admission per process."""

    def __init__(self, max_workers: int = MAX_UPLOAD_OPERATIONS):
        self._max_workers = max_workers
        self._slots = threading.BoundedSemaphore(max_workers)
        self._available_slots = max_workers
        self._lock = threading.Lock()
        self._executor: ThreadPoolExecutor | None = None
        self._closed = True
        self._cancellation_events: set[threading.Event] = set()

    @property
    def available_slots(self) -> int:
        with self._lock:
            return self._available_slots

    def start(self) -> None:
        with self._lock:
            if not self._closed and self._executor is not None:
                return
            self._executor = ThreadPoolExecutor(
                max_workers=self._max_workers,
                thread_name_prefix="upload-dependency",
            )
            self._closed = False

    def shutdown(self) -> None:
        """Stop admission and cancel queued work; running calls remain uncancellable."""
        with self._lock:
            self._closed = True
            executor = self._executor
            cancellation_events = tuple(self._cancellation_events)
        for cancellation_event in cancellation_events:
            cancellation_event.set()
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)

    def run(self, operation: Callable[[threading.Event], T], deadline: float) -> T:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not self._slots.acquire(timeout=remaining):
            raise UploadDependencyTimeout

        with self._lock:
            self._available_slots -= 1
            executor = self._executor
            if self._closed or executor is None:
                self._available_slots += 1
                self._slots.release()
                raise UploadDependencyTimeout

            cancellation_event = threading.Event()
            self._cancellation_events.add(cancellation_event)

        release_lock = threading.Lock()
        slot_released = False

        def release_slot() -> None:
            nonlocal slot_released
            with release_lock:
                if slot_released:
                    return
                slot_released = True
            self._finish_operation(cancellation_event)

        if deadline - time.monotonic() <= 0:
            release_slot()
            raise UploadDependencyTimeout

        try:
            future = executor.submit(self._run_operation, operation, cancellation_event, deadline)
        except BaseException:
            release_slot()
            raise

        future.add_done_callback(lambda completed: release_slot())

        try:
            result = future.result(timeout=max(0.0, deadline - time.monotonic()))
        except FutureTimeoutError:
            cancellation_event.set()
            if future.cancel() or not future.done():
                raise UploadDependencyTimeout from None
            try:
                result = future.result()
            except CancelledError:
                raise UploadDependencyTimeout from None

        if time.monotonic() >= deadline:
            cancellation_event.set()
            raise UploadDependencyTimeout
        return result

    @staticmethod
    def _run_operation(
        operation: Callable[[threading.Event], T],
        cancellation_event: threading.Event,
        deadline: float,
    ) -> T:
        if cancellation_event.is_set() or time.monotonic() >= deadline:
            raise UploadDependencyTimeout
        return operation(cancellation_event)

    def _finish_operation(self, cancellation_event: threading.Event) -> None:
        with self._lock:
            self._cancellation_events.discard(cancellation_event)
            self._available_slots += 1
            self._slots.release()


upload_operation_runner = UploadOperationRunner()
