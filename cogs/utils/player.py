from __future__ import annotations
import typing
import logging
from . import errors
import discord
from discord.ext import commands

log = logging.getLogger(__name__)


async def get(id: int, bot) -> player:
    """Gets a `Player` object from its user id."""
    return await player(id, bot).__ainit__()


class player:
    def __init__(self, id, bot) -> None:
        self.bot = bot
        self.id = id

    async def __ainit__(self):
        data = await self.bot.pool.fetchrow(
            "SELECT * FROM e_users WHERE id = $1", self.id
        )
        if data is None:
            self.exists = False
            raise errors.NotAPlayerError()
        data = tuple(data)
        self.raw_data = data
        self.exists = True
        self.id = int(data[0])
        self.name = str(data[1])
        self.guild_id = -1  # deprecrated
        self.balance = int(data[3])
        self.bal = self.balance
        self.total_earnings = int(data[4])
        # see the @property below for data[5]
        self.lotteries_won = int(data[6])
        return self

    @property
    def profile_color(self):
        return int(("0x" + (self.raw_data[5]).strip()), 0)

    def validate_bet(
        self,
        amount: typing.Union[int, str],
        minimum: int = 1,
        allow_all: bool = True,
        b_max: int = -1,
    ):
        """Validates a players bet to ensure that the player can't bet too much or too little money."""
        if allow_all:
            if isinstance(amount, str) and amount.strip() == "all":
                amount = self.balance
        amount = int(amount)
        if amount != amount:
            raise errors.InvalidBetAmountError("Invalid bet. Nice try, though")
        if self.balance < amount:
            raise errors.InvalidBetAmountError(
                f"That bet is too big. You only have ${self.balance}."
            )
        if amount < minimum:
            raise errors.InvalidBetAmountError(
                f"Too small of a bet. (Minimum ${minimum})"
            )
        if b_max != -1:  # Too large
            if amount > b_max:
                raise errors.InvalidBetAmountError(
                    f"Too large of a bet. (Maximum ${b_max})"
                )
        return amount

    async def refresh(self):
        """Gives you a new object with updated data from database."""
        new_player = await get(self.id, self.bot)
        return new_player

    async def update_balance(
        self,
        amount: int,
        ctx: typing.Union[commands.Context, discord.Interaction],
        ignore_total_earned: bool = False,
    ):
        """Updates player balance.
        `amount` can be positive or negative.
        This will automatically add to total earnings."""
        amount = int(amount)
        temp = self.bal
        temp += amount
        if temp < 0:
            del temp
            raise errors.BalanceUpdateError(
                f"New balance cannot be negative ({self.bal} < 0)"
            )
        self.bal += amount
        await self.bot.pool.execute(
            "UPDATE e_users SET bal = (bal + $1) WHERE id = $2", amount, self.id
        )
        if (amount > 0) or (
            ignore_total_earned
        ):  # we dont want the total earnings to be the same as balance, so dont add negative amounts
            await self.bot.pool.execute(
                "UPDATE e_users SET totalearnings = (totalearnings + $1) WHERE id = $2",
                amount,
                self.id,
            )
        author = None
        command = ctx.command
        if isinstance(ctx, discord.Interaction):
            author = ctx.user
            command = ctx.command
        else:
            author = ctx.author
        i_or_d = "increased" if amount > 0 else "decreased"
        msg = f"{author} ({author.id}) balance {i_or_d} by {amount} with command '{(command.parent.name+'') if command.parent is not None else ''}{command.name}'"
        log.info(msg)

    async def transfer_money(self, amount: int, to: player):
        """Transfers money from one player to another. Automatically refreshes both objects.
        Requires the `to` arg to be a player object."""
        await self.bot.pool.execute(
            "UPDATE e_users SET bal = (bal - $1) WHERE id = $2", amount, self.id
        )
        await self.bot.pool.execute(
            "UPDATE e_users SET bal = (bal + $1) WHERE id = $2", amount, to.id
        )
        now = discord.utils.utcnow()
        log.info(
            f"[{now}] {to.name} ({to.id}) was paid by {self.name} ({self.id}); recieving players balance is now {to.balance + amount} (was {to.balance})"
        )

    async def get_job_data(self):
        """Gets job data because i havent written a class for it yet"""
        data = await self.bot.pool.fetchrow(
            "SELECT * FROM e_jobs WHERE id = $1", self.id
        )
        return tuple(data)

    async def update_name(self, name):
        """Updates name because of username update"""
        await self.bot.pool.execute(
            "UPDATE e_users SET name = $1 WHERE id = $2", name, self.id
        )

    async def get_commands_used(self):
        data = await self.bot.pool.fetchrow(
            "SELECT commandsUsed FROM e_player_stats WHERE id = $1", self.id
        )
        return data.get("commandsused")

    @staticmethod
    async def create(bot, member_object):
        """Adds the user to the database.
        Returns a player object."""
        await bot.pool.execute(
            "INSERT INTO e_users(id, name, bal, totalearnings, profilecolor, lotterieswon) VALUES ($1, $2, 100, 0, 'FFFFFF', 0)",
            member_object.id,
            member_object.name,
        )
        await bot.pool.execute(
            "INSERT INTO e_player_stats(id, gamesPlayed, amountPaid, commandsUsed) VALUES ($1, 0, 0, 0)",
            member_object.id,
        )
        return get(member_object.id, bot=bot)

    def __str__(self) -> str:
        return f"<@{self.id}>"
