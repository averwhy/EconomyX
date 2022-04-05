import discord
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.botviews import X
OWNER_ID = 267410788996743168

class player_meta(commands.Cog):
    """
    These commands are player meta. You can use these to get things like player profiles.
    """
    def __init__(self,bot):
        self.bot = bot
    
    @commands.cooldown(1,5,BucketType.user)
    @commands.command(aliases=["p"])
    async def profile(self,ctx,user: discord.User = None):
        """Views your profile. Can also view another users profile. They must be in the database."""
        if user is None:
            user = ctx.author
        data = await self.bot.get_player(user.id)
        if data is None:
            await ctx.send(f"You dont have a profile. Try `{ctx.clean_prefix}register`")
            return
        embedcolor = int(("0x"+data[5]),0)
        embed = discord.Embed(title=f"{str(user)}'s Profile",description=f"`ID: {user.id}`",color=embedcolor)
        embed.set_thumbnail(url=user.avatar.url)
        embed.add_field(name="Balance",value=f"${data[3]}")
        embed.add_field(name="Total earnings",value=f"${data[4]}")
        embed.add_field(name="Lotteries Won", value=f"{data[6]}",inline=False)
        embed.set_footer(text=f"EconomyX v{self.bot.version}",icon_url=self.bot.user.avatar.url)
        await ctx.send(embed=embed)
    
    @commands.cooldown(1,60,BucketType.user)
    @commands.command(aliases=["start","open"])
    async def register(self,ctx):
        """Creates a profile with EconomyX. You can also use this is delete your account/profile."""
        async with ctx.channel.typing():
            await asyncio.sleep(0.5)
            data = await self.bot.usercheck(ctx.author.id)
            if not data:
                msg = await self.bot.add_player(ctx.author)
                await ctx.send(msg)
                return
        msg2 = await ctx.send(f"Youre already in the database, {ctx.author.mention}\nIf you would like, i can purge your data from the database.\nSay `Yes` if you would like to start this process.")
        await self.bot.begin_user_deletion(ctx, msg2)

    @commands.command()
    async def tips(self, ctx):
        from .utils.botviews import X
        n = ctx.me.name
        """Tips and tricks for money making in EconomyX"""
        tip = f"""*Disclaimer: Money with EconomyX is not real currency and cannot be exchanged for real currency. Please read the ToS for more info (found in the support server).*
        When you register with {n}, you start out with $100. Using that money, you have to make more money.
        There's a few ways you can do this.
        1. Play money-making games
            There's many games you can play that you can earn money with. The simplest is `e$bet`, which has a 50% chance win rate.
            If you're looking for higher risk but higher reward games, try `e$roulette`. If you select the 'green' option, theres a ~2.97 percent chance you will win **35x** your bet!
        
        2. Invest in stocks
            Stocks can be a great way of making money. Say for example you invest $1,000 into a stock at 10 points. Then, you sell your investment when the stock is at 20 points.
            On the backend, the math would look like this: `(20 - 10) * 1000`. which means you would be paid $10,000!
            Remember, stock points randomly flucuate because they are ***not*** based off of real stocks.
            
        3. Win the lottery
            This method is not quite the best. You can buy a lottery ticket for $100, and that money is pooled into the lottery. If you win, you will earn everybodys winnings.
            If the lottery has a lot of contestants, the probability of winning is low. So don't bank all your money on this!
            
        If you have any questions or feedback, join the EconomyX support server (`e$support`)"""

        await ctx.send(tip, view=X())
        
    @commands.group(aliases=["c","change","custom"],invoke_without_command=True)
    async def customize(self,ctx):
        """Customize command."""
        await ctx.send("Usage: `e$customize <guild/color>`")
         
    @commands.cooldown(1,60,BucketType.user)
    @customize.command(name="guild", enabled=False)
    async def gld(self, ctx, newguild: int = None):
        """Allows you to change the guild you belong to. This wont effect your money or anything, just the guild (server) you belong to."""
        data = await self.bot.get_player(ctx.author.id)
        if data is None:
            await ctx.send(f"You dont have a profile. Try `{ctx.clean_prefix}register`")
        if newguild is None:
            askmessage = await ctx.send(f"`Are you sure you want to change your guild to this server?`")
            await askmessage.add_reaction(emoji="\U00002705") # white check mark
            def check(reaction, user):
                return user == ctx.message.author and str(reaction.emoji) == "\U00002705"
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=10, check=check)
            except asyncio.TimeoutError:
                await askmessage.edit(content="`Prompt timed out. Try again`")
            else:
                try:
                    await askmessage.clear_reactions()
                except:
                    print(f"Failed to remove reactions in guild {ctx.message.guild.name} ({ctx.message.guild.id}), channel #{ctx.message.channel.name}")
                await self.bot.db.execute("UPDATE e_users SET guildid = ? WHERE id = ?",(ctx.guild.id,ctx.author.id,))
                await self.bot.db.commit()
                await ctx.send(f"`Success! You now belong to {ctx.guild.name}!`")
        if newguild is not None:
            try:
                grabbed_guild = self.bot.get_guild(newguild)
                if grabbed_guild is None:
                    grabbed_guild = await self.bot.fetch_guild(newguild)
            except Exception as e:
                await ctx.send(f"`I couldn't find that guild. More info:` ```\n{e}\n```")
                return # cancels rest of function
            askmessage = await ctx.send(f"`Are you sure you want to change your guild to {grabbed_guild.name}?`")
            await askmessage.add_reaction(emoji="\U00002705") # white check mark
            def check2(reaction, user):
                return user == ctx.message.author and str(reaction.emoji) == "\U00002705"
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=10, check=check2)
            except asyncio.TimeoutError:
                await askmessage.edit(content="`Prompt timed out. Try again`")
            else:
                try:
                    await askmessage.clear_reactions()
                except:
                    print(f"Failed to remove reactions in guild {ctx.message.guild.name} ({ctx.message.guild.id}), channel #{ctx.message.channel.name}")
                await self.bot.db.execute("UPDATE e_users SET guildid = ? WHERE id = ?",(newguild,ctx.author.id,))
                await self.bot.db.commit()
                await askmessage.edit(content=f"`Success! You now belong to {grabbed_guild.name}!`")

    @commands.cooldown(1,10,BucketType.user)
    @customize.command(aliases=["colour","c"])
    async def color(self,ctx,hexcolor : str = None):
        """Allows you to change the color that shows on your profile, and other certain commands, like `help`."""
        data = await self.bot.get_player(ctx.author.id)
        if data is None:
            await ctx.send(f"You dont have a profile. Try `{ctx.clean_prefix}register`")
            return
        try:
            hexcolor = hexcolor.upper()
            newhexcolor = int((f"0x{hexcolor}"),0)
            embed = discord.Embed(title="<-- Theres a preview of your chosen color!", description=f"**Are you sure you would like to change your profile color to hex value {hexcolor}?**", colour=discord.Color(newhexcolor))
        except:
            await ctx.send("There was an error with coverting that hex color. If you need help, try this link: https://htmlcolorcodes.com/color-picker/")
        if hexcolor is None:
            await ctx.send("Please provide a valid hex color value! (Without the #)")
            return
        else:
            askmessage = await ctx.send(embed=embed)
            await askmessage.add_reaction("\U00002705") # white check mark

            def check(reaction, user):
                return user == ctx.message.author and str(reaction.emoji) == "\U00002705"
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=10, check=check)
            except asyncio.TimeoutError:
                try:
                    await askmessage.clear_reactions()
                except: # forbidden (most likely)
                    pass
                mbed = discord.Embed(title="Timed out :(", description=f"Try again?", colour=discord.Colour(0xfcd703))
                await askmessage.edit(embed=mbed)
                return
            else:
                async with ctx.channel.typing():
                    try:
                        await askmessage.clear_reactions()
                    except: # forbidden (most likely)
                        await askmessage.delete() # we'll just delete our message /shrug
                    await self.bot.db.execute("UPDATE e_users SET profilecolor = ? WHERE id = ?",(hexcolor,ctx.author.id,))
                    await self.bot.db.commit()
                    await ctx.send(f"Success! Do {ctx.prefix}profile to see your new profile color.")     
                
    @commands.command(aliases=["lb"])
    async def leaderboard(self,ctx):
        """Views a leaderboard of users, sorted by their balance, descending."""
        async with ctx.channel.typing():
            c = await self.bot.db.execute("SELECT * FROM e_users ORDER BY bal DESC")
            data = await c.fetchmany(5)
            data2 = await self.bot.get_player(ctx.author.id)
            if data2 is None:
                color = discord.Color.blue()
            else:
                color = int(("0x"+data2[5]),0)
                
            embed = discord.Embed(title="User Leaderboard",description="Sorted by balance, descending",color=color)
            for i in data:
                await asyncio.sleep(0.1)
                embed.add_field(name=f"{i[1]}",value=f"${i[3]}",inline=False)
            await ctx.send(embed=embed)
        
def setup(bot):
    bot.add_cog(player_meta(bot))