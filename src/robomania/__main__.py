from __future__ import annotations

from pathlib import Path

import click

from robomania.bot import main


@click.command()
@click.option(
    '-c',
    '--config',
    default='.env',
    help='Path to .env file storing configuration',
    type=click.Path(
        exists=True,
        dir_okay=False,
        writable=False,
        readable=True,
        allow_dash=False,
        path_type=Path
    )
)
def run(config: Path) -> None:
    main(config)


if __name__ == '__main__':
    run()
