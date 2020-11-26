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
    
    @commands.cooldown(1,2,BucketType.user)
    @commands.command(aliases=["b"])
    async def bet(self,ctx,amount: float):
        amount = float(amount)
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `^register`.")
            return
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
    async def rockpaperscissors(self, ctx):
        await ctx.send("Usage: `^rps <rock/paper/scissors>`")
    
    @commands.cooldown(1,10,BucketType.user)
    @rockpaperscissors.command(aliases=["p"])
    async def paper(self, ctx):
        player = await self.bot.get_player(ctx.author.id)
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
            return
        if final_outcome == "lose":
            await ctx.send(f"Damn, I won.\n{m}\nThanks for the $100.")
            await self.bot.db.execute("UPDATE e_users SET bal = (bal - 100) WHERE id = ?",(ctx.author.id,))
            return
        if final_outcome == "draw":
            await ctx.send(f"Oh?\n{m}\nTie. None of us pay")
            return
        
    @commands.cooldown(1,10,BucketType.user)
    @rockpaperscissors.command(aliases=["r"])
    async def rock(self, ctx):
        player = await self.bot.get_player(ctx.author.id)
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
            return
        if final_outcome == "lose":
            await ctx.send(f"Damn, I won.\n{m}\nThanks for the $100.")
            await self.bot.db.execute("UPDATE e_users SET bal = (bal - 100) WHERE id = ?",(ctx.author.id,))
            return
        if final_outcome == "draw":
            await ctx.send(f"Oh?\n{m}\nTie. None of us pay")
            return
        
    @commands.cooldown(1,10,BucketType.user)
    @rockpaperscissors.command(aliases=["s","scissor"])
    async def scissors(self, ctx):
        player = await self.bot.get_player(ctx.author.id)
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
            return
        if final_outcome == "lose":
            await ctx.send(f"Damn, I won.\n{m}\nThanks for the $100.")
            await self.bot.db.execute("UPDATE e_users SET bal = (bal - 100) WHERE id = ?",(ctx.author.id,))
            return
        if final_outcome == "draw":
            await ctx.send(f"Oh?\n{m}\nTie. None of us pay")
            return
        
        


        
        
        
        
def setup(bot):
    bot.add_cog(game(bot))