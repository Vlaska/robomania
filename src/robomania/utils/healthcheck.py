import json
import logging

from aiohttp import web
from aiohttp.web_request import Request
from disnake.ext.commands import Bot  # type: ignore[attr-defined]
from typing_extensions import Self

from robomania.utils.constants import (
    HEALTHCHECK_GOOD_STATUS_CODE,
    HEALTHCHECK_POOR_STATUS_CODE,
)

logger = logging.getLogger("robomania.healthcheck")


class HealthcheckClient:
    runner: web.AppRunner

    def __init__(self, bot: Bot, app: web.Application, max_latency: float = 20) -> None:
        self.bot = bot
        self.max_latency = max_latency
        self.app = app

    async def healthcheck(self, request: Request) -> web.Response:
        if (
            self.bot.latency > self.max_latency
            or self.bot.user is None
            or not self.bot.is_ready()
            or self.bot.is_closed()
        ):
            message = "not ok"
            status = HEALTHCHECK_POOR_STATUS_CODE
        else:
            message = "ok"
            status = HEALTHCHECK_GOOD_STATUS_CODE

        body = json.dumps({"status": message})
        return web.Response(body=body, status=status, content_type="application/json", charset="utf-8")

    async def shutdown(self) -> None:
        logger.info("Shutting down healthcheck server")
        await self.runner.shutdown()
        await self.runner.cleanup()

    @classmethod
    async def start(cls, bot: Bot, max_latency: float = 20) -> Self:
        app = web.Application(loop=bot.loop)
        client = HealthcheckClient(bot, app, max_latency)
        app.add_routes(
            [
                web.get("/healthcheck", client.healthcheck),
            ]
        )
        # web.run_app(app, host='localhost', port=6302)
        runner = web.AppRunner(app)
        await runner.setup()
        client.runner = runner
        site = web.TCPSite(runner, "0.0.0.0", 6302)
        await site.start()

        logger.info("Started healthcheck server")

        return client
