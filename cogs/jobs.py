import random
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
OWNER_ID = 267410788996743168

class jobs(commands.Cog):
    """
    This is for the work command. More is planned for this.
    """
    def __init__(self,bot):
        self.bot = bot
    
    @commands.cooldown(1,300,BucketType.user)
    @commands.command(aliases=["w"])
    async def work(self,ctx):
        """Work. You earn a random number between 1 and 500."""
        player = await self.bot.get_player(ctx.author.id)
        if player is None:
            await ctx.send("You dont have a profile! Get one with `e$register`.")
            return
        pay = random.randint(1,500)
        if pay > 350:
            await ctx.send(f"You worked and got paid ${pay}.\nDamn, you must be good at what you do.")
        elif pay > 300:
            await ctx.send(f"You worked and got paid ${pay}.\nNice job *(no pun intended)*.")
        elif pay > 250:
            await ctx.send(f"You worked and got paid ${pay}.\nNot bad.")
        elif pay > 200:
            await ctx.send(f"You worked and got paid ${pay}.\nEh. You can do better than that.")
        elif pay > 150:
            await ctx.send(f"You worked and got paid ${pay}.\nYou should ask for a raise sometime.")
        elif pay > 100:
            await ctx.send(f"You worked and got paid ${pay}.\nHmm... chances are you made a very poor career choice.")
        elif pay > 50:
            await ctx.send(f"You worked and got paid ${pay}.\nYou should ask for a raise sometime.")
        else:
            await ctx.send(f"You worked and got paid ${pay}.\nDamn, did you sleep on the job?")
        await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(pay, ctx.author.id,))
        await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(pay,ctx.author.id,))
        await self.bot.db.commit()

        

def setup(bot):
    bot.add_cog(jobs(bot))