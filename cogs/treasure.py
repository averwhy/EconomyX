import discord
import random
import humanize
import logging
from typing import Union
from asyncpg import Record
from datetime import timedelta
from discord.ext import commands
from discord.ext.commands import Context
from .utils import player as Player
from .utils.botviews import X, Confirm
from datetime import datetime

OWNER_ID = 267410788996743168
CHECK = "\U00002705"

log = logging.getLogger(__name__)

class Perk:
    def __init__(self, id: int, name: str, desc: str, cost: int, uses: int):
        self.id = id
        self.name = name
        self.description = desc
        self.cost = cost
        self.uses = uses

    @staticmethod
    def get(perk_id: int):
        """Gets a Perk object from a given ID"""
        return PERKS[perk_id]

class Ore:
    def __init__(self, id: int, name: str, sellcost: int, rarity: float):
        self.id = id
        self.name = name
        self.sell_cost = sellcost
        self.rarity = rarity

    @staticmethod
    def get(ore_id: int):
        """Gets a Ore object from a given ID"""
        return REWARDS[ore_id]

class Shovel:
    def __init__(self, id: int, name: str, price: int, multiplier: float):
        self.id = id
        self.name = name
        self.price = price
        self.multiplier = multiplier

    def dig(self, has_perk_2: bool = False) -> tuple:
        """Algorithim to generate the amount of ores to mine, randomly selects based on probability, then returns them as a list"""
        probabilities = [0.26] + [0.74 / 8] * 8  # 26% for 0, rest evenly spread
        scale = self.id / 40
        quantity_multiplier = 1
        if has_perk_2:
            quantity_multiplier = 2
        for i in range(1, 5):
            probabilities[i] *= 1 - scale
        for i in range(5, 9):
            probabilities[i] *= scale
        total = sum(probabilities)
        probabilities = [p / total for p in probabilities]
        ore_count = random.choices(range(9), weights=probabilities)[0]
        return random.choices(
            REWARDS,
            weights=[O.rarity for O in REWARDS],
            k=ore_count * quantity_multiplier,
        )

    @staticmethod
    def get(shovel_id: int):
        """Gets a Shovel object from a given ID"""
        return SHOVELS[shovel_id]

SHOVELS = (
    Shovel(0, "Wooden Spoon", 0, 0.5),
    Shovel(1, "Clay Spoon", 500, 0.55),
    Shovel(2, "Limestone Spade", 900, 0.58),
    Shovel(3, "Shale Spade", 1500, 0.6),
    Shovel(4, "Sandstone Spade", 1850, 0.64),
    Shovel(5, "Slate Spade", 2250, 0.67),
    Shovel(6, "Siltstone Shovel", 2700, 0.7),
    Shovel(7, "Flimsy Plastic Shovel Shovel", 3550, 0.75),
    Shovel(8, "Granite Shovel", 4040, 0.8),
    Shovel(9, "Marl Shovel", 4750, 0.85),
    Shovel(10, "Tin Shovel", 5050, 0.9),
    Shovel(11, "Granite Shovel", 6000, 1),  # gets harder from here
    Shovel(12, "Silver Shovel", 7250, 1.03),
    Shovel(13, "Gold Shovel", 9500, 1.05),
    Shovel(14, "Magnesium Shovel", 11250, 1.06),
    Shovel(15, "Copper Shovel", 13950, 1.07),
    Shovel(16, "Aluminium Shovel", 16700, 1.08),
    Shovel(17, "Bronze Shovel", 20000, 1.085),
    Shovel(18, "Brass Shovel", 26750, 1.09),
    Shovel(19, "Platinum Shovel", 30750, 1.1),
    Shovel(20, "Strontianite Shovel", 40550, 1.12),
    Shovel(21, "Iron Shovel", 46000, 1.13),
    Shovel(22, "Nickel Shovel", 50000, 1.14),
    Shovel(23, "Steel Shovel", 56050, 1.15),
    Shovel(24, "Lindgrenite", 62200, 1.17),
    Shovel(25, "Obsidian Shovel", 70750, 1.18),
    Shovel(26, "Titanium Shovel", 85000, 1.2),
    Shovel(27, "Pyrite Shovel", 96000, 1.21),
    Shovel(28, "Quartz Shovel", 103550, 1.22),
    Shovel(29, "Tungsten Shovel", 100600, 1.23),
    Shovel(30, "Beryl Shovel", 115900, 1.24),
    Shovel(31, "Titanium Drill", 120000, 1.3),
    Shovel(32, "Quartz Drill", 130750, 1.31),
    Shovel(33, "Tungsten Drill", 140600, 1.32),
    Shovel(34, "Beryl Drill", 150550, 1.33),
    Shovel(35, "Hardend Steel Drill", 162000, 1.34),
    Shovel(36, "Tungsten Carbide Drill", 170000, 1.35),
    Shovel(37, "Titanium Carbide Drill", 179900, 1.37),
    Shovel(38, "Aluminium Boride Drill", 187000, 1.38),
    Shovel(39, "Rhenium Diboride Drill", 190400, 1.39),
    Shovel(40, "Diamond Drill", 1000001, 1.51),
)

