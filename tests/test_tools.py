from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from pydantic import ValidationError

from search1api_langchain import (
    Search1APIAskInput,
    Search1APIAskTool,
    Search1APICrawlInput,
    Search1APICrawlTool,
    Search1APINewsTool,
    Search1APISearchInput,
    Search1APISearchTool,
)


class FakeSyncClient:
    instances: list[FakeSyncClient] = []

    def __init__(self, api_key: str | None, **settings: Any) -> None:
        self.api_key = api_key
        self.settings = settings
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.closed = False
        self.__class__.instances.append(self)

    def __enter__(self) -> FakeSyncClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.closed = True

    def search(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("search", args, kwargs))
        return {
            "results": [
                {
                    "title": "Result",
                    "link": "https://example.com",
                    "published_date": "2026-10-12",
                    "metadata": {"stars": 0},
                }
            ]
        }

    def news(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("news", args, kwargs))
        return {
            "results": [
                {
                    "title": "News",
                    "link": "https://example.com/news",
                    "metadata": {"points": 0, "num_comments": 0},
                }
            ]
        }

    def ask(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("ask", args, kwargs))
        return {
            "query": args[0],
            "intent": {
                "search_query": "Bun",
                "sources": ["github"],
                "time_range": "week",
            },
            "results": [
                {
                    "title": "Bun",
                    "link": "https://github.com/oven-sh/bun",
                    "snippet": "Runtime",
                    "source": "github",
                    "relevance": 0.9,
                }
            ],
            "errors": [],
        }

    def crawl(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("crawl", args, kwargs))
        return {"results": {"content": "Example content"}}


class FakeAsyncClient:
    instances: list[FakeAsyncClient] = []

    def __init__(self, api_key: str | None, **settings: Any) -> None:
        self.api_key = api_key
        self.settings = settings
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.closed = False
        self.__class__.instances.append(self)

    async def __aenter__(self) -> FakeAsyncClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        self.closed = True

    async def search(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("search", args, kwargs))
        return {"results": [{"title": "Async", "link": "https://example.com"}]}

    async def news(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("news", args, kwargs))
        return {"results": [{"title": "Async news"}]}

    async def ask(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("ask", args, kwargs))
        return {"query": args[0], "intent": {}, "results": [], "errors": []}

    async def crawl(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("crawl", args, kwargs))
        return {"results": {"content": "Async content"}}


@pytest.fixture(autouse=True)
def fake_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeSyncClient.instances.clear()
    FakeAsyncClient.instances.clear()
    monkeypatch.setattr("search1api_langchain.tools.Search1API", FakeSyncClient)
    monkeypatch.setattr("search1api_langchain.tools.AsyncSearch1API", FakeAsyncClient)


def test_search_maps_all_inputs_and_returns_json() -> None:
    tool = Search1APISearchTool(api_key="secret")

    output = tool.invoke(
        {
            "query": "LangChain agents",
            "search_service": "github",
            "max_results": 8,
            "page": 2,
            "crawl_results": 2,
            "image": True,
            "include_sites": ["github.com"],
            "exclude_sites": ["gist.github.com"],
            "language": "en",
            "time_range": "week",
        }
    )

    assert json.loads(output)["results"][0]["title"] == "Result"
    client = FakeSyncClient.instances[-1]
    assert client.closed is True
    assert client.api_key == "secret"
    assert client.calls == [
        (
            "search",
            ("LangChain agents",),
            {
                "search_service": "github",
                "max_results": 8,
                "page": 2,
                "crawl_results": 2,
                "image": True,
                "include_sites": ["github.com"],
                "exclude_sites": ["gist.github.com"],
                "language": "en",
                "time_range": "week",
            },
        )
    ]


def test_news_defaults_do_not_crawl() -> None:
    tool = Search1APINewsTool(api_key="secret")

    output = json.loads(tool.invoke({"query": "AI news"}))
    assert output["results"][0]["metadata"] == {"points": 0, "num_comments": 0}

    _, args, kwargs = FakeSyncClient.instances[-1].calls[-1]
    assert args == ("AI news",)
    assert kwargs["crawl_results"] == 0
    assert kwargs["max_results"] == 5


def test_crawl_accepts_only_http_urls() -> None:
    with pytest.raises(ValidationError):
        Search1APICrawlInput(url="file:///etc/passwd")

    tool = Search1APICrawlTool(api_key="secret")
    output = tool.invoke({"url": "https://example.com/page", "enable_fallback": True})

    assert json.loads(output)["results"]["content"] == "Example content"
    assert FakeSyncClient.instances[-1].calls[-1] == (
        "crawl",
        ("https://example.com/page",),
        {"enable_fallback": True},
    )


def test_crawl_results_cannot_exceed_max_results() -> None:
    with pytest.raises(ValidationError, match="crawl_results"):
        Search1APISearchInput(
            query="invalid",
            max_results=2,
            crawl_results=3,
        )


def test_credentials_are_resolved_lazily_and_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = Search1APISearchTool(api_key="explicit-secret")
    assert "explicit-secret" not in repr(tool)
    assert "api_key" not in tool.model_dump()

    lazy_tool = Search1APISearchTool()
    monkeypatch.setenv("SEARCH1API_KEY", "lazy-secret")
    lazy_tool.invoke({"query": "lazy credentials"})
    assert FakeSyncClient.instances[-1].api_key == "lazy-secret"


def test_async_search_uses_async_sdk() -> None:
    tool = Search1APISearchTool(api_key="secret")

    output = asyncio.run(tool.ainvoke({"query": "async agents"}))

    assert json.loads(output)["results"][0]["title"] == "Async"
    client = FakeAsyncClient.instances[-1]
    assert client.closed is True
    assert client.calls[-1][0] == "search"


@pytest.mark.parametrize("engine", ["bingcn", "yandex", "grokipedia"])
def test_current_engines_and_week(engine: str) -> None:
    tool = Search1APISearchTool(api_key="secret")
    output = json.loads(
        tool.invoke({"query": "q", "search_service": engine, "time_range": "week"})
    )
    assert output["results"][0]["metadata"] == {"stars": 0}
    assert output["results"][0]["published_date"] == "2026-10-12"
    assert "stars" not in output["results"][0]
    assert FakeSyncClient.instances[-1].calls[-1][2]["search_service"] == engine


def test_removed_engine_and_invalid_page_rejected() -> None:
    with pytest.raises(ValidationError):
        Search1APISearchInput(query="q", search_service="sogou")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Search1APISearchInput(query="q", page=0)


def test_ask_accepts_only_query_and_preserves_the_response() -> None:
    tool = Search1APIAskTool(api_key="secret")
    response = json.loads(tool.invoke({"query": "  Bun this week  "}))
    assert response["query"] == "Bun this week"
    assert response["results"][0]["source"] == "github"
    assert response["results"][0]["relevance"] == 0.9
    client = FakeSyncClient.instances[-1]
    assert client.calls == [("ask", ("Bun this week",), {"timeout": 45.0})]
    assert client.closed
    with pytest.raises(ValidationError):
        Search1APIAskInput(query=" ")
    with pytest.raises(ValidationError):
        Search1APIAskInput(query="q", max_results=2)  # type: ignore[call-arg]


def test_async_ask_uses_the_async_sdk() -> None:
    response = asyncio.run(
        Search1APIAskTool(api_key="secret").ainvoke({"query": "Bun"})
    )
    assert json.loads(response)["query"] == "Bun"
    client = FakeAsyncClient.instances[-1]
    assert client.calls == [("ask", ("Bun",), {"timeout": 45.0})]
    assert client.closed
