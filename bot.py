import discord
from discord.ext import commands
import aiosqlite
import sys, os
import traceback
import asyncio
import time
import typing
from datetime import datetime
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True" 
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"

desc = "EconomyX is a money system for Discord. It's straightfoward with only economy related commands, to keep it simple. I was made by averwhy#3899."

class EcoBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def prompt(self, authorid, message: discord.Message, *, timeout=60.0, delete_after=True, author_id=None):
        """Credit to Rapptz
        https://github.com/Rapptz/RoboDanny/blob/715a5cf8545b94d61823f62db484be4fac1c95b1/cogs/utils/context.py#L93"""
        confirm = None

        for emoji in ('\N{WHITE HEAVY CHECK MARK}', '\N{CROSS MARK}'):
            await message.add_reaction(emoji)

        def check(payload):
            nonlocal confirm
            if payload.message_id != message.id or payload.user_id != authorid:
                return False
            codepoint = str(payload.emoji)
            if codepoint == '\N{WHITE HEAVY CHECK MARK}':
                confirm = True
                return True
            elif codepoint == '\N{CROSS MARK}':
                confirm = False
                return True
            return False

        try:
            await bot.wait_for('raw_reaction_add', check=check, timeout=timeout)
        except asyncio.TimeoutError:
            confirm = None

        try:
            if delete_after:
                await message.delete()
        finally:
            return confirm

    async def add_player(self,member_object):
        """Adds a player to the database"""
        try:
            await bot.db.execute("INSERT INTO e_users VALUES (?, ?, ?, 100, 0, 'FFFFFF', 0)",(member_object.id,member_object.name,member_object.guild.id,))
            await bot.db.commit()
            return f"Done! View your profile with `{self.default_prefix}profile`"
        except Exception as e:
            return str(e)
        
    async def get_player(self,id):
        """Gets a player from the database"""
        cur = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(id,))
        data = await cur.fetchone()
        await bot.db.commit()
        return data
    
    async def get_stock(self, name_or_id):
        """Gets a stock from the database. Checks both name and ID."""
        cur = await bot.db.execute("SELECT * FROM e_stocks WHERE stockid = ?",(name_or_id,))
        data = await cur.fetchone()
        if data is None:
            cur = await bot.db.execute("SELECT * FROM e_stocks WHERE name = ?",(name_or_id,))
            data = await cur.fetchone()
        await bot.db.commit()
        return data
    
    async def get_stock_from_player(self, user):
        """Gets a stock from the database. Takes a user/member object."""
        cur = await bot.db.execute("SELECT * FROM e_stocks WHERE ownerid = ?",(user.id,))
        data = await cur.fetchone()
        await bot.db.commit()
        return data
    
    async def begin_user_deletion(self, ctx, i_msg):
        """Begins the user deletion process."""
        player = await self.get_player(ctx.author.id)
        if player is None: return
        def check(m):
            return m.content.lower() == 'yes' and m.channel == ctx.channel and m.author == ctx.author
        user_response = await bot.wait_for('message', check=check)
        msg = await ctx.send(
        """**If you proceed, you will __permanently__ lose the following data:**
            - Your profile (money, total earned amount, custom color, etc)
            - Your invests (money invested, etc)
            - Any owned stock (The fee spent to create it, its points, etc (all investers get refunded))
        *All* data involving you will be deleted.
        **Are you sure you would like to continue?** ***__There is no going back.__***
        """)
        did_they = await self.prompt(ctx.author.id, msg, timeout=30, delete_after=False)
        if did_they:
            await bot.db.execute("DELETE FROM e_users WHERE id = ?",(ctx.author.id,))
            await bot.db.execute("DELETE FROM e_invests WHERE userid = ?",(ctx.author.id,))
            await bot.db.execute("DELETE FROM e_stocks WHERE ownerid = ?",(ctx.author.id,))
            await ctx.send("Okay, it's done. According to my database, you no longer exist.\nThank you for using EconomyX. \U0001f5a4\U0001f90d")
        if not did_they:
            await ctx.send("Phew, canceled. None of your data was deleted.")
        if did_they is None: return
        await msg.delete()
        return
        
    async def usercheck(self,uid):
        """Checks if an user exists in the database"""
        cur = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(uid,))
        data = await cur.fetchone()
        return data is not None
        # False = Not in database
        # True = In database
        
    async def on_bet_win(self,member_object,amount_bet):
        """This is called when an user wins at the bet game."""
        c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_object.id,))
        data = await c.fetchone()
        if data is not None:
            amount_won = amount_bet * 2
            #update user
            await bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount_bet,member_object.id,))
            await bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(amount_bet,member_object.id,))
            #get new data
            c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_object.id,))
            await bot.db.commit()
            data2 = await c.fetchone()
            newbalance = float(data[3])
            
            return [amount_won,newbalance]
        else:
            return None
        
    async def on_bet_loss(self,member_object,amount_bet):
        """This is called when an user loses at the bet game."""
        c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_object.id,))
        data = await c.fetchone()
        if data is not None:
            amount_lost = amount_bet
            #update user
            await bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(amount_bet,member_object.id,))
            #get new data
            c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_object.id,))
            await bot.db.commit()
            data2 = await c.fetchone()
            newbalance = float(data[3])
            
            return newbalance
        else:
            return None
        
    async def update_balance(self, userobj, **kwargs):
        """Updates balance."""
        
        player = await bot.get_player(userobj.id)
        if player is None:
            return False
        amount = kwargs['amount'] # Required
        try:
            #Optional:
            reason = kwargs['reason'] # str
            id_override = kwargs['id_override'] # int
            earned_update = kwargs['update_earned'] # bool
        except KeyError:
            pass
        
        await bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount, userobj.id))
        if amount > 0:
            #They gained money, update total gained
            await bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(amount,userobj.id,))
    
    async def transfer_money(self,member_paying: typing.Union[discord.User, discord.Member] ,member_getting_paid: typing.Union[discord.User, discord.Member],amount):
        """Transfers money from one player to another."""
        c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_paying.id,))
        data1 = await c.fetchone()
        c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_getting_paid.id,))
        data2 = await c.fetchone()
        #update users
        await bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(amount,member_paying.id,))
        await bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount,member_getting_paid.id,))
        await bot.db.commit()
        
    async def get_player_color(self, memberobject):
        """Gets a players custom color."""
        player = await bot.get_player(memberobject.id)
        if player is None:
            return None
        else:
            return int(("0x"+player[5]),0)
        
    def utc_calc(self, timestamp: str):
        """Returns a pretty format of the amount of time ago from a given UTC Timestamp."""
        delta_uptime = datetime.utcnow() - datetime.strptime(timestamp,"%Y-%m-%d %H:%M:%S.%f")
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        return [days, hours, minutes, seconds]
    
    def lottery_countdown_calc(self, timestamp:str): # thanks pikaninja
        delta_uptime =  datetime.strptime(timestamp,"%Y-%m-%d %H:%M:%S.%f") - datetime.utcnow()
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        return [days, hours, minutes, seconds]

