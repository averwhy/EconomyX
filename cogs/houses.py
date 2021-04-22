import discord
from discord.ext import commands

class houses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
def setup(bot):
    bot.add_cog(houses(bot))