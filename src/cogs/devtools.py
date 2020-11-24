import discord
import platform
import time
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
import asyncio
OWNER_ID = 267410788996743168

class devtools(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    async def cog_check(self,ctx):
        return ctx.author.id == OWNER_ID
    
    @commands.group(invoke_without_command=True)
    async def dev(self, ctx):
        #bot dev commands
        await ctx.send("`You're missing one of the below arguements:` ```md\n- reload\n- loadall\n- status <reason>\n- ban <user> <reason>\n```")

    @dev.command(aliases=["r","reloadall"])
    async def reload(self, ctx):
        output = ""
        amount_reloaded = 0
        async with ctx.channel.typing():
            for e in self.bot.initial_extensions:
                try:
                    self.bot.reload_extension(e)
                    amount_reloaded += 1
                except Exception as e:
                    e = str(e)
                    output = output + e + "\n"
            await asyncio.sleep(1)
            if output == "":
                await ctx.send(content=f"`{len(self.bot.initial_extensions)} cogs succesfully reloaded.`") # no output = no error
            else:
                await ctx.send(content=f"`{amount_reloaded} cogs were reloaded, except:` ```\n{output}```") # output

    @dev.command(aliases=["load","l"])
    async def loadall(self, ctx):
        output = ""
        amount_loaded = 0
        async with ctx.channel.typing():
            for e in self.bot.initial_extensions:
                try:
                    self.bot.load_extension(e)
                    amount_loaded += 1
                except Exception as e:
                    e = str(e)
                    output = output + e + "\n"
            await asyncio.sleep(1)
            if output == "":
                await ctx.send(content=f"`{len(self.bot.initial_extensions)} cogs succesfully loaded.`") # no output = no error
            else:
                await ctx.send(content=f"`{amount_loaded} cogs were loaded, except:` ```\n{output}```") # output

    @dev.command()
    async def status(self, ctx, *, text):
        # Setting `Playing ` status
        if text is None:
            await ctx.send(f"{ctx.guild.me.status}")
        if len(text) > 60:
            await ctx.send("`Too long you pepega`")
            return
        try:
            await self.bot.change_presence(activity=discord.Game(name=text))
            await ctx.message.add_reaction("\U00002705")
        except Exception as e:
            await ctx.message.add_reaction("\U0000274c")
            await ctx.send(f"`{e}`")
            
    # @dev.command(aliases=["userban"])
    # async def ban(self, ctx, user1: discord.User = None, *, reason = None):
    #     if user1 is None:
    #         await ctx.send("`You must provide an user ID/Mention!`")
    #     else:
    #         data = await grab_db_user(user1.id)
    #         askmessage = await ctx.send(f"`Are you sure you want to ban` {user1.name} `({user1.id})?`")
    #         await askmessage.add_reaction(emoji="\U00002705") # white check mark
            
    #         def check(reaction, user):
    #             return user == ctx.message.author and str(reaction.emoji) == "\U00002705"
    #         try:
    #             reaction, user = await self.bot.wait_for('reaction_add', timeout=secondstoReact, check=check)
    #         except asyncio.TimeoutError:
    #             await askmessage.edit(content="`Timed out.`")
    #         else:
    #             dbuser = db_user()
    #             await dbuser.db_ban(userobject=user1,reason=reason)
    #             await ctx.send(f"`Banned {user1.name}!`")
    #             banlogs = self.bot.get_channel(771008991748554775)
    #             if banlogs is None:
    #                 banlogs = await self.bot.fetch_channel(771008991748554775)
    #             await banlogs.send(f"__**User ban**__\n**User:** {str(user1)}\n**ID:** {user1.id}\n**Reason:** {reason}\n \n**Banned by:** {ctx.author.mention}")

    # @dev.command(aliases=["userunban"])
    # async def unban(self, ctx,user: discord.User = None):
    #     if user is None:
    #         await ctx.send("`You must provide an user ID/Mention!`")
    #     else:
    #         async with aiosqlite.connect('fishypy.db') as db:
    #             c = await db.execute("SELECT * FROM bannedusers WHERE userid = ?",(user.id,))
    #             data = await c.fetchone()
    #             if data is None:
    #                 await ctx.send("`That user does not appear to be banned.`")
    #             else:
    #                 await db.execute("DELETE FROM bannedusers WHERE userid = ?",(user.id,))
    #                 await db.commit()
    #                 banlogs = self.bot.get_channel(771008991748554775)
    #                 if banlogs is None:
    #                     banlogs = await self.bot.fetch_channel(771008991748554775)
    #                 await banlogs.send(f"__**User unban**__\n**User:** {str(user)}\n**ID:** {user.id}\n \n**Unbanned by:** {ctx.author.mention}")
    #                 await ctx.message.add_reaction("\U00002705")

    @dev.command()
    async def stop(self, ctx):
        askmessage = await ctx.send("`you sure?`")
        def check(m):
            newcontent = m.content.lower()
            return newcontent == 'yea' and m.channel == ctx.channel
        try:
            await self.bot.wait_for('message', timeout=5, check=check)
        except asyncio.TimeoutError:
            await askmessage.edit(content="`Timed out. haha why didnt you respond you idiot`")
        else:
            await askmessage.clear_reactions()
            await ctx.send("`bye`")
            print(f"Bot is being stopped by {ctx.message.author} ({ctx.message.id})")
            await self.bot.db.commit()
            await self.bot.db.close()
            await self.bot.logout()
            
    @dev.command(aliases=["rc"])
    async def resetcooldown(self, ctx, *cmdnames):
        output = ""
        if "all" in cmdnames:
            for c in self.bot.commands:
                try:
                    c._buckets._cooldown.reset()
                    output = output + (f"Cooldown on command {c.name} successfully reset") + "\n"
                except Exception as e:
                    e = str(e)
                    output = output + e + "\n"
        else:
            for c in cmdnames:
                try:
                    cmd = self.bot.get_command(c)       
                    cmd._buckets._cooldown.reset()
                    output = output + (f"Cooldown on command {cmd.name} successfully reset") + "\n"
                except Exception as e:
                    e = str(e)
                    output = output + e + "\n"
        await ctx.send(f"```{output}\n```")
        
    @dev.group(invoke_without_command=True)
    async def sql(self, ctx):
        await ctx.send("`Youre missing one of the below params:` ```md\n- fetchone\n- fetchall\n- run\n```") 
            
    @sql.command()
    async def fetchone(self, ctx, *, statement):
        try:
            c = await self.bot.db.execute(statement)
            data = await c.fetchone()
            await self.bot.db.commit()
            await ctx.send(data)
        except Exception as e:
            await ctx.send(f"```sql\n{e}\n```")
            
    @sql.command()
    async def fetchall(self, ctx, *, statement):
        try:
            c = await self.bot.db.execute(statement)
            data = await c.fetchall()
            await self.bot.db.commit()
            await ctx.send(data)
        except Exception as e:
            await ctx.send(f"```sql\n{e}\n```")
    @sql.command()
    async def run(self, ctx, *, statement):
        try:
            c = await self.bot.db.execute(statement)
            await self.bot.db.commit()
            await ctx.message.add_reaction(emoji="\U00002705")
        except Exception as e:
            await ctx.send(f"```sql\n{e}\n```")
        

def setup(bot):
    bot.add_cog(devtools(bot))