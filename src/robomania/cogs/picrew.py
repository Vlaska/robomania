# type: ignore[name-defined]
from __future__ import annotations

import datetime
import logging
from typing import cast

import disnake
import validators
from disnake import AllowedMentions, ApplicationCommandInteraction
from disnake.ext import commands, tasks

from robomania import config
from robomania.bot import Robomania
from robomania.models.picrew_model import PicrewModel
from robomania.types.post import Post
from robomania.utils.exceptions import DuplicateError

logger = logging.getLogger("robomania.cogs.picrew")


class PicrewPost:
    picrew_info: PicrewModel
    post: Post
    mentions = AllowedMentions(users=False)

    def __init__(self, info: PicrewModel) -> None:
        self.picrew_info = info

        if self.picrew_info.user:
            user_mention = self.picrew_info.user.mention
        else:
            user_mention = "*nieznany*"

        tw = ""
        if info.tw:
            tw = f"TW: {info.tw}\n"

        post_text = f"{self.picrew_info.link}\n{tw}" f"Post link dodany przez: {user_mention}"

        self.post = Post(post_text)

    async def send(self, channel: disnake.TextChannel) -> None:
        await self.post.send(channel, allowed_mentions=self.mentions)

    async def respond(self, inter: ApplicationCommandInteraction) -> None:
        text = self.post.text
        await inter.send(text, allowed_mentions=self.mentions)


class Picrew(commands.Cog):
    target_channel: disnake.TextChannel

    def __init__(self, bot: Robomania) -> None:
        self.bot = bot

        target_channel_id = config.settings.picrew_target_channel
        self.target_channel = cast(disnake.TextChannel, self.bot.get_channel(target_channel_id))
        self.automatic_post.start()

    @commands.slash_command()
    async def picrew(self, inter: ApplicationCommandInteraction) -> None:
        pass

    @picrew.sub_command()
    async def add_new_link(
        self,
        inter: ApplicationCommandInteraction,
        url: str,
        tw: str = None,
    ) -> None:
        """
        Add a new Picrew link to post later. {{ ADD_PICREW }}

        Parameters
        ----------
        inter : :class:`ApplicationCommandInteraction`
            Command interaction
        url : :class:`str`
            Picrew link, must be valid url {{ ADD_PICREW_URL }}
        tw : :class:`str`
            Trigger warning {{ ADD_PICREW_TW }}
        """
        if not validators.url(url) or "picrew.me" not in url:
            await inter.send("Nieprawidłowy link.")
            return

        await inter.response.defer()

        picrew = PicrewModel(inter.user, url, inter.created_at, False, tw=tw)

        try:
            await picrew.save(self.bot.get_db("robomania"))
        except DuplicateError:
            await inter.send("Link został już dodany 😥.")
        else:
            await inter.send("Dodano 😊")

    @picrew.sub_command()
    async def status(
        self,
        inter: ApplicationCommandInteraction,
    ) -> None:
        """
        Show informations about picrew links. {{ PICREW_STATUS }}

        Parameters
        ----------
        inter : :class:`ApplicationCommandInteraction`
            Command interaction
        """
        await inter.response.defer()

        db = self.bot.get_db("robomania")
        count = await PicrewModel.count_posted_and_not_posted(db)

        await inter.followup.send(
            f"Obecnie {count.not_posted} linków czeka na wysłanie. "
            f"Do tej pory zostało wysłanych {count.posted} linków."
        )

    @picrew.sub_command()
    async def post(self, inter: ApplicationCommandInteraction) -> None:
        """Send a picrew link. {{ PICREW_SEND }}

        Parameters
        ----------
        inter : ApplicationCommandInteraction
            Command interaction
        """
        db = self.bot.get_db("robomania")

        await inter.response.defer()

        posts = await PicrewModel.get_random(db, 1)
        if not posts:
            await inter.followup.send("Brak linków do wysłania.")
            return

        post = PicrewPost(posts[0])
        await post.respond(inter)

    @tasks.loop(time=datetime.time(hour=15))
    async def automatic_post(self) -> None:
        logger.info("Posting new picrew link.")
        db = self.bot.get_db("robomania")

        posts = await PicrewModel.get_random_unposted(db, 1)
        if not posts:
            logger.info("No unposted picrew links.")
            return

        tmp = posts[0]

        logger.info(f"Sending picrew link {tmp.link}")

        post = PicrewPost(tmp)
        await post.send(self.target_channel)

        await tmp.set_to_posted(db)

    @automatic_post.before_loop
    async def init(self) -> None:
        logger.info("Waiting for connection to discord...")
        await self.bot.wait_until_ready()
        if self.target_channel is None:
            self.target_channel = await self.bot.fetch_channel(config.settings.picrew_target_channel)


def setup(bot: Robomania) -> None:
    bot.add_cog(Picrew(bot))
