from typing import Mapping
import typing
import discord
import platform
import time
import os
import humanize
from datetime import datetime, timezone
from discord.ext import commands, menus
from discord.ext.commands.cooldowns import BucketType
import aiosqlite
import inspect
from .utils import botmenus
from .utils import player as Player
OWNER_ID = 267410788996743168
# CREDIT TO KAL CREDIT TO KAL CREDIT TO KAL CREDIT TO KAL CREDIT TO KAL CREDIT TO KAL CREDIT TO KAL CREDIT TO KAL CREDIT TO KAL CREDIT TO KAL
# oh and also credit to kal
# await kal.credit(kal=kal)
# kal to credit

class HelpCommand(commands.HelpCommand):
    """Sup averwhy hopefully this is all easy to understand."""

    # This fires once someone does `<prefix>help`
    async def send_bot_help(self, mapping: Mapping[typing.Optional[commands.Cog], typing.List[commands.Command]]):
        ctx = self.context
        clr = await ctx.bot.get_player_color(ctx.author)
        if clr is None:
            if ctx.guild is not None: clr = ctx.guild.me.color
            else: clr = discord.Color.dark_gray()
        embed = discord.Embed(title="EconomyX Help", color=clr)
        embed.set_footer(text=f"Do {ctx.clean_prefix}help [command] for more info")
        for cog, cmds in mapping.items():
            filtered = await self.filter_commands(cmds, sort=True)
            if filtered:
                all_commands = "  ".join(f"`{c.name}`" for c in cmds)
                if cog and cog.description:
                    embed.add_field(name=cog.qualified_name,
                                    value=f"-> {all_commands}",
                                    inline=False)

        await ctx.send(embed=embed)

    # This fires once someone does `<prefix>help <cog>`
    async def send_cog_help(self, cog: commands.Cog):
        ctx = self.context
        embed = discord.Embed(title=f"Help for {cog.qualified_name}")
        embed.set_footer(text=f"Do {ctx.clean_prefix}help [command] for more info")

        entries = await self.filter_commands(cog.get_commands(), sort=True)
        for cmd in entries:
            embed.add_field(name=f"{ctx.clean_prefix}{cmd.name} {cmd.signature}",
                            value=f"{cmd.help or cmd.description}",
                            inline=False)

        await ctx.send(embed=embed)

    # This fires once someone does `<prefix>help <command>`
    async def send_command_help(self, command: commands.Command):
        ctx = self.context

        embed = discord.Embed(title=f"{ctx.clean_prefix}{command.qualified_name} {command.signature}",
                              description=f"{command.help or command.description}")
        embed.set_footer(text=f"Do {ctx.clean_prefix}help [command] for more info")

        await ctx.send(embed=embed)

    # This fires once someone does `<prefix>help <group>`
    async def send_group_help(self, group: commands.Group):
        ctx = self.context

        embed = discord.Embed(title=f"{ctx.clean_prefix}{group.qualified_name} {group.signature}",
                              description=group.help)
        embed.set_footer(text=f"Do {ctx.clean_prefix}help [command] for more help")

        for command in group.commands:
            embed.add_field(name=f"{ctx.clean_prefix}{command.name} {command.signature}",
                            value=(command.description or command.help),
                            inline=False)

        await ctx.send(embed=embed)


