"""Queue manager for BFS crawling."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CrawlTask:
    """Unit of work in crawl queue."""

    url: str
    depth: int


class QueueManager:
    """FIFO queue for BFS traversal."""

    def __init__(self) -> None:
        self._queue: deque[CrawlTask] = deque()

    def enqueue(self, task: CrawlTask) -> None:
        self._queue.append(task)

    def dequeue(self) -> CrawlTask:
        return self._queue.popleft()

    def is_empty(self) -> bool:
        return not self._queue

    def __len__(self) -> int:
        return len(self._queue)