REWARDS = (
    Ore(0, "Coal", 20, 0.55),
    Ore(1, "Iron", 40, 0.40),
    Ore(2, "Nickel", 45, 0.37),
    Ore(3, "Bronze", 50, 0.35),
    Ore(4, "Copper", 55, 0.33),
    Ore(5, "Aluminium", 59, 0.30),
    Ore(6, "Silver", 64, 0.28),
    Ore(7, "Zinc", 66, 0.27),
    Ore(8, "Quartz", 70, 0.21),
    Ore(9, "Manganese", 71, 0.21),
    Ore(8, "Pyrite", 76, 0.20),
    Ore(9, "Agate", 80, 0.18),
    Ore(10, "Silica", 84, 0.16),
    Ore(11, "Gold", 89, 0.14),
    Ore(12, "Platinum", 95, 0.12),
    Ore(13, "Palladium", 101, 0.10),
    Ore(14, "Rhodium", 108, 0.09),
    Ore(15, "Titanium", 115, 0.07),
    Ore(16, "Diamond", 155, 0.05),
    Ore(17, "Uranium", 205, 0.03),
    Ore(18, "Plutonium", 220, 0.02),
    Ore(19, "Tritium", 270, 0.01),
    Ore(20, "Econium", 1000, 0.002),
)

PERKS = (
    Perk(0, "Gloves", "shortens your cooldown by 30% for 10 digs", 1200, 10),
    Perk(1, "Energy Drink", "removes cooldown once", 600, 1),
    Perk(2, "Metal Detector", "doubles the ore quantity mined for 5 digs", 1100, 5),
    Perk(
        3, "Rock Polisher", "increases revenue from sold ores by 30% one time", 1500, 1
    ),
)

