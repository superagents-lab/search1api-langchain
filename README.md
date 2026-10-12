# Search1API for LangChain

Official Search1API tools for LangChain agents. The package exposes live web
search, news search, and page crawling through LangChain's standard tool
interface while relying on the official Search1API Python SDK for
authentication, retries, timeouts, and API errors.

> The similarly named `langchain-search1api` package on PyPI is an independent
> third-party project. `search1api-langchain` is the official package maintained
> by Search1API.

## Install

```bash
pip install search1api-langchain
```

Set an API key:

```bash
export SEARCH1API_API_KEY="your-api-key"
```

`SEARCH1API_KEY` is also accepted for compatibility with the Search1API CLI.
Create a key in the
[Search1API dashboard](https://app.s1.dev).

## Use all tools

```python
from search1api_langchain import Search1APIToolkit

tools = Search1APIToolkit().get_tools()

search = tools[0]
result = search.invoke(
    {
        "query": "latest LangChain agent releases",
        "max_results": 5,
        "time_range": "month",
    }
)
print(result)
```

The toolkit returns:

- `search1api_search` for discovering ranked web sources;
- `search1api_news` for recent news articles;
- `search1api_crawl` for reading a known URL as clean content; and
- `search1api_ask` for automatic source routing and relevance ranking.

Pass the returned list directly to a LangChain agent:

```python
from langchain.agents import create_agent
from search1api_langchain import Search1APIToolkit

agent = create_agent(
    model="openai:gpt-5.4",
    tools=Search1APIToolkit().get_tools(),
)

response = agent.invoke(
    {"messages": [{"role": "user", "content": "What changed in LangChain this month?"}]}
)
```

The agent example also requires the `langchain` package and the integration
package for the selected model.

## Use tools individually

```python
from search1api_langchain import (
    Search1APICrawlTool,
    Search1APINewsTool,
    Search1APISearchTool,
)

search = Search1APISearchTool()
news = Search1APINewsTool()
crawl = Search1APICrawlTool()

search.invoke({"query": "agent observability", "search_service": "google"})
news.invoke({"query": "AI regulation", "time_range": "day"})
crawl.invoke({"url": "https://example.com/article"})
```

Every tool supports LangChain's asynchronous invocation:

```python
result = await search.ainvoke({"query": "async Python agents"})
```

An explicit key and client settings can be supplied when environment-based
configuration is not appropriate:

```python
tool = Search1APISearchTool(
    api_key="your-api-key",
    timeout=45,
    max_retries=3,
)
```

API keys use Pydantic's secret type and are excluded from model serialization.

## Credits

Plain Search and News requests cost one credit. Setting `crawl_results` asks
Search1API to read the top result pages and costs one additional credit for each
successful crawl. The tools therefore default `crawl_results` to `0`.

A Crawl request costs one credit. See
[Credits and limits](https://s1.dev/docs/essentials/credits-and-limits)
for current details.

## Development

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
ruff format --check .
ruff check .
mypy src/search1api_langchain
pytest
python -m build
```

## License

MIT


## Current API capabilities

Search supports `bingcn`, `yandex`, and `grokipedia`; the removed `sogou`
engine is no longer offered. Search and news support `day`, `week`, `month`,
and `year` time ranges. Search also accepts `page` on engines with native
pagination.

Agentic Search (`ask`) accepts only a natural-language `query`. The server
chooses the engines and time window and returns `query`, `intent`, ranked
`results`, and `errors`. Each Ask result includes its `source` and `relevance`.
It returns search results, not a generated answer, and costs **5 credits per
call**. Use regular search when the engine and keywords are already known.

Search/news engine-specific attributes live inside each result's optional
`metadata`: GitHub uses `kind`, `stars`, `language`, and `num_comments`;
Hacker News news results use `story_url`, `points`, and `num_comments`.
`published_date` remains optional at the result top level. Numeric zero counts
are preserved; unavailable attributes are omitted. When displaying Grokipedia
results, credit them as "Powered by xAI".

```python
from search1api_langchain import Search1APIAskTool

result = Search1APIAskTool().invoke({"query": "recent papers on speculative decoding"})
```

The toolkit includes `search1api_ask` by default. `ask_timeout` defaults to
45 seconds independently of the other tools' `timeout`. Both synchronous and
asynchronous invocation are supported. Requires `search1api>=0.4`.
