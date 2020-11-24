import discord
import platform
import time
import random
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
OWNER_ID = 267410788996743168

class game(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    @commands.cooldown(1,5,BucketType.user)
    @commands.command(aliases=["b"])
    async def bet(self,ctx,amount: float = None):
        y = random.choice([True,False])
        if y:
            data = await bot.on_bet_win(ctx.author) # returns list
            if data is not None:
                await ctx.send(f"Won ${data[0]}\nNew balance: {data[1]}")
            else:
                await ctx.send("Youre not in the database! Try `^register`")
        if not y:
            data = await bot.on_bet_loss(ctx.author) # returns new balance
            if data is not None:
                await ctx.send(f"Lost ${amount}\nNew balance: {data}")
            else:
                await ctx.send("Youre not in the database! Try `^register`")
        
        
        
        
def setup(bot):
    bot.add_cog(game(bot))