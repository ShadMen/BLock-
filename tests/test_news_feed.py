from backend.services.news_feed import ChannelPost, merge_channel_feeds


def test_merge_channel_feeds_desc():
    f1 = [
        ChannelPost(timestamp=100, channel_id="a", post_id="a1", content="1"),
        ChannelPost(timestamp=90, channel_id="a", post_id="a2", content="2"),
    ]
    f2 = [
        ChannelPost(timestamp=95, channel_id="b", post_id="b1", content="3"),
        ChannelPost(timestamp=80, channel_id="b", post_id="b2", content="4"),
    ]

    out = merge_channel_feeds([f1, f2], limit=4)
    assert [p.timestamp for p in out] == [100, 95, 90, 80]
