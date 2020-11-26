import discord
import platform
import time
import random
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
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
        embed = discord.Embed(title="EconomyX Info",description="oh oops, remind me to finish this lol",color=color)
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