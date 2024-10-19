import asyncio
import discord
import sys, time, random
from discord.ext import menus
from discord.ext import commands, tasks
from .utils import player as Player
import aiosqlite
import traceback
import humanize
import logging
from discord import Webhook
import aiohttp
from .utils.errors import NotAPlayerError

OWNER_ID = 267410788996743168
SUPPORT_SERVER = 798014878018174976
log = logging.getLogger(__name__)


class EmojiListSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, entry):
        # Takes a list of embeds
        return entry.set_footer(
            text=f"Page {(menu.current_page * self.per_page) + 1}/{self.get_max_pages()}"
        )


success_emojis = [
    "<:YEP:819979975096533032>",
    "<a:cookdance:829764800758022175>",
    "<a:CRANKING:1152119357179170816>",
    "<:Pepege:821906846192631849>",
    "<a:om:1223345179373600839>",
    "<a:om62:1210662179813068851>",
    "<a:reow:1210662056450072656>",
    "<a:bih:1212526076106907728>",
    "<a:YESS:1238651990939144222>",
    "<a:snod:798165766888488991>",
    "<:peepoGlad:819979951876079657>",
    "<:5Head:819980082873237536>",
]
failed_emojis = [
    "<a:AwareMan:1122794710721908777>",
    "<:Dentge:1154444232304635986>",
    "<:omeStare:1224964966050824284>",
    "<:painnnnn:837004732450734190>",
    "<:blobweary:809765011152568330>",
    "<a:SOYSCREAM:1091233925667487814>",
    "<:Weirdge:821906833848533075>",
    "<:TrollAware:1213770138780962877>",
    "<a:Alright:1212526220655464510>," "<a:forsnotL:1210663171765968918>",
    "<a:forsenFaint:1210662767468748820>",
    "<a:sno:784149860726865930>",
    "<a:no:798969459645218879>",
    "<a:ppPoof:1212154512467558520>",
]


