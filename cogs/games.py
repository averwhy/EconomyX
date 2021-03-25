import discord
import platform
import time
import random
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
OWNER_ID = 267410788996743168

class games(commands.Cog):
    """
    Money making games. These are all gambling games at the moment.
    """
    def __init__(self,bot):
        self.bot = bot
    
    @commands.cooldown(1,2,BucketType.user)
    @commands.command(aliases=["b"], description="Bets money. There is a 50/50 chance on winning and losing.")
    async def bet(self, ctx, amount):
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        if amount.lower() == "all":
            amount = player[3]
        amount = int(amount)
        if amount != amount:
            await ctx.send("Thats not a valid amount. Nice try, though")
            return
        if player[3] < amount:
            await ctx.send(f"That bet is too big. You only have ${player[3]}.")
            return
        if amount < 1:
            await ctx.send("Too small of a bet.")
            return
        
        y = random.choice([True,False])
        
        if y:
            data = await self.bot.on_bet_win(ctx.author,amount) # returns list
            await ctx.send(f"Won ${amount}\nNew balance: ${(data[1]+amount)}")
        if not y:
            data = await self.bot.on_bet_loss(ctx.author,amount) # returns new balance
            await ctx.send(f"Lost ${amount}\nNew balance: ${(data-amount)}")
            
    @commands.command(aliases=['rl'])
    async def roulette(self, ctx, amount):
        """Roulette gambling command. Starts a propmpt in which the user reacts with the color they wish to bet."""
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        if amount.lower() == "all":
            amount = player[3]
        amount = int(amount)
        if amount != amount:
            await ctx.send("Thats not a valid amount. Nice try, though")
            return
        if player[3] < amount:
            await ctx.send(f"That bet is too big. You only have ${player[3]}.")
            return
        if amount < 5:
            await ctx.send("Too small of a bet. (Minimum 5)")
            return
        
        confirm = await ctx.send("Choose one of the 3 colors to bet on `(🔴: 2x, ⚫: 2x, 🟢: 35x)`:")
        rlist = ['🔴', '⚫', '🟢', '❌']
        for r in rlist:
            await confirm.add_reaction(r)
        def check(r, u):
            return r.message.id == confirm.id and str(r.emoji) in rlist and u.id == ctx.author.id
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
        except asyncio.TimeoutError:
            await confirm.delete()
            return await ctx.reply("Timed out after 60s.")
        result = random.choices(rlist, weights=(48.6, 48.6, 2.799999999999997, 0), k=1)
        if str(reaction.emoji) == rlist[3]: #cancel
            await confirm.delete()
            return await ctx.reply("Cancelled, you did not lose/gain any money.")
        if result[0] == rlist[2]: # green
            newamount = amount * 35
            await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(newamount, ctx.author.id,))
            await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(newamount, ctx.author.id,))
            return await ctx.send(f"Your choice: {str(reaction.emoji)}, result: {str(result[0])}\n**You won BIG!**\nMoney earned: ${int(amount * 35)} (`${int(amount)} x 35`)")
        elif reaction.emoji == result[0]:
            await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount, ctx.author.id,))
            await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(amount, ctx.author.id,))
            return await ctx.send(f"Your choice: {str(reaction.emoji)}, result: {str(result[0])}\n**You won!**\nMoney earned: ${int(amount)}")
        else:
            await self.bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(amount, ctx.author.id,))
            return await ctx.send(f"Your choice: {str(reaction.emoji)}, result: {str(result[0])}\n**You lost.**\nMoney lost: ${int(amount)}")
        
    
    @commands.group(aliases=["rps"],invoke_without_command=True, description="Rock paper scissors.")
    async def rockpaperscissors(self, ctx, amount, choice):
        """Rock paper scissor game. `amount` is money you want to bet, and choice must be `rock`, `paper`, or `scissor` (singular, no 's)"""
        summary = ""
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        if len(choice) < 4 or len(choice) > 7:
            return await ctx.send("Invalid choice.")
        if amount.lower() == "all":
            amount = player[3]
        if amount != amount:
            await ctx.send("Thats not a valid amount. Nice try, though")
            return
        if player[3] < amount:
            await ctx.send(f"That bet is too big. You only have ${player[3]}.")
            return
        if amount < 5:
            await ctx.send("Too small of a bet. (Minimum 5)")
            return
        rand = random.randint(0,2)
        choices = ["paper", "scissor", "rock"]
        if not choice.strip() in choices:
            return await ctx.send("It looks like you didn't specify `rock`, `paper`, or `scissor` (singular, no 's).")
        outcome_list = ["draw", "lose", "win"]
        result = (choices.index(choice)+rand)%3
        summary += "I drew {}, you {}\n".format(choices[result], outcome_list[rand])
        if outcome_list[rand] == "draw":
            summary += "You lost no money."
        elif outcome_list[rand] == "lose":
            summary += f"You lost ${amount}."
            await self.bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(amount, ctx.author.id,))
        elif outcome_list[rand] == "win":
            summary += f"You won ${amount}"
            await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount, ctx.author.id,))
            await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(amount, ctx.author.id,))
        await ctx.reply(summary)
            

    @commands.cooldown(1,15,BucketType.user)
    @commands.command(description="Guess game with money. You have 5 chances to guess the number randomly chosen between 1-10.\nThis amounts to a 50/50 chance.")
    async def guess(self, ctx, amount: int):
        amount = int(amount)
        amount = round(amount,2)
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        if amount != amount:
            await ctx.send("Thats not a valid amount.")
            return
        if player[3] < amount:
            await ctx.send(f"That bet is too big. You only have ${player[3]}.")
            return
        if amount < 1:
            await ctx.send("Too small of a bet.")
            return
        
        await ctx.send(f"Alright, your bet is ${amount}. If you lose, you pay that. If you win, you earn that.\nI'm thinking of a number between 1 and 10. You have 5 tries.")
        tries = 5
        guessed_it = False
        the_number = random.randint(1,10)
        while not guessed_it:
            def check(m):
                return m.channel == ctx.channel and m.author == ctx.author

            msg = await self.bot.wait_for('message', check=check)
            try:
                content = int(msg.content)
                if content > 10:
                    await ctx.send("Guess a number **between 1 and 10.**")
                    continue
                if content == the_number:
                    await ctx.send(f"You guessed it! The number was {the_number}.\nAs promised, here's your winnings of ${amount}.")
                    await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount, ctx.author.id,))
                    await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(amount,ctx.author.id,))
                    return
                else:
                    tries -= 1
                    if tries == 0:
                        await ctx.send(f"You're out of tries, and haven't guessed my number.\nYou lose ${amount}.")
                        await self.bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(amount, ctx.author.id,))
                        return
                    await ctx.send(f"That's not it!\nYou have {tries} attempt(s) left.")
            except:
                content = msg.content
                content = content.lower()
                if "cancel" in content:
                    await ctx.send("Guessing game cancelled. You did not lose or gain any money.")
                    return
                else:
                    await ctx.send("Guess a **number**!")
                
    # @commands.command(aliases=['bj'])
    # async def blackjack(self, ctx, amount):
    #     values = {'Two':2, 'Three':3, 'Four':4, 'Five':5, 'Six':6, 'Seven':7, 'Eight':8, 'Nine':9, 'Ten':10, 'Jack':10,'Queen':10, 'King':10, 'Ace':11}
        
    #     player = await self.bot.get_player(ctx.author.id)
    #     if player is None:
    #         await ctx.send("You dont have a profile! Get one with `e$register`.")
    #         return
    #     if amount.lower() == "all":
    #         amount = player[3]
    #     amount = int(amount)
    #     if amount != amount:
    #         await ctx.send("Thats not a valid amount. Nice try, though")
    #         return
    #     if player[3] < amount:
    #         await ctx.send(f"That bet is too big. You only have ${player[3]}.")
    #         return
    #     if amount < 5:
    #         await ctx.send("Too small of a bet. (Minimum 5)")
    #         return
        
    #     player_cards = []
    #     dealer_cards = []
    #     dealer_cards.append()

def setup(bot):
    bot.add_cog(games(bot))