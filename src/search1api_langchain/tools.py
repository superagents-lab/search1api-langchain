"""LangChain tools backed by the official Search1API Python SDK."""

from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, SecretStr, model_validator
from search1api import AsyncSearch1API, Search1API
from search1api.types import NewsEngine, SearchEngine, TimeRange


class Search1APISearchInput(BaseModel):
    """Input accepted by :class:`Search1APISearchTool`."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, description="The web search query.")
    search_service: SearchEngine | None = Field(
        default=None,
        description="Optional search engine. Search1API chooses its default if omitted.",
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of ranked results to return.",
    )
    page: int | None = Field(
        default=None,
        ge=1,
        le=100,
        description="Optional results page for engines with native pagination.",
    )
    crawl_results: int = Field(
        default=0,
        ge=0,
        le=50,
        description=(
            "Number of top results to crawl for full text. Keep at 0 unless full "
            "page content is needed because successful crawls use extra credits."
        ),
    )
    image: bool = Field(
        default=False,
        description="Whether to request image results when the engine supports them.",
    )
    include_sites: list[str] = Field(
        default_factory=list,
        description="Optional domains to include.",
    )
    exclude_sites: list[str] = Field(
        default_factory=list,
        description="Optional domains to exclude.",
    )
    language: str | None = Field(
        default=None,
        description="Optional language hint.",
    )
    time_range: TimeRange | None = Field(
        default=None,
        description="Optional recency filter.",
    )

    @model_validator(mode="after")
    def validate_crawl_results(self) -> Search1APISearchInput:
        """Reject a crawl count that the Search1API contract cannot satisfy."""
        if self.crawl_results > self.max_results:
            raise ValueError("crawl_results cannot be greater than max_results")
        return self


class Search1APINewsInput(BaseModel):
    """Input accepted by :class:`Search1APINewsTool`."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, description="The news search query.")
    search_service: NewsEngine | None = Field(
        default=None,
        description="Optional news source. Search1API chooses its default if omitted.",
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of news results to return.",
    )
    crawl_results: int = Field(
        default=0,
        ge=0,
        le=50,
        description=(
            "Number of top articles to crawl for full text. Keep at 0 unless full "
            "article content is needed because successful crawls use extra credits."
        ),
    )
    image: bool = Field(
        default=False,
        description="Whether to request image results when the source supports them.",
    )
    include_sites: list[str] = Field(
        default_factory=list,
        description="Optional domains to include.",
    )
    exclude_sites: list[str] = Field(
        default_factory=list,
        description="Optional domains to exclude.",
    )
    language: str | None = Field(
        default=None,
        description="Optional language hint.",
    )
    time_range: TimeRange | None = Field(
        default=None,
        description="Optional recency filter.",
    )

    @model_validator(mode="after")
    def validate_crawl_results(self) -> Search1APINewsInput:
        """Reject a crawl count that the Search1API contract cannot satisfy."""
        if self.crawl_results > self.max_results:
            raise ValueError("crawl_results cannot be greater than max_results")
        return self


class Search1APICrawlInput(BaseModel):
    """Input accepted by :class:`Search1APICrawlTool`."""

    model_config = ConfigDict(extra="forbid")

    url: HttpUrl = Field(description="The public HTTP or HTTPS URL to read.")
    enable_fallback: bool = Field(
        default=False,
        description="Whether Search1API may use its fallback crawler.",
    )


class _Search1APIBaseTool(BaseTool):
    """Shared authenticated Search1API client configuration."""

    model_config = ConfigDict(extra="forbid")

    api_key: SecretStr | None = Field(default=None, exclude=True, repr=False)
    base_url: str = Field(
        default="https://api.search1api.com",
        exclude=True,
        repr=False,
    )
    timeout: float = Field(default=30.0, gt=0, exclude=True, repr=False)
    max_retries: int = Field(default=2, ge=0, exclude=True, repr=False)
    retry_delay: float = Field(default=0.5, ge=0, exclude=True, repr=False)

    def _resolved_api_key(self) -> str | None:
        if self.api_key is not None:
            return self.api_key.get_secret_value()
        return os.getenv("SEARCH1API_API_KEY") or os.getenv("SEARCH1API_KEY")

    def _sync_client(self) -> Search1API:
        return Search1API(
            self._resolved_api_key(),
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
        )

    def _async_client(self) -> AsyncSearch1API:
        return AsyncSearch1API(
            self._resolved_api_key(),
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
        )


def _json_content(response: Any) -> str:
    """Serialize an SDK response into content that an agent can consume."""
    return json.dumps(response, ensure_ascii=False, separators=(",", ":"))


