import random
import asyncio
from .utils.botviews import X
from .utils import player as Player
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
OWNER_ID = 267410788996743168

class games(commands.Cog):
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
    
    @commands.cooldown(1,2,BucketType.user)
    @commands.command(aliases=["b"], description="Bets money. There is a 50/50 chance on winning and losing.")
    async def bet(self, ctx, amount):
        player = await Player.get(ctx.author.id, self.bot)
        player.validate_bet(amount)
        if isinstance(amount, str) and amount.strip() == "all":
            amount = player.bal
        
        y = random.choice([True,False])
        if y:
            data = await self.bot.on_bet_win(ctx.author,amount) # returns list
            await ctx.send(f"Won ${amount}\nNew balance: ${(data[1]+amount)}")
        if not y:
            data = await self.bot.on_bet_loss(ctx.author,amount) # returns new balance
            await ctx.send(f"Lost ${amount}\nNew balance: ${(data-amount)}")
            
    @commands.command(aliases=['rl'])
    async def roulette(self, ctx, amount):
        """Roulette gambling command. Starts a propmpt in which the user reacts with the color they wish to bet."""
        player = await Player.get(ctx.author.id, self.bot)
        player.validate_bet(amount)
        
        confirm = await ctx.send("Choose one of the 3 colors to bet on `(🔴: 2x, ⚫: 2x, 🟢: 35x)`:")
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
        result = random.choices(rlist, weights=(48.6, 48.6, 2.799999999999997, 0), k=1)
        if str(reaction.emoji) == rlist[3]: #cancel
            await confirm.delete()
            return await ctx.reply("Cancelled, you did not lose/gain any money.")
        if result[0] == rlist[2]: # green
            newamount = amount * 35
            await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(newamount, ctx.author.id,))
            await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(newamount, ctx.author.id,))
            return await ctx.send(f"Your choice: {str(reaction.emoji)}, result: {str(result[0])}\n**You won BIG!**\nMoney earned: ${int(amount * 35)} (`${int(amount)} x 35`)")
        elif reaction.emoji == result[0]:
            await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount, ctx.author.id,))
            await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(amount, ctx.author.id,))
            return await ctx.send(f"Your choice: {str(reaction.emoji)}, result: {str(result[0])}\n**You won!**\nMoney earned: ${int(amount)}")
        else:
            await self.bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(amount, ctx.author.id,))
            return await ctx.send(f"Your choice: {str(reaction.emoji)}, result: {str(result[0])}\n**You lost.**\nMoney lost: ${int(amount)}")
        
    
    @commands.group(aliases=["rps"],invoke_without_command=True, description="Rock paper scissors.")
    async def rockpaperscissors(self, ctx, amount, choice):
        """Rock paper scissor game. `amount` is money you want to bet, and choice must be `rock`, `paper`, or `scissor` (singular, no 's)"""
        player = await Player.get(ctx.author.id, self.bot)
        player.validate_bet(amount)
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
            await self.bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(amount, ctx.author.id,))
        elif outcome_list[rand] == "win":
            summary += f"You won ${amount}"
            await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount, ctx.author.id,))
            await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(amount, ctx.author.id,))
        await ctx.reply(summary)
            

    @commands.cooldown(1,15,BucketType.user)
    @commands.command(description="Guessing game with money.")
    async def guess(self, ctx, amount: int):
        """Guesing game with money. You have 5 chances to guess the number randomly chosen between 1-10.\nThis amounts to a 50/50 chance."""
        player = await Player.get(ctx.author.id, self.bot)
        player.validate_bet(amount)
        
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
                    await self.bot.db.execute("UPDATE e_users SET bal = (bal + ?) WHERE id = ?",(amount, ctx.author.id,))
                    await self.bot.db.execute("UPDATE e_users SET totalearnings = (totalearnings + ?) WHERE id = ?",(amount,ctx.author.id,))
                    return
                else:
                    tries -= 1
                    if tries == 0:
                        await ctx.send(f"You're out of tries, and haven't guessed my number.\nYou lose ${amount}.")
                        await self.bot.db.execute("UPDATE e_users SET bal = (bal - ?) WHERE id = ?",(amount, ctx.author.id,))
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
        from .utils.botviews import Blackjack
        
        player = await Player.get(ctx.author.id, self.bot)
        player.validate_bet(amount, minimum=10)
        if isinstance(amount, str) and amount.strip() == "all":
            amount = player.bal
        
        bjview = Blackjack(self.bot, ctx.author, amount) # This view does all the work :)
        embed = discord.Embed(title="Blackjack")
        embed.add_field(name="Your cards", value=f"{bjview.player_cards[0]}, {bjview.player_cards[1]} ({bjview.player_total})")
        embed.add_field(name="Dealer cards", value=f"?, {bjview.dealer_cards[1]} ({bjview.dealer_hidden_total})", inline=False)
        file = discord.File("./cogs/assets/cards-clipart.png", filename="cards.png")
        embed.set_thumbnail(url="attachment://cards.png")
        game_message = await ctx.send(file=file, embed=embed, view=bjview)
        if bjview.player_total == 21:
            await bjview.blackjack(ctx.message)
        if bjview.player_total >= 22:
            await bjview.lose()
        if await bjview.wait():
            try: await game_message.delete()
            except discord.NotFound: pass # it wouldnt be a forbidden error, since its the bot's own message. it could only
            # be a not found if the message was already deleted before it timed out
            await ctx.send(f"{ctx.author.mention}, your blackjack game timed out.")
        

    @commands.command()
    async def craps(self, ctx, amount):
        """Craps betting game. This is a simplified version for EconomyX.
        Two dice are rolled, and added together. If you win, the amount you bet is added to your account. If you lose, the amount you bet is taken from your account.
        - Roll a 7 or 11 and you win.
        - Roll a 2, 3 or 12 and you lose.
        - Roll a 4-6 or 8-10, re-roll until you either roll a 7 and lose, or roll your original roll and win 2x your bet."""
        player = await Player.get(ctx.author.id, self.bot)
        player.validate_bet(amount, minimum=10)
        dice1 = random.randrange(1,6)
        dice2 = random.randrange(1,6)
        dices = dice1 + dice2
        rolls = 1

        async def win(amount:int, dice_1, dice_2, main_message) -> None:
            nonlocal ctx
            await ctx.bot.update_balance(ctx.author, amount=amount)
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
            await ctx.bot.update_balance(ctx.author, amount=0-amount)
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