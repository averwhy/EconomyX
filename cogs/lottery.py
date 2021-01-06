import discord
import platform
import time
import asyncio
from datetime import datetime, timedelta
from discord.ext import commands, menus
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
import aiosqlite

class lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @tasks.loop(seconds=60)
    async def lottery_task(self):
        await self.bot.wait_until_ready()
        c  = await self.bot.db.execute("select * from e_lottery_main")
        lotterystamp = (await c.fetchone())[1]
        piss = datetime.strptime(lotterystamp,"%Y-%m-%d %H:%M:%S.%f")
        shit = datetime.utcnow()
        diff = (piss - shit) / timedelta(seconds=1)
        await self.bot.db.commit()
        if diff > 0:
            #That would be in the future, dont draw
            return
        if diff < -1800:
            print("draw")
            # -1800 seconds would be 30 mins (we want to draw every 30 mins)
            # So, lets draw, then reset
            c = await self.bot.db.execute("SELECT amountpooled FROM e_lottery_main")
            winningamount = (await c.fetchone())[0]
            c = await self.bot.db.execute("SELECT * FROM e_lottery_users ORDER BY RANDOM()")
            winningplayer = await c.fetchone()
            #enhanced-dpy time
            user = await self.bot.try_user(winningplayer[0])
            ts = self.bot.utc_calc(winningplayer[3])
            try:
                await user.send(f"Hey {str(user)}, **you won the lottery in EconomyX!**\nYou bought a ticket {ts[1]}h, {ts[2]}m, {ts[3]}s ago.\nYou won")
            except:
                #we cant dm them. Sad!
                # i guess we'll just pay them and up their stats. oh well
                c = await self.bot.db.execute("SELECT * FROM e_users WHERE id = ?",(winningplayer[0],))
                await c.fetchone()
                
                
        
    @commands.group()
    async def _lottery(self, ctx):
        await self.bot.db.execute("SELECT * FROM e_lottery_users")
        
    @lottery.command()
    async def buy(self, ctx):
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        if player[3] < 50:
            await ctx.send(f"You cant afford to buy a lottery ticket ($50). You only have ${player[3]}.")
            return
        
        c = await self.bot.db.execute("SELECT drawingwhen FROM e_lottery_main")
        drawingwhen = await c.fetchone()
        ts = self.bot.utc_calc(drawingwhen[0])
        await ctx.send(f"You bought a lottery ticket for $50. The next lottery drawing is in: ```autohotkey\n{ts[1]}h, {ts[2]}m, {ts[3]}s```")