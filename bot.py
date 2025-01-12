import discord
import asyncpg
import sys, os
import traceback
import asyncio
import time
import typing
import humanize
import config as Config
import logging
from cogs.utils import player as Player
from discord.ext import commands
from datetime import datetime, timezone
from cogs.utils.errors import InvalidBetAmountError, NotAPlayerError
from dateutil import parser

log = logging.getLogger(__name__)

os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"

class EcoBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def prompt(
        self,
        authorid,
        message: discord.Message,
        *,
        timeout=60.0,
        delete_after=True,
        author_id=None,
    ):
        """Credit to Rapptz
        https://github.com/Rapptz/RoboDanny/blob/715a5cf8545b94d61823f62db484be4fac1c95b1/cogs/utils/context.py#L93
        """
        confirm = None

        for emoji in ("\N{WHITE HEAVY CHECK MARK}", "\N{CROSS MARK}"):
            await message.add_reaction(emoji)

        def check(payload):
            nonlocal confirm
            if payload.message_id != message.id or payload.user_id != authorid:
                return False
            codepoint = str(payload.emoji)
            if codepoint == "\N{WHITE HEAVY CHECK MARK}":
                confirm = True
                return True
            elif codepoint == "\N{CROSS MARK}":
                confirm = False
                return True
            return False

        try:
            await bot.wait_for("raw_reaction_add", check=check, timeout=timeout)
        except asyncio.TimeoutError:
            confirm = None

        try:
            if delete_after:
                await message.delete()
        finally:
            return confirm

    async def setup_hook(self):
        self.pool = await asyncpg.create_pool(dsn=Config.db_dsn(), command_timeout=60)
        con = await self.pool.acquire()
        try:
            await con.execute(
                "CREATE TABLE IF NOT EXISTS e_users (id BIGINT PRIMARY KEY UNIQUE NOT NULL, name TEXT NOT NULL, bal BIGINT NOT NULL DEFAULT 100, totalearnings BIGINT NOT NULL DEFAULT 0, profilecolor VARCHAR(6) NOT NULL DEFAULT 'FFFFFF', lotterieswon INTEGER NOT NULL DEFAULT 0)"
            )
            await con.execute(
                "CREATE TABLE IF NOT EXISTS e_prefixes (userid BIGINT REFERENCES e_users(id), prefix VARCHAR(3) NOT NULL, setwhen TIMESTAMP NOT NULL DEFAULT now())"
            )
            cur = await con.fetch("SELECT userid, prefix FROM e_prefixes")
            cur = [tuple(p) for p in cur]
            self.prefixes = {user_id: prefix for user_id, prefix in cur}
        finally:
            log.info("Database connected")
            await self.pool.release(con)

        self.previous_balance_cache = {}

        success = failed = 0
        for cog in self.initial_extensions:
            try:
                await self.load_extension(f"{cog}")
                success += 1
            except Exception:
                log.error(f"failed to load {cog}, error:\n", file=sys.stderr)
                failed += 1
                traceback.print_exc()
            finally:
                continue
        log.info(f"loaded {success} cogs successfully, with {failed} failures.")

    async def get_stock(self, name_or_id):
        """Gets a stock from the database. Checks both name and ID."""
        data = None
        try:
            data = await bot.pool.fetchrow(
                "SELECT * FROM e_stocks WHERE stockid = $1", name_or_id
            )
        except asyncpg.DataError:
            try:
                data = await bot.pool.fetchrow(
                    "SELECT * FROM e_stocks WHERE name = $1", name_or_id
                )
            except asyncpg.DataError:
                return None
        return tuple(data)

    async def get_stock_from_player(self, userid):
        """Gets a stock from the database. Takes a user/member object."""
        data = await bot.pool.fetchrow(
            "SELECT * FROM e_stocks WHERE ownerid = $1", userid
        )
        return tuple(data)

    async def begin_user_deletion(self, ctx, i_msg):
        """Begins the user deletion process."""
        player = await self.get_player(ctx.author.id)
        if player is None:
            return

        def check(m):
            return (
                m.content.lower() == "yes"
                and m.channel == ctx.channel
                and m.author == ctx.author
            )

        await bot.wait_for("message", check=check)
        embed = discord.Embed(
            title="If you proceed, you will permanently lose the following data:",
            description="""**
            - Your profile (money, total earned amount, lotteries won, etc)

            - Your invests (money invested, etc)

            - Any owned stock (The fee spent to create it, its points, etc (all investers get refunded))

            - All achievements you've earned**

        \n*All* data involving you will be deleted.
        \nAre you sure you would like to continue? **There is __no__ going back.**
        """,
            color=discord.Color.red(),
        )
        msg = await ctx.send(embed=embed)
        did_they = await self.prompt(ctx.author.id, msg, timeout=30, delete_after=False)
        if did_they:
            await bot.pool.execute("DELETE FROM e_users WHERE id = $1", ctx.author.id)
            await ctx.send("Okay, it's done. According to my database, you no longer exist.\nThank you for using EconomyX.")
        if not did_they:
            await ctx.send("Phew, canceled. None of your data was deleted.")
        if did_they is None:
            return
        await msg.delete()
        return

    def utc_calc(
        self,
        timestamp: typing.Union[str, datetime],
        style: str = None,
        raw: bool = False,
        tz: timezone = timezone.utc,
    ):
        formatted_ts = None
        if isinstance(timestamp, str):
            formatted_ts = parser.parse(timestamp)
        else:
            formatted_ts = timestamp
        if raw:
            return formatted_ts
        if style:
            return discord.utils.format_dt(
                formatted_ts, style
            )  # Why tf did i put this in here, im terrible at writing methods lmao
        return humanize.precisedelta(formatted_ts.astimezone())

    def lottery_countdown_calc(
        self, timestamp: typing.Union[str, datetime]
    ):  # thanks pikaninja
        if isinstance(timestamp, str):
            timestamp = parser.parse(timestamp)
        delta_uptime = timestamp - discord.utils.utcnow()
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        return [days, hours, minutes, seconds]

