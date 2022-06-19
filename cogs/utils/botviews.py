from typing import Union
import discord, random, asyncio
from discord.ext import commands
from . import player as Player
# class Hit(discord.ui.Button):
#     def __init__(self):
#         super().__init__(label='Hit', style=discord.ButtonStyle.green, disabled=False)

#     async def callback(self, interaction: discord.ui.Interaction):
        
class Blackjack(discord.ui.View):
    def __init__(self, bot, owner: discord.Member, bet_amount):
        super().__init__()
        self.bot = bot
        self.values = values = {'Two':2, 'Three':3, 'Four':4, 'Five':5, 'Six':6, 'Seven':7, 'Eight':8, 'Nine':9, 'Ten':10, 'Jack':10,'Queen':10, 'King':10, 'Ace':11}
        self.value = None
        self.player_cards = random.choices(list(values.keys()), k=2)
        self.dealer_cards = random.choices(list(values.keys()), k=2)
        self.amount = bet_amount
        self.owner = owner
        self.player_total = 0
        self.dealer_total = 0
        self.dealer_hidden_total = values[self.dealer_cards[1]]
        for c in self.player_cards: self.player_total += values[c]
        for c in self.dealer_cards: self.dealer_total += values[c]
        iter = 0
        for c in self.dealer_cards:
            if iter==0: continue #ignores the first card
            self.dealer_hidden_total += self.values[c]
            iter += 1
        self.file = discord.File("./cogs/assets/cards-clipart.png", filename="cards.png")

    def recalculate_totals(self):
        self.player_total, self.dealer_total, self.dealer_hidden_total = 0, 0, 0
        for c in self.player_cards: self.player_total += self.values[c] 
        for c in self.dealer_cards: self.dealer_total += self.values[c]
        iter = 0
        for c in self.dealer_cards:
            if iter==0: continue
            self.dealer_hidden_total += self.values[c]
            iter += 1

    def readable_player_cards(self) -> str:
        print(self.player_cards)
        to_return = ""
        last_one = len(self.player_cards)
        iter = 0
        for c in self.player_cards:
            if iter == last_one:
                to_return = to_return + c
                continue
            to_return = to_return + c + ", "
            iter += 1
        return to_return
    
    def readable_dealer_cards(self) -> str:
        print(self.dealer_cards)
        to_return = ""
        last_one = len(self.dealer_cards)
        iter = 0
        for c in self.dealer_cards:
            if iter == last_one:
                to_return = to_return + c
                continue
            to_return = to_return + c + ", "
            iter += 1
        return to_return
    
    async def update_embed(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name="Player cards", value=f"{self.readable_player_cards()} ({self.player_total})")
        embed.set_field_at(1, name="Dealer cards", value=f"{self.readable_player_cards()} ({self.dealer_total})", inline=False)
        await interaction.message.edit(attachments=[], embed=embed, view=self)

    async def win(self, interaction: Union[discord.Interaction, commands.Context], button_clicked: int, player_msg: str = "", dealer_msg: str = ""):
        if isinstance(interaction, commands.Context): user = interaction.author
        else: user = interaction.user
        player = await Player.get(user.id, self.bot)
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.set_footer(text=f"You won ${self.amount}!")
        embed.set_field_at(0, name="Player cards", value=f"{self.readable_player_cards()} ({self.player_total}) {player_msg}")
        embed.set_field_at(1, name="Dealer cards", value=f"{self.readable_player_cards()} ({self.dealer_total}) {dealer_msg}", inline=False)
        self.disable_all()
        self.children.pop(2)
        self.style_button(button_clicked, discord.ButtonStyle.success)
        await player.update_balance(self.amount)
        await interaction.message.edit(content=f"{str(self.owner)} won!", attachments=[], embed=embed, view=self)
    
    async def lose(self, interaction: discord.Interaction, button_clicked: int, player_msg: str = "", dealer_msg: str = ""):
        if isinstance(interaction, commands.Context): user = interaction.author
        else: user = interaction.user
        player = await Player.get(user.id, self.bot)
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.set_footer(text=f"You lost ${self.amount}.")
        embed.set_field_at(0, name="Player cards", value=f"{self.player_cards[0]}, {self.player_cards[1]} ({self.player_total}) {player_msg}")
        embed.set_field_at(1, name="Dealer cards", value=f"{self.dealer_cards[0]}, {self.dealer_cards[1]} ({self.dealer_total}) {dealer_msg}", inline=False)
        self.disable_all()
        self.children.pop(2)
        self.style_button(button_clicked, discord.ButtonStyle.success)
        await player.update_balance(self.amount)
        await interaction.message.edit(content=f"{str(self.owner)} lost.", attachments=[], embed=embed, view=self)
    
    async def push(self, interaction: discord.Interaction, button_clicked: int, player_msg: str = "", dealer_msg: str = ""):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.greyple()
        embed.set_footer(text=f"You lost {self.amount}.")
        embed.set_field_at(0, name="Player cards", value=f"{self.player_cards[0]}, {self.player_cards[1]} ({self.player_total}) {player_msg}")
        embed.set_field_at(1, name="Dealer cards", value=f"{self.dealer_cards[0]}, {self.dealer_cards[1]} ({self.dealer_total}) {dealer_msg}", inline=False)
        self.disable_all()
        self.style_button(button_clicked, discord.ButtonStyle.success)
        await interaction.message.edit(content=f"Push! No one won the game.", attachments=[], embed=embed, view=self)

    async def blackjack(self, message: discord.Message):
        await asyncio.sleep(0.2)
        embed = message.embeds[0]
        embed.color = discord.Color.green()
        embed.set_footer(text=f"You won ${self.amount}!")
        embed.set_field_at(0, name="Player cards", value=f"{self.player_cards[0]}, {self.player_cards[1]} ({self.player_total}) **BLACKJACK!!**")
        embed.set_field_at(1, name="Dealer cards", value=f"{self.dealer_cards[0]}, {self.dealer_cards[1]} ({self.dealer_total})", inline=False)
        self.disable_all()
        self.children.pop(2)
        await message.edit(content=f"{str(self.owner)} won the game!", attachments=[], embed=embed, view=self)

    def style_button(self, num, style: discord.ButtonStyle):
        self.children[num].style = style

    def disable_all(self, stop_at=-1, except_for=-1, styles=discord.ButtonStyle.gray):
        iter = 0
        for i in self.children:
            if iter == stop_at: break
            if iter == except_for: continue
            i.disabled = True
            i.style=styles
            iter += 1

    @discord.ui.button(label='Hit', style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner.id: return await interaction.response.send_message("This isn't your game of Blackjack.", ephemeral=True)
        newcard = random.choice(list(self.values.keys()))
        self.player_cards.append(newcard)
        self.recalculate_totals()
        if self.player_total == 21:
            #player blackjack
            await interaction.response.send_message(f"You drew a {newcard}, your new card total is {self.player_total}. Blackjack!", ephemeral=True)
            await self.win(interaction, 0, player_msg="**BLACKJACK!**")
            self.stop()
        elif self.player_total > 21:
            #player bust
            await interaction.response.send_message(f"You drew a {newcard}, your new card total is {self.player_total}. Bust!", ephemeral=True)
            await self.lose(interaction, 0, player_msg="**Bust!**")
            self.stop()
        elif self.player_total < 21:
            #They can still hit or stand
            await interaction.response.send_message(f"You hit and drew a {newcard}, bringing your total to {self.player_total}. Press `Hit` or `Stand` to continue.", ephemeral=True)
            self.recalculate_totals()
            await self.update_embed(interaction)
        return
    
    @discord.ui.button(label='Stand', style=discord.ButtonStyle.primary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button,):
        if interaction.user.id != self.owner.id: return await interaction.response.send_message("This isn't your game of Blackjack.", ephemeral=True)
        if self.dealer_total >= 17 and self.dealer_total < 21:
            #dealer stands
            if self.player_total > self.dealer_total:
                await interaction.response.send_message(f"You stood. The dealer's hidden card was a {self.dealer_cards[0]}, making their total {self.dealer_total}.\nYou win!", ephemeral=True)
                await self.win(interaction, 1, player_msg="**Higher total!**")
                self.stop()
            elif self.player_total < self.dealer_total:
                await interaction.response.send_message(f"You stood. The dealer's hidden card was a {self.dealer_cards[0]}, making their total {self.dealer_total}.\nYou lost. \:(", ephemeral=True)
                await self.lose(interaction, 1, dealer_msg="**Higher total!**")
                self.stop()
            elif self.player_total == self.dealer_total:
                await interaction.response.send_message(f"You stood. The dealer's hidden card was a {self.dealer_cards[0]}, making their total {self.dealer_total}.\nPush! No one won.", ephemeral=True)
                await self.push(interaction, 1, dealer_msg='**Push!**', player_msg='**Push!**')
                self.stop()
        
        elif self.dealer_total > 21:
            #dealer instant bust
            await interaction.response.send_message(f"The dealer drew a {newcard}. Their hidden card was a {self.dealer_cards[0]}, which makes their card total {self.dealer_total}. Dealer bust!", ephemeral=True)
            await self.win(interaction, 1, dealer_msg="**Bust!**")
            self.stop()

        elif self.dealer_total <= 16:
            #dealer draws
            newcard = random.choice(list(self.values.keys()))
            self.dealer_cards.append(newcard)
            self.recalculate_totals()
            if self.dealer_total > 21:
                #dealer busts
                await interaction.response.send_message(f"The dealer drew a {newcard}. Their hidden card was a {self.dealer_cards[0]}, which makes their card total {self.dealer_total}. Dealer bust!", ephemeral=True)
                await self.win(interaction, 1, dealer_msg="**Bust!**")
                self.stop()
            elif self.dealer_total >= 17:
                if self.dealer_total > self.player_total:
                    await interaction.response.send_message(f"The dealer drew a {newcard}. Their hidden card was a {self.dealer_cards[0]}, which makes their card total {self.dealer_total}.\nYou lose. \:(", ephemeral=True)
                    await self.lose(interaction, 1, dealer_msg="**Higher total!**")
                    self.stop()
                elif self.dealer_total < self.player_total:
                    await interaction.response.send_message(f"The dealer drew a {newcard}. Their hidden card was a {self.dealer_cards[0]}, which makes their card total {self.dealer_total}.\nYou win!", ephemeral=True)
                    await self.win(interaction, 1, player_msg="**Higher total!**")
                    self.stop()
            else:
                #dealer draws (again)
                await asyncio.sleep(0.5)
                newcard = random.choice(list(self.values.keys()))
                self.dealer_cards.append(newcard)
                self.recalculate_totals()
                if self.dealer_total > 21:
                    #dealer busts
                    await interaction.response.send_message(f"The dealer drew a {newcard}. Their hidden card was a {self.dealer_cards[0]}, which makes their card total {self.dealer_total}. Dealer bust!", ephemeral=True)
                    await self.win(interaction, 1, dealer_msg="**Bust!**")
                    self.stop()
                elif self.dealer_total >= 17:
                    if self.dealer_total > self.player_total:
                        await interaction.response.send_message(f"The dealer drew a {newcard}. Their hidden card was a {self.dealer_cards[0]}, which makes their card total {self.dealer_total}.\nYou lose. \:(", ephemeral=True)
                        await self.lose(interaction, 1, dealer_msg="**Higher total!**")
                        self.stop()
                    elif self.dealer_total < self.player_total:
                        await interaction.response.send_message(f"The dealer drew a {newcard}. Their hidden card was a {self.dealer_cards[0]}, which makes their card total {self.dealer_total}.\nYou win!", ephemeral=True)
                        await self.win(interaction, 1, player_msg="**Higher total!**")
                        self.stop()
        elif self.dealer_total == 21:
            #dealer blackjacks
            await self.lose(interaction, 1, dealer_msg="**BLACKJACK!**")
            self.stop()
        return
            
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner.id: return await interaction.response.send_message("This isn't your game of Blackjack.", ephemeral=True)
        self.stop()
        await interaction.message.delete()

class X(discord.ui.View):
    """Simple class to offer a delete button"""
    def __init__(self):
        super().__init__()
    
    @discord.ui.button(label="", emoji="\U0001f5d1")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != interaction.user.id: return await interaction.response.send_message("No.", ephemeral=True)
        self.stop()
        await interaction.message.delete()

class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != interaction.user.id: return await interaction.response.send_message("No.", ephemeral=True)
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != interaction.user.id: return await interaction.response.send_message("No.", ephemeral=True)
        self.value = False
        self.stop()