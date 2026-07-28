# Changelog

## 0.1.0 - Unreleased

- Add Search, News, and Crawl LangChain tools.
- Add a toolkit that configures all three tools together.
- Support synchronous and asynchronous invocation.
- Resolve credentials lazily from explicit configuration,
  `SEARCH1API_API_KEY`, or `SEARCH1API_KEY`.
- Use the official Search1API Python SDK for transport and errors.
