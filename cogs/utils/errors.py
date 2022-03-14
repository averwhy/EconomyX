from discord.ext import commands

class BalanceUpdateError(commands.CommandError):
    pass

class InvalidBetAmountError(commands.CommandError):
    pass

class BlacklistedChannelError(commands.CommandError):
    pass

class BlacklistedUserError(commands.CommandError):
    pass