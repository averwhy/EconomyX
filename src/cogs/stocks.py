import discord
import platform
import time
import random
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
from discord.ext import tasks
from better_profanity import profanity
OWNER_ID = 267410788996743168

class stocks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.main_stock_loop.start()
        
    @tasks.loop(seconds=300)
    async def main_stock_loop(self):
        c = await self.bot.db.execute("SELECT stockid, points FROM e_stocks")
        all_stocks = await c.fetchall()
        for s in all_stocks:
            bruh = random.choice([True, False]) # true = add, false = subtract
            if bruh:
                amount = random.uniform(0.1,2)
                amount = round(amount,2)
                await self.bot.db.execute("UPDATE e_stocks points = (bal + ?) WHERE stockid = ?",(amount, s[0]))
            if not bruh:
                amount = random.uniform(0.1,2)
                amount = round(amount,2)
                await self.bot.db.execute("UPDATE e_stocks points = (bal - ?) WHERE stockid = ?",(amount, s[0]))
        print(f"{len(all_stocks)} stocks updated")
    
    @commands.group(aliases=["stocks","st"], invoke_without_command=True)
    async def stock(self, ctx):
        pass
    
    @stock.command()
    async def view(self, ctx, user: discord.User = None):
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `^register`.")
            return
        if user is None:
            user = ctx.author
        embedcolor = int(("0x"+player[5]),0)
        embed = discord.Embed(title=f"{str(user)}'s stock portfolio",description=f"`ID: {user.id}`",color=embedcolor)
        playerstock = await self.bot.get_stock(ctx.author.id)
        if playerstock is None:
            embed.add_field(name="Owned stock",value="None")
        else:
            embed.add_field(name="Owned Stock",value=playerstock[1])
        await ctx.send(embed=embed)
    
    @stock.command(aliases=["c"])
    async def create(self, ctx, name: str):
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `^register`.")
            return
        if player[3] < 1000:
            await ctx.send(f"Sorry. You have to have at least $1000 to create a stock.\nYour balance: ${player[3]}")
            return
        playerstock = await self.bot.get_stock(ctx.author.id)
        if playerstock is not None:
            await ctx.send("You already have a stock. If you want to rename it, use `^stock rename <name>`")
        
        stockid = random.randint(0000,9999)
        clean_name = profanity.censor(name)
        msg = await ctx.send(f"Stock name: {clean_name}\nID: {stockid}\nStarting points: 10\n**Are you sure you want to create this stock for $1000?**")
        await msg.add_reaction("\U00002705")
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=check)
        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
            except:
                pass
            await msg.edit(content="Timed out after 30 seconds.")
        else:
            try:
                await ctx.reply('👍')
            except:
                await ctx.send('👍')
            await self.bot.db.execute("INSERT INTO e_stocks VALUES (?, ?, 10.0, 10.0, ?)",(stockid, clean_name, ctx.author.id,))
            
    @stock.command(aliases=["r"])
    async def rename(self, ctx, name: str):
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `^register`.")
            return
        playerstock = await self.bot.get_stock(ctx.author.id)
        if playerstock is None:
            await ctx.send("You don't have a stock. If you want make one, use `^stock create <name>`")
        
        clean_name = profanity.censor(name)
        msg = await ctx.send(f"Stock name: {clean_name}\nStarting points: 10\n**Are you sure you want to create this stock for $1000?**")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=check)
        except asyncio.TimeoutError:
            pass
        else:
            try:
                await ctx.reply('👍')
            except:
                await ctx.send('👍')
            await self.bot.db.execute("UPDATE e_stocks SET ",(clean_name, ctx.author.id,))
        
def setup(bot):
    bot.add_cog(stocks(bot))