import discord
import asyncio
import logging
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from .utils import player as Player
from .utils.errors import NotAPlayerError
from .utils.botviews import X

log = logging.getLogger(__name__)
OWNER_ID = 267410788996743168


class player_meta(commands.Cog, command_attrs=dict(name="Player Meta")):
    """
    These commands are player meta. You can use these to get things like player profiles.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 5, BucketType.user)
    @commands.command(aliases=["p"])
    async def profile(self, ctx, user: discord.User = None):
        """Views your profile. Can also view another users profile. They must be in the database."""
        if user is None:
            user = ctx.author
        player = await Player.get(user.id, self.bot)
        job_desc = ""
        try:
            job_data = await player.get_job_data()
        except TypeError:  # errors if not found
            job_desc = "None!"
        else:
            job_desc = f"Level {job_data[2]} | Worked {job_data[3]} times"
        achcount = len(
            tuple(
                await self.bot.pool.fetch(
                    "SELECT * FROM e_achievements WHERE userid = $1", ctx.author.id
                )
            )
        )
        gamesplayed = (
            tuple(
                await self.bot.pool.fetch(
                    "SELECT gamesPlayed FROM e_player_stats WHERE id = $1",
                    ctx.author.id,
                )
            )
        )[0][
            0
        ] 
        embedcolor = player.profile_color
        embed = discord.Embed(
            title=f"{str(user)}'s Profile",
            description=f"`ID: {user.id}`",
            color=embedcolor,
        )
        try:
            embed.set_thumbnail(url=user.avatar.url)
        except:
            pass
        embed.add_field(name="Balance", value=f"${player.balance}")
        embed.add_field(name="Total earnings", value=f"${player.total_earnings}")
        embed.add_field(name="Games played", value=gamesplayed)
        embed.add_field(name="Achievements", value=f"{achcount}/30")
        embed.add_field(name="Lotteries Won", value=f"{player.lotteries_won}")
        embed.add_field(name="Job Stats", value=job_desc, inline=False)
        embed.add_field(name="Treasure Hunting Stats", value="Coming soon...")
        embed.set_footer(
            text=f"EconomyX v{self.bot.version}", icon_url=self.bot.user.avatar.url
        )
        await player.update_name(ctx.author.name)
        await self.bot.stats.add("totalprofilesViewed")
        await ctx.send(embed=embed)

    @commands.cooldown(1, 60, BucketType.user)
    @commands.command(aliases=["start", "open"])
    async def register(self, ctx):
        """Creates a profile with EconomyX. You can also use this to delete your account/profile."""
        try:
            await Player.get(ctx.author.id, self.bot)
        except NotAPlayerError:
            await Player.player.create(bot=self.bot, member_object=ctx.author)
            await ctx.send(
                f"Success! You can get started by viewing your profile: `{ctx.clean_prefix}profile`"
            )
            return
        msg2 = await ctx.send(
            f"Youre already in the database, {ctx.author.mention}\nIf you would like, i can delete all of your data from the database.\nSay `Yes` if you would like to start this process."
        )
        await self.bot.begin_user_deletion(ctx, msg2)

    @commands.command()
    async def tips(self, ctx):
        n = ctx.me.name
        """Tips and tricks for money making in EconomyX"""
        tip = f"""*Disclaimer: Money with EconomyX is not real currency and cannot be exchanged for real currency. Please read the ToS for more info (found in the support server).*
        When you register with {n}, you start out with $100. Using that money, you can make more money.
        There's a few ways you can do this:
        1. Play money-making games
            There's many games you can play that you can earn money with. The simplest is `{ctx.clean_prefix}bet`, which has a 50% chance win rate.
            If you're looking for higher risk but higher reward games, try `{ctx.clean_prefix}roulette`. If you select the 'green' option, theres a ~1 percent chance you will win **25x** your bet!
        
        2. Invest in stocks
            Stocks can be a great way of making money. Say for example you invest $1,000 into a stock at 10 points. Then, you sell your investment when the stock is at 20 points.
            On the backend, the math would look like this: `(20 - 10) * 1000`. which means you would be paid $10,000!
            Remember, stock points randomly flucuate because they are ***not*** based off of real stocks.
            
        3. Win the lottery
            This method is not quite the best. You can buy a lottery ticket for $100, and that money is pooled into the lottery. If you win, you will earn everybodys winnings times two.
            If the lottery has a lot of contestants, the probability of winning is low. However it doesn't hurt to just buy a ticket every day!
            
        If you have any questions or feedback, join the EconomyX support server (`{ctx.clean_prefix}support`)"""

        await ctx.send(tip, view=X())

    @commands.cooldown(1, 10, BucketType.user)
    @commands.command(aliases=["colour", "c"])
    async def color(self, ctx, hexcolor: str = None):
        """Allows you to change the color that shows on your profile, and other certain commands that use embeds, like `help`."""
        await Player.get(ctx.author.id, self.bot)
        if hexcolor is None:
            return await ctx.send(
                "Please provide a valid hex color value (without the `#`)"
            )
        try:
            if len(hexcolor.strip()) != 6:
                return await ctx.send(
                    "That hex code is the wrong length! Remember not to include the `#`."
                )
            hexcolor = hexcolor.upper()
            newhexcolor = int((f"0x{hexcolor}"), 0)
            embed = discord.Embed(
                title="Heres a preview of your chosen color!",
                description=f"Are you sure you would like to change your profile color to hex value {hexcolor}?",
                colour=discord.Color(newhexcolor),
            )
        except Exception as e:
            log.error(f'Error converting hex color "{hexcolor}": {e}')
            await ctx.send(
                "There was an error with coverting that hex color. If you need help, try this link: https://htmlcolorcodes.com/color-picker/"
            )
        else:
            askmessage = await ctx.send(embed=embed)
            await askmessage.add_reaction("\U00002705")  # white check mark

            def check(reaction, user):
                return (
                    user == ctx.message.author and str(reaction.emoji) == "\U00002705"
                )

            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=10, check=check
                )
            except asyncio.TimeoutError:
                try:
                    await askmessage.clear_reactions()
                except:  # forbidden (most likely)
                    pass
                mbed = discord.Embed(
                    title="Timed out :(",
                    description=f"Try again?",
                    colour=discord.Colour(0xFCD703),
                )
                await askmessage.edit(embed=mbed)
                return
            else:
                async with ctx.channel.typing():
                    try:
                        await askmessage.clear_reactions()
                    except:  # forbidden (most likely)
                        await askmessage.delete()  # we'll just delete our message /shrug
                    await self.bot.pool.execute(
                        "UPDATE e_users SET profilecolor = $1 WHERE id = $2",
                        hexcolor,
                        ctx.author.id,
                    )
                    await ctx.send(
                        f"Success! Do {ctx.prefix}profile to see your new profile color."
                    )

    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx):
        """Views a leaderboard of users, sorted by their balance, descending."""
        async with ctx.channel.typing():
            all_users = await self.bot.pool.fetch(
                "SELECT * FROM e_users ORDER BY bal DESC"
            )
            data = []
            for u in range(5):
                data.append(tuple(all_users)[u])

            embed_color = discord.Color.from_rgb(0, 0, 0)
            try: 
                player = await Player.get(ctx.author.id, self.bot)
                embed_color = player.profile_color
            except NotAPlayerError: pass

            embed = discord.Embed(
                title="User Leaderboard",
                description="Sorted by balance, descending",
                color=embed_color,
            )
            for i in data:
                await asyncio.sleep(0.1)
                embed.add_field(name=f"{i[1]}", value=f"${i[3]}", inline=False)
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(player_meta(bot))
