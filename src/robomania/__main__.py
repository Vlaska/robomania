from __future__ import annotations

import logging

import click
import requests

from robomania.bot import configure_bot, main
from robomania.utils.constants import HEALTHCHECK_GOOD_STATUS_CODE

logger = logging.getLogger("robomania.healthcheck")


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    if ctx.invoked_subcommand != "healthcheck":
        configure_bot()
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)


@cli.command()
def setup_database() -> None:
    from robomania.models import create_collections

    create_collections()


@cli.command()
def healthcheck() -> int:
    try:
        response = requests.get("http://localhost:6302/healthcheck", timeout=1000)
    except Exception:
        logger.exception("Healthcheck failed")
        return 1

    if response.status_code == HEALTHCHECK_GOOD_STATUS_CODE:
        return 0
    return 1


@cli.command()
def run() -> None:
    main()


if __name__ == "__main__":
    cli()
