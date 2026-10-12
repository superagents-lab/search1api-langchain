from __future__ import annotations

from search1api_langchain import Search1APIToolkit


def test_toolkit_returns_the_complete_tool_set() -> None:
    toolkit = Search1APIToolkit(api_key="secret")

    tools = toolkit.get_tools()

    assert [tool.name for tool in tools] == [
        "search1api_search",
        "search1api_news",
        "search1api_crawl",
        "search1api_ask",
    ]
    assert all("secret" not in repr(tool) for tool in tools)
    assert all("api_key" not in tool.model_dump() for tool in tools)


def test_toolkit_returns_fresh_tools() -> None:
    toolkit = Search1APIToolkit(api_key="secret")

    first = toolkit.get_tools()
    second = toolkit.get_tools()

    assert first is not second
    assert all(left is not right for left, right in zip(first, second, strict=True))


def test_toolkit_has_a_separate_ask_timeout() -> None:
    tools = Search1APIToolkit(timeout=10, ask_timeout=60).get_tools()
    assert tools[0].timeout == 10  # type: ignore[attr-defined]
    assert tools[-1].timeout == 60  # type: ignore[attr-defined]
