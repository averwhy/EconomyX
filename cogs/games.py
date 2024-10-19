import random
import asyncio
import logging
from .utils.botviews import X
from .utils import player as Player
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from typing import Union
from .utils.errors import NotAPlayerError
OWNER_ID = 267410788996743168

log = logging.getLogger(__name__)

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
    def __str__(self):
        return f"{self.rank} of {self.suit}"
class Deck:
    def __init__(self):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        self.cards = [Card(rank, suit) for rank in ranks for suit in suits]
    def shuffle(self):
        random.shuffle(self.cards)
    def deal(self, amount: int = 1) -> Union[Card, list[Card]]:
        result = []
        for i in range(amount):
            result.append(self.cards.pop())
        return result if amount>1 else result[0]
    @staticmethod
    def get_values(cards: Union[Card, list[Card]]) -> int:
        ace_in_results = False
        total_value = 0
        if not isinstance(cards, list): cards = [cards]
        for card in cards:
            if card.rank not in ('J','Q','K','A'):
                total_value += int(card.rank)
                continue
            elif card.rank == 'A':
                ace_in_results = True
                total_value += 11
                continue
            else:
                total_value += 10 # its either a J, Q or K
                continue
        if ace_in_results and len(cards) > 1:
            if total_value > 21:
                # 11 was added to the total, so we will subtract 10
                # this way it has a value of 1
                total_value -= 10
            else:
                #the value is below 21, no need to change the value
                pass
        
        return total_value
                

