import typing
import discord
from discord.ext import commands

class InvalidStatistic(commands.CommandError):
    pass

class statistics(commands.Cog):
    """
    EconomyX statistics tracking.
    """
    def __init__(self, bot):
        self.bot = bot
    
    async def add(self, stat_name: str, amount: int = 1):
        """Adds a given amount to a statistic value. Default is 1."""
        results = await (await self.bot.db.execute("SELECT statname FROM e_bot_stats")).fetchall()
        valid_stats = [s[0] for s in results]
        if stat_name not in valid_stats:
            print("invalid moment")
            raise InvalidStatistic(f"{stat_name} is not a valid statistic to add to")
        stat_name = stat_name.strip()
        amount = int(amount)
        await self.bot.db.execute(f"UPDATE e_bot_stats SET statvalue = (statvalue + ?) WHERE statname = ?", (amount, stat_name))
        await self.bot.db.commit()

    @commands.command()
    async def stats(self, ctx):
        embed = discord.Embed(title='EconomyX Statistics', description="Note: Stats are accurate as of the 6/17/2023 reset.\nObviously the stats look weird, they are accurate but a WIP for appearance \n*-developer averwhy*",color=discord.Color.from_rgb(0,0,0))
        results = await (await self.bot.db.execute("SELECT * FROM e_bot_stats")).fetchall()
        for e in results:
            embed.add_field(name=e[0], value=f"{e[1]}\n({self.bot.utc_calc(e[2],type='R')})")
        
        await ctx.send(embed=embed)
        

    async def cog_load(self):
        await self.bot.db.execute("CREATE TABLE IF NOT EXISTS e_bot_stats (statname string, statvalue int, trackingsince blob)")
        # need to make sure essential bot stats are in place
        cur = await self.bot.db.execute("SELECT * FROM e_bot_stats")
        result = await cur.fetchall()
        if len(result) == 0:
            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totalLost', 0, ?)", (discord.utils.utcnow(),))
            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totalbetLost', 0, ?)", (discord.utils.utcnow(),))
            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totalbjLost', 0, ?)", (discord.utils.utcnow(),))
            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totalcrapsLost', 0, ?)", (discord.utils.utcnow(),))
            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totalguessLost', 0, ?)", (discord.utils.utcnow(),))
            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totalrpsLost', 0, ?)", (discord.utils.utcnow(),))
            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totalrouletteLost', 0, ?)", (discord.utils.utcnow(),))

            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totalinvestLost', 0, ?)", (discord.utils.utcnow(),))
            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totalstocksInvested', 0, ?)", (discord.utils.utcnow(),))
            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totalPaid', 0, ?)", (discord.utils.utcnow(),))
            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totalLotteries', 0, ?)", (discord.utils.utcnow(),))
            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totallotteryTicketsBought', 0, ?)", (discord.utils.utcnow(),))
            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totalprofilesViewed', 0, ?)", (discord.utils.utcnow(),))

            await self.bot.db.execute("INSERT INTO e_bot_stats VALUES ('totalCommands', 0, ?)", (discord.utils.utcnow(),))
        self.bot.stats = self
    
    async def cog_unload(self):
        self.bot.stats = None

    @commands.Cog.listener()
    async def on_command(self, ctx):
        await self.add('totalCommands') # adds 1 to totalCommands

async def setup(bot):
    await bot.add_cog(statistics(bot))