import discord
from discord.ext import commands
import aiosqlite
import sys, os
import traceback
import asyncio
import time
class EcoBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def add_player(self,member_object):
        try:
            await bot.db.execute("INSERT INTO e_users VALUES (?, ?, ?, 100.0, 0.0, 'FFFFFF')",(member_object.id,member_object.name,member_object.guild.id,))
            await bot.db.commit()
            return "Done! View your profile with `^profile`"
        except Exception as e:
            return str(e)
        
    async def get_player(self,id):
        cur = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(id,))
        print(cur)
        data = await cur.fetchone()
        await bot.db.commit()
        if data is None:
            return None
        else:
            return data
        
    async def usercheck(self,id):
        cur = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(id,))
        print(cur)
        data = await cur.fetchone()
        return data is not None
        # False = Not in database
        # True = In database
        
    async def on_bet_win(self,member_object,amount_bet):
        c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_object.id))
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
            c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_object.id))
            data2 = await c.fetchone()
            newbalance = float(data[4])
            
            return [amount_won,newbalance]
        else:
            return None
        
    async def on_bet_loss(self,member_object,amount_bet):
        c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_object.id))
        data = await c.fetchone()
        if data is not None:
            amount_lost = amount_bet
            #update user
            await bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(amount_bet,member_object.id,))
            #then guild updates
            await bot.db.execute("UPDATE e_guilds SET bal = (bal - ?) WHERE id = ?",(amount_bet,data[2],))
            #get new data
            c = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(member_object.id))
            data2 = await c.fetchone()
            newbalance = float(data[4])
            
            return newbalance
        else:
            return None
       
            
bot = EcoBot(command_prefix=commands.when_mentioned_or("^"),intents=discord.Intents(reactions = True, messages = True, guilds = True, members = True))

bot.initial_extensions = ["jishaku","cogs.playermeta","cogs.devtools"]
with open("TOKEN.txt",'r') as t:
    TOKEN = t.readline()
bot.time_started = time.localtime()
bot.version = '0.0.1'
bot.newstext = None
bot.news_set_by = "no one yet.."


async def startup():
    await bot.wait_until_ready()
    bot.db = await aiosqlite.connect('economyx.db')
    
    await bot.db.execute("CREATE TABLE IF NOT EXISTS e_users (id int, name text, guildid int,bal double, totalearnings double, profilecolor text)")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS e_guilds (id int, name text, bal double, totalearnings double)")
    print("Database connected")
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
    elif isinstance(error, discord.ext.commands.errors.NotOwner):
        msgtodelete = await ctx.send("`ERROR: Missing permissions.`")
        await asyncio.sleep(10)
        await msgtodelete.delete()
    else:
        await ctx.send(f"```diff\n- {error}\n```")
        # All other Errors not returned come here. And we can just print the default TraceBack.
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

for cog in bot.initial_extensions:
    try:
        bot.load_extension(f"{cog}")
        print(f"loaded {cog}")
    except Exception as e:
        print(f"Failed to load {cog}, error:\n", file=sys.stderr)
        traceback.print_exc()
asyncio.set_event_loop(asyncio.SelectorEventLoop())
bot.run(TOKEN, bot = True, reconnect = True)