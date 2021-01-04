import discord
import platform
import time
import random
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
OWNER_ID = 267410788996743168

class money_meta(commands.Cog):
    """
    These commands are meta about money, such as pay or balance.
    """
    def __init__(self,bot):
        self.bot = bot
    
    @commands.cooldown(1,30,BucketType.user)
    @commands.command(aliases=["payuser"])
    async def pay(self,ctx, user: discord.User, amount):
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        amount = float(amount)
        if player[3] < amount:
            await ctx.send(f"You cant pay them that much. You only have ${player[3]}.")
            return
        player_getting_paid = await self.bot.get_player(user.id)
        if player_getting_paid is None:
            await ctx.send("That person doesn't seem to have a profile.")
            return
        try:
            await self.bot.transfer_money(ctx.author,user,amount)
            await bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(amount,user.id,))
            await ctx.reply("Transfer successful.")
        except Exception as e:
            await ctx.send(f"Something went wrong.\n{e}")
            
    @commands.cooldown(1,3,BucketType.user)
    @commands.command(aliases=["balance"])
    async def bal(self,ctx, user: discord.User = None):
        if user is None:
            data = await self.bot.get_player(ctx.author.id)
            if data is None:
                await ctx.send("You dont have a profile. Try `e$register`")
                return
            await ctx.send(f"{str(ctx.author)}'s balance: ${data[3]}")
        if user is not None:
            data = await self.bot.get_player(user.id)
            if data is None:
                await ctx.send("They dont seem to have a profile.")
                return
            await ctx.send(f"{str(user)}'s balance: ${data[3]}")
            
    @commands.cooldown(1,10,BucketType.user)
    @commands.command()
    async def rob(self,ctx):
        await ctx.send("You can't rob. It's aganist the law.")
        
        
        
        
def setup(bot):
    bot.add_cog(money_meta(bot))