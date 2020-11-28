import discord
import platform
import time
import random
import asyncio
import re
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
import aiosqlite
OWNER_ID = 267410788996743168

class misc(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
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
        
def setup(bot):
    bot.add_cog(misc(bot))