import typing
import discord
import logging
from discord.ext import commands

log = logging.getLogger(__name__)


class InvalidStatistic(commands.CommandError):
    pass


class statistics(commands.Cog, command_attrs=dict(name="Statistics")):
    """
    EconomyX statistics tracking.
    """

    def __init__(self, bot):
        self.bot = bot

    async def add(self, stat_name: str, amount: int = 1):
        """Adds a given amount to a BOT statistic value. Default is 1."""
        results = await self.bot.pool.fetch("SELECT statname FROM e_bot_stats")
        valid_stats = [s[0] for s in tuple(results)]
        if stat_name not in valid_stats:
            log.warning("invalid stat moment...")
            raise InvalidStatistic(f"{stat_name} is not a valid statistic to add to")
        stat_name = stat_name.strip()
        amount = int(amount)
        await self.bot.pool.execute(
            "UPDATE e_bot_stats SET statvalue = (statvalue + $1) WHERE statname = $2",
            amount,
            stat_name,
        )

    async def user_add_games(
        self, player: typing.Union[discord.Member, discord.User], amount: int = 1
    ):
        """Adds to gamesPlayed to a USER statistic value. Default is 1."""
        amount = int(amount)
        await self.bot.pool.execute(
            "UPDATE e_player_stats SET gamesPlayed = (gamesPlayed + $1) WHERE id = $2",
            amount,
            player.id,
        )

    async def user_add_commands(
        self, player: typing.Union[discord.Member, discord.User], amount: int = 1
    ):
        """Adds to commandsUsed to a USER statistic value. Default is 1."""
        amount = int(amount)
        await self.bot.pool.execute(
            "UPDATE e_player_stats SET commandsUsed = (commandsUsed + $1) WHERE id = $2",
            amount,
            player.id,
        )

    async def user_add_paid(
        self, player: typing.Union[discord.Member, discord.User], amount: int = 1
    ):
        """Adds to amountPaid to a USER statistic value. Default is 1."""
        amount = int(amount)
        await self.bot.pool.execute(
            "UPDATE e_player_stats SET amountPaid = (amountPaid + $1) WHERE id = $2",
            amount,
            player.id,
        )

    @commands.command(hidden=True)
    async def stats(self, ctx):
        embed = discord.Embed(
            title="EconomyX Statistics",
            description="Note: Stats are accurate as of the 6/17/2023 reset.\nObviously the stats look weird, they are accurate but a WIP for appearance \n*-developer averwhy*",
            color=discord.Color.from_rgb(0, 0, 0),
        )
        results = await self.bot.pool.fetch("SELECT * FROM e_bot_stats")
        for e in tuple(results):
            embed.add_field(
                name=e[0], value=f"{e[1]}\n({self.bot.utc_calc(e[2],style='R')})"
            )

        await ctx.send(embed=embed)

    async def cog_load(self):
        # await self.bot.pool.execute("CREATE TABLE IF NOT EXISTS e_bot_stats (statname TEXT, statvalue BIGINT NOT NULL DEFAULT 0, trackingsince TIMESTAMP NOT NULL DEFAULT now())")
        # need to make sure essential bot stats are in place
        result = await self.bot.pool.fetch("SELECT * FROM e_bot_stats")
        if len(result) == 0:
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totalLost')"
            )
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totalbetLost')"
            )
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totalbjLost')"
            )
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totalcrapsLost')"
            )
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totalguessLost')"
            )
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totalrpsLost')"
            )
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totalrouletteLost')"
            )
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totalinvestLost')"
            )
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totalstocksInvested')"
            )
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totalPaid')"
            )
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totalLotteries')"
            )
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totallotteryTicketsBought')"
            )
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totalprofilesViewed')"
            )
            await self.bot.pool.execute(
                "INSERT INTO e_bot_stats(statname) VALUES ('totalCommands')"
            )

        # now for user stats
        # await self.bot.pool.execute("CREATE TABLE IF NOT EXISTS e_player_stats (id BIGINT REFERENCES e_users(id), gamesPlayed INTEGER, amountPaid BIGINT, commandsUsed INTEGER, trackingsince TIMESTAMP NOT NULL DEFAULT now())")
        self.bot.stats = self

    async def cog_unload(self):
        self.bot.stats = None

    @commands.Cog.listener()
    async def on_command(self, ctx):
        await self.add("totalCommands")  # adds 1 to totalCommands
        await self.user_add_commands(ctx.author)


async def setup(bot):
    await bot.add_cog(statistics(bot))
