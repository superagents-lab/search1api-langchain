# Changelog

## 0.2.0 - 2026-10-12

- Add the default query-only Ask tool (Agentic Search in n8n), with a 5-credit cost disclosure.
- Add Bing China, Yandex, and Grokipedia and remove Sogou. Support `week` in search/news and native search pagination.
- Preserve nested engine metadata, zero counters, and optional top-level publication dates; preserve Ask routing, source, relevance, and errors.

## 0.1.0 - 2026-07-29

- Add Search, News, and Crawl LangChain tools.
- Add a toolkit that configures all three tools together.
- Support synchronous and asynchronous invocation.
- Resolve credentials lazily from explicit configuration,
  `SEARCH1API_API_KEY`, or `SEARCH1API_KEY`.
- Use the official Search1API Python SDK for transport and errors.
