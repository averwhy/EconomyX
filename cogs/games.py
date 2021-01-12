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
            
    @commands.group(aliases=["rps"],invoke_without_command=True)
    async def rockpaperscissors(self, ctx, description="Rock paper scissors. "):
        await ctx.send("Usage: `e$rps <rock/paper/scissors>`")
    
    @commands.cooldown(1,5,BucketType.user)
    @rockpaperscissors.command(aliases=["p"], description="Paper")
    async def paper(self, ctx):
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        if player[3] < 100:
            await ctx.send(f"Sorry. You have to have at least $100 to play rock paper scissors.\nYour balance: ${player[3]}")
            return
        
        rand = random.randint(0,2)
        choices = ["paper", "scissors", "rock"]
        outcome_list = ["draw", "lose", "win"]
        result = (choices.index("paper")+rand)%3
        final_outcome = outcome_list[rand]
        m = ("I drew {}, you drew paper.".format(choices[result]))
        if final_outcome == "win":
            await ctx.send(f"Hey, you won.\n{m}\nHeres $100.")
            await self.bot.db.execute("UPDATE e_users SET bal = (bal + 100) WHERE id = ?",(ctx.author.id,))
            await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + 100) WHERE id = ?",(ctx.author.id,))
            return
        if final_outcome == "lose":
            await ctx.send(f"Damn, I won.\n{m}\nThanks for the $100.")
            await self.bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(ctx.author.id,))
            return
        if final_outcome == "draw":
            await ctx.send(f"Oh?\n{m}\nTie. None of us pay")
            return
        
    @commands.cooldown(1,5,BucketType.user)
    @rockpaperscissors.command(aliases=["r"], description="Rock")
    async def rock(self, ctx):
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        if player[3] < 100:
            await ctx.send(f"Sorry. You have to have at least $100 to play rock paper scissors.\nYour balance: ${player[3]}")
            return
        
        rand = random.randint(0,2)
        choices = ["paper", "scissors", "rock"]
        outcome_list = ["draw", "lose", "win"]
        result = (choices.index("rock")+rand)%3
        final_outcome = outcome_list[rand]
        m = ("I drew {}, you drew rock".format(choices[result]))
        if final_outcome == "win":
            await ctx.send(f"Hey, you won.\n{m}\nHeres $100.")
            await self.bot.db.execute("UPDATE e_users SET bal = (bal + 100) WHERE id = ?",(ctx.author.id,))
            await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + 100) WHERE id = ?",(ctx.author.id,))
            return
        if final_outcome == "lose":
            await ctx.send(f"Damn, I won.\n{m}\nThanks for the $100.")
            await self.bot.db.execute("UPDATE e_users SET bal = (bal - 100) WHERE id = ?",(ctx.author.id,))
            return
        if final_outcome == "draw":
            await ctx.send(f"Oh?\n{m}\nTie. None of us pay")
            return
        
    @commands.cooldown(1,5,BucketType.user)
    @rockpaperscissors.command(aliases=["s","scissor"], description="Scissors")
    async def scissors(self, ctx):
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        if player[3] < 100:
            await ctx.send(f"Sorry. You have to have at least $100 to play rock paper scissors.\nYour balance: ${player[3]}")
            return
        
        rand = random.randint(0,2)
        choices = ["paper", "scissors", "rock"]
        outcome_list = ["draw", "lose", "win"]
        result = (choices.index("scissors")+rand)%3
        final_outcome = outcome_list[rand]
        m = ("I drew {}, you drew scissors.".format(choices[result]))
        if final_outcome == "win":
            await ctx.send(f"Hey, you won.\n{m}\nHeres $100.")
            await self.bot.db.execute("UPDATE e_users SET bal = (bal + 100) WHERE id = ?",(ctx.author.id,))
            await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + 100) WHERE id = ?",(ctx.author.id,))
            return
        if final_outcome == "lose":
            await ctx.send(f"Damn, I won.\n{m}\nThanks for the $100.")
            await self.bot.db.execute("UPDATE e_users SET bal = (bal - 100) WHERE id = ?",(ctx.author.id,))
            return
        if final_outcome == "draw":
            await ctx.send(f"Oh?\n{m}\nTie. None of us pay")
            return
        
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
                
        
        
def setup(bot):
    bot.add_cog(games(bot))