class TreasureShopButton(discord.ui.View):
    def __init__(self, player: Player, cost: int):
        super().__init__()
        self.player = player
        self.cost = cost
        self.value = False

    @discord.ui.button(label="Upgrade", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != interaction.user.id:
            return await interaction.response.send_message("No.", ephemeral=True)
        self.player = await self.player.refresh()
        self.children[0].disabled = True
        if self.player.bal < self.cost:
            await interaction.message.edit(
                embed=interaction.message.embeds[0], view=self
            )
            await interaction.response.send_message(
                f"You can't afford that upgrade! You need ${self.cost-self.player.bal} more.",
                ephemeral=True,
            )
            return self.stop()
        self.value = True
        await interaction.message.edit(embed=interaction.message.embeds[0], view=self)
        await interaction.response.defer()
        self.stop()

class PerkShopMenu(discord.ui.Select):
    def __init__(self):
        perklist = [
            discord.SelectOption(label=p.name, description=p.description, value=p.id)
            for p in PERKS
        ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Buy perks...", min_values=1, max_values=1, options=perklist
        )

    async def callback(self, interaction: discord.Interaction):
        conf = Confirm(disable_after_click=True)
        chosen_perk = Perk.get(int(self.values[0]))
        await interaction.response.send_message(
            f"Purchase perk '{chosen_perk.name}' for ${chosen_perk.cost}?",
            view=conf,
            ephemeral=True,
        )
        await conf.wait()
        if conf.value is False:
            self.values = []  # reset chosen values
        self.disabled = True
        await interaction.message.edit(view=self.view)
        return self.view.stop()

class PerkShopView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(PerkShopMenu())

class treasurehunting(commands.Cog, command_attrs=dict(name="Treasures")):
    """Treasure hunting for money! Dig up various ores and even some more valuable prizes."""

    def __init__(self, bot):
        self.bot = bot
        self.perk_1_prompt_cache = list()
        self.none_found_messages = (
            "After a valiant effort, your search turns up treasure-less.",
            "Your luck ran dry..",
            "After being washed out by rain, you return home empty handed.",
            "A sandstorm stirs up any chance you had of finding treasure.",
            "You trekked out to your treasure hunting spot... before realizing you forgot your tool at home.",
            "A bird crapped on you, so you decide to give up for now.",
            "Can't find them all.",
            "Your treasure-hunt turns up treasure-less.",
            "Quicksand trapped you before you could find anything..",
        )
        self.found_messages = (
            "Your digging yielded success!",
            "Right before you were going to give up, your tool made a 'dink'!",
            "The mine almost collasped on you, but it was worth it-",
            "The clouds cleared out, allowing you to find something!",
            "After some rainfall, you see something shiny in the ground.",
            "The dust storm that passed through left something shiny in the ground...",
            "After accidently backing into a cliff, a bunch of rocks fall down revealing treasure!",
            "Word of a new digging spot was spreading, so you tried it out!",
            "\U000026cf\U0000fe0f Honest days work,",
            "Someone you were walking behind dropped something.",
        )

    async def cog_load(self):
        await self.bot.pool.execute(
            """CREATE TABLE IF NOT EXISTS "e_treasure" 
                                    (id bigint REFERENCES e_users(id),
                                    currentshovel smallint,
                                    timesdug integer,
                                    lastdug timestamp with time zone,
                                    lastmins smallint,
                                    totalearned bigint DEFAULT 0
                                    )"""
        )
        await self.bot.pool.execute(
            """CREATE TABLE IF NOT EXISTS "e_treasure_inventory" 
                                    (id bigint REFERENCES e_users(id),
                                    oreid smallint,
                                    minedwith smallint,
                                    dugwhen timestamp with time zone
                                    )"""
        )
        await self.bot.pool.execute(
            """CREATE TABLE IF NOT EXISTS "e_treasure_shovel_stats" 
                                    (id bigint REFERENCES e_users(id),
                                    shovelid smallint,
                                    timesdug integer
                                    )
                                    """
        )
        await self.bot.pool.execute(
            """CREATE TABLE IF NOT EXISTS "e_treasure_perks" 
                                    (id bigint REFERENCES e_users(id),
                                    perkid smallint,
                                    usesleft smallint,
                                    boughtwhen timestamp with time zone not null default now())"""
        )

    def can_dig(self, data: tuple) -> bool:
        """Returns True if the player can dig, False if not."""
        last_dug = data[3]
        last_mins = int(data[4])
        cooldown = last_dug + timedelta(
            minutes=last_mins
        )
        if cooldown < discord.utils.utcnow():
            return True  # can work
        return False  # cant work
    
    async def get_treasure_data(self, player: Player) -> Union[Record, None]:
        player_treasure_data = await self.bot.pool.fetchrow(
            "SELECT * FROM e_treasure WHERE id = $1",
            player.id,
        )
        if not player_treasure_data:
            # no player!
            return None
        return player_treasure_data

    async def create_treasure_data(self, player: Player) -> Record:
        await self.bot.pool.execute(
            "INSERT INTO e_treasure(id, currentshovel, timesdug, lastmins, totalearned) VALUES ($1, 0, 0, 0, 0)",
            player.id,
        )
        await self.bot.pool.execute(
            "INSERT INTO e_treasure_shovel_stats(id, shovelid, timesdug) VALUES ($1, 0, 0)",
            player.id,
        )
        return await self.bot.pool.fetchrow(
            "SELECT * FROM e_treasure WHERE id = $1",
            player.id,
        )

    async def post_dig(self, player: Player, mins: float) -> None:
        await self.bot.pool.execute(
            """
            UPDATE e_treasure SET
                timesdug = timesdug + 1,
                lastdug = $1,
                lastmins = $2
            WHERE id = $3
        """,
            discord.utils.utcnow(),
            mins,
            player.id,
        )

    @commands.group(aliases=["tr"], invoke_without_command=True)
    async def treasure(self, ctx: Context):
        """Shows your treasure hunting info"""
        player = await Player.get(ctx.author.id, self.bot)   

        #global data that will be shown regardless
        total_diggers = tuple(
            await self.bot.pool.fetchrow("SELECT COUNT(*) FROM e_treasure")
        )[0]
        total_digs = tuple(
            await self.bot.pool.fetchrow("SELECT SUM(timesdug) FROM e_treasure")
        )[0]
        total_earnt = tuple(
            await self.bot.pool.fetchrow(
                "SELECT SUM(totalearned) FROM e_treasure"
            )
        )[0]

        #per-user data that is only shown if they've dug before
        player_desc = ""  # stores totalmoney, shovel, and times dug
        player_data = await self.get_treasure_data(player)
        if player_data is not None:
            # show their info
            player_perks = await self.bot.pool.fetch("SELECT * FROM e_treasure_perks WHERE id = $1", player.id)
            neat_perks = ', '.join([p.name for p in PERKS if p.id in [r.get('perkid') for r in player_perks]])
            player_inv = await self.bot.pool.fetch("SELECT * FROM e_treasure_inventory WHERE id = $1", player.id)
            player_desc = f"Current shovel: {Shovel.get(player_data[1]).name}\nTimes dug: {player_data[2]}\nPerks: {neat_perks if len(neat_perks) != 0 else "None!"}\nInventory: {len(player_inv)} ores"
            pass
        else:
            player_desc = f"You haven't dug for treasure before! Try `{ctx.clean_prefix}dig` to start."

        await ctx.send(
            embed=discord.Embed(
                title="Treasure Hunting",
                description=f"{humanize.intcomma(total_diggers)} diggers with a combined total of ${humanize.intcomma(total_earnt)} earned, and {humanize.intcomma(total_digs)} times dug.",
                color=player.profile_color,
            ).add_field(name="Your stats", value=player_desc)
        )

    @commands.group(invoke_without_command=True, aliases=["treasureshop"])
    async def shop(self, ctx: Context):
        """Interactive shop for treasure hunting tools and perks"""
        await ctx.send(
            f"Usage: `{ctx.clean_prefix}shop (tools/perks)` <:blobthumbsup:819979852576587907>"
        )

    @shop.command()
    async def tools(self, ctx: Context):
        player = await Player.get(ctx.author.id, self.bot)
        if await self.get_treasure_data(player) is None:
            return await ctx.send(f"You haven't dug for treasure before! Try `{ctx.clean_prefix}dig` before you shop for perks.")
        ownedShovels = await self.bot.pool.fetch(
            "SELECT shovelid FROM e_treasure_shovel_stats WHERE id = $1", ctx.author.id
        )
        currentShovel = (await self.bot.pool.fetchrow(
            "SELECT currentshovel FROM e_treasure WHERE id = $1", player.id
        )).get('currentshovel')
        ownedIDs = [s.get("shovelid") for s in ownedShovels]
        lowerlimit = currentShovel
        upperlimit = max(ownedIDs) + 5
        toollist = [
            ( f"[${t.price}] {t.name} ({t.multiplier}) {CHECK if t.id in ownedIDs else ''}" )
            for t in SHOVELS
            if t.id <= upperlimit and t.id >= lowerlimit
        ]
        alltools = "\n".join(toollist)
        embed = discord.Embed(
            title="⛏ Treasure Tool Shop",
            description=f"You have ${player.bal}\n-# [price] (name) (quality)\n```ml\n{lowerlimit} previous...\n{alltools}\nand {len(SHOVELS)-upperlimit} more...\n```",
            color=player.profile_color,
        )
        embed.set_footer(text=f"Tool shop for @{ctx.author.name}")
        next_tool = SHOVELS[(max(ownedIDs) + 1)]
        shopview = TreasureShopButton(player=player, cost=next_tool.price)
        shopmsg = await ctx.send(embed=embed, view=shopview)
        await shopview.wait()
        if shopview.value:
            await player.update_balance(amount=(next_tool.price * -1), ctx=ctx)
            await self.bot.pool.execute(
                "UPDATE e_treasure SET currentshovel = $1 WHERE id = $2",
                next_tool.id,
                player.id,
            )
            await self.bot.pool.execute(
                "INSERT INTO e_treasure_shovel_stats(id, shovelid, timesdug) VALUES ($1, $2, 0)",
                player.id,
                next_tool.id,
            )
            await shopmsg.add_reaction("\U00002705")
        else:
            await shopmsg.delete()

    @shop.command()
    async def perks(self, ctx: Context):
        player = await Player.get(ctx.author.id, self.bot)
        if await self.get_treasure_data(player) is None:
            return await ctx.send(f"You haven't dug for treasure before! Try `{ctx.clean_prefix}dig` before you shop for perks.")
        activePerks = await self.bot.pool.fetch(
            "SELECT perkid FROM e_treasure_perks WHERE id = $1", ctx.author.id
        )
        activeIDs = [s.get("perkid") for s in activePerks]
        perklist = [
            (
                f"[{p.id}] {p.name} ({p.description}) {CHECK if p.id in activeIDs else ''}"
            )
            for p in PERKS
        ]
        allperks = "\n".join(perklist)
        embed = discord.Embed(
            title="⛏ Treasure Perk Shop",
            description=f"-# [id] (name) (description)\n```ml\n{allperks}```",
            color=player.profile_color,
        )
        embed.set_footer(text=f"Perk shop for @{ctx.author.name}")
        perkview = PerkShopView()
        shopmsg = await ctx.send(embed=embed, view=perkview)
        await perkview.wait()
        if len(perkview.children[0].values) >= 1: # if theres more than 0 things chosen (it wont be more than 1)
            chosen_perk = Perk.get(int(perkview.children[0].values[0]))
            if chosen_perk.id in activeIDs:
                return await ctx.reply(
                    f"You already have '{chosen_perk.name}'! Use it before buying another."
                )
            await player.update_balance(amount=(chosen_perk.cost * -1), ctx=ctx)
            await self.bot.pool.execute(
                "INSERT INTO e_treasure_perks(id, perkid, usesleft) VALUES ($1, $2, $3)",
                player.id,
                chosen_perk.id,
                chosen_perk.uses,
            )
            await shopmsg.add_reaction("\U00002705")

    @commands.command(aliases=["d"])
    async def dig(self, ctx: Context):
        """Dig for treasure using your equipped shovel/tool! Random cooldown between 7-20 mins"""
        player = await Player.get(ctx.author.id, self.bot)
        player_treasure_data = await self.get_treasure_data(player)
        player_perks = await self.bot.pool.fetch(
            "SELECT * FROM e_treasure_perks WHERE id = $1", ctx.author.id
        )
        perk_ids = [r.get("perkid") for r in player_perks]
        right_now = discord.utils.utcnow()
        if player_treasure_data is None:
            # no player!
            player_treasure_data = await self.create_treasure_data(player)
            await ctx.send(
                f"You've dug for treasure for the first time! View your stats with `{ctx.clean_prefix}treasure`"
            )
        elif self.can_dig(player_treasure_data) is False:
            if 1 in perk_ids: # check for energy drink
                if player.id in self.perk_1_prompt_cache:
                    return
                self.perk_1_prompt_cache.append(player.id)
                conf = Confirm(disable_after_click=True)
                conf_msg = await ctx.send(
                    f"You're too tired to dig right now... But you have an energy drink in your pocket! Drink it to reset the cooldown?",
                    view=conf,
                )
                await conf.wait() # ask if they want to use it
                if conf.value: 
                    await self.bot.pool.execute(
                        "DELETE FROM e_treasure_perks WHERE perkid = 1 AND id = $1", player.id
                    )
                    await self.bot.pool.execute(
                        "UPDATE e_treasure SET lastmins = 0 WHERE id = $1", player.id
                    )
                    await conf_msg.edit(content="Cooldown reset! <a:rooMonster:1323063184696938550>")
                    await ctx.invoke(self.dig)
                    return self.perk_1_prompt_cache.remove(player.id)
                else:
                    await conf_msg.delete()
                    return
            else: # doesn't have energy drink
                await ctx.send(
                    f"You're too tired to dig right now.. <:blobfeelsbad:819979895451025428>.. {discord.utils.format_dt(player_treasure_data[3] + timedelta(minutes=player_treasure_data[4]), 'R')}"
                )
                return


        player_shovel = Shovel.get(player_treasure_data[1])
        has_perk_2 = False
        perk_0_msg = ""
        perk_2_msg = ""
        mins = round(random.uniform(7.0, 20.0), 0)
        if 2 in perk_ids:
            perk_2 = ([p for p in player_perks if p.get("perkid") == 2])[0]
            if perk_2.get("usesleft") == 0:
                await self.bot.pool.execute(
                    "DELETE FROM e_treasure_perks WHERE id = $1 AND perkid = 2",
                    ctx.author.id,
                )
            else:
                has_perk_2 = True
                await self.bot.pool.execute(
                    "UPDATE e_treasure_perks SET usesleft = (usesleft) - 1 WHERE id = $1 AND perkid = 2",
                    ctx.author.id,
                )
                perk_2_msg = (
                    f" - *Metal Detector active, {perk_2.get('usesleft')} uses left*"
                )
        if 0 in perk_ids:
            # Gloves: shorten cooldown by 30%
            mins *= 0.7
            perk_0_uses = await self.bot.pool.fetchrow("SELECT usesleft FROM e_treasure_perks WHERE id = $1 AND perkid = 0", ctx.author.id)
            if perk_0_uses.get("usesleft") == 1:
                await self.bot.pool.execute("DELETE FROM e_treasure_perks WHERE id = $1 AND perkid = 0", ctx.author.id)
            else:
                await self.bot.pool.execute("UPDATE e_treasure_perks SET usesleft = usesleft - 1 WHERE id = $1 AND perkid = 0", ctx.author.id)
            perk_0_msg = f"\n-# Gloves shortened your cooldown by 30% ({perk_0_uses.get("usesleft") - 1} uses left)"
        
        dug_ores = player_shovel.dig(has_perk_2=has_perk_2)
        if len(dug_ores) == 0: # got nothing lul
            mins /= 1.5
            await ctx.send(
                f"{random.choice(self.none_found_messages)} +{len(dug_ores)} ores, ready again {discord.utils.format_dt(right_now + timedelta(minutes=mins), 'R')}{perk_0_msg}"
            )
            return await self.post_dig(player, mins)

        # they got some ores
        neat_ores = ""
        for o in dug_ores:
            await self.bot.pool.execute(
                "INSERT INTO e_treasure_inventory(id, oreid, minedwith, dugwhen) VALUES ($1, $2, $3, $4)",
                ctx.author.id,
                o.id,
                player_shovel.id,
                right_now,
            )
            neat_ores = (
                neat_ores
                + f"{len([oc for oc in dug_ores if oc.id == o.id])}x {o.name}, "
            )
        mins_ts = discord.utils.format_dt(
            right_now + timedelta(minutes=mins), "R"
        )
        await self.post_dig(player, mins)
        await ctx.send(
            f"{random.choice(self.found_messages)} +{len(dug_ores)} ores, ready again {mins_ts}\n-# {neat_ores.removesuffix(', ')}{perk_2_msg}{perk_0_msg}"
        )

    @commands.command(aliases=["ore"])
    async def ores(self, ctx: Context):
        """Shows a list of obtainable ores"""
        player = await Player.get(ctx.author.id, self.bot)
        embed = discord.Embed(
            title="\U0001faa8 Treasure Ores", color=player.profile_color
        )
        ore_list = (
            "id  |   name    |  cost  | rarity\n----+-----------+--------+-------\n"
            + "\n".join(
                [
                    f"{ore.id}{'  ' if len(str(ore.id)) == 1 else ' '} | {ore.name}{(' ')*(11-(len(ore.name)+1))}| ~${ore.sell_cost}{(' ')*(8-(len(str(ore.sell_cost))+3))}| {ore.rarity}"
                    for ore in REWARDS
                ]
            )
        )
        embed.description = f"-# \U00002139\U0000fe0f Sell price is impacted by tool quality\n```ml\n{ore_list}\n```"
        await ctx.send(embed=embed, view=X())

    @commands.group(aliases=["inv"], invoke_without_command=True)
    async def inventory(self, ctx: Context):
        """Shows your treasure inventory. To sell ores, use e$inventory sell"""
        player = await Player.get(ctx.author.id, self.bot)
        embed = discord.Embed(
            title="\U0001f392 Treasure Inventory", color=player.profile_color
        )
        ores = [
            tuple(o)
            for o in (
                await self.bot.pool.fetch(
                    "SELECT * FROM e_treasure_inventory WHERE id = $1", ctx.author.id
                )
            )
        ]
        ore_counts = {}
        if len(ores) == 0:
            embed.description = "*Its looking empty in here...*"
        for o in ores:
            try:
                ore_counts[o[1]] += 1
            except KeyError:
                ore_counts[o[1]] = 1
        total_sell_estimate = 0
        for key, value in sorted(ore_counts.items()):
            ore = Ore.get(key)
            embed.add_field(
                name=f"{value}x {ore.name}", value=f"~${ore.sell_cost * value}"
            )
            total_sell_estimate += ore.sell_cost * value
        if total_sell_estimate != 0:
            embed.set_footer(text=f"Sell total estimate: ~${total_sell_estimate}")
        else:
            embed.set_footer(
                text=f"Do {ctx.clean_prefix}dig to start digging for treasure!"
            )

        await ctx.send(embed=embed, view=X())

    @inventory.command(name="sell", aliases=["s", "sellall"])
    async def sell_(self, ctx: Context):
        """Sells your treasure inventory"""
        player = await Player.get(ctx.author.id, self.bot)
        has_sell_perk = False
        inventory = await self.bot.pool.fetch(
            "SELECT * FROM e_treasure_inventory WHERE id = $1", ctx.author.id
        )
        if len(inventory) == 0:
            return await ctx.send("\U0001f392 ... Your inventory is empty")
        selltotal = 0
        for entry in inventory:
            selltotal += (
                Ore.get(entry.get("oreid")).sell_cost
                * Shovel.get(entry.get("minedwith")).multiplier
            )
        activePerks = await self.bot.pool.fetch(
            "SELECT perkid FROM e_treasure_perks WHERE id = $1", ctx.author.id
        )
        if 3 in [p.get("perkid") for p in activePerks]:
            has_sell_perk = True
            selltotal *= 1.30  # 30% sell perk
        conf = Confirm()
        conf_msg = await ctx.send(
            f"Sell the treasures in your inventory for ${int(selltotal)}? {'*+30% from Rock Polisher perk*' if has_sell_perk else ''}",
            view=conf,
        )
        await conf.wait()
        if conf.value:
            await conf_msg.delete()
            await self.bot.pool.execute(
                "DELETE FROM e_treasure_inventory WHERE id = $1", ctx.author.id
            )
            await player.update_balance(amount=selltotal, ctx=ctx)
            await self.bot.pool.execute(
                    "UPDATE e_treasure SET totalearned = totalearned + $1 WHERE id = $2",
                    selltotal,
                    player.id,
                )
            if has_sell_perk:
                await self.bot.pool.execute(
                    "DELETE FROM e_treasure_perks WHERE id = $1 AND perkid = 3",
                    ctx.author.id,
                )
            await ctx.message.add_reaction("\U00002705")
        else:
            # cancel
            await conf_msg.delete()
            return await ctx.message.add_reaction("\U0000274c")


async def setup(bot):
    await bot.add_cog(treasurehunting(bot))