async def get_prefix(bot, message):
    return bot.prefixes.get(message.author.id, bot.default_prefix)

desc = "EconomyX is a money system for Discord. It's straightfoward with only economy related commands, to keep it simple. I was made by averwhy#3899."
bot = EcoBot(
    command_prefix=get_prefix,
    description=desc,
    chunk_guilds_on_startup=False,
    intents=discord.Intents(
        reactions=True, messages=True, guilds=True, members=True, message_content=True
    ),
)

bot.initial_extensions = [
    "jishaku",
    "cogs.player_meta",
    "cogs.devtools",
    "cogs.games",
    "cogs.money_meta",
    "cogs.misc",
    "cogs.jobs",
    "cogs.stocks",
    "cogs.jsk_override",
    "cogs.lottery",
    "cogs.stats",
    "cogs.achievements",
    "cogs.treasure",
]
bot.time_started = time.localtime()
bot.version = "1.1.0"
bot.newstext = None
bot.news_set_by = "no one yet.."
bot.total_command_errors = 0
bot.total_command_completetions = 0
bot.launch_time = discord.utils.utcnow()
bot.maintenance = False
bot.updates_channel = 798014940086403083
bot.default_prefix = "e$"


@bot.event
async def on_ready():
    log.info("------------------------------------")
    log.info(f"\U00002705 Logged in as {bot.user.name} ({bot.user.id}) {bot.version}")
    log.info("------------------------------------")


@bot.event
async def on_command_completion(command):
    bot.total_command_completetions += 1


class MaintenenceActive(commands.CheckFailure):
    pass


@bot.check
async def maintenance_mode(ctx):
    if bot.maintenance and ctx.author.id != 267410788996743168:
        raise MaintenenceActive()
    return True


@bot.event
async def on_command_error(ctx: commands.Context, error):  # this is an event that runs when there is an error in a command
    try:
        if ctx.command.cog == bot.get_cog("games"):
            return
    except AttributeError:  # ctx.command is none for some reason
        pass
    if isinstance(error, MaintenenceActive):
        embed_color = discord.Color(discord.Color.brand_red())
        try: 
            player = await Player.get(ctx.author.id, bot)
            embed_color = player.profile_color
        except NotAPlayerError: pass

        embed = discord.Embed(
            description=f"Sorry, but maintenance mode is active.\nCheck out {ctx.clean_prefix} for updates.",
            color=embed_color,
        )
        await ctx.send(embed=embed)
    elif isinstance(error, discord.ext.commands.errors.CommandNotFound):
        return
    elif isinstance(error, NotAPlayerError):
        await ctx.send(f"You dont have a profile! Get one with `{ctx.clean_prefix}register`.")
        return
    elif isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        s = humanize.naturaldelta(round(error.retry_after, 2))
        await ctx.send(f"Error: Cooldown for {s}.", delete_after=15)
        return
    elif isinstance(error, commands.CheckFailure):
        # these should be handled in cogs
        return
    elif isinstance(error, ValueError):
        return await ctx.send("It looks like that's an invalid amount.")
    elif isinstance(error, InvalidBetAmountError):
        await ctx.send(error)
    else:
        bot.total_command_errors += 1
        await ctx.send(f"```diff\n- {error}\n```")
        log.warning("Ignoring exception in command {}:".format(ctx.command))
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr
        )


@bot.event
async def on_error(event):
    # All other Errors not returned come here. And we can just print the default TraceBack.
    if hasattr(event, "__traceback__"):
        log.error("A global error has occured:", file=sys.stderr)
        traceback.print_exception(
            type(event), event, event.__traceback__, file=sys.stderr
        )
    else:
        pass


async def startup():
    async with bot:
        await bot.start(Config.token)


if __name__ == "__main__":
    asyncio.set_event_loop(asyncio.SelectorEventLoop())
    discord.utils.setup_logging(root=True)
    try:
        asyncio.run(startup())
    except KeyboardInterrupt:
        log.critical("Forced shutdown...")
        bot.pool.close()