class Search1APISearchTool(_Search1APIBaseTool):
    """Search the live web with Search1API."""

    name: str = "search1api_search"
    description: str = (
        "Search the live web and return ranked, source-backed results. Use "
        "crawl_results only when the task needs full page text."
    )
    args_schema: type[BaseModel] = Search1APISearchInput

    def _run(
        self,
        query: str,
        search_service: SearchEngine | None = None,
        max_results: int = 5,
        page: int | None = None,
        crawl_results: int = 0,
        image: bool = False,
        include_sites: list[str] | None = None,
        exclude_sites: list[str] | None = None,
        language: str | None = None,
        time_range: TimeRange | None = None,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        del run_manager
        with self._sync_client() as client:
            response = client.search(
                query,
                search_service=search_service,
                max_results=max_results,
                page=page,
                crawl_results=crawl_results,
                image=image,
                include_sites=include_sites or [],
                exclude_sites=exclude_sites or [],
                language=language,
                time_range=time_range,
            )
        return _json_content(response)

    async def _arun(
        self,
        query: str,
        search_service: SearchEngine | None = None,
        max_results: int = 5,
        page: int | None = None,
        crawl_results: int = 0,
        image: bool = False,
        include_sites: list[str] | None = None,
        exclude_sites: list[str] | None = None,
        language: str | None = None,
        time_range: TimeRange | None = None,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> str:
        del run_manager
        async with self._async_client() as client:
            response = await client.search(
                query,
                search_service=search_service,
                max_results=max_results,
                page=page,
                crawl_results=crawl_results,
                image=image,
                include_sites=include_sites or [],
                exclude_sites=exclude_sites or [],
                language=language,
                time_range=time_range,
            )
        return _json_content(response)


class Search1APINewsTool(_Search1APIBaseTool):
    """Search recent news with Search1API."""

    name: str = "search1api_news"
    description: str = (
        "Search recent news and return source-backed articles. Use a time_range "
        "for recency and crawl_results only when full article text is needed."
    )
    args_schema: type[BaseModel] = Search1APINewsInput

    def _run(
        self,
        query: str,
        search_service: NewsEngine | None = None,
        max_results: int = 5,
        crawl_results: int = 0,
        image: bool = False,
        include_sites: list[str] | None = None,
        exclude_sites: list[str] | None = None,
        language: str | None = None,
        time_range: TimeRange | None = None,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        del run_manager
        with self._sync_client() as client:
            response = client.news(
                query,
                search_service=search_service,
                max_results=max_results,
                crawl_results=crawl_results,
                image=image,
                include_sites=include_sites or [],
                exclude_sites=exclude_sites or [],
                language=language,
                time_range=time_range,
            )
        return _json_content(response)

    async def _arun(
        self,
        query: str,
        search_service: NewsEngine | None = None,
        max_results: int = 5,
        crawl_results: int = 0,
        image: bool = False,
        include_sites: list[str] | None = None,
        exclude_sites: list[str] | None = None,
        language: str | None = None,
        time_range: TimeRange | None = None,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> str:
        del run_manager
        async with self._async_client() as client:
            response = await client.news(
                query,
                search_service=search_service,
                max_results=max_results,
                crawl_results=crawl_results,
                image=image,
                include_sites=include_sites or [],
                exclude_sites=exclude_sites or [],
                language=language,
                time_range=time_range,
            )
        return _json_content(response)


class Search1APICrawlTool(_Search1APIBaseTool):
    """Read a public URL with Search1API."""

    name: str = "search1api_crawl"
    description: str = (
        "Read a known public HTTP or HTTPS URL and return clean page content. "
        "Use this when the URL is already known; use search for discovery."
    )
    args_schema: type[BaseModel] = Search1APICrawlInput

    def _run(
        self,
        url: HttpUrl,
        enable_fallback: bool = False,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        del run_manager
        with self._sync_client() as client:
            response = client.crawl(str(url), enable_fallback=enable_fallback)
        return _json_content(response)

    async def _arun(
        self,
        url: HttpUrl,
        enable_fallback: bool = False,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> str:
        del run_manager
        async with self._async_client() as client:
            response = await client.crawl(
                str(url),
                enable_fallback=enable_fallback,
            )
        return _json_content(response)


class Search1APIAskInput(BaseModel):
    """Natural-language request; routing and result limits are server-owned."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    query: str = Field(min_length=1, max_length=500)


class Search1APIAskTool(_Search1APIBaseTool):
    """Route and rank a natural-language search request with Search1API."""

    name: str = "search1api_ask"
    description: str = (
        "Describe what to find in natural language. Search1API chooses the engines "
        "and time window and returns results ranked by relevance. Costs 5 credits. "
        "Use search when you already know the engine and keywords."
    )
    args_schema: type[BaseModel] = Search1APIAskInput
    timeout: float = Field(default=45.0, gt=0, exclude=True, repr=False)

    def _run(
        self,
        query: str,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        del run_manager
        with self._sync_client() as client:
            return _json_content(client.ask(query, timeout=self.timeout))

    async def _arun(
        self,
        query: str,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> str:
        del run_manager
        async with self._async_client() as client:
            return _json_content(await client.ask(query, timeout=self.timeout))
