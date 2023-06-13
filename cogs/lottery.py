import discord
from datetime import datetime, timedelta, timezone
from discord.ext import commands
from discord.ext import tasks
from .utils import player as Player
from .utils.errors import NotAPlayerError

class lottery(commands.Cog):
    """The lottery. Users buy tickets and every 12 hours it is drawn. Use the `lottery` command to see when the next drawing is."""
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        await self.bot.db.execute("CREATE TABLE IF NOT EXISTS e_lottery_users (userid int, username text, boughtwhen blob)")
        await self.bot.db.execute("CREATE TABLE IF NOT EXISTS e_lottery_main (drawingwhen blob, drawingnum int)")
        self.lottery_task.start()

    async def cog_unload(self):
        self.lottery_task.cancel()
    
    async def reset_lottery_time(self):
        newdrawingtime = discord.utils.utcnow() + timedelta(hours=12)
        await self.bot.db.execute("UPDATE e_lottery_main SET drawingwhen = ?",(newdrawingtime,))
        await self.bot.db.commit()
    
    @tasks.loop(seconds=120)
    async def lottery_task(self):
        await self.draw()
    
    async def draw(self, force: bool = False):
        """Draws lottery"""
        await self.bot.wait_until_ready()
        c = await self.bot.db.execute("select * from e_lottery_main")
        data = await c.fetchone()
        if data is None:
            #no lottery data :(
            date = discord.utils.utcnow() + timedelta(hours=12)
            await self.bot.db.execute("INSERT INTO e_lottery_main VALUES (?, 0)",(date,))
            await self.bot.db.commit()
            return
        lotterystamp = data[0]
        piss = datetime.strptime(lotterystamp.strip('+00:00'),"%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
        shit = discord.utils.utcnow()
        diff = (piss - shit) / timedelta(seconds=1)
        if diff < 0 or force:
            print("draw")
            # 0 bigger than the diff would be 12 hours (we want to draw every 12 hours)
            # So, lets draw, then reset
            cur = await self.bot.db.execute("SELECT COUNT(*) FROM e_lottery_users")
            data2 = await cur.fetchone()
            if int(data2[0]) <= 0:
                print("no users, drawing again in 12 hours")
                await self.reset_lottery_time()
                return
            winningamount = (data2[0] * 100)
            c = await self.bot.db.execute("SELECT * FROM e_lottery_users ORDER BY RANDOM()")
            winningplayer = await c.fetchone()
            user = await self.bot.fetch_user(winningplayer[0])
            ts = self.bot.utc_calc(winningplayer[2])
            try:
                await user.send(f"Hey {user.mention}, **You won the lottery in EconomyX!**\nYou bought a ticket {ts} ago.\nYou won ${winningamount}")
            except discord.Forbidden:
                #we cant dm them. Sad!
                # i guess we'll just pay them and up their stats. oh well
                pass
            await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(winningamount,winningplayer[0],))
            await self.bot.db.execute("UPDATE e_users SET lotterieswon = (lotterieswon + 1) WHERE id = ?",(winningplayer[0],))
            await self.bot.db.execute("DELETE FROM e_lottery_users")
            await self.bot.db.execute("UPDATE e_lottery_main SET drawingnum = (drawingnum + 1)")
            await self.bot.stats.add('totalLotteries')
            await self.reset_lottery_time() # it commits in here
        elif diff > 0:
            #Too soon, dont draw
            return
        
    @commands.group(name="lottery",aliases=["lot"], invoke_without_command=True)
    async def _lottery(self, ctx):
        """Base lottery command. Views active lottery stats."""
        c = await self.bot.db.execute("SELECT COUNT(*) FROM e_lottery_users")
        usercount = (await c.fetchone())[0]
        try: 
            pcolor = (await Player.get(ctx.author.id, self.bot)).profile_color
        except NotAPlayerError:
            color = 0x2F3136
        c = await self.bot.db.execute("SELECT * FROM e_lottery_main")
        lotinfo = await c.fetchone()
        embed = discord.Embed(title=f"Lottery #{lotinfo[1]}",color=pcolor)
        embed.add_field(name="Potential winnings",value=f"${(usercount * 100)}")
        embed.add_field(name="Bought tickets", value=usercount)
        ts = self.bot.lottery_countdown_calc(lotinfo[0])
        embed.add_field(name="Next drawing",value=f"`{ts[1]}h, {ts[2]}m, {ts[3]}s`")
        
        await ctx.send(embed=embed)
        
    @_lottery.command(aliases=["purchase"])
    async def buy(self, ctx):
        """Buys a lottery command for 100 dollars. Note that you cannot sell or refund them."""
        player = await Player.get(ctx.author.id, self.bot)
        if player.balance < 100:
            await ctx.send(f"You cant afford to buy a lottery ticket ($100). You only have ${player.balance}.")
            return
        c = await self.bot.db.execute("SELECT * FROM e_lottery_users WHERE userid = ?",(ctx.author.id,))
        lcheck = await c.fetchone()
        if lcheck is not None:
            return await ctx.send("You've already bought a lottery ticket. Use `e$lottery` to view when it will be drawn.")
        
        c = await self.bot.db.execute("SELECT * FROM e_lottery_main")
        drawingwhen = await c.fetchone()
        ts = self.bot.lottery_countdown_calc(drawingwhen[0])
        await self.bot.db.execute("INSERT INTO e_lottery_users VALUES (?, ?, ?)",(ctx.author.id, ctx.author.name, discord.utils.utcnow(),))
        await player.update_balance(-100, ctx=ctx)
        await self.bot.stats.add('totalLotteries')
        await ctx.send(f"You bought a lottery ticket for $100. The next lottery drawing is in `{ts[1]}h, {ts[2]}m, {ts[3]}s`. I will DM you if you are picked.")
        
        
async def setup(bot):
    await bot.add_cog(lottery(bot))