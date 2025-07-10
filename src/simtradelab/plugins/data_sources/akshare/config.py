from typing import List

from pydantic import Field

from simtradelab.plugins.config.validator import BasePluginConfig


class AkShareDataPluginConfig(BasePluginConfig):
    """Configuration model for the AkShare Data Source plugin."""

    symbols: List[str] = Field(
        ..., min_length=1, description="List of stock symbols to track."
    )
    start_date: str
    end_date: str
