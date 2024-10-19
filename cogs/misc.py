from typing import Mapping
import typing
import discord
import platform
import time
import os
import humanize
from discord.ext import commands, menus
from discord.ext.commands.cooldowns import BucketType
import asyncpg
import inspect
from .utils import botmenus
from .utils import player as Player
from .utils.errors import NotAPlayerError

OWNER_ID = 267410788996743168


# Thanks to Kal for helping me out with this
class HelpCommand(commands.HelpCommand):

    # This fires once someone does `<prefix>help`
    async def send_bot_help(
        self,
        mapping: Mapping[typing.Optional[commands.Cog], typing.List[commands.Command]],
    ):
        ctx = self.context
        try:
            pcolor = (await Player.get(ctx.author.id, ctx.bot)).profile_color
        except NotAPlayerError:
            pcolor = discord.Color.dark_gray()
        embed = discord.Embed(title="EconomyX Help", color=pcolor)
        embed.set_footer(
            text=f"Do {ctx.clean_prefix}help [command] or {ctx.clean_prefix}help [category] for more info"
        )
        for cog, cmds in mapping.items():
            filtered = await self.filter_commands(cmds, sort=True)
            if filtered:
                all_commands = "  ".join(
                    f"`{c.name}`" if not c.hidden else "" for c in cmds
                )
                if cog and cog.description:
                    embed.add_field(
                        name=cog.qualified_name, value=f"-> {all_commands}", inline=True
                    )
        await ctx.send(embed=embed)

    # This fires once someone does `<prefix>help <cog>`
    async def send_cog_help(self, cog: commands.Cog):
        ctx = self.context
        embed = discord.Embed(title=f"Help for {cog.qualified_name}")
        embed.set_footer(text=f"Do {ctx.clean_prefix}help [command] for more info")

        entries = await self.filter_commands(cog.get_commands(), sort=True)
        for cmd in entries:
            if cmd.hidden:
                continue
            embed.add_field(
                name=f"{ctx.clean_prefix}{cmd.name} {cmd.signature}",
                value=f"{cmd.help or cmd.description}",
                inline=False,
            )
        await ctx.send(embed=embed)

    # This fires once someone does `<prefix>help <command>`
    async def send_command_help(self, command: commands.Command):
        ctx = self.context

        embed = discord.Embed(
            title=f"{ctx.clean_prefix}{command.qualified_name} {command.signature}",
            description=f"{command.help or command.description}",
        )
        embed.set_footer(text=f"Do {ctx.clean_prefix}help [command] for more info")
        await ctx.send(embed=embed)

    # This fires once someone does `<prefix>help <group>`
    async def send_group_help(self, group: commands.Group):
        ctx = self.context
        embed = discord.Embed(
            title=f"{ctx.clean_prefix}{group.qualified_name} {group.signature}",
            description=group.help,
        )
        embed.set_footer(text=f"Do {ctx.clean_prefix}help [command] for more help")

        for command in group.commands:
            embed.add_field(
                name=f"{ctx.clean_prefix}{command.name} {command.signature}",
                value=(command.description or command.help),
                inline=False,
            )
        await ctx.send(embed=embed)


