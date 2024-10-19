import typing
import discord
import aiohttp
import logging
from .utils import player as Player
from discord.ext import commands

log = logging.getLogger(__name__)

class Achievement:
    def __init__(self, name, desc):
        self.name = name
        self.desc = desc

AchievementsDict = {
    1: Achievement('Getting Started', 'Play your first game'),
    2: Achievement('Regular Gambler', 'Play 100 games'),
    3: Achievement('Serial Gambler', 'Play 1000 games'),
    4: Achievement('True Gambler', 'Spend all your money (reach 0$)'),
    5: Achievement('Working class', 'Work for the first time'),
    6: Achievement('Blue Collar Worker', 'Reach job level 10'),
    7: Achievement('Workaholic', 'Reach job level 20'),
    8: Achievement('Stonks', '<:stonks:1071087769209806922> Buy your first share in stock'),
    9: Achievement('Day trader', 'Sell shares of a stock that total $1,000 in profit'),
    10: Achievement('Wolf of Wall Street', 'Sell shares of a stock that total $100,000 in profit'),
    11: Achievement('Small buisness', 'Create your first stock'),
    12: Achievement('Insider Trading', 'Invest in your own stock'),
    13: Achievement('$AMZN', 'Get a stock value of 200 points'),
    14: Achievement('$FAZE', 'Get a stock value of 0 points'), 
    15: Achievement('Lucky duck', 'Win a lottery'),
    16: Achievement('Luckiest Duck', 'Win 5 Lotteries'),
    17: Achievement('Lower Class', 'Obtain $10,000 in balance'),
    18: Achievement('Middle Class', 'Obtain $50,000 in balance'),
    19: Achievement('Rich Kid', 'Obtain $150,000 in balance'),
    20: Achievement('Upper Class', 'Obtain $1,000,000 in balance'),
    21: Achievement('The 1%', 'Obtain $10,000,000 in balance'),
    22: Achievement('Billionaire', 'Reach $1,000,000,000 in balance'),
    23: Achievement('Jeff Bezos', 'Obtain $50,000,000,000 in balance'),
    24: Achievement('Kind Heart', 'Pay a total of $10,000'),
    25: Achievement('Regular Donator','Pay a total of $50,000'),
    26: Achievement('Philanthropist', 'Pay a total of $1,000,000'),
    27: Achievement('Successful History', 'Reach a total earned amount of $1,000,000,000,000 (1 Trillion dollars)'),
    28: Achievement('EconomyX Enjoyer','<:gigachad:1071094100998230047> Use 1000 commands with EconomyX'),
    29: Achievement('Dedicated User', '<:gigachad:1071094100998230047> Use 10,000 commands with EconomyX'),
    30: Achievement('#1 Fan', 'Use 100,000 commands with EconomyX <:gigachad:1071094100998230047>'),
}

