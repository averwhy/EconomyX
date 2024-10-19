import random
import discord
from discord.ext import commands
from .utils import player as Player
from datetime import timedelta

OWNER_ID = 267410788996743168

XP_REQUIREMENTS = {
    1: 0,
    2: 100,
    3: 200,
    4: 350,
    5: 400,
    6: 500,
    7: 600,
    8: 700,
    9: 800,
    10: 900,
    11: 1000,
    12: 1200,
    13: 1400,
    14: 1600,
    15: 1800,
    16: 2000,
    17: 2200,
    18: 2500,
    19: 2800,
    20: 3300,
}
LEVEL_PAY = {
    1: 10,
    2: 12,
    3: 15,
    4: 20,
    5: 22,
    6: 24,
    7: 25,
    8: 27,
    9: 30,
    10: 32,
    11: 33,
    12: 34,
    13: 35,
    14: 36,
    15: 38,
    16: 40,
    17: 42,
    18: 45,
    19: 49,
    20: 55,
}


class jobs(commands.Cog, command_attrs=dict(name="Jobs")):
    """
    This is for the work command.
    """

    def __init__(self, bot):
        self.bot = bot

    def level_bar(self, xp):
        return f"`[{'#' * (decimal := round(xp % 1 * 20))}{'_' * (20 - decimal)}]`"

    def get_level(self, player_xp):  # messy method to get level based on xp
        for xp in XP_REQUIREMENTS.values():
            if xp >= player_xp:
                result = list(XP_REQUIREMENTS.keys())[
                    list(XP_REQUIREMENTS.values()).index(xp) - 1
                ]
                if result == 20:
                    result = 1  # fuck this shit
                return result
            elif xp >= 3300:
                return 20

    def can_work(self, data: tuple):
        """Returns True if the player can work, False if not."""
        last_worked = data[4]
        last_hours = int(data[5]) / 2  # half their last worked hours
        cooldown = last_worked + timedelta(
            hours=last_hours
        )  # cooldown is 2-4 hours in the future from last worked
        now = discord.utils.utcnow()
        if cooldown < now:
            return True  # can work
        return False  # cant work

    @commands.group()
    async def job(self, ctx):
        """Base command for jobs. Here you can view you stats (xp & level), available jobs, and more."""
        player = await Player.get(ctx.author.id, self.bot)
        total_workers = (
            tuple(await self.bot.pool.fetchrow("SELECT COUNT(*) FROM e_jobs"))
        )[0]
        total_worked = (
            tuple(await self.bot.pool.fetchrow("SELECT SUM(timesworked) FROM e_jobs"))
        )[0]
        total_xp = (tuple(await self.bot.pool.fetchrow("SELECT SUM(xp) FROM e_jobs")))[
            0
        ]
        try:
            (
                tuple(
                    await self.bot.pool.fetchrow(
                        "SELECT * FROM e_jobs WHERE id = $1", player.id
                    )
                )
            )[0]
        except TypeError:
            player_desc = "You haven't worked yet! Use `e$work` to start."
        else:
            data = tuple(
                await self.bot.pool.fetchrow(
                    "SELECT * FROM e_jobs WHERE id = $1", player.id
                )
            )
            player_xp = data[1]
            player_level = data[2]
            player_timesworked = data[3]
            player_lastworked = self.bot.utc_calc(data[4], style="R")
            progress_bar = self.level_bar(
                player_xp / XP_REQUIREMENTS[(self.get_level(player_xp) + 1)]
            )
            player_desc = f"Level {player_level}, {player_xp} XP. Worked {player_timesworked} times, last worked {player_lastworked}\nSalary: ${LEVEL_PAY[player_level]}/hr\n{self.get_level(player_xp)} {progress_bar} {self.get_level(player_xp) + 1}  ({player_xp} XP/{XP_REQUIREMENTS[(self.get_level(player_xp) + 1)]} XP)"
        await ctx.send(
            embed=discord.Embed(
                title="Jobs",
                description=f"{total_workers} workers with a combined total of {total_xp} XP, and {total_worked} times worked.",
                color=player.profile_color,
            ).add_field(name="Your stats", value=player_desc)
        )
        pass

    @commands.command(aliases=["w"])
    async def work(self, ctx):
        """Work. You work a random number of hours between 4-8. The cooldown for working is half the hours you've worked"""
        player = await Player.get(ctx.author.id, self.bot)
        hours = random.randint(4, 8)
        xp = hours * 2
        player_worked = await self.bot.pool.fetchrow(
            "SELECT * FROM e_jobs WHERE id = $1", player.id
        )
        if player_worked is None:
            # no player!
            await self.bot.pool.execute(
                "INSERT INTO e_jobs(id, lastworked, lasthours) VALUES ($1, $2, $3)",
                player.id,
                discord.utils.utcnow(),
                hours,
            )
            player_worked = await self.bot.pool.fetchrow(
                "SELECT * FROM e_jobs WHERE id = $1", player.id
            )
            await ctx.send(
                f"You've started working for the first time! View your stats with `{ctx.clean_prefix}job`"
            )
        elif not self.can_work(player_worked):
            return await ctx.send(
                f"You worked too recently! You can work {discord.utils.format_dt(self.bot.utc_calc(player_worked[4], raw=True) + timedelta(hours=hours/2), style='R')}"
            )
        current_level = self.get_level(player_worked[1])
        new_level = self.get_level((player_worked[1] + xp))
        pay = LEVEL_PAY[current_level]
        did_level_up = ""
        if current_level != new_level:
            # level up
            did_level_up = f"\n**Level up!** You're now level {new_level}, and make ${LEVEL_PAY[new_level]} an hour."
        await ctx.send(
            f"You worked {hours} hours and earned ${pay * hours}, and {xp} XP.{did_level_up}"
        )

        await self.bot.pool.execute(
            """
            UPDATE e_jobs SET
            xp = xp + $1,
            level = $2,
            timesworked = timesworked + 1,
            lastworked = $3,
            lasthours = $4
            WHERE id = $5
        """,
            xp,
            new_level,
            discord.utils.utcnow(),
            hours,
            player.id,
        )
        await player.update_balance(pay * hours, ctx=ctx)


async def setup(bot):
    await bot.add_cog(jobs(bot))
