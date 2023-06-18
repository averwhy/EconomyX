from __future__ import annotations
import typing
from . import errors
import discord
from discord.ext import commands
async def get(id: int, bot):
    return await player(id, bot).__ainit__()

class player:
    def __init__(self, id, bot) -> None:
        self.bot = bot
        self.id = id
    
    async def __ainit__(self):
        cur = await self.bot.db.execute("SELECT * FROM e_users WHERE id = ?",(self.id,))
        data = await cur.fetchone()
        if data is None:
            self.exists = False
            raise errors.NotAPlayerError()
        self.raw_data = data
        self.exists = True
        self.id = int(data[0])
        self.name = str(data[1])
        self.guild_id = int(data[2])
        self.balance = int(data[3])
        self.bal = self.balance
        self.total_earnings = int(data[4])
        # see the @property below for data[5]
        self.lotteries_won = int(data[6])
        return self

    @property
    def profile_color(self):
        return int(("0x" + (self.raw_data[5]).strip()), 0)


    def validate_bet(self, amount: typing.Union[int, str], minimum: int = 1, allow_all: bool = True, max: int = -1):
        """Validates a players bet to ensure that the player can't bet too much or too little money."""
        if allow_all:
            if isinstance(amount, str) and amount.strip() == "all":
                amount = self.balance
        amount = int(amount)
        if amount != amount:
            raise errors.InvalidBetAmountError("Invalid bet. Nice try, though")
        if self.balance < amount:
            raise errors.InvalidBetAmountError(f"That bet is too big. You only have ${self.balance}.")
        if amount < minimum:
            raise errors.InvalidBetAmountError(f"Too small of a bet. (Minimum ${minimum})")
        if max != -1: # There is max
            if amount > max:
                raise errors.InvalidBetAmountError(f"Too large of a bet. (Maximum ${max})")
        return amount
            

    async def refresh(self):
        """Gives you a new object with updated data from database."""
        cur = await self.bot.db.execute("SELECT * FROM e_users WHERE id = ?",(self.id,))
        new_data = await cur.fetchone()
        return player(new_data, self.bot)

    async def update_balance(self, amount: int, ctx: typing.Union[commands.Context, discord.Interaction], ignore_total_earned: bool = False):
        """Updates player balance. 
        `amount` can be positive or negative.
        This will automatically add to total earnings."""
        amount = int(amount)
        temp = self.bal
        temp += amount
        if temp < 0:
            del temp
            raise errors.BalanceUpdateError(f"New balance cannot be negative ({self.bal} < 0)")
        self.bal += amount
        self.bot.previous_balance_cache[self.id] = amount # set previous balance in cache, helps with achievements
        await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount, self.id))
        if (not ignore_total_earned) or (amount < 0): # we dont want the total earnings to be the same as balance, so dont add negative amounts
            await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?", (amount, self.id))
        await self.bot.db.commit()
        author = None
        command = ctx.command
        if isinstance(ctx, discord.Interaction):
            author = ctx.user
        else:
            author = ctx.author
        i_or_d = "increased" if amount > 0 else "decreased"
        now = discord.utils.utcnow()
        print(f"[{now}] {author} ({author.id}) balance {i_or_d} by {amount} with command '{command.name}'")

    async def transfer_money(self, amount: int, to: player):
        """Transfers money from one player to another. Automatically refreshes both objects.
        Requires the `to` arg to be a player object."""
        await self.bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(amount, self.id))
        await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount, to.id))
        await self.bot.db.commit()
        now = discord.utils.utcnow()
        print(f"[{now}] {to.name} ({to.id}) was paid by {self.name} ({self.id}); recieving players balance is now {to.balance + amount} (was {to.balance})")

    async def get_job_data(self):
        """Gets job data because i havent written a class for it yet"""
        cur = await self.bot.db.execute("SELECT * FROM e_jobs WHERE id = ?", (self.id,))
        data = await cur.fetchone()
        return data
    
    async def update_name(self, name):
        """Updates name because of username update"""
        await self.bot.db.execute("UPDATE e_users SET name = ? WHERE id = ?", (name, self.id))
    
    async def get_commands_used(self):
        cur = await self.bot.db.execute("SELECT commandsUsed FROM e_player_stats WHERE id = ?", (self.id,))
        data = await cur.fetchone()
        return data[0]

    @staticmethod
    async def create(bot, member_object):
        """Adds the user to the database.
        Returns a player object."""
        try:
            await bot.db.execute("INSERT INTO e_users VALUES (?, ?, ?, 100, 0, 'FFFFFF', 0)",(member_object.id,member_object.name,member_object.guild.id,))
            await bot.db.commit()
            data = await (await bot.db.execute("SELECT * FROM e_users WHERE id = ?", (member_object.id,))).fetchone()
            return player(bot)
        except Exception as e:
            return str(e)