class devtools(commands.Cog, command_attrs=dict(name="Devtools", hidden=True)):
    """
    Dev commands. thats really it
    """

    def __init__(self, bot):
        self.bot = bot
        self.log_hook = open("WEBHOOK.txt", "r").readline()

    async def cog_load(self):
        self.database_backup_task.start()

    async def cog_unload(self):
        try:
            await self.database_backup_task.cancel()
        except TypeError:
            pass

    @tasks.loop(minutes=10)  # TODO fix later
    async def database_backup_task(self):
        pass

    #     try:
    #         self.bot.backup_db = await aiosqlite.connect('ecox_backup.db')
    #         await self.bot.db.backup(self.bot.backup_db)
    #         await self.bot.backup_db.close()
    #         return
    #     except Exception as e:
    #         print(f"An error occured while backing up the database:\n`{e}`")
    #         return

    async def cog_check(self, ctx):
        return ctx.author.id == OWNER_ID

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        await self.bot.process_commands(after)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        guildstatvc = await self.bot.fetch_channel(798014995496960000)
        playerstatvc = await self.bot.fetch_channel(809977048868585513)
        await guildstatvc.edit(name=f"Guilds: {len(self.bot.guilds)}")
        total_db_users = await self.bot.pool.fetchrow("SELECT COUNT(*) FROM e_users")
        await playerstatvc.edit(name=f"Players: {tuple(total_db_users)[0]}")

        ts = humanize.precisedelta(guild.created_at.replace(tzinfo=None))
        msg = f"""+1 guild ```prolog
Guild:           {guild.name}
ID:              {guild.id}
Members:         {guild.member_count}
Boost level:     {guild.premium_tier}
Desc:            {(guild.description or 'None')}
Created:         {ts} ago```
        """
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(self.log_hook, session=session)
            await webhook.send(msg)
        log.info(
            f"Joined new guild '{guild.name}', new guild count: {len(self.bot.guilds)}"
        )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if guild.owner is None or len(guild.name) <= 0:
            return
        guildstatvc = await self.bot.fetch_channel(798014995496960000)
        playerstatvc = await self.bot.fetch_channel(809977048868585513)
        await guildstatvc.edit(name=f"Guilds: {len(self.bot.guilds)}")
        total_db_users = await self.bot.pool.fetchrow("SELECT COUNT(*) FROM e_users")
        await playerstatvc.edit(name=f"Players: {tuple(total_db_users)[0]}")

        ts = humanize.precisedelta(guild.created_at.replace(tzinfo=None))
        msg = f"""-1 guild ```prolog
Guild:           {guild.name}
ID:              {guild.id}
Members:         {guild.member_count}
Boost level:     {guild.premium_tier}
Desc:            {(guild.description or 'None')}
Created:         {ts} ago```
        """
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(self.log_hook, session=session)
            await webhook.send(msg)
        log.info(
            f"Left a guild '{guild.name}', new guild count: {len(self.bot.guilds)}"
        )

    @commands.group(invoke_without_command=True, hidden=True, aliases=["dv"])
    async def dev(self, ctx):
        # bot dev commands
        await ctx.send("invalid subcommand <:PepePoint:759934591590203423>")

    @dev.command()
    async def force(self, ctx):
        """Forces a draw of the lottery"""
        try:
            await self.bot.get_cog("lottery").draw(force=True)
            await ctx.message.add_reaction("\U00002705")
        except Exception as error:
            await ctx.send(f"An error occured while force drawing: `{error}`")
            log.warning(
                "Ignoring exception in command {}:".format(ctx.command), file=sys.stderr
            )
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )
            return

    @dev.command(aliases=["us"])
    async def updatestats(self, ctx):
        async with ctx.channel.typing():
            guildstatvc = await self.bot.fetch_channel(798014995496960000)
            playerstatvc = await self.bot.fetch_channel(809977048868585513)
            await guildstatvc.edit(name=f"Guilds: {len(self.bot.guilds)}")
            total_db_users = await self.bot.pool.fetchrow(
                "SELECT COUNT(*) FROM e_users"
            )
            await playerstatvc.edit(name=f"Players: {tuple(total_db_users)[0]}")
        await ctx.send("Updated support server stats")

    @dev.command(aliases=["fuckoff", "die", "halt", "cease", "shutdown", "logout"])
    async def stop(self, ctx):
        await ctx.send("<a:ppPoof:1212154512467558520>")
        log.warning(f"Bot is being stopped by {ctx.message.author} ({ctx.author.id})")
        await asyncio.wait_for(self.bot.pool.close(), timeout=45.0)
        await self.bot.close()

    @dev.command()
    async def sql(self, ctx, *, query):
        # parser = argparse.ArgumentParser().add_argument('-s', '--search', action='store_true')
        # do_search = parser.parse_args()
        # print(args.verbose)
        failed = False
        error = ""
        p1 = time.perf_counter()
        try:
            result = None  # prevents deepsource from yelling at me
            result = await self.bot.pool.fetch(query)
        except Exception as e:
            failed = True
            error = e
        finally:
            p2 = time.perf_counter()
            perf = round((p2 - p1) * 1000, 2)
            if failed:
                rfe = random.choice(failed_emojis)
                await ctx.send(f"{rfe} `{perf}s`: {error}")
                return
            rse = random.choice(success_emojis)
            await ctx.send(f"{rse} `{perf}ms`: {str(result)}")
            return

    @dev.group(invoke_without_command=True)
    async def eco(self, ctx):
        pass

    @eco.command()
    async def reset(self, ctx, user: discord.User = None):
        if user is None:
            await ctx.send("Provide an user")
            return
        try:
            await Player.get(ctx.author.id, self.bot)
        except NotAPlayerError:
            return await ctx.send("That player doesn't seem to have a profile.")
        await self.bot.pool.execute(
            "UPDATE e_users SET bal = 100 WHERE id = $1", user.id
        )
        await ctx.send("Reset.")

    @eco.command()
    async def give(self, ctx, user: discord.User, amount):
        amount = float(amount)
        try:
            player = await Player.get(ctx.author.id, self.bot)
        except NotAPlayerError:
            return await ctx.send("That player doesn't seem to have a profile.")
        await self.bot.pool.execute(
            "UPDATE e_users SET bal = (bal + $1) WHERE id = $2", amount, user.id
        )
        await ctx.send(f"Success.\nNew balance: ${(player.balance + amount)}")

    @eco.command(name="set")
    async def setamount(self, ctx, user: discord.User, amount: int):
        try:
            await Player.get(ctx.author.id, self.bot)
        except NotAPlayerError:
            return await ctx.send("That player doesn't seem to have a profile.")
        await self.bot.pool.execute(
            "UPDATE e_users SET bal = $1 WHERE id = $2", amount, user.id
        )
        await ctx.send("Success.")

    @dev.command(aliases=["bu"], disabled=True)
    async def backup(self, ctx):
        try:
            self.bot.backup_db = await aiosqlite.connect("ecox_backup.db")
            # await self.bot.pool.backup(self.bot.backup_db) #TODO fix me now
            # await self.bot.backup_db.close()
            # await ctx.send("done, lol")
            return
        except Exception as e:
            await ctx.send(f"An error occured while backing up the database:\n`{e}`")
            return

    @dev.group(aliases=["s"], invoke_without_command=True)
    async def status(self, ctx):
        await ctx.send(f"Current status: {self.bot.status}")

    @status.command(name="stream", aliases=["streaming"])
    async def streamingstatus(self, ctx, *, name):
        if ctx.author.id != 267410788996743168:
            return
        await self.bot.change_presence(
            activity=discord.Streaming(name=name, url="https://twitch.tv/avrwhy/")
        )
        await ctx.send("aight, done")

    @status.command()
    async def playing(self, ctx, *, text):
        # Setting `Playing ` status
        if text is None:
            await ctx.send(f"{ctx.guild.me.status}")
        if len(text) > 60:
            await ctx.send("Too long you pepega")
            return
        try:
            await self.bot.change_presence(activity=discord.Game(name=text))
            await ctx.message.add_reaction("\U00002705")
        except Exception as e:
            await ctx.message.add_reaction("\U0000274c")
            await ctx.send(f"`{e}`")

    @dev.command()
    async def m(self, ctx):
        if self.bot.maintenance:
            self.bot.maintenance = False
            return await ctx.send("Maintenence is now off.")
        else:
            self.bot.maintenance = True
            return await ctx.send("Maintenence is now on.")

    @dev.command()
    async def cdr(self, ctx, for_id: int = OWNER_ID):
        """Resets cooldown for treasure and working"""
        await self.bot.pool.execute(
            "UPDATE e_treasure SET lastmins = 0 WHERE id = $1", for_id
        )
        await self.bot.pool.execute(
            "UPDATE e_jobs SET lasthours = 0 WHERE id = $1", for_id
        )
        await ctx.message.add_reaction("\U0001f44d")

    @dev.command(aliases=["emojis", "emoji", "emote", "em"])
    async def emotes(self, ctx, ename: str = None):
        """Shows all emotes that the bot can see"""
        player = await Player.get(ctx.author.id, self.bot)
        allemojis = self.bot.emojis
        if ename is not None:
            allemojis = []
            for n in self.bot.emojis:
                if n.name == ename.strip():
                    allemojis.append(n)
        charlim = 4096
        charcount = 0
        current_message = ""
        descs = []
        embeds = []
        for e in allemojis:
            if (len(str(e)) + charcount) >= charlim:
                # no space in message
                descs.append(current_message)
                current_message = ""
                charcount = 0
            else:
                # space in message
                current_message = current_message + str(e) + " "
                charcount += len(str(e)) + 1
        for d in descs:
            embeds.append(
                discord.Embed(
                    title="EconomyX Emojis", description=d, color=player.profile_color
                )
            )
        if len(embeds) == 0:
            return await ctx.send("No results")
        emojipage = menus.MenuPages(
            source=EmojiListSource(embeds), clear_reactions_after=True
        )
        await emojipage.start(ctx)

    @dev.command(aliases=["steal"])
    async def yoink(self, ctx, emoji, *, args: str = None):
        custom_name = None
        converter = commands.PartialEmojiConverter()
        try:
            result = await converter.convert(ctx, emoji)
        except commands.errors.PartialEmojiConversionFailure:
            return await ctx.send("Is that an emoji? <:Weirdge:821906833848533075>")

        emojibytes = await result.read()
        server = self.bot.get_guild(SUPPORT_SERVER)
        if not server:
            server = await self.bot.fetch_guild(SUPPORT_SERVER)
        if args and "as:" in args:
            args = args.strip("as:")
            custom_name = args
        custom_name = result.name if custom_name is not None else result.name
        try:
            await server.create_custom_emoji(
                name=custom_name,
                image=emojibytes,
                reason=f"Cloned by {ctx.author.name}",
            )
        except discord.Forbidden:
            return await ctx.send(
                f"{random.choice(failed_emojis)} Failed. either no space or i dont have perms"
            )
        await ctx.message.add_reaction(random.choice(success_emojis))

    @dev.command(aliases=["r", "rl"])
    async def reload(self, ctx, *cogs: str):
        failed = 0
        if len(cogs) == 0:
            cogs = self.initial_extensions
        else:
            cogs = [
                f"cogs.{c.removeprefix('cogs.')}" for c in cogs
            ]  # this will add 'cogs.' to every extension given
        for c in cogs:
            try:
                try:
                    await self.bot.unload_extension(f"{c}")
                except commands.ExtensionNotLoaded:
                    pass  # its already unloaded so we'll just load it
                await self.bot.load_extension(f"{c}")
                log.info(f"Reloaded {c.removeprefix('cogs.')} cog")
            except Exception as e:
                failed += 1
                log.error(str(e))
        if failed == 0:
            return await ctx.message.add_reaction(random.choice(success_emojis))
        else:
            await ctx.message.add_reaction(random.choice(failed_emojis))
            await asyncio.sleep(0.2)
            return await ctx.send(
                "<:Ermm:1278588088893050993> there were errors check console"
            )

    @dev.command(aliases=["ul", "u"])
    async def unload(self, ctx, *cogs: str):
        failed = 0
        if len(cogs) == 0:
            cogs = self.initial_extensions
        else:
            cogs = [
                f"cogs.{c.removeprefix('cogs.')}" for c in cogs
            ]  # this will add 'cogs.' to every extension given
        for c in cogs:
            try:
                await self.bot.unload_extension(f"{c}")
                log.info(f"Unloaded {c.removeprefix('cogs.')} cog")
            except Exception as e:
                failed += 1
                log.error(str(e))
        if failed == 0:
            return await ctx.message.add_reaction(random.choice(success_emojis))
        else:
            await ctx.message.add_reaction(random.choice(failed_emojis))
            await asyncio.sleep(0.2)
            return await ctx.send(
                "<:Ermm:1278588088893050993> there were errors check console"
            )

    @dev.command()
    async def sudo(
        self, ctx, target: discord.Member, channel: discord.TextChannel = None
    ):
        msg = ctx.message
        new_channel = channel or ctx.channel
        msg.channel = new_channel
        msg.author = target
        msg.content = ctx.prefix + ctx.command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)


async def setup(bot):
    await bot.add_cog(devtools(bot))
