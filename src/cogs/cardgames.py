import discord
import platform
import time
import random
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import CheckFailure, check
OWNER_ID = 267410788996743168

def generate_deck(suites=4, type_cards=13):
    "Generate a randomized deck of cards."
    cards = []
    for suite in range(suites):
        for type_card in range(1, type_cards+1):
            cards.append(type_card)
    random.shuffle(cards)
    return cards

def play_war(deck, ctx):
    a_cards = deck[:len(deck)/2]
    b_cards = deck[len(deck)/2:]
    a_stash = []
    b_stash = []

    rnd = 1
    while a_cards and b_cards:
        # by using pop, we're playing from the end forward
        a_card = a_cards.pop()
        b_card = b_cards.pop()

        if a_card == b_card:
            a_stash.extend([a_card]+a_cards[-3:])
            a_cards = a_cards[:-3]
            a_cards.append(a_stash.pop())

            b_stash.extend([b_card]+b_cards[-3:])
            b_cards = b_cards[:-3]
            b_cards.append(b_stash.pop())
        elif a_card > b_card:
            # ordering of a_stash and b_stash is undefined by game rules
            a_cards = [a_card, b_card] + a_stash + b_stash + a_cards
            a_stash = []
            b_stash = []
        elif b_card > a_card:
            # ordering of a_stash and b_stash is undefined by game rules
            b_cards = [b_card, a_card] + b_stash + a_stash + b_cards
            a_stash = []
            b_stash = []
        rnd += 1

   
class cardgames(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    @commands.cooldown(1,2,BucketType.user)
    @commands.command()
    async def war(self,ctx,amount: float):
       cards = generate_deck()
       
         
        
def setup(bot):
    bot.add_cog(cardgames(bot))