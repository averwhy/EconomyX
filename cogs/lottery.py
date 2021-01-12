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

class lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lottery_task.start()
        
    @tasks.loop(seconds=30)
    async def lottery_task(self):
        await self.bot.wait_until_ready()
        c = await self.bot.db.execute("select * from e_lottery_main")
        lotterystamp = (await c.fetchone())[0]
        piss = datetime.strptime(lotterystamp,"%Y-%m-%d %H:%M:%S.%f")
        shit = datetime.utcnow()
        diff = (piss - shit) / timedelta(seconds=1)
        await self.bot.db.commit()
        print(diff)
        if diff > 0:
            #That would be in the future, dont draw
            return
        if diff < -1800:
            print("draw")
            # -1800 seconds would be 30 mins (we want to draw every 30 mins)
            # So, lets draw, then reset
            cur = await self.bot.db.execute("SELECT COUNT(*) FROM e_lottery_users")
            winningamount = ((await cur.fetchone())[0] * 100)
            c = await self.bot.db.execute("SELECT * FROM e_lottery_users ORDER BY RANDOM()")
            winningplayer = await c.fetchone()
            #enhanced-dpy time
            user = await self.bot.fetch_user(winningplayer[0])
            ts = self.bot.utc_calc(winningplayer[2])
            try:
                await user.send(f"Hey {user.mention}, **You won the lottery in EconomyX!**\nYou bought a ticket {ts[1]}h, {ts[2]}m, {ts[3]}s ago.\nYou won ${winningamount}")
            except:
                #we cant dm them. Sad!
                # i guess we'll just pay them and up their stats. oh well
                pass
            await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(winningamount,winningplayer[0],))
            await self.bot.db.execute("DELETE FROM e_lottery_users")
            newdrawingtime = datetime.utcnow() + timedelta(minutes=30)
            await self.bot.db.execute("UPDATE e_lottery_main SET drawingwhen = ?",(newdrawingtime,))
            await self.bot.db.execute("UPDATE e_lottery_main SET drawingnum = (drawingnum + 1)")
            await self.bot.db.commit()
        
    @commands.group(name="lottery",aliases=["lot"], invoke_without_command=True)
    async def _lottery(self, ctx):
        """Base lottery command. Views active lottery stats."""
        c = await self.bot.db.execute("SELECT COUNT(*) FROM e_lottery_users")
        usercount = (await c.fetchone())[0]
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        pcolor = await self.bot.get_player_color(ctx.author)
        c = await self.bot.db.execute("SELECT * FROM e_lottery_main")
        lotinfo = await c.fetchone()
        embed = discord.Embed(title=f"Lottery #{lotinfo[1]}",color=pcolor)
        embed.add_field(name="Potential winnings",value=f"${(usercount * 100)}")
        embed.add_field(name="Bought tickets", value=usercount)
        ts = self.bot.lottery_countdown_calc(lotinfo[0])
        embed.add_field(name="Next drawing",value=f"`{ts[1]}h, {ts[2]}m, {ts[3]}s`")
        
        await ctx.send(embed=embed)
        
    @_lottery.command()
    async def buy(self, ctx):
        """Buys a lottery command for 100 dollars. Note that you cannot sell or refund them."""
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        if player[3] < 100:
            await ctx.send(f"You cant afford to buy a lottery ticket ($100). You only have ${player[3]}.")
            return
        c = await self.bot.db.execute("SELECT * FROM e_lottery_users WHERE userid = ?",(ctx.author.id,))
        lcheck = await c.fetchone()
        if lcheck is not None:
            return await ctx.send("You've already bought a lottery ticket. Use `e$lottery` to view when it will be drawn.")
        
        c = await self.bot.db.execute("SELECT * FROM e_lottery_main")
        drawingwhen = await c.fetchone()
        ts = self.bot.lottery_countdown_calc(drawingwhen[0])
        await self.bot.db.execute("INSERT INTO e_lottery_users VALUES (?, ?, ?)",(ctx.author.id, ctx.author.name, datetime.utcnow(),))
        await self.bot.db.execute("UPDATE e_users SET bal = (bal - 100) WHERE id = ?",(ctx.author.id,))
        await ctx.send(f"You bought a lottery ticket for $100. The next lottery drawing is in `{ts[1]}h, {ts[2]}m, {ts[3]}s`. I will DM you if you are picked.")
        
        
def setup(bot):
    bot.add_cog(lottery(bot))