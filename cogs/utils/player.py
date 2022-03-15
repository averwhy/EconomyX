from __future__ import annotations
from bot import EcoBot
import errors

class player:
    def __init__(self, bot: EcoBot) -> None:
        self.bot = bot

    
    async def __ainit__(self, bot):
        cur = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(id,))
        data = await cur.fetchone()
        self.raw_data = data
        self.id = int(data[0])
        self.name = str(data[1])
        self.guild_id = int(data[2])
        self.balance = int(data[3])
        self.bal = self.balance
        self.total_earnings = int(data[4])
        # see the @property below for data[5]
        self.lotteries_won = int(data[6])

    @property
    def profile_color(self):
        return int(("0x" + (self.raw_data[5]).strip()), 0)

    async def validate_bet(self, amount: int, minimum: int = 1):
        if amount != amount:
            raise errors.InvalidBetAmountError("Invalid bet. Nice try, though")
        if player[3] < amount:
            raise errors.InvalidBetAmountError(f"That bet is too big. You only have ${player[3]}.")
        if amount < minimum:
            raise errors.InvalidBetAmountError(f"Too small of a bet. (Minimum {minimum})")

    async def refresh(self):
        """Gives you a new object with updated data from database."""
        cur = await self.bot.db.execute("SELECT * FROM e_users WHERE id = ?",(self.id,))
        new_data = await cur.fetchone()
        return player(new_data, self.bot)

    async def update_balance(self, amount: int):
        """Updates player balance. 
        `amount` can be positive or negative.
        This will automatically add to total earnings."""
        temp = self.bal
        temp += amount
        if temp < 0:
            del temp
            raise errors.BalanceUpdateError(f"New balance cannot be negative ({self.bal} < 0)")
        self.bal += amount
        
        await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount, self.id))
        await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?", (amount, self.id))
        await self.bot.db.commit()

    async def transfer_money(self, amount: int, to: player):
        """Transfers money from one player to another. Automatically refreshes both objects.
        Requires the `to` arg to be a player object."""
        await self.bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(amount, self.id))
        await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount, to.id))
        await self.bot.db.commit()

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