class misc(commands.Cog, command_attrs=dict(name="Misc")):
    """These are miscellaneous bot commands, primarily meta about the bot."""

    def __init__(self, bot):
        self.bot = bot
        self.bot._original_help_command = bot.help_command
        bot.help_command = HelpCommand()
        bot.help_command.cog = self

        with open("PrivacyPolicy.txt", "r") as t:
            self.pp = []
            fulltext = t.read()
            splice_1 = fulltext[0:606]
            splice_2 = fulltext[606:1922]
            splice_3 = fulltext[1922 : len(fulltext)]
            for o in [splice_1, splice_2, splice_3]:
                self.pp.append(o)

    def cog_unload(self):
        self.bot.help_command = self.bot._original_help_command

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx):
        """Views the prefix you use with the bot. Note that this is only per-user."""
        prefixdata = self.bot.prefixes.get(ctx.author.id, "e$")
        pcolor = (await Player.get(ctx.author.id, self.bot)).profile_color
        if pcolor is None:
            pcolor = discord.Color.random()
        embed = discord.Embed(color=pcolor)
        embed.add_field(name=f"{str(ctx.author)}'s prefix", value=prefixdata)
        embed.set_footer(text=f"To change prefix, use {ctx.clean_prefix}prefix set")
        await ctx.send(embed=embed)

    @prefix.command(
        name="set",
        aliases=["new", "change", "s", "n", "c"],
        description="Allows you to change the prefix you use with the bot. Note that this is only per-user.",
    )
    async def _set(self, ctx, newprefix=""):
        """Changes the prefix that you use with the bot."""
        if len(newprefix) > 5:
            return await ctx.send("That prefix is too long.")

        data = await self.bot.pool.fetchrow(
            "SELECT * FROM e_prefixes WHERE userid = $1", ctx.author.id
        )
        if tuple(data) is None:
            await self.bot.pool.execute(
                "INSERT INTO e_prefixes(userid, prefix, setwhen) VALUES ($1, $2, $3)",
                ctx.author.id,
                newprefix,
                discord.utils.utcnow(),
            )
        else:
            await self.bot.pool.execute(
                "UPDATE e_prefixes SET prefix = $1 WHERE userid = $2",
                newprefix,
                ctx.author.id,
            )
        self.bot.prefixes[ctx.author.id] = newprefix
        if newprefix == "":
            await ctx.reply(
                f"Your new prefix is... nothing? <:meowshrug:789970107458781207> Anyway, do note this is your prefix, and no one elses"
            )
            return
        await ctx.reply(
            f"Your new prefix is `{newprefix}`. Do note this is your prefix, and no one elses"
        )

    @prefix.command(name="reset")
    async def _reset(self, ctx):
        """Resets to default prefix."""
        await self.bot.pool.fetchrow(
            "DELETE FROM e_prefixes WHERE userid = $1", ctx.author.id
        )
        try:
            self.bot.prefixes.pop(ctx.author.id)
        except KeyError:
            return await ctx.send(
                "Your prefix is already set the default prefix <:meowshrug:789970107458781207>"
            )
        await ctx.send("Your prefix was reset to the default prefix of `e$`")

    @commands.cooldown(1, 10, BucketType.channel)
    @commands.command(aliases=["information"])
    async def info(self, ctx):
        """Shows bot information and statistics."""
        try:
            player = await Player.get(ctx.author.id, self.bot)
            color = player.profile_color
        except:
            color = discord.Color.blurple()
        money_total = await self.bot.pool.fetchrow("SELECT SUM(bal) FROM e_users")
        total_db_users = await self.bot.pool.fetchrow("SELECT COUNT(id) FROM e_users")
        total_stocks = await self.bot.pool.fetchrow("SELECT COUNT(*) FROM e_stocks")
        total_invested = await self.bot.pool.fetchrow(
            "SELECT SUM(invested) FROM e_invests"
        )
        num_invested = await self.bot.pool.fetchrow("SELECT COUNT(*) FROM e_invests")
        desc = f"""**Guilds:** {len(self.bot.guilds)}
        **Number of players:** {tuple(total_db_users)[0]}
        **Current Money Total:** ${humanize.intcomma(tuple(money_total)[0])}
        **Total Stocks:** {tuple(total_stocks)[0]}
        **Total number of invests:** {tuple(num_invested)[0]}
        **Total money invested in stocks:** ${humanize.intcomma(tuple(total_invested)[0])}
        **Top.gg link (vote me pls :>)**: https://top.gg/bot/780480654277476352
        **Support Server:** *See invite above*
        **Protip: See a live count of the users, guilds, and players in the support server!*
        """
        embed = discord.Embed(title="EconomyX Info", description=desc, color=color)
        embed.set_footer(
            text=f"Made with Python {platform.python_version()}, discord.py {discord.__version__}, and PostgreSQL {asyncpg.__version__}",
            icon_url="https://images-ext-1.discordapp.net/external/0KeQjRAKFJfVMXhBKPc4RBRNxlQSiieQtbSxuPuyfJg/http/i.imgur.com/5BFecvA.png",
        )
        await ctx.send(content="https://discord.gg/epQZEp933x", embed=embed)

    @commands.command()
    async def support(self, ctx):
        source_url = "https://github.com/averwhy/EconomyX"
        await ctx.send(
            f"https://discord.gg/epQZEp933x\nYou can also create an issue on my Github repository: <{source_url}>"
        )

    @commands.cooldown(1, 5, BucketType.user)
    @commands.command()
    async def invite(self, ctx):
        """Returns a link that you can use to invite EconomyX to your server."""
        try:
            player = await Player.get(ctx.author.id, self.bot)
            color = player.profile_color
        except:
            color = discord.Color.blurple()
        await ctx.send(
            embed=discord.Embed(
                title="EconomyX Bot Invite",
                description=f"Join the support server! `{ctx.clean_prefix}support`",
                url="https://discord.com/api/oauth2/authorize?client_id=780480654277476352&permissions=0&scope=bot",
                color=color,
            )
        )

    @commands.cooldown(1, 10, BucketType.user)
    @commands.command()
    async def uptime(self, ctx):
        """Shows the uptime for EconomyX"""
        self.bot.launch_time
        relative = discord.utils.format_dt(self.bot.launch_time, "R")
        full = discord.utils.format_dt(self.bot.launch_time, "F")
        await ctx.send(f"{full} / {relative}")

    @commands.command()
    async def ping(self, ctx):
        """Shows EconomyX's latency/connection to Discord."""
        try:
            pcolor = (await Player.get(ctx.author.id, ctx.bot)).profile_color
        except NotAPlayerError:
            pcolor = discord.Color.random()
        start = time.perf_counter()
        message = await ctx.send(
            embed=discord.Embed(
                title="<a:ppCircle:1277157700421161083>", color=discord.Color.random()
            )
        )
        end = time.perf_counter()
        start2 = time.perf_counter()
        await self.bot.pool.fetchrow("SELECT * FROM e_users")
        end2 = time.perf_counter()
        duration = round(((end - start) * 1000), 1)
        db_duration = round(((end2 - start2) * 1000), 1)
        newembed = discord.Embed(title="Pong!", color=pcolor)
        ws = round((self.bot.latency * 1000), 1)
        newembed.add_field(name="Typing", value=f"{duration}ms")
        newembed.add_field(name="Websocket", value=f"{ws}ms")
        newembed.add_field(name="Database", value=f"{db_duration}ms")
        await message.edit(embed=newembed)

    # CREDIT TO RAPPTZ FOR THIS
    # https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/meta.py#L355-L393
    @commands.command(description="Gets the source on github for any command.")
    async def source(self, ctx, *, command: str = None):
        source_url = "https://github.com/averwhy/EconomyX"
        branch = "main"
        if command is None:
            return await ctx.send(source_url)

        if command == "help":
            await ctx.send(
                "<https://github.com/averwhy/EconomyX/blob/main/cogs/misc.py#L21-L81>"
            )
            return
        if command in ('jsk', 'jishaku'):
            await ctx.send(
                "Jishaku is a debug and testing command made for discord.py. The code can be found here:\n<https://github.com/Gorialis/jishaku>"
            )
            return
        else:
            obj = self.bot.get_command(command.replace(".", " "))
            if obj is None:
                return await ctx.send("Could not find command.")

            src = obj.callback.__code__
            module = obj.callback.__module__
            filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        if not module.startswith("discord"):
            # not a built-in command
            location = os.path.relpath(filename).replace("\\", "/")
        else:
            location = module.replace(".", "/") + ".py"

        final_url = f"<{source_url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>"
        await ctx.send(final_url)

    @commands.command(aliases=["pp", "privacypolicy"])
    async def privacy_policy(self, ctx):
        """An interactive command to view EconomyX's Privacy Policy."""
        p = menus.MenuPages(
            source=botmenus.PPSource(self.pp), clear_reactions_after=True
        )
        await p.start(ctx)

    @commands.command()
    @commands.cooldown(1, 60, BucketType.user)
    async def news(self, ctx):
        channel = self.bot.get_channel(self.bot.updates_channel)
        if channel is None:
            channel = await self.bot.fetch_channel(self.bot.updates_channel)
        try:
            clr = (await Player.get(ctx.author.id, self.bot)).profile_color
        except NotAPlayerError:
            if ctx.guild:
                clr = ctx.guild.me.color
            else:
                clr = discord.Color.dark_gray()
        (latest_message,) = [message async for message in channel.history(limit=1)]
        embed = discord.Embed(
            title="EconomyX News",
            description=f"{latest_message.content}\n\n[Jump to message]({latest_message.jump_url})  |  [Can't see message? Join support server](https://discord.gg/epQZEp933x)",
            color=clr,
        )
        isdev = "(Developer) " if latest_message.author.id == OWNER_ID else ""
        embed.set_footer(
            text=f"Set by {isdev}{str(latest_message.author)}, {humanize.precisedelta(latest_message.created_at.astimezone().replace(tzinfo=None))} ago",
            icon_url=latest_message.author.avatar.url,
        )
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.cooldown(1, 60, BucketType.channel)
    async def reallylongcat(self, ctx):
        return await ctx.send(
            "<:lc_0_0:818242033897832488>\n<:lc_0_1:818242049027342406>\n<:lc_0_2:818242062645854249>\n<:lc_0_3:818242081788002346>\n<:lc_0_4:818242096041427004>\n<:lc_0_5:818242107152007208>"
        )

    @commands.command(hidden=True)
    @commands.cooldown(1, 60, BucketType.channel)
    async def reallywidecat(self, ctx):
        return await ctx.send(
            "<:swag1:782786337387315221><:swag2:782786368123306014><:swag3:782786380954730536>"
        )


async def setup(bot):
    await bot.add_cog(misc(bot))
