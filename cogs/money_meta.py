import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from .utils import player as Player
from .utils.errors import NotAPlayerError
OWNER_ID = 267410788996743168

class money_meta(commands.Cog):
    """
    These commands are meta about money, such as pay or balance.
    """
    def __init__(self,bot):
        self.bot = bot
    
    @commands.cooldown(1,5,BucketType.user)
    @commands.command(aliases=["payuser"])
    async def pay(self, ctx, user: discord.User, amount: int):
        player = await Player.get(ctx.author.id, self.bot)
        amount = player.validate_bet(amount, max=100000)
        if player.balance < amount:
            await ctx.send(f"You cant pay them that much. You only have ${player.balance}.")
            return
        try:
            await Player.get(ctx.author.id, self.bot)
        except NotAPlayerError:
            return await ctx.send("That player doesn't seem to have a profile.")
        try:
            await self.bot.transfer_money(ctx.author,user,amount)
            await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(amount,user.id,))
            await self.bot.stats.user_add_paid(ctx.author, amount)
            await ctx.reply("Transfer successful.")
        except Exception as e:
            await ctx.send(f"Something went wrong.\n{e}")
            
    #@commands.cooldown(1,3,BucketType.user)
    @commands.command(aliases=["balance"])
    async def bal(self,ctx, user: discord.User = None):
        if user is None:
            try:
                player = await Player.get(ctx.author.id, self.bot)
            except NotAPlayerError:
                return await ctx.send("That player doesn't seem to have a profile.")
            await ctx.send(f"{str(ctx.author)}'s balance: ${player.balance}")
        if user is not None:
            try:
                player = await Player.get(user.id, self.bot)
            except NotAPlayerError:
                return await ctx.send("That player doesn't seem to have a profile.")
            await ctx.send(f"{str(user)}'s balance: ${player.balance}")
            
    @commands.cooldown(1,10,BucketType.user)
    @commands.command()
    async def rob(self,ctx):
        await ctx.send("You can't rob. It's against the law.")
        
        
        
        
async def setup(bot):
    await bot.add_cog(money_meta(bot))