class Blackjack(discord.ui.View):
    def __init__(self, bot, ctx: commands.Context, owner: Player.player, bet_amount):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.file = discord.File("./cogs/assets/cards-clipart.png", filename="cards.png")
        self.player = owner
        self.player_bet = bet_amount
        self.player_hand = []
        self.dealer_hand = []

        #Dealing
        self.deck = deck = Deck()
        deck.shuffle()
        self.player_hand = deck.deal(2)
        self.dealer_hand = deck.deal(2)

    @property
    def dealer_total(self):
        return Deck.get_values(self.dealer_hand)
    
    @property
    def player_total(self):
        return Deck.get_values(self.player_hand)

    async def create_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Blackjack")
        p_cards = ", ".join([f"{str(c)}" for c in self.player_hand])
        embed.add_field(name="Player cards", value=f"{p_cards} ({Deck.get_values(self.player_hand)})")
        embed.add_field(name="Dealer cards", value=f"{str(self.dealer_hand[0])}, ?", inline=False)
        embed.set_thumbnail(url="attachment://cards.png")
        self.embed = embed
        return embed

    async def update_embed(self, interaction: discord.Interaction, message_text: str = None, show_dealer_cards: bool = False) -> None:
        embed = self.embed if self.embed != interaction.message.embeds[0] else interaction.message.embeds[0]
        p_cards = ", ".join([f"{str(c)}" for c in self.player_hand])
        embed.set_field_at(0, name="Player cards", value=f"{p_cards} ({Deck.get_values(self.player_hand)})")
        if show_dealer_cards:
            d_cards = ", ".join([f"{str(c)}" for c in self.dealer_hand])
            embed.set_field_at(1, name="Dealer cards", value=f"{d_cards} ({Deck.get_values(self.dealer_hand)})", inline=False)
        else: embed.set_field_at(1, name="Dealer cards", value=f"{str(self.dealer_hand[0])}, ?", inline=False)
        self.embed.set_thumbnail(url="attachment://cards.png")
        try:
            await interaction.response.defer()
        except discord.errors.InteractionResponded:
            pass
        finally:
            await interaction.message.edit(content=message_text, embed=embed, view=self)

    async def win(self, interaction: discord.Interaction, button_clicked: int):
        self.embed.color = discord.Color.green()
        self.embed.set_footer(text=f"You won ${self.player_bet}!")
        self.disable()
        self.children.pop(2)
        self.style_button(button_clicked, discord.ButtonStyle.success)
        await self.player.update_balance(self.player_bet, self.ctx)
        await self.update_embed(interaction, message_text=f"{str(self.player)} won!", show_dealer_cards=True)
        self.stop()
    
    async def lose(self, interaction: discord.Interaction, button_clicked: int):
        self.embed.color = discord.Color.red()
        self.embed.set_footer(text=f"You lost ${self.player_bet}")
        self.disable()
        self.children.pop(2)
        self.style_button(button_clicked, discord.ButtonStyle.success)
        await self.player.update_balance(self.player_bet*-1, self.ctx)
        await self.bot.stats.add('totalbjLost', (abs(self.player_bet))) # adds to totalbjLost stat
        await self.update_embed(interaction, message_text=f"{str(self.player)} lost.", show_dealer_cards=True)
        self.stop()
    
    async def push(self, interaction: discord.Interaction, button_clicked: int):
        self.embed.color = discord.Color.yellow()
        self.embed.set_footer(text=(f"Push! You earn ${abs((self.player_bet) * 0.5)}"))
        self.disable()
        self.children.pop(2)
        self.style_button(button_clicked, discord.ButtonStyle.secondary)
        await self.player.update_balance(abs(self.player_bet*0.5), self.ctx)
        #await interaction.message.edit(content=f"Push!", attachments=[], embed=self.embed, view=self)
        await self.update_embed(interaction, message_text=f"{str(self.player)} pushed!", show_dealer_cards=True)
        self.stop()

    async def blackjack(self, message: discord.Message):
        self.embed.color = discord.Color.brand_green()
        self.embed.set_footer(text=f"BLACKJACK! You won ${abs(self.player_bet)}")
        self.embed.set_thumbnail(url='attachment://cards.png')
        d_cards = ", ".join([f"{str(c)}" for c in self.dealer_hand])
        self.embed.set_field_at(1, name="Dealer cards", value=f"{d_cards} ({Deck.get_values(self.dealer_hand)})", inline=False)
        self.disable()
        self.children.pop(2)
        await self.player.update_balance(abs(self.player_bet), self.ctx)
        await message.edit(content=f"BLACKJACK! {str(self.player)}", attachments=[], embed=self.embed, view=self)
        self.stop()

    def style_button(self, num, style: discord.ButtonStyle):
        self.children[num].style = style

    def disable(self, stop_at=-1, except_for=-1, only=-1, styles=discord.ButtonStyle.gray):
        iter = 0
        for i in self.children:
            if only != -1:
                if iter == only:
                    i.disabled = True
                    i.style=styles
                    break
                else:
                    iter+=1
            else:
                if iter == stop_at: break
                if iter == except_for: continue
                i.disabled = True
                i.style=styles
                iter += 1

    @discord.ui.button(label='Hit', style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            new_card = self.deck.deal()
            self.player_hand.append(new_card)
            if self.player_total == 21:
                await self.blackjack(interaction.message)
                await interaction.response.defer()
                self.stop()
            if self.player_total >= 22:
                await self.lose(interaction, 0)
                self.stop()
            if self.player_total < 21:
                #Continue playing
                self.disable(only=2) # remove cancel button
                await self.update_embed(interaction)
        except Exception as e:
            log.error(f"error in hit: {e}")
        
    
    @discord.ui.button(label='Stand', style=discord.ButtonStyle.primary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button,):
        #We are presuming that the player total is not at or above 21,
        #as it is handled before
        try:
            if self.dealer_total <= 17:
                #Dealer draws
                #Reveal cards first
                self.disable()
                await self.update_embed(interaction, show_dealer_cards=True)
                try: await interaction.response.defer()
                except: pass
                while not (self.dealer_total >= 17) or not (self.dealer_total <= 22):
                    new_card = self.deck.deal()
                    self.dealer_hand.append(new_card)
                    await asyncio.sleep(1.5)
                    if self.dealer_total == 21:
                        #Dealer blackjack
                        await self.lose(interaction, 1)
                        return
                    if self.dealer_total >= 22:
                        #Dealer bust
                        await self.win(interaction, 1)
                        return
                    await self.update_embed(interaction, show_dealer_cards=True)
            #So now we compare player with dealer
            if self.dealer_total > self.player_total:
                #dealer won
                await self.lose(interaction, 1)
                self.stop()
            elif self.dealer_total < self.player_total:
                await self.win(interaction, 1)
                self.stop()
            else: #Theyre equal
                await self.push(interaction, 1)
                self.stop()
        except Exception as e:
            log.error(f"error in stand: {e}")

        
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player.id: return await interaction.response.send_message("This isn't your game of Blackjack.", ephemeral=True)
        self.stop()
        await interaction.message.delete()

class games(commands.Cog, command_attrs=dict(name='Games')):
    """
    Money making games. These are all gambling games at the moment.
    """
    def __init__(self,bot):
        self.bot = bot
        self.dice_emojis = {
            0 : "<:dice_0:950189343727824947>",
            1 : "<:dice_1:950189347490115635>",
            2 : "<:dice_2:950189350249988137>",
            3 : "<:dice_3:950189353194381342>",
            4 : "<:dice_4:950189355929047110>",
            5 : "<:dice_5:950189358554705920>",
            6 : "<:dice_6:950189361159360522"
        }

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        await Player.get(ctx.author.id, self.bot)
        await self.bot.stats.user_add_games(ctx.author)

    async def cog_command_error(self, ctx, error: Exception):
        if isinstance(error, NotAPlayerError):
            return await ctx.send("You dont have a profile! Get one with `e$register`.")
        await ctx.reply(f"A error occured with your game...\n{error}")
    
    @commands.cooldown(1,2,BucketType.user)
    @commands.command(aliases=["b"], description="Bets money. There is a 50/50 chance on winning and losing.")
    async def bet(self, ctx, amount):
        player = await Player.get(ctx.author.id, self.bot)
        amount = player.validate_bet(amount, max=10000)
        
        y = random.choice([True,False])
        if not y:
            amount *= -1

        await player.update_balance(amount, ctx)
        if amount < 0: await self.bot.stats.add('totalbetLost', (abs(amount))) # adds to totalbetLost stat if amount is negative (player lost money)
        await ctx.send(f"You {['lost', 'won'][y]} ${abs(amount)}, new balance: {player.balance + amount}")
            
    @commands.command(aliases=['rl'])
    async def roulette(self, ctx, amount):
        """Roulette gambling command. Starts a propmpt in which the user reacts with the color they wish to bet."""
        player = await Player.get(ctx.author.id, self.bot)
        amount = player.validate_bet(amount, max=10000)
        
        confirm = await ctx.send("Choose one of the 3 colors to bet on `(🔴: 2x, ⚫: 2x, 🟢: 25x)`:")
        rlist = ['🔴', '⚫', '🟢', '❌']
        for r in rlist:
            await confirm.add_reaction(r)
        def check(r, u):
            return r.message.id == confirm.id and str(r.emoji) in rlist and u.id == ctx.author.id
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
        except asyncio.TimeoutError:
            await confirm.delete()
            return await ctx.reply("Timed out after 60s.")
        result = random.choices(rlist, weights=(49.4, 49.4, 1.2, 0), k=1)
        try: await confirm.clear_reactions()
        except discord.Forbidden: pass
        if str(reaction.emoji) == rlist[3]: #cancel
            await confirm.delete()
            return await ctx.reply("Cancelled, you did not lose/gain any money.")
        if result[0] == rlist[2]: # green
            newamount = amount * 25
            await player.update_balance(newamount, ctx)
            return await ctx.send(f"Your choice: {str(reaction.emoji)}, result: {str(result[0])}\n**You won ${int(amount * 35)}!** <a:cookdance:829764800758022175>")
        elif reaction.emoji == result[0]:
            await player.update_balance(amount, ctx)
            return await ctx.send(f"Your choice: {str(reaction.emoji)}, result: {str(result[0])}\nYou won ${amount}!")
        else:
            await player.update_balance((0-amount), ctx)
            await self.bot.stats.add('totalrouletteLost', (abs(amount))) # adds to totalrouletteLost stat
            return await ctx.send(f"Your choice: {str(reaction.emoji)}, result: {str(result[0])}\nYou lost ${int(amount)}.")
        
    
    @commands.group(aliases=["rps"],invoke_without_command=True, description="Rock paper scissors.")
    async def rockpaperscissors(self, ctx, amount, choice):
        """Rock paper scissor game. `amount` is money you want to bet, and choice must be `rock`, `paper`, or `scissor` (singular, no 's)"""
        player = await Player.get(ctx.author.id, self.bot)
        amount = player.validate_bet(amount, max=10000)
        rand = random.randint(0,2)
        summary = ""
        choices = ["paper", "scissor", "rock"]
        if not choice.strip().lower() in choices:
            return await ctx.send("It looks like you didn't specify `rock`, `paper`, or `scissor` (singular, no 's).")
        outcome_list = ["tied with me", "lose", "win"]
        result = (choices.index(choice)+rand)%3
        summary += "I drew {}, you {}.\n".format(choices[result], outcome_list[rand])
        if outcome_list[rand] == "tied with me":
            summary += "You lost no money."
        elif outcome_list[rand] == "lose":
            summary += f"You lost ${amount}."
            await player.update_balance((0-amount), ctx)
            await self.bot.stats.add('totalrpsLost', (abs(amount))) # adds to totalrpsLost stat
        elif outcome_list[rand] == "win":
            summary += f"You won ${amount}"
            await player.update_balance(amount, ctx=ctx)
        await ctx.reply(summary)
            

    @commands.cooldown(1,15,BucketType.user)
    @commands.command(description="Guessing game with money.")
    async def guess(self, ctx, amount: int):
        """Guesing game with money. You have 5 chances to guess the number randomly chosen between 1-10.\nThis amounts to a 50/50 chance."""
        player = await Player.get(ctx.author.id, self.bot)
        amount = player.validate_bet(amount, max=10000)
        
        await ctx.send(f"Alright, your bet is ${amount}. If you lose, you pay that. If you win, you earn that.\nI'm thinking of a number between 1 and 10. You have 5 tries.")
        tries = 5
        guessed_it = False
        the_number = random.randint(1,10)
        while not guessed_it:
            def check(m):
                return m.channel == ctx.channel and m.author == ctx.author

            msg = await self.bot.wait_for('message', check=check)
            try:
                content = int(msg.content)
                if content > 10:
                    await ctx.send("Guess a number **between 1 and 10.**")
                    continue
                if content == the_number:
                    await ctx.send(f"You guessed it! The number was {the_number}.\nAs promised, here's your winnings of ${amount}.")
                    await player.update_balance(amount, ctx)
                    return
                else:
                    tries -= 1
                    if tries == 0:
                        await ctx.send(f"You're out of tries, and haven't guessed my number.\nYou lose ${amount}.")
                        await player.update_balance((0-amount), ctx)
                        await self.bot.stats.add('totalguessLost', (abs(amount))) # adds to totalguessLost stat
                        return
                    await ctx.send(f"That's not it!\nYou have {tries} attempt(s) left.")
            except:
                content = msg.content
                content = content.lower()
                if "cancel" in content:
                    await ctx.send("Guessing game cancelled. You did not lose or gain any money.")
                    return
                else:
                    await ctx.send("Guess a **number**!")
                
    @commands.command(aliases=['bj'], enabled=True)
    async def blackjack(self, ctx, amount):
        """Blackjack card game.
        This has minor changes to work with EconomyX.
        
        The basic premise of the game is the player is dealt 2 cards. The dealer also has 2 cards, however, one is hidden. The goal of the game is to get a combined total of 21 or as close to it as possible. Then player can win when:
        - They have a higher card value total than the dealer, but not higher than 21.
        - They have a card value total of 21.
        - The dealer 'busts' (obtains a card total higher than 21) when drawing another card.
        
        When you 'hit', you're drawing another card. This should be done when your card value total is around 14 or lower.
        When you 'stand', you're keeping the cards you currently have. The dealer will then either reveal their hidden card (if *their*  card total is 17 or higher), or draw another (if their card total is 16 or lower.)"""        
        player = await Player.get(ctx.author.id, self.bot)
        amount = player.validate_bet(amount, minimum=1, max=10000)
        
        bjview = Blackjack(self.bot, ctx, player, amount)
        embed = await bjview.create_embed()
        game_msg = await ctx.send(file=bjview.file, embed=embed, view=bjview)
        if bjview.player_total == 21:
            await asyncio.sleep(0.25)
            await bjview.blackjack(game_msg)
        if bjview.player_total >= 22:
            await bjview.lose()
        if bjview.dealer_total >= 22:
            await bjview.win()
        if await bjview.wait():
            # try: await game_msg.delete()
            # except discord.NotFound: pass # it wouldnt be a forbidden error, since its the bot's own message. it could only
            # be a not found if the message was already deleted before it timed out
            await ctx.send(f"{ctx.author.mention}, your blackjack game timed out.", delete_after=45)

    @commands.command()
    async def craps(self, ctx, amount):
        """Craps betting game. This is a simplified version for EconomyX.
        Two dice are rolled, and added together. If you win, the amount you bet is added to your account. If you lose, the amount you bet is taken from your account.
        - Roll a 7 or 11 and you win.
        - Roll a 2, 3 or 12 and you lose.
        - Roll a 4-6 or 8-10, re-roll until you either roll a 7 and lose, or roll your original roll and win 2x your bet."""
        player = await Player.get(ctx.author.id, self.bot)
        amount = player.validate_bet(amount, minimum=10, max=10000)
        dice1 = random.randrange(1,6)
        dice2 = random.randrange(1,6)
        dices = dice1 + dice2
        rolls = 1

        async def win(amount:int, dice_1, dice_2, main_message) -> None:
            nonlocal ctx
            await player.update_balance(amount, ctx=ctx)
            try: updated_embed = main_message.embeds[0]
            except (ReferenceError, AttributeError):
                updated_embed = discord.Embed(title="Craps", description="").set_footer(text=f"Amount bet: {amount} | Rolls: {rolls}")
            updated_embed.description = f"{updated_embed.description}\nRoll {rolls} | Dice 1: {self.dice_emojis[dice_1]},  Dice 2: {self.dice_emojis[dice_2]} ({(dice_1 + dice_2)})\n\n**You win!**"
            updated_embed.color = discord.Color.green()
            updated_embed.set_footer(text=f"Amount won: ${amount} | Rolls: {rolls}")
            try: 
                await main_message.edit(
                embed=updated_embed, view=X())
            except (ReferenceError, AttributeError):
                await ctx.send(embed=updated_embed, view=X())
            return
        async def loss(amount: int, dice_1, dice_2, main_message) -> None:
            nonlocal ctx
            await player.update_balance((0-amount), ctx=ctx)
            await self.bot.stats.add('totalcrapsLost', (abs(amount))) # adds to totalcrapsLost stat
            try: updated_embed = main_message.embeds[0]
            except (ReferenceError, AttributeError):
                updated_embed = discord.Embed(title="Craps", description="").set_footer(text=f"Amount bet: {amount} | Rolls: {rolls}")
            updated_embed.description = f"{updated_embed.description}\nRoll {rolls} | Dice 1: {self.dice_emojis[dice_1]},  Dice 2: {self.dice_emojis[dice_2]} ({(dice_1 + dice_2)})\n\n**You lost.** \:("
            updated_embed.color = discord.Color.red()
            updated_embed.set_footer(text=f"Amount lost: ${amount} | Rolls: {rolls}")
            try: 
                await main_message.edit(
                embed=updated_embed, view=X())
            except (ReferenceError, AttributeError):
                await ctx.send(embed=updated_embed, view=X())
            return
        async def reroll() -> tuple:
            nonlocal rolls
            rolls += 1
            return (random.randrange(1,6), random.randrange(1,6))

        if dices in [7, 11]:
            return await win(amount, dice1, dice2, None)

        if dices in [2, 3, 12]:
            return await loss(amount, dice1, dice2, None)

        main_message = await ctx.send(embed=discord.Embed(
            title="Craps",
            description=f"Roll {rolls} | Dice 1: {self.dice_emojis[dice1]},  Dice 2: {self.dice_emojis[dice2]} ({dices})"
        ).set_footer(text=f"Amount bet: {amount} | Rolls: {rolls}"))
        
        if dices in [4,5,6,8,9,10]:
            nd1, nd2 = await reroll() #nd = new dice
            nds = nd1 + nd2 #nds = new dices
            while nds != 7:
                if nds == dices: break
                updated_embed = main_message.embeds[0]
                updated_embed.description = f"{updated_embed.description}\nRoll {rolls} | Dice 1: {self.dice_emojis[nd1]},  Dice 2: {self.dice_emojis[nd2]} ({nds})"
                await asyncio.sleep(1)
                try: 
                    await main_message.edit(embed=updated_embed.set_footer(text=f"Amount bet: {amount} | Rolls: {rolls}"))
                except discord.errors.HTTPException:
                    # Too long
                    updated_embed.description = f"...\nRoll {rolls} | Dice 1: {self.dice_emojis[nd1]},  Dice 2: {self.dice_emojis[nd2]} ({nds})"
                    await main_message.edit(embed=updated_embed.set_footer(text=f"Amount bet: {amount} | Rolls: {rolls}"))
                nd1, nd2 = await reroll()
                nds = nd1 + nd2
            await asyncio.sleep(1)
            if nds == 7:
                await loss(amount, nd1, nd2, main_message)
                return
            
            #assume at this point, they rolled their original roll
            await win((amount * 2), nd1, nd2, main_message)
        

async def setup(bot):
    await bot.add_cog(games(bot))