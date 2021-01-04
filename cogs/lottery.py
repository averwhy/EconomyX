import discord
import platform
import time
import random
import asyncio
import re, os
from datetime import datetime, timedelta
from discord.ext import commands, menus
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
import aiosqlite
import inspect

class lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @tasks.loop(seconds=60)
    async def lottery_task(self):
        await self.bot.wait_until_ready()
        c  = await self.bot.db.execute("select * from e_lottery_main")
        lotterystamp = (await c.fetchone())[1]
        piss = datetime.strptime(lotterystamp,"%Y-%m-%d %H:%M:%S.%f")
        cum = datetime.utcnow()
        diff = (piss - cum) / timedelta(seconds=1)
        await self.bot.db.commit()
        
        
    @commands.group()
    async def _lottery(self, ctx):
        c = await self.bot.db.execute("SELECT COUNT(*) FROM e_lottery_users")
    
    @lottery.command()
    async def buy(self, ctx):
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        if player[3] < 50:
            await ctx.send(f"You cant afford to buy a lottery ticket. You only have ${player[3]}.")
            return
        await ctx.send("ok")
        