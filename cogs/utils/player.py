from __future__ import annotations

async def usercheck(self, uid, bot):
    """Checks if an user exists in the database"""
    cur = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(uid,))
    data = await cur.fetchone()
    return data is not None
    # False = Not in database
    # True = In database

class BalanceUpdateError(Exception):
    pass

class player:
    def __init__(self, data, bot) -> None:
        self.raw_data = data
        self.id = int(data[0])
        self.name = str(data[1])
        self.guild_id = int(data[2])
        self.balance = int(data[3])
        self.bal = self.balance
        self.total_earnings = int(data[4])
        # see the @property below for data[5]
        self.lotteries_won = int(data[6])

        self.bot = bot

    @property
    def profile_color(self):
        return int(("0x" + (self.raw_data[5]).strip()), 0)

    async def refresh(self, data):
        """Gives you a new object with updated data from database."""
        cur = await self.bot.db.execute("SELECT * FROM e_users WHERE id = ?",(self.id,))
        new_data = await cur.fetchone()
        return player(new_data, self.bot)

    async def update_balance(self, amount: int):
        """Updates player balance. 
        `amount` can be positive or negative.
        This will automatically add to total earnings."""
        self.bal += amount
        if self.bal < 0:
            raise BalanceUpdateError(f"Balance cannot be negative ({self.bal} < 0)")
        
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
    async def create(self, bot, member_object):
        """Adds the user to the database.
        Returns a player object."""
        try:
            await bot.db.execute("INSERT INTO e_users VALUES (?, ?, ?, 100, 0, 'FFFFFF', 0)",(member_object.id,member_object.name,member_object.guild.id,))
            await bot.db.commit()
            data = await (await bot.db.execute("SELECT * FROM e_users WHERE id = ?", (member_object.id,))).fetchone()
            return player(data, bot)
        except Exception as e:
            return str(e)