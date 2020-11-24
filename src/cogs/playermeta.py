import discord
import platform
import time
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
OWNER_ID = 267410788996743168

class playermeta(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    @commands.cooldown(1,60,BucketType.user)
    @commands.command(aliases=["p"])
    async def profile(self,ctx,user: discord.User = None):
        if user is None:
            c = await self.bot.get_player(ctx.author.id)
            data = await c.fetchone()
            embedcolor = int(("0x"+data[7]),0)
            embed = discord.Embed(title=f"{str(ctx.author)}'s Profile",description=f"`ID: {ctx.author.id}",color=embedcolor)
            embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.add_field(name="Balance",value=f"${data[3]}")
            embed.add_field(name="Total earnings",value=f"${data[4]}")
            embed.set_footer(text=f"EconomyX v{self.bot.version}",icon_url=self.bot.user.avatar_url)
            await ctx.send(embed=embed)
    
    @commands.cooldown(1,60,BucketType.user)
    @commands.command(aliases=["start"])
    async def register(self,ctx):
        async with ctx.channel.typing():
            await asyncio.sleep(0.5)
            c = await self.bot.usercheck(ctx.author.id)
            data = await c.fetchone()
            if data is not None:
                await ctx.send(f"Youre already in the database, {ctx.author.mention}")
            msg = await self.bot.add_player(ctx.author)
            await ctx.send(msg)
        
        
        
        
def setup(bot):
    bot.add_cog(playermeta(bot))