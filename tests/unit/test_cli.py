import pytest

from simtradelab import __version__
from simtradelab.cli import main


def test_cli_version(capsys):
    with pytest.raises(SystemExit, match="0"):
        main(["--version"])
    assert capsys.readouterr().out.strip() == __version__