class misc(commands.Cog):
    """These are miscellaneous bot commands, primarily meta about the bot."""
    def __init__(self,bot):
        self.bot = bot
        self.bot._original_help_command = bot.help_command
        bot.help_command = HelpCommand()
        bot.help_command.cog = self
        
        with open("PrivacyPolicy.txt",'r') as t:
            self.pp = []
            fulltext = t.read()
            splice_1 = fulltext[0:606]
            splice_2 = fulltext[606:1922]
            splice_3 = fulltext[1922:len(fulltext)]
            for o in [splice_1, splice_2, splice_3]:
                self.pp.append(o)
    
    def cog_unload(self):
        self.bot.help_command = self.bot._original_help_command
    
    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx):
        """Views the prefix you use with the bot. Note that this is only per-user."""
        prefixdata = self.bot.prefixes.get(ctx.author.id, 'e$')
        pcolor = await Player.get(ctx.author.id, self.bot).profile_color
        if pcolor is None: pcolor = discord.Color.random()
        embed = discord.Embed(color=pcolor)
        embed.add_field(name=f"{str(ctx.author)}'s prefix", value=prefixdata)
        await ctx.send(embed=embed)
    
    @prefix.command(name="set",aliases=["new","change","s","n","c"],description="Allows you to change the prefix you use with the bot. Note that this is only per-user.")
    async def _set(self, ctx, newprefix = ''):
        if len(newprefix) > 5:
            return await ctx.send("That prefix is too long.")
        
        c = await self.bot.db.execute("SELECT * FROM e_prefixes WHERE userid = ?",(ctx.author.id,))
        data = await c.fetchone()
        if data is None:
            await self.bot.db.execute("INSERT INTO e_prefixes VALUES (?, ?, ?)",(newprefix, ctx.author.id, discord.utils.utcnow(),))
        else:
            await self.bot.db.execute("UPDATE e_prefixes SET prefix = ? WHERE userid = ?",(newprefix, ctx.author.id,))
        await self.bot.db.commit()
        self.bot.prefixes[ctx.author.id] = newprefix
        if newprefix == '':
            await ctx.send(f"Your new prefix is nothing. Do note this is your prefix, and no one elses.")
            return
        await ctx.send(f"Your new prefix is `{newprefix}`. Do note this is your prefix, and no one elses.")
    
    @commands.cooldown(1,10,BucketType.channel)
    @commands.command(aliases=["information"])
    async def info(self,ctx):
        """Shows bot information and statistics."""
        try:
            player = await Player.get(ctx.author.id, self.bot)
            color = player.profile_color
        except:
            color = discord.Color.blurple()
        c = await self.bot.db.execute("SELECT SUM(bal) FROM e_users")
        money_total = await c.fetchone()
        c = await self.bot.db.execute("SELECT COUNT(id) FROM e_users")
        total_db_users = await c.fetchone()
        c = await self.bot.db.execute("SELECT COUNT(*) FROM e_stocks")
        total_stocks = await c.fetchone()
        c = await self.bot.db.execute("SELECT SUM(invested) FROM e_invests")
        total_invested = await c.fetchone()
        c = await self.bot.db.execute("SELECT COUNT(*) FROM e_invests")
        num_invested = await c.fetchone()
        desc = f"""**Guilds:** {len(self.bot.guilds)}
        **Total Users:** {len(self.bot.users)}
        **Commands:** {len(self.bot.commands)}
        **Current Money Total:** ${money_total[0]}
        **Total Stocks:** {total_stocks[0]}
        **Total number of invests:** {num_invested[0]}
        **Total money invested in stocks:** ${total_invested[0]}
        **Number of users in database:** {total_db_users[0]}
        **Database changes in this session:** {self.bot.db.total_changes}
        **Active database transaction:** {self.bot.db.in_transaction}
        **Top.gg link (vote me pls :>): https://top.gg/bot/780480654277476352**
        **Support Server:** *See invite above*
        **Protip: See a live count of the users, guilds, and players in the support server!*
        """
        embed = discord.Embed(title="EconomyX Info",description=desc,color=color)
        embed.set_footer(text=f"Made with Python {platform.python_version()}, discord.py {discord.__version__}, and aiosqlite {aiosqlite.__version__}",icon_url="https://images-ext-1.discordapp.net/external/0KeQjRAKFJfVMXhBKPc4RBRNxlQSiieQtbSxuPuyfJg/http/i.imgur.com/5BFecvA.png")
        await ctx.send(content="https://discord.gg/epQZEp933x", embed=embed)
    
    @commands.command()
    async def support(self, ctx):
        source_url = 'https://github.com/averwhy/EconomyX'
        await ctx.send(f"https://discord.gg/epQZEp933x\nYou can also create an issue on my Github repository: <{source_url}>")
    
    @commands.cooldown(1,5,BucketType.user)
    @commands.command()
    async def invite(self,ctx):
        """Returns a link that you can use to invite EconomyX to your server."""
        try:
            player = await Player.get(ctx.author.id, self.bot)
            color = player.profile_color
        except:
            color = discord.Color.blurple()
        await ctx.send(embed=discord.Embed(title="EconomyX Bot Invite",description=f"Join the support server! `{ctx.clean_prefix}support`",url="https://discord.com/api/oauth2/authorize?client_id=780480654277476352&permissions=0&scope=bot",color=color))
    
    @commands.cooldown(1,10,BucketType.user)
    @commands.command()
    async def uptime(self, ctx):
        """Shows the uptime for EconomyX"""
        delta_uptime = discord.utils.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        await ctx.send(f"```autohotkey\n{days}d, {hours}h, {minutes}m, {seconds}s\n```")
        
    @commands.command()
    async def ping(self, ctx):
        """Shows EconomyX's latency/connection to Discord."""
        em = discord.PartialEmoji(name="loading",animated=True,id=782995523404562432)
        start = time.perf_counter()
        message = await ctx.send(embed=discord.Embed(title=f"Ping... {em}",color=discord.Color.random()))
        end = time.perf_counter()
        start2 = time.perf_counter()
        await self.bot.db.commit()
        end2 = time.perf_counter()
        duration = round(((end - start) * 1000),1)
        db_duration = round(((end2 - start2) * 1000),1)
        newembed = discord.Embed(title="Pong!",color=discord.Color.random())
        ws = round((self.bot.latency * 1000),1)
        newembed.add_field(name="Typing",value=f"{duration}ms")
        newembed.add_field(name="Websocket",value=f"{ws}ms")
        newembed.add_field(name="Database",value=f"{db_duration}ms")
        await message.edit(embed=newembed)

        
    # CREDIT TO RAPPTZ FOR THIS
    # https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/meta.py#L355-L393
    @commands.command(description="Gets the source on github for any command.")
    async def source(self, ctx, *, command: str = None):
        source_url = 'https://github.com/averwhy/EconomyX'
        branch = 'main'
        if command is None:
            return await ctx.send(source_url)
        
        if command == 'help':
            await ctx.send("<https://github.com/averwhy/EconomyX/blob/main/cogs/misc.py#L21-L81>")
            return
        if command == 'jsk' or command == 'jishaku':
            await ctx.send("Jishaku is a debug and testing command made for discord.py. The code can be found here:\n<https://github.com/Gorialis/jishaku>")
            return
        else:
            obj = self.bot.get_command(command.replace('.', ' '))
            if obj is None:
                return await ctx.send('Could not find command.')

            src = obj.callback.__code__
            module = obj.callback.__module__
            filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        if not module.startswith('discord'):
            # not a built-in command
            location = os.path.relpath(filename).replace('\\', '/')
        else:
            location = module.replace('.', '/') + '.py'

        final_url = f'<{source_url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>'
        await ctx.send(final_url)

    @commands.command(aliases=["pp","privacypolicy"])
    async def privacy_policy(self, ctx):
        """An interactive command to view EconomyX's Privacy Policy."""
        p = menus.MenuPages(source=botmenus.PPSource(self.pp), clear_reactions_after=True)
        await p.start(ctx)
    
    @commands.command()
    @commands.cooldown(1, 15, BucketType.user)
    async def news(self, ctx):
        channel = self.bot.get_channel(self.bot.updates_channel)
        if channel is None:
            channel = await self.bot.fetch_channel(self.bot.updates_channel)
        clr = await ctx.bot.get_player_color(ctx.author)
        if clr is None:
            if ctx.guild: clr = ctx.guild.me.color
            else: clr = discord.Color.dark_gray()
        latest_message, = [message async for message in channel.history(limit=1)]
        embed = discord.Embed(title="EconomyX News", description=f"{latest_message.content}\n\n[Jump to message]({latest_message.jump_url})  |  [Can't see message? Join support server](https://discord.gg/epQZEp933x)", color=clr)
        isdev = "(Developer) " if latest_message.author.id == OWNER_ID else ""
        embed.set_footer(text=f"Set by {isdev}{str(latest_message.author)}, {humanize.precisedelta(latest_message.created_at.replace(tzinfo=None))} ago", icon_url=latest_message.author.avatar.url)
        await ctx.send(embed=embed)

        
async def setup(bot):
    await bot.add_cog(misc(bot))
