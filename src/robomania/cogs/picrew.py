# type: ignore[name-defined]
from __future__ import annotations

import datetime
from typing import cast

import disnake
import validators
from disnake import AllowedMentions, ApplicationCommandInteraction
from disnake.ext import commands, tasks

from robomania.bot import Robomania
from robomania.config import Config
from robomania.models.picrew_model import PicrewModel
from robomania.types.post import Post
from robomania.utils.exceptions import DuplicateError


class PicrewPost:
    picrew_info: PicrewModel
    post: Post

    def __init__(self, info: PicrewModel) -> None:
        self.picrew_info = info

        if self.picrew_info.user:
            user_mention = self.picrew_info.user.mention
        else:
            user_mention = '*nieznany*'

        self.post = Post(
            f'{self.picrew_info.link}\n'
            f'Post link dodany przez: {user_mention}'
        )

    async def send(self, channel: disnake.TextChannel) -> None:
        await self.post.send(channel)

    async def respond(self, inter: ApplicationCommandInteraction) -> None:
        text = self.post.text
        await inter.send(
            text,
            allowed_mentions=AllowedMentions(users=False)
        )


class Picrew(commands.Cog):
    target_channel: disnake.TextChannel

    def __init__(self, bot: Robomania) -> None:
        self.bot = bot

        target_channel_id = Config.picrew_target_channel
        self.target_channel = cast(
            disnake.TextChannel,
            self.bot.get_channel(target_channel_id)
        )

    @commands.slash_command()
    async def picrew(self, inter: ApplicationCommandInteraction) -> None:
        pass

    @picrew.sub_command()
    async def add_new_link(
        self,
        inter: ApplicationCommandInteraction,
        url: str,
    ) -> None:
        """
        Add a new Picrew link to post later. {{ ADD_PICREW }}

        Parameters
        ----------
        inter : :class:`ApplicationCommandInteraction`
            Command interaction
        url : :class:`str`
            Picrew link, must be valid url {{ ADD_PICREW_URL }}
        """
        if not validators.url(url) or 'picrew.me' not in url:
            await inter.send(
                'Nieprawidłowy link.'
            )
            return

        await inter.response.defer()

        picrew = PicrewModel(inter.user, url, inter.created_at, False)

        try:
            await picrew.save(self.bot.get_db('robomania'))
        except DuplicateError:
            await inter.send('Link został już dodany 😥.')
        else:
            await inter.send('Dodano 😊')

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

        db = self.bot.get_db('robomania')
        count = await PicrewModel.count_posted_and_not_posted(db)

        await inter.followup.send(
            f'Obecnie {count.not_posted} linków czeka na wysłanie. '
            f'Do tej pory zostało wysłanych {count.posted} linków.'
        )

    @picrew.sub_command()
    async def post(self, inter: ApplicationCommandInteraction) -> None:
        """Send a picrew link. {{ PICREW_SEND }}

        Parameters
        ----------
        inter : ApplicationCommandInteraction
            Command interaction
        """
        db = self.bot.get_db('robomania')

        await inter.response.defer()

        posts = await PicrewModel.get_random_unposted(db, 1)
        if not posts:
            await inter.followup.send(
                'Brak linków do wysłania.'
            )
            return

        post = PicrewPost(posts[0])
        await post.respond(inter)

    @tasks.loop(time=datetime.time(15, tzinfo=Robomania.timezone))
    async def automatic_post(self) -> None:
        db = self.bot.get_db('robomania')

        posts = await PicrewModel.get_random_unposted(db, 1)
        if not posts:
            return

        tmp = posts[0]
        post = PicrewPost(tmp)
        await post.send(self.target_channel)

        await tmp.set_to_posted(db)


def setup(bot: Robomania) -> None:
    bot.add_cog(Picrew(bot))