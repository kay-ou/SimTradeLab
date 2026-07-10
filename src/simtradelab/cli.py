"""SimTradeLab command-line entry point."""

from __future__ import annotations

import argparse

from simtradelab import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="simtradelab", description="SimTradeLab backtesting framework")
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args(argv)
    return 0