class achievements(commands.Cog, command_attrs=dict(name='Achievements')):
    """
    Achievements management.
    """
    def __init__(self, bot):
        self.bot = bot
        self.HOOK_TOKEN = open("ACH_WEBHOOK.txt",'r').readline()

    async def has_ach(self, player: typing.Union[discord.Member, discord.User, int], ach_id: int):
        if type(player) != int:
            player = player.id
        c = await self.bot.pool.fetchrow("SELECT * FROM e_achievements WHERE userid = $1 AND achid = $2", player, ach_id)
        if c:
            return False #can't award
        else:
            return True #can award
    
    async def give_ach(self, player: typing.Union[discord.Member, discord.User], ach_id: int):
        if not await self.has_ach(player, ach_id):
            log.info(f"{player.name} already has achievement {ach_id}")
            return
        await self.bot.pool.execute("INSERT INTO e_achievements(userid, achid) VALUES ($1, $2)", player.id, ach_id)
        now = discord.utils.utcnow()
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(self.HOOK_TOKEN, session=session)
            await webhook.send(f"{player.name} got achievement **{(AchievementsDict[ach_id]).name}**! ({discord.utils.format_dt(now)})")
        log.info(f"awarded achievement {ach_id} to {player.name} ({player.id})")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        # Listener for some achievement criterias
        earned_achievements = []
        player = await Player.get(ctx.author.id, self.bot)
        #1
        if ctx.command.cog_name.lower() == 'games':
            if await self.has_ach(ctx.author, 1):
                earned_achievements.append(1)
        #2
        if ctx.command.cog_name.lower() == 'games':
            result = await self.bot.pool.fetchrow("SELECT gamesPlayed from e_player_stats WHERE id = $1", ctx.author.id)
            if (tuple(result)[0]) >= 100:
                if await self.has_ach(ctx.author, 2):
                    earned_achievements.append(2)
        #3
        if ctx.command.cog_name.lower() == 'games':
            result = await self.bot.pool.fetchrow("SELECT gamesPlayed from e_player_stats WHERE id = $1", ctx.author.id)
            if (tuple(result)[0]) >= 1000:
                if await self.has_ach(ctx.author, 3):
                    earned_achievements.append(3)
        #4
        if player.bal == 0:
            if await self.has_ach(ctx.author, 4):
                earned_achievements.append(4)
        #5
        if ctx.command.name == 'work':
            if await self.has_ach(ctx.author, 5):
                earned_achievements.append(5)
        #6
        if ctx.command.name == 'work':
            result = await self.bot.pool.fetchrow("SELECT level FROM e_jobs WHERE id = $1", ctx.author.id)
            if tuple(result)[0] >= 10 and (await self.has_ach(ctx.author, 6)):
                earned_achievements.append(6)
        #7
        if ctx.command.name == 'work':
            result = await self.bot.pool.fetchrow("SELECT level FROM e_jobs WHERE id = $1", ctx.author.id)
            if tuple(result)[0] >= 20 and (await self.has_ach(ctx.author, 7)):
                earned_achievements.append(7)
        #8
        if ctx.command.name == 'invest':
            playerinvests = await self.bot.pool.fetch("SELECT * FROM e_invests WHERE userid = $1", ctx.author.id)
            if len(playerinvests) > 0:
                if await self.has_ach(ctx.author, 8):
                    earned_achievements.append(8)
        #9 is checked on e$invest sell
        #10 is checked on e$invest sell
        #11
        if ctx.command.name == 'create': #e$stock create
            playerstock = await self.bot.get_stock_from_player(ctx.author.id)
            if (playerstock is not None) and (await self.has_ach(ctx.author, 11)):
                earned_achievements.append(11)
        #12
        if ctx.command.name == 'invest':
            playerinvests = await self.bot.pool.fetch("SELECT stockid FROM e_invests WHERE userid = $1", ctx.author.id)
            playerstock = await self.bot.get_stock_from_player(ctx.author.id)
            if playerstock is not None: # it can be none because some people will do e$invest without owning a stock
                owned_stock_id = playerstock[0]
                if owned_stock_id in playerinvests:
                    if await self.has_ach(ctx.author, 12):
                        earned_achievements.append(12)
        #13 is done in the stock update loop
        #14 is done in stock update loop
        #15 is done in lottery loop
        #16 is done in lottery loop
        #17
        if player.bal >= 10000:
            if await self.has_ach(ctx.author, 17):
                earned_achievements.append(17)
        #18
        if player.bal >= 50000:
            if await self.has_ach(ctx.author, 18):
                earned_achievements.append(18)
        #19
        if player.bal >= 150000:
            if await self.has_ach(ctx.author, 19):
                earned_achievements.append(19)
        #20
        if player.bal >= 1000000:
            if await self.has_ach(ctx.author, 20):
                earned_achievements.append(20)
        #21
        if player.bal >= 10000000:
            if await self.has_ach(ctx.author, 21):
                earned_achievements.append(21)
        #22
        if player.bal >= 1000000000:
            if await self.has_ach(ctx.author, 22):
                earned_achievements.append(22)
        #23
        if player.bal >= 50000000000:
            if await self.has_ach(ctx.author, 23):
                earned_achievements.append(23)
        #24
        if ctx.command.name == 'pay':
            result = await self.bot.pool.fetchrow("SELECT amountPaid from e_player_stats WHERE id = $1", ctx.author.id)
            if (tuple(result)[0] >= 10000) and (await self.has_ach(ctx.author, 24)):
                earned_achievements.append(24)
        #25
        if ctx.command.name == 'pay':
            result = await self.bot.pool.fetchrow("SELECT amountPaid from e_player_stats WHERE id = $1", ctx.author.id)
            if (tuple(result)[0] >= 50000) and (await self.has_ach(ctx.author, 25)):
                earned_achievements.append(25)
        #26
        if ctx.command.name == 'pay':
            result = await self.bot.pool.fetchrow("SELECT amountPaid from e_player_stats WHERE id = $1", ctx.author.id)
            if (tuple(result)[0] >= 1000000) and (await self.has_ach(ctx.author, 26)):
                earned_achievements.append(26)
        #27
        if player.total_earnings >= 1000000000000:
            if await self.has_ach(ctx.author, 27):
                earned_achievements.append(27)
        #28
        if await player.get_commands_used() >= 1000:
            if await self.has_ach(ctx.author, 28):
                earned_achievements.append(28)
        #29
        if await player.get_commands_used() >= 10000:
            if await self.has_ach(ctx.author, 29):
                earned_achievements.append(29)
        #30
        if await player.get_commands_used() >= 100000:
            if await self.has_ach(ctx.author, 30):
                earned_achievements.append(30)

        if len(earned_achievements) > 0: # if its not 0, an achievement criteria was met
            msg = ""
            for a in earned_achievements:
                await self.give_ach(ctx.author, a)
                msg = msg + (f"**Achievement get!** {AchievementsDict[a].name}\n*See your achievements with `{ctx.clean_prefix}achievements`*\n")
            await ctx.reply(msg)
        
    async def get_player_ach(self, player):
        result = await self.bot.pool.fetch("SELECT * FROM e_achievements WHERE userid = $1", player.id)
        return tuple(result)

    @commands.group(invoke_without_command=True, name='achievements', aliases=['ach', 'achieve'])
    async def achievement(self, ctx):
        player = await Player.get(ctx.author.id, self.bot)
        achs = await self.get_player_ach(player)
        embed = discord.Embed(title='Achievements', color=player.profile_color)
        for a in achs:
            embed.add_field(name=AchievementsDict[a[1]].name, value=f"{AchievementsDict[a[1]].desc}\nUnlocked {self.bot.utc_calc(a[2], type='R')}")
        if len(achs) == 0:
            embed.description = f"{ctx.author.name} has no achievements yet!"
        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(achievements(bot))