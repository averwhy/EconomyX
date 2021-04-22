from discord.ext import commands

class crypto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    #WIP
        
def setup(bot):
    bot.add_cog(crypto(bot))