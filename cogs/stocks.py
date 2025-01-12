import discord
import re
import random
import asyncio
import logging
from utils.errors import NotAPlayerError
from discord.ext import commands
from discord.ext import tasks
from .utils.botviews import Confirm
from .utils import player as Player

OWNER_ID = 267410788996743168
log = logging.getLogger(__name__)


class stocks(commands.Cog, command_attrs=dict(name="Stocks")):
    """
    Stock commands (except investments).
    """

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.main_stock_loop.start()

    async def cog_unload(self):
        self.main_stock_loop.cancel()

    @tasks.loop(seconds=630)
    async def main_stock_loop(self):
        await self.bot.wait_until_ready()
        all_stocks = await self.bot.pool.fetch("SELECT * FROM e_stocks")
        for s in all_stocks:
            s = tuple(s)
            previous_amount = s[2]
            bruh = random.choice([True, False])  # true = add, false = subtract
            amount = random.uniform(0.09, 0.65)
            amount = round(amount, 2)
            if bruh:
                await self.bot.pool.execute(
                    "UPDATE e_stocks SET points = (points + $1) WHERE stockid = $2",
                    amount,
                    s[0],
                )
                if (s[2] + amount) >= 200:
                    ach = self.bot.get_cog("achievements")
                    if await ach.has_ach(s[4], 13):
                        player = await self.bot.fetch_user(s[4])
                        await ach.give_ach(player, 13)
            if not bruh:
                cv = s[2]  # current value
                if (cv - amount) < 0.00:
                    amount = 0.00  # we dont want it to go negative
                    ach = self.bot.get_cog("achievements")
                    if await ach.has_ach(s[4], 14):
                        player = await self.bot.fetch_user(s[4])
                        await ach.give_ach(player, 14)
                else:
                    await self.bot.pool.execute(
                        "UPDATE e_stocks SET points = (points - $1) WHERE stockid = $2",
                        amount,
                        s[0],
                    )
            # then update previous amount for e$stock view
            await self.bot.pool.execute(
                "UPDATE e_stocks SET previouspoints = $1 WHERE stockid = $2",
                previous_amount,
                s[0],
            )
        log.info(f"{len(all_stocks)} stocks updated")

    @commands.command(aliases=["port", "pf"])
    async def portfolio(self, ctx, user: discord.User = None):
        """Views a players stock portfolio. Includes all investments, and owned stocks."""
        player = await Player.get(ctx.author.id, self.bot)
        if player is None:
            await ctx.send(f"You dont have a profile! Get one with `{ctx.clean_prefix}register`.")
            return
        if user is None:
            user = ctx.author
        embed = discord.Embed(
            title=f"{str(user)}'s stock portfolio",
            description=f"`ID: {user.id}`",
            color=player.profile_color,
        )
        playerstock = await self.bot.get_stock_from_player(ctx.author.id)
        if playerstock is None:
            embed.add_field(name="Owned stock", value="None")
        else:
            embed.add_field(
                name="Owned Stock", value=f"{playerstock[1]} [`{playerstock[0]}`]"
            )
            tl = self.bot.utc_calc(playerstock[5], style="R")
            embed.add_field(name="Stock Created", value=tl)
            embed.add_field(name="Stock Points", value=f"{round(playerstock[2],1)}")
        playerinvests = await self.bot.pool.fetch(
            "SELECT * FROM e_invests WHERE userid = $1", user.id
        )
        if len(playerinvests) == 0:
            embed.add_field(name="Invested Stocks", value="None")
        else:
            t = ""
            for i in playerinvests:
                tl = self.bot.utc_calc(i[5], style="R")
                t = t + (
                    f"{i[3]} [`{i[0]}`]: invested ${i[2]} @ {round(i[4],1)} points, {tl}\n"
                )
            if t == "":
                t = "None!"
            embed.add_field(name="Invests", value=t, inline=False)
        await ctx.send(embed=embed)

    @commands.group(aliases=["stocks", "st"], invoke_without_command=True)
    async def stock(self, ctx):
        """Stocks management commands. Invoking without a command shows list of top stocks."""
        player = await Player.get(ctx.author.id, self.bot)
        allstocks = await self.bot.pool.fetch(
            "SELECT * FROM e_stocks ORDER BY points DESC;"
        )
        try:
            cur = await self.bot.pool.fetchrow("SELECT SUM(invested) FROM e_invests")
            total_invested = f"${((tuple(cur))[0])}"
        except Exception:  # TODO: find out what integer overflow error is
            total_invested = (
                "\n**More than 9.23 quintillion ($9,223,372,036,854,775,807) dollars**"
            )

        total_points = await self.bot.pool.fetchrow("SELECT SUM(points) FROM e_stocks")
        embed = discord.Embed(
            title="All Stocks",
            description=f"Total amount invested: {total_invested},\nTotal stock points: {round(tuple(total_points)[0], 2)}",
            color=player.profile_color,
        )
        counter = 0
        for i in allstocks:
            i = tuple(i)
            if counter > 10:
                break
            investor_count = await self.bot.pool.fetchrow(
                "SELECT COUNT(*) FROM e_invests WHERE stockid = $1", i[0]
            )
            tl = self.bot.utc_calc(i[5], style="R")
            embed.add_field(
                name=i[1],
                value=f"ID: {i[0]}, Points: {round(i[2],1)}, {tuple(investor_count)[0]} Investors, Created {tl}",
            )
            counter += 1
        await ctx.send(embed=embed)

    @stock.command(description="Views a specified stock.", aliases=["info", "show"])
    async def view(self, ctx, name_or_id):
        """Shows a stock. You can specify a name or ID."""
        stock = await self.bot.get_stock(name_or_id)
        if not stock:
            return await ctx.send(
                "I couldn't find that stock, check the name or ID again. Note: Names are case sensitive."
            )
        embed_color = discord.Color(discord.Color.brand_red())
        try: 
            player = await Player.get(ctx.author.id, self.bot)
            embed_color = player.profile_color
        except NotAPlayerError: pass
        embed = discord.Embed(title=f"{stock[1]}", description=f"ID: {stock[0]}", color=embed_color)
        tl1 = self.bot.utc_calc(stock[5], style="R")
        tl2 = self.bot.utc_calc(stock[5], style="F")
        embed.add_field(name="Stock Created", value=f"{tl2} / {tl1}")
        upordown = "UP" if stock[3] < stock[2] else "DOWN"
        embed.add_field(
            name="Stock Points",
            value=f"`{round(stock[2],1)}`, {upordown} from `{round(stock[3],1)}` points",
        )
        embed.add_field(name="Owner", value=f"<@{stock[4]}>", inline=False)
        if str(stock[6]).startswith("http"):
            embed.set_thumbnail(url=stock[6])
        await ctx.send(embed=embed)

    @stock.command(aliases=["c"], description="Creates a new stock.")
    async def create(self, ctx, name, icon_url):
        """Creates a stock. A name and direct link to an image are required."""
        player = await Player.get(ctx.author.id, self.bot)
        if player.balance < 1000:
            return await ctx.send(
                f"Sorry. You have to have $1000 to create a stock.\nYour balance: ${player.balance}"
            )
        playerstock = await self.bot.get_stock_from_player(ctx.author.id)
        if playerstock is not None:
            return await ctx.send(
                f"You already have a stock. If you want to edit it, use `{ctx.clean_prefix}stock edit`"
            )
        if len(name) > 5:
            return await ctx.send(
                "The stock name must be less than or equal to 5 characters."
            )
        if not name.isalpha():
            return await ctx.send("Stock names must be letters only.")
        name = name.upper()
        result = re.findall(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            icon_url,
        )
        if result == []:
            return await ctx.send("Invalid URL provided.")

        stockid = random.randint(1000, 9999)
        view = Confirm()
        msg = await ctx.send(
            f"Stock name: {name}\nIcon URL: <{icon_url}>\nID: {stockid}\nStarting points: 10\n**Are you sure you want to create this stock for $1000?**",
            view=view,
        )
        await view.wait()
        if view.value is None:
            return await msg.edit(content=f"Timed out after 3 minutes.")
        elif view.value:
            await self.bot.pool.execute(
                "UPDATE e_users SET bal = (bal - 1000) WHERE id = $1", ctx.author.id
            )
            await self.bot.pool.execute(
                "INSERT INTO e_stocks(id, name, ownerid, icon_url) VALUES ($1, $2, $3, $4)",
                stockid,
                name,
                ctx.author.id,
                icon_url,
            )
            await msg.delete()
            return await ctx.reply("👍")
        else:
            return await msg.delete()

    @stock.command(
        description="Deletes an owned stock. Please consider renaming first, before deleting. You do not get refunded the money you paid to create the stock."
    )
    async def delete(self, ctx):
        await Player.get(ctx.author.id, self.bot)  # Check if player exists
        playerstock = await self.bot.get_stock_from_player(ctx.author)
        if playerstock is None:
            return await ctx.send(
                f"You don't have a stock. If you want make one, use `{ctx.clean_prefix}stock create <name>`"
            )

        investor_count = await self.bot.pool.fetchrow(
            "SELECT COUNT(*) FROM e_invests WHERE stockid = $1", playerstock[0]
        )
        sum_invested = await self.bot.pool.fetchrow(
            "SELECT SUM(invested) FROM e_invests WHERE stockid = $1", playerstock[0]
        )
        tl = self.bot.utc_calc(playerstock[5])
        view = Confirm()
        msg = await ctx.send(
            f"**Are you sure you want to delete your stock?**\nStock name: {playerstock[1]}, Stock ID: {playerstock[0]}, Current points: {playerstock[2]}\nInvestors: {tuple(investor_count)[0]}, Total amount invested: ${tuple(sum_invested)[0]}\nCreated {tl} ago\n__Investments will not be deleted. Investors will be refunded the amount they invested. You will not be refunded.__",
            view=view,
        )
        await view.wait()
        if view.value is None:
            return await msg.edit(
                f"Timed out after 3 minutes. Your stock wasn't deleted."
            )
        elif view.value:
            await self.bot.pool.execute(
                "DELETE FROM e_stocks WHERE ownerid = $1", ctx.author.id
            )
            await msg.delete()
            await ctx.reply("👍")
        else:
            await msg.delete()

    @stock.command(
        aliases=["e"], description="Edits a stock. Don't invoke with arguments."
    )
    async def edit(self, ctx):
        await Player.get(ctx.author.id, self.bot)
        playerstock = await self.bot.get_stock_from_player(ctx.author.id)
        if playerstock is None:
            return await ctx.send(
                f"You don't have a stock. If you want make one, use `{ctx.clean_prefix}stock create <name>`"
            )

        # todo: make a view for this \/ \/
        rlist = [
            "1\N{variation selector-16}\N{combining enclosing keycap}",
            "2\N{variation selector-16}\N{combining enclosing keycap}",
            "❌",
        ]
        confirm = await ctx.send(
            f"What do you want to edit?\n{rlist[0]} : `Name`\n{rlist[1]} : `Icon`"
        )
        for r in rlist:
            await confirm.add_reaction(r)

        def check(r, u):
            return (
                r.message.id == confirm.id
                and str(r.emoji) in rlist
                and u.id == ctx.author.id
            )

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=30, check=check
            )
        except asyncio.TimeoutError:
            try:
                await confirm.clear_reactions()
            except:
                pass
            await confirm.edit("Timed out after 30s.")
        if str(reaction) == rlist[0]:
            msg = await ctx.reply(
                "What should the new stock name be? (Must be alphanumeric.)"
            )

            def check2(message: discord.Message) -> bool:
                return (
                    message.author == ctx.author
                    and message.channel.id == ctx.channel.id
                )

            try:
                message = await self.bot.wait_for("message", timeout=30, check=check2)
            except asyncio.TimeoutError:
                return await ctx.edit("")
            # This will be executed if the author responded properly
            else:
                name = message.content
                if not name.isalnum():
                    return await ctx.send("New name must be alphanumeric. (A-Z, 0-9)")

                name = name.upper()
                msg = await ctx.send(
                    f"Old stock name: {playerstock[1]}\nNew Stock name: {name}\n**Are you sure you want to rename this stock for $100?**"
                )

                def check3(reaction, user):
                    return user == ctx.author and str(reaction.emoji) == "✅"

                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add", timeout=30, check=check3
                    )
                except asyncio.TimeoutError:
                    pass
                else:
                    try:
                        await ctx.reply("👍")
                    except:
                        await ctx.send("👍")
                    await self.bot.pool.execute(
                        "UPDATE e_stocks SET name = $1 WHERE ownerid = $2",
                        name,
                        ctx.author.id,
                    )

    @commands.group(invoke_without_command=True)
    async def invest(self, ctx, name_or_id, amount):
        """The base command for investments.
        Invoking `invest` without a subcommand allows you to invest in stocks."""
        player = await Player.get(ctx.author.id, self.bot)
        amount = player.validate_bet(amount, b_max=100000)
        stock = await self.bot.get_stock(name_or_id)
        if stock is None:
            await ctx.send("I couldn't find that stock. Double check the name/ID.")
            return

        investment = await self.bot.pool.fetchrow(
            "SELECT * FROM e_invests WHERE stockid = $1 AND userid = $2",
            stock[0],
            ctx.author.id,
        )
        if tuple(investment) is not None:
            await ctx.send("You're already invested in this stock.")
            return
        stock = await self.bot.get_stock(name_or_id)  # Getting the stock again?!?!?
        am = random.uniform(0.1, 0.5)
        am = round(am, 2)
        await self.bot.pool.execute(
            "UPDATE e_stocks SET points = (points + $1) WHERE stockid = $2",
            am,
            name_or_id,
        )
        await self.bot.pool.execute(
            "UPDATE e_stocks SET points = (points + $1) WHERE name = $2", am, name_or_id
        )
        await self.bot.pool.execute(
            "INSERT INTO e_invests VALUES ($1, $2, $3, $4)",
            stock[0],
            ctx.author.id,
            amount,
            stock[2],
        )
        await player.update_balance(amount * -1, ctx=ctx)
        await self.bot.stats.add("totalstocksInvested")
        await ctx.send(
            f"Invested ${amount} in **{stock[1]}** at {round(stock[2], 2)} points!"
        )

    @invest.command(
        invoke_without_command=True,
        description="Sells an investment.\nThe money you earn back is calculated like this: `money_to_pay = (current_stock_points - points_at_investment) * amount_invested`",
    )
    async def sell(self, ctx, name_or_id):
        name_or_id = name_or_id.upper()
        player = await Player.get(ctx.author.id, self.bot)
        investment = await self.bot.pool.fetchrow(
            "SELECT * FROM e_invests WHERE stockname = $1 AND userid = $2",
            name_or_id,
            ctx.author.id,
        )
        if tuple(investment) is None:
            investment = await self.bot.pool.fetchrow(
                "SELECT * FROM e_invests WHERE stockid = $1 AND userid = $2",
                name_or_id,
                ctx.author.id,
            )
            if tuple(investment) is None:
                return await ctx.send(
                    "I couldn't find that stock, or you're not invested in it. Double check the name or ID."
                )

        stock = await self.bot.pool.fetchrow(
            "SELECT * FROM e_stocks WHERE stockid = $1", tuple(investment)[0]
        )
        if stock is None:
            await ctx.send(
                f"This stock no longer exists. You will be refunded ${tuple(investment)[2]} (the money you invested)."
            )
            await player.update_balance(
                int(tuple(investment)[2]), ctx=ctx, ignore_total_earned=True
            )
            await self.bot.pool.execute(
                "DELETE FROM e_invests WHERE stockname = $1 AND userid = $2",
                name_or_id,
                ctx.author.id,
            )
            await self.bot.pool.execute(
                "DELETE FROM e_invests WHERE stockid = $1 AND userid = $2",
                name_or_id,
                ctx.author.id,
            )
            return
        stock = tuple(stock)
        points_at_investment = round(tuple(investment)[4], 2)
        current_stock_points = round(stock[2], 2)
        amount_invested = int(tuple(investment)[2])
        money_to_pay = (
            current_stock_points - points_at_investment
        ) * amount_invested  # TODO fix me someday
        money_to_pay = int(money_to_pay)
        if money_to_pay > 0:
            summary = f"${money_to_pay} will be depositied into your account.\nYou invested ${round(amount_invested,2)}, at {points_at_investment} points. The current points is {current_stock_points}"
        else:
            summary = f"${money_to_pay} will be taken from your account.\nYou invested ${amount_invested}, at {points_at_investment} points. The current points is {current_stock_points}."
        if (money_to_pay - amount_invested) > 0:
            summary += f"\nThis is a net **profit** of ${(money_to_pay - amount_invested)}\n**Are you sure you want to sell your investment?**"
        elif (money_to_pay - amount_invested) < 0:
            gross_bal = player.bal + (money_to_pay - amount_invested)
            if gross_bal < 0:
                return await ctx.send(
                    f"You cannot sell this investment, because it would put you into debt (${(gross_bal)}). Try again later when the stock has higher points."
                )
            summary += f"\nThis is a net **loss** of ${(money_to_pay - amount_invested)}\n**Are you sure you want to sell your investment?**"
        else:
            summary += f"\nYou are essentially being refunded, as the amount you are getting paid is the same you invested.\n**Are you sure you want to sell your investment?**"
        msg = await ctx.send(summary)
        sellornot = await self.bot.prompt(ctx.author.id, msg, timeout=30)
        if not sellornot:
            await ctx.send("Cancelled, your investment was not sold.")
        else:
            am = random.uniform(0.1, 0.5)
            am = round(am, 2)
            await self.bot.pool.execute(
                "UPDATE e_stocks SET points = (points - $1) WHERE stockid = $2",
                am,
                stock[0],
            )
            await player.update_balance(money_to_pay, ctx=ctx)
            if money_to_pay < 0:
                await self.bot.stats.add(
                    "totalinvestLost", (abs(money_to_pay))
                )  # adds to totalinvestLost stat if amount is negative (player lost money)
            await self.bot.pool.execute(
                "DELETE FROM e_invests WHERE userid = $1 AND stockid = $2",
                ctx.author.id,
                stock[0],
            )
            await ctx.reply("👍")

            ach = self.bot.get_cog("achievements")
            if money_to_pay >= 1000:
                if await ach.has_ach(ctx.author, 9):
                    await ach.give_ach(ctx.author, 9)
                    await ctx.reply(
                        f"**Achievement get!** Day trader\n*See your achievements with {ctx.clean_prefix}achievements*"
                    )
            if money_to_pay >= 100000:
                if await ach.has_ach(ctx.author, 10):
                    await ach.give_ach(ctx.author, 10)
                    await ctx.reply(
                        f"**Achievement get!** Wolf of Wall Street\n*See your achievements with {ctx.clean_prefix}achievements*"
                    )
        for r in msg.reactions:
            try:
                await r.remove()
            except:
                pass


async def setup(bot):
    await bot.add_cog(stocks(bot))