async def get_prefix(bot, message):
    return bot.prefixes.get(message.author.id, bot.default_prefix)
              
bot = EcoBot(command_prefix=get_prefix,description=desc,intents=discord.Intents(reactions=True, messages=True, guilds=True, members=True, message_content=True))

bot.initial_extensions = ["jishaku","cogs.player_meta","cogs.devtools","cogs.games","cogs.money_meta","cogs.misc","cogs.jobs","cogs.stocks","cogs.jsk_override", "cogs.lottery"]
with open("TOKEN.txt",'r') as t:
    TOKEN = t.readline()
bot.time_started = time.localtime()
bot.version = '0.4.0'
bot.newstext = None
bot.news_set_by = "no one yet.."
bot.total_command_errors = 0
bot.total_command_completetions = 0
bot.launch_time = datetime.utcnow()
bot.maintenance = False
bot.updates_channel = 798014940086403083
bot.default_prefix = "e$"
print(bot.launch_time)

async def startup():
    bot.db = await aiosqlite.connect('economyx.db')
    await bot.db.execute("CREATE TABLE IF NOT EXISTS e_users (id int, name text, guildid int, bal int, totalearnings int, profilecolor text, lotterieswon int)")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS e_stocks (stockid int, name text, points double, previouspoints double, ownerid int, created text, icon_url blob)")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS e_invests (stockid int, userid int, invested int, stockname text, invested_at double, invested_date blob)")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS e_lottery_users (userid int, username text, boughtwhen blob)")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS e_lottery_main (drawingwhen blob, drawingnum int)")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS e_prefixes (userid int, prefix blob, setwhen blob)")
    #await bot.db.execute("CREATE TABLE IF NOT EXISTS e_crypto (userid int)")
    print("Database connected")
    
    bot.backup_db = await aiosqlite.connect('ecox_backup.db')
    print("Backup database is ready")
    await bot.backup_db.close()
    
    cur = await bot.db.execute("SELECT * FROM e_prefixes")
    bot.prefixes = {user_id: prefix for user_id, prefix in (await cur.fetchall())}
bot.loop.create_task(startup())

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('---------------------------------')
    
@bot.event
async def on_command_completion(command):
    await bot.db.commit() # just cuz
    bot.total_command_completetions += 1
    
class MaintenenceActive(commands.CheckFailure):
    pass
    
@bot.check
async def maintenance_mode(ctx):
    if bot.maintenance and ctx.author.id != 267410788996743168:
        raise MaintenenceActive()
    return True
    
@bot.event
async def on_command_error(ctx, error): # this is an event that runs when there is an error
    if isinstance(error, MaintenenceActive):
        embed = discord.Embed(description="Sorry, but maintenance mode is active. EconomyX will be back soon!",color=discord.Color(0xffff00))
        await ctx.send(embed=embed, delete_after=60)
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):      
        return
    elif isinstance(error, discord.ext.commands.errors.CommandOnCooldown): 
        s = round(error.retry_after,2) # todo: convert to humanize instead of this dumb math
        if s > 3600: # over 1 hour
            s /= 3600
            s = round(s,1)
            s = f"{s} hour(s)"
        elif s > 60: # over 1 minute
            s /= 60
            s = round(s,2)
            s = f"{s} minute(s)"
        else: #below 1 min
            s = f"{s} seconds"
        await ctx.send(f"`ERROR: Youre on cooldown for {s}!`", delete_after=15)
        return
    elif isinstance(error, commands.CheckFailure):
        # these should be handled in cogs
        return
    elif isinstance(error, ValueError):
        return await ctx.send("It looks like that's an invalid amount.")
    else:
        bot.total_command_errors += 1
        await ctx.send(f"```diff\n- {error}\n```")
        # All other Errors not returned come here. And we can just print the default TraceBack.
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

for cog in bot.initial_extensions:
    success, failed = 0
    try:
        bot.load_extension(f"{cog}")
        success += 1
    except Exception as e:
        print(f"Failed to load {cog}, error:\n", file=sys.stderr)
        failed += 1
        traceback.print_exc()
    print(f"loaded {success} cogs successfully, with {failed} failures.")
        
asyncio.set_event_loop(asyncio.SelectorEventLoop())
bot.run(TOKEN)