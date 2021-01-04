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

class stocks(commands.Cog):
    """
    Stock commands (except investments).
    """
    def __init__(self, bot):
        self.bot = bot
        self.main_stock_loop.start()
        
    @tasks.loop(seconds=299)
    async def main_stock_loop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(1)
        c = await self.bot.db.execute("SELECT stockid, points FROM e_stocks")
        all_stocks = await c.fetchall()
        for s in all_stocks:
            bruh = random.choice([True, False]) # true = add, false = subtract
            if bruh:
                amount = random.uniform(0.1,2)
                amount = round(amount,1)
                await self.bot.db.execute("UPDATE e_stocks SET points = (points + ?) WHERE stockid = ?",(amount, s[0]))
            if not bruh:
                amount = random.uniform(0.1,2)
                amount = round(amount,1)
                if (s[2] - amount) < 0:
                    amount = 0 # we dont want it to go negative
                else:
                    await self.bot.db.execute("UPDATE e_stocks SET points = (points + ?) WHERE stockid = ?",(amount, s[0]))
                await self.bot.db.execute("UPDATE e_stocks SET points = (points - ?) WHERE stockid = ?",(amount, s[0]))
        print(f"{len(all_stocks)} stocks updated")
    
    @commands.command(aliases=["port","pf"])
    async def portfolio(self, ctx, user: discord.User = None):
        """Views a players stock portfolio."""
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        if user is None:
            user = ctx.author
        embedcolor = int(("0x"+player[5]),0)
        embed = discord.Embed(title=f"{str(user)}'s stock portfolio",description=f"`ID: {user.id}`",color=embedcolor)
        playerstock = await self.bot.get_stock(ctx.author.id)
        if playerstock is None:
            embed.add_field(name="Owned stock",value="None")
        else:
            embed.add_field(name="Owned Stock",value=f"{playerstock[1]} [`{playerstock[0]}`]")
            tl = self.bot.utc_calc(playerstock[5])
            embed.add_field(name="Stock Created",value=f"{tl[0]}d, {tl[1]}h, {tl[2]}m, {tl[3]}s ago")
            embed.add_field(name="Stock Points",value=f"{round(playerstock[2],1)}")
        c = await self.bot.db.execute("SELECT * FROM e_invests WHERE userid = ?",(user.id,))
        playerinvests = await c.fetchall()
        if playerinvests is None:
            embed.add_field(name="Invested Stocks",value="None")
        else:
            t = ""
            for i in playerinvests:
                tl = self.bot.utc_calc(i[5])
                t = t + (f"{i[3]} [`{i[0]}]: invested ${i[2]} at {round(i[4],1)} points `{tl[0]}d, {tl[1]}h, {tl[2]}m, {tl[3]}s ago")
            if t == "":
                t = "None!"
            embed.add_field(name="Invests",value=t,inline=False)
        await ctx.send(embed=embed)
        
    @commands.group(aliases=["stocks","st"], invoke_without_command=True)
    async def stock(self, ctx):
        """Stocks management commands. Invoking without a command shows list of top stocks."""
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        embedcolor = int(("0x"+player[5]),0)
        cur = await self.bot.db.execute("SELECT * FROM e_stocks ORDER BY points DESC;")
        allstocks = await cur.fetchall()
        cur = await self.bot.db.execute("SELECT SUM(invested) FROM e_invests")
        total_invested = await cur.fetchone()
        cur = await self.bot.db.execute("SELECT SUM(points) FROM e_stocks")
        total_points = await cur.fetchone()
        embed = discord.Embed(title="All Stocks",description=f"Total amount invested: ${total_invested[0]}, Total stock points: {total_points[0]}")
        counter = 0
        for i in allstocks:
            if counter > 10:
                break
            cur = await self.bot.db.execute("SELECT COUNT(*) FROM e_invests WHERE stockid = ?",(i[0],))
            investor_count = await cur.fetchone()
            tl = self.bot.utc_calc(i[5])
            embed.add_field(name=i[1],value=f"ID: {i[0]}, Points: {round(i[2],1)}, {investor_count[0]} Investors, Created {tl[0]}d, {tl[1]}h, {tl[2]}m, {tl[3]}s ago")
            counter += 1
        await ctx.send(embed=embed)
    
    @stock.command()
    async def view(self, ctx, user: discord.User = None):
        await stocks.portfolio(self, ctx, user)
    
    @stock.command(aliases=["c"], description="Creates a new stock.")
    async def create(self, ctx, name: str):
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            return await ctx.send("You dont have a profile! Get one with `e$register`.")
        if player[3] < 1000:
            return await ctx.send(f"Sorry. You have to have at least $1000 to create a stock.\nYour balance: ${player[3]}")
        playerstock = await self.bot.get_stock(ctx.author.id)
        if playerstock is not None:
            return await ctx.send("You already have a stock. If you want to rename it, use `e$stock rename <name>`")
        if len(name) > 5:
            return await ctx.send("The stock name must be less than or equal to 5 characters.")
        if not name.isalnum():
            return await ctx.send("Stock names must be alphanumeric.")
        name = name.upper()
        
        stockid = random.randint(0000,9999)
        msg = await ctx.send(f"Stock name: {name}\nID: {stockid}\nStarting points: 10\n**Are you sure you want to create this stock for $1000?**")
        await msg.add_reaction("\U00002705")
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=check)
        except asyncio.TimeoutError:
            for i in msg.reactions:
                try: await i.remove()
                except: pass
            await msg.edit(content="Timed out after 30 seconds.")
        else:
            try:
                await ctx.reply('👍')
            except:
                await ctx.send('👍')
            stock_created_at = datetime.utcnow()
            await self.bot.db.execute("UPDATE e_users SET bal = (bal - 1000) WHERE id = ?",(ctx.author.id,))
            await self.bot.db.execute("INSERT INTO e_stocks VALUES (?, ?, 10.0, 10.0, ?, ?)",(stockid, name, ctx.author.id, stock_created_at,))
    
    @stock.command(description="Deletes an owned stock. Please consider renaming first, before deleting. You do not get refunded the money you paid to create the stock.")
    async def delete(self, ctx):
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            return await ctx.send("You dont have a profile! Get one with `e$register`.")
        playerstock = await self.bot.get_stock(ctx.author.id)
        if playerstock is None:
            return await ctx.send("You don't have a stock. If you want make one, use `e$stock create <name>`")
        
        cur = await self.bot.db.execute("SELECT COUNT(*) FROM e_invests WHERE stockid = ?",(playerstock[0],))
        investor_count = await cur.fetchone()
        cur = await self.bot.db.execute("SELECT SUM(invested) FROM e_invests WHERE stockid = ?",(playerstock[0],))
        sum_invested = await cur.fetchone()
        tl = self.bot.utc_calc(playerstock[5])
        msg = await ctx.send(f"**Are you sure you want to delete your stock?**\nStock name: {playerstock[1]}, Stock ID: {playerstock[0]}, Current points: {playerstock[2]}\nInvestors: {investor_count[0]}, Total amount invested: ${sum_invested[0]}\nCreated {tl[0]}d, {tl[1]}h, {tl[2]}m, {tl[3]}s ago\n__Investments will not be deleted. Investors will be refunded the amount they invested. You will not be refunded.__")
        await msg.add_reaction("✅")
        def check(reaction, user): 
            return reaction.emoji == '✅' and user == ctx.author
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await msg.edit(content="Timeout. Your stock wasn't deleted.")
        else:
            await self.bot.db.execute("DELETE FROM e_stocks WHERE ownerid = ?",(ctx.author.id,))
            try: await ctx.reply('👍')
            except: await ctx.send('👍')
        for i in msg.reactions:
            try: await i.remove()
            except Exception as e: print(e)
        
    @stock.command(aliases=["r"], description="Renames an owned stock, costs $100.")
    async def rename(self, ctx, name: str):
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        playerstock = await self.bot.get_stock(ctx.author.id)
        if playerstock is None:
            return await ctx.send("You don't have a stock. If you want make one, use `e$stock create <name>`")
        if not name.isalnum():
            return await ctx.send("New name must be alphanumeric. (A-Z, 0-9)")
        
        msg = await ctx.send(f"Old stock name: {playerstock[1]}\nNew Stock name: {name}\n**Are you sure you want to rename this stock for $100?**")
        
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
            await self.bot.db.execute("UPDATE e_stocks SET ",(name, ctx.author.id,))
            
    @commands.group(invoke_without_command=True)
    async def invest(self, ctx, name_or_id, amount):
        """The base command for investments.
        Invoking `invest` without a subcommand allows you to invest in stocks."""
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        if amount.lower() == "all":
            amount = player[3]
        amount = float(amount)
        if amount != amount:
            await ctx.send("Thats not a valid amount. Nice try, though")
            return
        if player[3] < amount:
            await ctx.send(f"That investment is too big. You only have ${player[3]}.")
            return
        cur = await self.bot.db.execute("SELECT * FROM e_stocks WHERE name = ?",(name_or_id,))
        stock = await cur.fetchone()
        if stock is None:
            cur = await self.bot.db.execute("SELECT * FROM e_stocks WHERE stockid = ?",(name_or_id,))
            stock = await cur.fetchone()
            if stock is None:
                await ctx.send("I couldn't find that stock. Double check the name/ID.")
                return
            
        cur = await self.bot.db.execute("SELECT * FROM e_invests WHERE stockid = ? AND userid = ?",(stock[0],ctx.author.id,))
        investment = await cur.fetchone()
        if investment is not None:
            await ctx.send("You're already invested in this stock.")
            return
        #(stockid int, userid int, invested double, stockname text, invested_at double, invested_date blob)
        rn = datetime.utcnow()
        await self.bot.db.execute("INSERT INTO e_invests VALUES (?, ?, ?, ?, ?, ?)",(stock[0], ctx.author.id, amount, stock[1], stock[2],rn,))
        await ctx.send(f"Invested ${amount} in **{stock[1]}** at {stock[2]} points!")
        
    @invest.command(invoke_without_command=True, description="Sells an investment.\nThe money you earn back is calculated like this: `money_to_pay = ((current_stock_points - points_at_investment) / 10) * amount_invested`")
    async def sell(self, ctx, name_or_id):
        name_or_id = name_or_id.upper()
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        cur = await self.bot.db.execute("SELECT * FROM e_invests WHERE stockname = ? AND userid = ?",(name_or_id,ctx.author.id,))
        investment = await cur.fetchone()
        if investment is None:
            cur = await self.bot.db.execute("SELECT * FROM e_invests WHERE stockid = ? AND userid = ?",(name_or_id,ctx.author.id,))
            investment = await cur.fetchone()
            if investment is None:
                await ctx.send("I couldn't find that stock, or you're not invested in it. Double check the name or ID.")
                return
            
        c = await self.bot.db.execute("SELECT * FROM e_stocks WHERE stockid = ?",(investment[0],))
        stock = await c.fetchone()
        if stock is None:
            await ctx.send(f"This stock no longer exists. You will be refunded ${investment[2]} (the money you invested).")
            await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(investment[2],))
            await self.bot.db.execute("DELETE FROM e_invests WHERE stockname = ? AND userid = ?",(name_or_id, ctx.author.id,))
            await self.bot.db.execute("DELETE FROM e_invests WHERE stockid = ? AND userid = ?",(name_or_id, ctx.author.id,))
            return
        points_at_investment = investment[4]
        current_stock_points = stock[2]
        amount_invested = investment[2]
        money_to_pay = (current_stock_points - points_at_investment) * amount_invested
        if money_to_pay > 0:
            msg = await ctx.send(f"${round(money_to_pay,2)} will be depositied into your account.\nYou invested ${round(amount_invested,2)}.\nThis is a net **profit** of ${round((money_to_pay - amount_invested),2)}\n**Are you sure you want to sell your investment?**")
            await msg.add_reaction("✅")
            def check(reaction, user): 
                return reaction.emoji == '✅' and user == ctx.author
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await msg.edit(content="Timeout. Your investment was not sold.")
            else:
                await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(round(money_to_pay,2), ctx.author.id,))
                await self.bot.db.execute("DELETE FROM e_invests WHERE userid = ? AND stockid = ?",(ctx.author.id, name_or_id,))
                await self.bot.db.execute("DELETE FROM e_invests WHERE userid = ? AND stockname = ?",(ctx.author.id, name_or_id,))
                await self.bot.db.commit()
                try: await ctx.reply('👍')
                except: await ctx.send('👍')
        elif money_to_pay < 0:
            msg = await ctx.send(f"${round(money_to_pay,2)} will be taken from your account.\nYou invested ${round(amount_invested,2)}.\nThis is a net **loss** of ${round((money_to_pay - amount_invested),2)}\n**Are you sure you want to sell your investment?**")
            await msg.add_reaction("✅")
            def check(reaction, user): 
                return reaction.emoji == '✅' and user == ctx.author
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await msg.edit(content="Timeout. Your investment was not sold.")
            else:
                await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(round(money_to_pay,2), ctx.author.id,))
                await bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(round(money_to_pay,2),ctx.author.id,))
                await self.bot.db.execute("DELETE FROM e_invests WHERE userid = ? AND stockid = ?",(ctx.author.id, name_or_id,))
                await self.bot.db.execute("DELETE FROM e_invests WHERE userid = ? AND stockname = ?",(ctx.author.id, name_or_id,))
                try: await ctx.reply('👍')
                except: await ctx.send('👍')
        try: 
            for r in msg.reactions: await r.remove()
        except: pass
        
def setup(bot):
    bot.add_cog(stocks(bot))