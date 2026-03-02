"""Лента новостей каналов в стиле старых соцсетей: строго по времени."""

from __future__ import annotations

from dataclasses import dataclass
import heapq
from typing import Iterable


@dataclass(order=True)
class ChannelPost:
    """Пост канала.

    order=True позволяет сортировать через heapq по timestamp.
    """

    timestamp: int
    channel_id: str
    post_id: str
    content: str


def merge_channel_feeds(feeds: Iterable[list[ChannelPost]], limit: int = 100) -> list[ChannelPost]:
    """Объединяет несколько каналов в единую timeline.

    Алгоритм: k-way merge max-heap (через отрицательный timestamp).
    Ожидается, что каждый feed уже отсортирован по убыванию времени.
    """
    heap: list[tuple[int, int, int, ChannelPost]] = []
    indexed = list(feeds)

    for fi, feed in enumerate(indexed):
        if feed:
            heapq.heappush(heap, (-feed[0].timestamp, fi, 0, feed[0]))

    out: list[ChannelPost] = []
    while heap and len(out) < limit:
        _, fi, pi, post = heapq.heappop(heap)
        out.append(post)
        next_i = pi + 1
        if next_i < len(indexed[fi]):
            nxt = indexed[fi][next_i]
            heapq.heappush(heap, (-nxt.timestamp, fi, next_i, nxt))

    return out
