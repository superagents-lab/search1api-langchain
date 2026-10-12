"""Search1API toolkit for LangChain agents."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool, BaseToolkit
from pydantic import ConfigDict, Field, SecretStr

from .tools import (
    Search1APIAskTool,
    Search1APICrawlTool,
    Search1APINewsTool,
    Search1APISearchTool,
)


class Search1APIToolkit(BaseToolkit):
    """Load Search1API search, news, crawl, and ask tools together."""

    model_config = ConfigDict(extra="forbid")

    api_key: SecretStr | None = Field(default=None, exclude=True, repr=False)
    base_url: str = Field(
        default="https://api.search1api.com",
        exclude=True,
        repr=False,
    )
    timeout: float = Field(default=30.0, gt=0, exclude=True, repr=False)
    ask_timeout: float = Field(default=45.0, gt=0, exclude=True, repr=False)
    max_retries: int = Field(default=2, ge=0, exclude=True, repr=False)
    retry_delay: float = Field(default=0.5, ge=0, exclude=True, repr=False)

    def get_tools(self) -> list[BaseTool]:
        """Return a fresh set of configured Search1API tools."""
        settings: dict[str, Any] = {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
        }
        return [
            Search1APISearchTool(**settings),
            Search1APINewsTool(**settings),
            Search1APICrawlTool(**settings),
            Search1APIAskTool(**{**settings, "timeout": self.ask_timeout}),
        ]
