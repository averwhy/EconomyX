from __future__ import annotations

async def usercheck(self, uid, bot):
    """Checks if an user exists in the database"""
    cur = await bot.db.execute("SELECT * FROM e_users WHERE id = ?",(uid,))
    data = await cur.fetchone()
    return data is not None
    # False = Not in database
    # True = In database

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

    async def refresh(self, data = None):
        """Automatically refreshes object with data from database.
        Optionally updates database entry if data is provided."""

    async def update_balance(self, amount):
        """Updates player balance. 
        `amount` can be positive or negative.
        This will automatically add to total earnings."""

    async def transfer_money(self, amount: int, to: player):
        """Transfers money from one player to another. Automatically refreshes both objects.
        Requires the `to` arg to be a player object."""

    @staticmethod
    async def create(self, userid):
        """Adds the user to the database.
        Returns a player object."""