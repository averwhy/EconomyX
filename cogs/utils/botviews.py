import discord, random, asyncio
from discord.ext import commands

# class Hit(discord.ui.Button):
#     def __init__(self):
#         super().__init__(label='Hit', style=discord.ButtonStyle.green, disabled=False)

#     async def callback(self, interaction: discord.ui.Interaction):
        
class Blackjack(discord.ui.View):
    def __init__(self, owner: discord.Member, player_cards, dealer_cards, bet_amount):
        super().__init__()
        self.values = values = {'Two':2, 'Three':3, 'Four':4, 'Five':5, 'Six':6, 'Seven':7, 'Eight':8, 'Nine':9, 'Ten':10, 'Jack':10,'Queen':10, 'King':10, 'Ace':11}
        self.value = None
        self.player_cards = player_cards
        self.dealer_cards = dealer_cards
        self.amount = bet_amount
        self.owner = owner
        self.player_total = values[player_cards[0]] + values[player_cards[1]]
        self.dealer_total = values[dealer_cards[0]] + values[dealer_cards[1]]
        self.dealer_total_without_first_card = values[dealer_cards[1]]

    async def win(self, message: discord.Message):
        embed = message.embeds[0]
        embed.color = discord.Color.green()
        await message.edit(content=f"{str(self.owner)} won the game!", embed=embed)
    async def lose(self, message: discord.Message):
        embed = message.embeds[0]
        embed.color = discord.Color.green()
        await message.edit(content=f"{str(self.owner)} lost the game.", embed=embed)
    async def hit(self, message: discord.Message):
        pass
    async def stand(self, message: discord.Message):
        pass

    def disable_all(self):
        for i in self.children:
            i.disabled = True

    @discord.ui.button(label='Hit', style=discord.ButtonStyle.primary)
    async def hit(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.owner.id: return await interaction.response.send_message("This isn't your game of Blackjack.", ephemeral=True)
        newcard = random.choice(list(self.values.keys()))
        self.player_cards.append(newcard)
        await interaction.response.send_message(f"You drew a {newcard}, your new card total is {self.player_total + self.values[newcard]}", ephemeral=False)
        self.disable_all()
        await interaction.message.edit(view=self)
        await self.stop()
    
    @discord.ui.button(label='Stand', style=discord.ButtonStyle.primary)
    async def stand(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.owner.id: return await interaction.response.send_message("This isn't your game of Blackjack.", ephemeral=True)
        newcard = random.choice(list(self.values.keys()))
        self.player_cards.append(newcard)
        if self.dealer_total >= 17:
            #dealer stands
            await interaction.response.send_message(f"You stood. The dealer's hidden card was a {self.dealer_cards[0]}, making their total {self.dealer_total}", ephemeral=False)
        if self.dealer_total <= 16:
            #dealer draws
            await interaction.response.send_message(f"You stood. The dealer's hidden card was a {self.dealer_cards[0]}", ephemeral=False)
            
        self.disable_all()
        await interaction.message.edit(view=self)
        await self.stop()