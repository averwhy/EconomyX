import discord
import logging
from datetime import timedelta
from discord.ext import commands
from discord.ext import tasks
from .utils import player as Player
from .utils.errors import NotAPlayerError

log = logging.getLogger(__name__)


class lottery(commands.Cog, command_attrs=dict(name="Lottery")):
    """The lottery. Users buy tickets and every 12 hours it is drawn.
    The winning player earns 2x the money spent on all tickets (e.g. 5 tickets bought = $500, x2 = $1000 winnings).
    Use the `lottery` command to see when the next drawing is., and `lottery buy` to buy a ticket.
    """

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.lottery_task.start()

    async def cog_unload(self):
        self.lottery_task.cancel()

    async def reset_lottery_time(self):
        newdrawingtime = discord.utils.utcnow() + timedelta(hours=12)
        await self.bot.pool.execute(
            "UPDATE e_lottery_main SET drawingwhen = $1", newdrawingtime
        )

    @tasks.loop(seconds=120)
    async def lottery_task(self):
        await self.draw()

    async def draw(self, force: bool = False):
        """Draws lottery"""
        await self.bot.wait_until_ready()
        data = await self.bot.pool.fetchrow("select * from e_lottery_main")
        if data is None:
            # no lottery data :(
            date = discord.utils.utcnow() + timedelta(hours=12)
            await self.bot.pool.execute(
                "INSERT INTO e_lottery_main VALUES ($1, 1)", date
            )
            return
        piss = data[0]
        shit = discord.utils.utcnow()
        diff = (piss - shit) / timedelta(seconds=1)
        if diff < 0 or force:
            # 0 bigger than the diff would be 12 hours (we want to draw every 12 hours)
            # So, lets draw, then reset
            data2 = await self.bot.pool.fetchrow("SELECT COUNT(*) FROM e_lottery_users")
            if int(tuple(data2)[0]) <= 0:
                log.info("Lottery draw, no users, reset successfully")
                await self.reset_lottery_time()
                return
            winningamount = (data2[0] * 100) * 2
            winningplayer = await self.bot.pool.fetchrow(
                "SELECT * FROM e_lottery_users ORDER BY RANDOM()"
            )
            user = await self.bot.fetch_user(tuple(winningplayer)[0])
            ts = self.bot.utc_calc(winningplayer[2], style="R")
            try:
                await user.send(
                    f"Hey {user.mention}, **You won the lottery in EconomyX!**\nYou bought a ticket {ts}\nYou won ${winningamount}"
                )
            except discord.Forbidden:
                # we cant dm them. Sad!
                # i guess we'll just pay them and up their stats. oh well
                pass
            finally:
                await self.bot.pool.execute(
                    "UPDATE e_users SET bal = (bal + $1) WHERE id = $2",
                    winningamount,
                    winningplayer[0],
                )
                await self.bot.pool.execute(
                    "UPDATE e_users SET lotterieswon = (lotterieswon + 1) WHERE id = $1",
                    winningplayer[0],
                )
                await self.bot.pool.execute("DELETE FROM e_lottery_users")
                await self.bot.pool.execute(
                    "UPDATE e_lottery_main SET drawingnum = (drawingnum + 1)"
                )
                await self.bot.stats.add("totalLotteries")
                log.info(
                    f"Lottery draw, {user.name} won ${winningamount}. Reset successfully"
                )

            # achievement check
            ach = self.bot.get_cog("achievements")
            if await ach.has_ach(user, 15):
                await ach.give_ach(user, 15)
            player = await Player.get(user.id, self.bot)
            if player.lotteries_won >= 5:
                if await ach.has_ach(user, 16):
                    await ach.give_ach(user, 16)

            await self.reset_lottery_time()  # it commits in here
        elif diff > 0:
            # Too soon, dont draw
            return

    @commands.group(name="lottery", aliases=["lot"], invoke_without_command=True)
    async def _lottery(self, ctx):
        """Base lottery command. Views active lottery stats."""
        c = await self.bot.pool.fetchrow("SELECT COUNT(*) FROM e_lottery_users")
        usercount = tuple(c)[0]
        try:
            pcolor = (await Player.get(ctx.author.id, self.bot)).profile_color
        except NotAPlayerError:
            pcolor = 0x2F3136
        lotinfo = await self.bot.pool.fetchrow("SELECT * FROM e_lottery_main")
        embed = discord.Embed(title=f"Lottery #{tuple(lotinfo)[1]}", color=pcolor)
        embed.add_field(name="Potential winnings", value=f"${(usercount * 100) * 2}")
        embed.add_field(name="Bought tickets", value=usercount)
        ts = self.bot.lottery_countdown_calc(tuple(lotinfo)[0])
        embed.add_field(name="Next drawing", value=f"`{ts[1]}h, {ts[2]}m, {ts[3]}s`")

        await ctx.send(embed=embed)

    @_lottery.command(aliases=["purchase"])
    async def buy(self, ctx):
        """Buys a lottery command for 100 dollars. Note that you cannot sell or refund them."""
        player = await Player.get(ctx.author.id, self.bot)
        if player.balance < 100:
            await ctx.send(
                f"You cant afford to buy a lottery ticket ($100). You only have ${player.balance}."
            )
            return
        lcheck = await self.bot.pool.fetchrow(
            "SELECT * FROM e_lottery_users WHERE userid = $1", ctx.author.id
        )
        if lcheck is not None:
            return await ctx.send(
                f"You've already bought a lottery ticket. Use `{ctx.clean_prefix}lottery` to view when it will be drawn."
            )

        drawingwhen = await self.bot.pool.fetchrow("SELECT * FROM e_lottery_main")
        ts = self.bot.utc_calc(tuple(drawingwhen)[0], style="R")
        await self.bot.pool.execute(
            "INSERT INTO e_lottery_users VALUES ($1, $2, $3)",
            ctx.author.id,
            ctx.author.name,
            discord.utils.utcnow(),
        )
        await player.update_balance(-100, ctx=ctx)
        await self.bot.stats.add("totalLotteries")
        await ctx.send(
            f"You bought a lottery ticket for $100. The next lottery drawing is in {ts}. I will DM you if you are picked."
        )


async def setup(bot):
    await bot.add_cog(lottery(bot))
