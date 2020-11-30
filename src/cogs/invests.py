import discord
import platform
import time
import random
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
from discord.ext import tasks
from datetime import datetime
OWNER_ID = 267410788996743168

class invests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.main_invest_loop.start()
     
     
    @tasks.loop(seconds=300)
    async def main_invest_loop(self):
        await self.bot.wait_until_ready()
        c = await self.bot.db.execute("SELECT stockid, points FROM e_invests")
        all_invests = await c.fetchall()
        for i in all_invests:
            continue
        print(f"{len(all_invests)} invests updated")
     
        
def setup(bot):
    bot.add_cog(invests(bot))