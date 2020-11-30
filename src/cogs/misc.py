from typing import Mapping
import typing
import discord
import platform
import time
import random
import asyncio
import re, os
import datetime
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
import aiosqlite
import inspect
OWNER_ID = 267410788996743168


class HelpCommand(commands.HelpCommand):
    """Sup averwhy hopefully this is all easy to understand."""

    # This fires once someone does `<prefix>help`
    async def send_bot_help(self, mapping: Mapping[typing.Optional[commands.Cog], typing.List[commands.Command]]):
        ctx = self.context
        embed = discord.Embed(title="Bot Help")
        embed.set_footer(text=f"Do {self.clean_prefix}help [command] for more help")
        categories = []

        for cog, cmds in mapping.items():
            filtered = await self.filter_commands(cmds, sort=True)
            if filtered:
                all_commands = " ".join(f"`{c.name}`" for c in cmds)
                if cog and cog.description:
                    embed.add_field(name=cog.qualified_name,
                                    value=f"-> {all_commands}",
                                    inline=False)

        await ctx.send(embed=embed)

    # This fires once someone does `<prefix>help <cog>`
    async def send_cog_help(self, cog: commands.Cog):
        ctx = self.context
        embed = discord.Embed(title=f"Help for {cog.qualified_name}")
        embed.set_footer(text=f"Do {self.clean_prefix}help [command] for more help")

        entries = await self.filter_commands(cog.get_commands(), sort=True)
        for cmd in entries:
            embed.add_field(name=f"{self.clean_prefix}{cmd.name}",
                            value=f"{cmd.help}",
                            inline=False)

        await ctx.send(embed=embed)

    # This fires once someone does `<prefix>help <command>`
    async def send_command_help(self, command: commands.Command):
        ctx = self.context

        embed = discord.Embed(title=f"{self.clean_prefix}{command.qualified_name}",
                              description=f"{command.help}")
        embed.set_footer(text=f"Do {self.clean_prefix}help [command] for more help")

        await ctx.send(embed=embed)

    # This fires once someone does `<prefix>help <group>`
    async def send_group_help(self, group: commands.Group):
        ctx = self.context

        embed = discord.Embed(title=f"{self.clean_prefix}{group.qualified_name}",
                              description=group.help)
        embed.set_footer(text=f"Do {self.clean_prefix}help [command] for more help")

        for command in group.commands:
            embed.add_field(name=f"{self.clean_prefix}{command.name}",
                            value=command.description,
                            inline=False)

        await ctx.send(embed=embed)


class misc(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

        self.bot._original_help_command = bot.help_command

        bot.help_command = HelpCommand()
        bot.help_command.cog = self
    
    def cog_unload(self):
        self.bot.help_command = self.bot._original_help_command
    
    @commands.cooldown(1,10,BucketType.channel)
    @commands.command(aliases=["i"])
    async def info(self,ctx):
        data2 = await self.bot.get_player(ctx.author.id)
        if data2 is None:
            color = discord.Color.teal()
        else:
            color = int(("0x"+data2[5]),0)
        c = await self.bot.db.execute("SELECT SUM(bal) FROM e_users")
        money_total = await c.fetchone()
        c = await self.bot.db.execute("SELECT COUNT(id) FROM e_users")
        total_db_users = await c.fetchone()
        desc = f"""__**Developed by averwhy#3899**__
        **Guilds:** {len(self.bot.guilds)}
        **Total Users:** {len(self.bot.users)}
        **Current Money Total:** ${money_total[0]}
        **Number of users in database:** {total_db_users[0]}
        **Database changes in this session:** {self.bot.db.total_changes}
        """
        embed = discord.Embed(title="EconomyX Info",description=desc,color=color)
        embed.set_footer(text=f"Made with Python {platform.python_version()}, enchanced discord.py {discord.__version__}, and aiosqlite {aiosqlite.__version__}",icon_url="https://images-ext-1.discordapp.net/external/0KeQjRAKFJfVMXhBKPc4RBRNxlQSiieQtbSxuPuyfJg/http/i.imgur.com/5BFecvA.png")
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/460568954968997890/761037965987807232/dpycogs.png")
        await ctx.send(embed=embed)
    
    @commands.cooldown(1,5,BucketType.user)
    @commands.command()
    async def invite(self,ctx):
        data2 = await self.bot.get_player(ctx.author.id)
        if data2 is None:
            color = discord.Color.teal()
        else:
            color = int(("0x"+data2[5]),0)
        await ctx.send(embed=discord.Embed(title="EconomyX Bot Invite",description="",url="https://discord.com/api/oauth2/authorize?client_id=780480654277476352&permissions=264192&scope=bot",color=color))
    
    @commands.command()
    async def uptime(self, ctx):
        delta_uptime = datetime.utcnow() - bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        await ctx.send(f"{days}d, {hours}h, {minutes}m, {seconds}s")

        
    # CREDIT TO RAPPTZ FOR THIS
    # https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/meta.py#L355-L393
    @commands.command()
    async def source(self, ctx, *, command: str = None):
        source_url = 'https://github.com/averwhy/EconomyX'
        branch = 'main/src'
        if command is None:
            return await ctx.send(source_url)
        
        if command == 'help':
            await ctx.send("The help command is built into discord.py. However, the code for that can be found here:\n<https://github.com/Rapptz/discord.py/blob/master/discord/ext/commands/help.py>")
            return
        if command == 'jsk' or command == 'jishaku':
            await ctx.send("Jishaku is a debug and testing command made for discord.py. The code can be found here:\n<https://github.com/Gorialis/jishaku>")
            return
        else:
            obj = self.bot.get_command(command.replace('.', ' '))
            if obj is None:
                return await ctx.send('Could not find command.')

            # since we found the command we're looking for, presumably anyway, let's
            # try to access the code itself
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

        

        
def setup(bot):
    bot.add_cog(misc(bot))