from __future__ import annotations

from pathlib import Path

import click

from robomania.bot import configure_bot, main


@click.group(invoke_without_command=True)
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
@click.pass_context
def cli(ctx: click.Context, config: Path) -> None:
    configure_bot()
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)


@cli.command()
def setup_database() -> None:
    from robomania.models import create_collections

    create_collections()


@cli.command()
def run() -> None:
    main()


if __name__ == '__main__':
    cli()
