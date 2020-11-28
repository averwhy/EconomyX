import discord
from discord.ext import commands
import aiosqlite
import sys, os
import traceback
import asyncio
import time
import random
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True" 
os.environ["JISHAKU_HIDE"] = "True"

desc = "EconomyX is a money system for Discord. It's straightfoward with only economy related commands, to keep it simple. I was made by averwhy#3899."

class EcoBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def add_player(self,member_object):
        try:
            await bot.db.execute("INSERT INTO e_users VALUES (?, ?, ?, 100.0, 0.0, 'FFFFFF')",(member_object.id,member_object.name,member_object.guild.id,))
            # then update guild balance
            await bot.db.execute("UPDATE e_guilds SET bal = (bal + 100) WHERE id = ?",(member_object.guild.id,))
            await bot.db.commit()
            return "Done! View your profile with `^profile`"
        except Exception as e:
            return str(e)
        
    async def get_player(self,id):
        cur = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(id,))
        data = await cur.fetchone()
        await bot.db.commit()
        return data
        
    async def usercheck(self,id):
        cur = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(id,))
        data = await cur.fetchone()
        return data is not None
        # False = Not in database
        # True = In database
        
    async def on_bet_win(self,member_object,amount_bet):
        c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_object.id,))
        data = await c.fetchone()
        if data is not None:
            amount_won = amount_bet * 2
            #update user
            await bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount_bet,member_object.id,))
            await bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(amount_bet,member_object.id,))
            #then guild updates
            await bot.db.execute("UPDATE e_guilds SET bal = (bal + ?) WHERE id = ?",(amount_bet,data[2],))
            await bot.db.execute("UPDATE e_guilds SET totalearnings = (totalearnings + ?) WHERE id = ?",(amount_bet,data[2],))
            #get new data
            c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_object.id,))
            await bot.db.commit()
            data2 = await c.fetchone()
            newbalance = float(data[3])
            
            return [amount_won,newbalance]
        else:
            return None
        
    async def on_bet_loss(self,member_object,amount_bet):
        c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_object.id,))
        data = await c.fetchone()
        if data is not None:
            amount_lost = amount_bet
            #update user
            await bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(amount_bet,member_object.id,))
            #then guild updates
            await bot.db.execute("UPDATE e_guilds SET bal = (bal - ?) WHERE id = ?",(amount_bet,data[2],))
            #get new data
            c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_object.id,))
            await bot.db.commit()
            data2 = await c.fetchone()
            newbalance = float(data[3])
            
            return newbalance
        else:
            return None
    async def transfer_money(self,member_paying,member_getting_paid,amount):
        c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_paying.id,))
        data1 = await c.fetchone()
        c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_getting_paid.id,))
        data2 = await c.fetchone()
        #update users
        await bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(amount,member_paying.id,))
        await bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount,member_getting_paid.id,))
        #then guilds update
        await bot.db.execute("UPDATE e_guilds SET bal = (bal - ?) WHERE id = ?",(amount,data1[2],))
        await bot.db.execute("UPDATE e_guilds SET bal = (bal + ?) WHERE id = ?",(amount,data2[2],))
        
        await bot.db.commit()
       
            
bot = EcoBot(command_prefix=commands.when_mentioned_or("^","ecox ","ex "),intents=discord.Intents(reactions = True, messages = True, guilds = True, members = True))

bot.initial_extensions = ["jishaku","cogs.player_meta","cogs.devtools","cogs.games","cogs.money_meta","cogs.misc","cogs.jobs"]
with open("TOKEN.txt",'r') as t:
    TOKEN = t.readline()
bot.time_started = time.localtime()
bot.version = '0.1.1'
bot.newstext = None
bot.news_set_by = "no one yet.."
bot.total_command_errors = 0
bot.total_command_completetions = 0


async def startup():
    await bot.wait_until_ready()
    bot.db = await aiosqlite.connect('economyx.db')
    await bot.db.execute("CREATE TABLE IF NOT EXISTS e_users (id int, name text, guildid int,bal double, totalearnings double, profilecolor text)")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS e_guilds (id int, name text, bal double, totalearnings double)")
    print("Database connected")
    
    bot.backup_db = await aiosqlite.connect('ecox_backup.db')
    print("Backup database is ready")
    await bot.backup_db.close()
bot.loop.create_task(startup())

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('---------------------------------')
    
@bot.event
async def on_command(command):
    await bot.db.commit() # just cuz
    
@bot.event
async def on_command_error(ctx, error): # this is an event that runs when there is an error
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        #await ctx.message.add_reaction("\U00002753") # red question mark         
        return
    elif isinstance(error, discord.ext.commands.errors.CommandOnCooldown): 
        s = round(error.retry_after,2)
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
        msgtodelete = await ctx.send(f"`ERROR: Youre on cooldown for {s}!`")
        await asyncio.sleep(15)
        await msgtodelete.delete()
        return
    elif isinstance(error, commands.CheckFailure):
        # these will be handled in cogs
        return
    else:
        await ctx.send(f"```diff\n- {error}\n```")
        # All other Errors not returned come here. And we can just print the default TraceBack.
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

@bot.event
async def on_guild_join(guild):
    c = await bot.db.execute("SELECT * FROM e_guilds WHERE id = ?",(guild.id,))
    data = await c.fetchone()
    if data is None:
        await bot.db.execute("INSERT INTO e_guilds VALUES (?,?,0,0)",(guild.id,guild.name,))
    if data is not None:
        #already in database
        pass

for cog in bot.initial_extensions:
    try:
        bot.load_extension(f"{cog}")
        print(f"loaded {cog}")
    except Exception as e:
        print(f"Failed to load {cog}, error:\n", file=sys.stderr)
        traceback.print_exc()
asyncio.set_event_loop(asyncio.SelectorEventLoop())
bot.run(TOKEN, bot = True, reconnect = True)