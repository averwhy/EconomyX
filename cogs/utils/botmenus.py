from discord.ext import menus
import discord

class PPSource(menus.ListPageSource): # Privacy policy
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, entries):
        embed = discord.Embed(description=entries)
        embed.set_footer(text=f"Page {(menu.current_page + 1)}") # FUCK ZERO INDEXING
        return embed