import discord
import platform
import time
import asyncio
from datetime import datetime, timedelta
from discord.ext import commands, menus
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
import aiosqlite
from discord.ext import tasks

class crypto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    #WIP
        
def setup(bot):
    bot.add_cog(crypto(bot))