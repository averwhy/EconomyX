import contextlib
import jishaku.paginators
import jishaku.exception_handling
import discord
import re
from typing import Union
from collections import namedtuple
from jishaku.meta import __version__

# class CustomDebugCog(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
#     @Feature.Command(name="jishaku", aliases=["jsk"], invoke_without_command=True, ignore_extra=False)
#     async def jsk(self, ctx: commands.Context):
#         """
#         The Jishaku debug and diagnostic commands.
#         This command on its own gives a status brief.
#         All other functionality is within its subcommands.
#         """
#         summary = [
#             f"Jishaku v{__version__}, discord.py `{package_version('discord.py')}`, "
#             f"`Python {sys.version}` on `{sys.platform}`".replace("\n", ""),
#             f"Module was loaded {humanize.naturaltime(self.load_time)}, "
#             f"cog was loaded {humanize.naturaltime(self.start_time)}.",
#             ""
#         ]
#         # detect if [procinfo] feature is installed
#         if psutil:
#             try:
#                 proc = psutil.Process()
#                 with proc.oneshot():
#                     try:
#                         mem = proc.memory_full_info()
#                         summary.append(f"Using {humanize.naturalsize(mem.rss)} physical memory and "
#                                        f"{humanize.naturalsize(mem.vms)} virtual memory, "
#                                        f"{humanize.naturalsize(mem.uss)} of which unique to this process.")
#                     except psutil.AccessDenied:
#                         pass
#                     try:
#                         name = proc.name()
#                         pid = proc.pid
#                         thread_count = proc.num_threads()
#                         summary.append(f"Running on PID {pid} (`{name}`) with {thread_count} thread(s).")
#                     except psutil.AccessDenied:
#                         pass
#                     summary.append("")  # blank line
#             except psutil.AccessDenied:
#                 summary.append(
#                     "psutil is installed, but this process does not have high enough access rights "
#                     "to query process information."
#                 )
#                 summary.append("")  # blank line
#         cache_summary = f"{len(self.bot.guilds)} guild(s) and {len(self.bot.users)} user(s)"
#         # Show shard settings to summary
#         if isinstance(self.bot, discord.AutoShardedClient):
#             summary.append(f"This bot is automatically sharded and can see {cache_summary}.")
#         elif self.bot.shard_count:
#             summary.append(f"This bot is manually sharded and can see {cache_summary}.")
#         else:
#             summary.append(f"This bot is not sharded and can see {cache_summary}.")
#         # pylint: disable=protected-access
#         if self.bot._connection.max_messages:
#             message_cache = f"Message cache capped at {self.bot._connection.max_messages}"
#         else:
#             message_cache = "Message cache is disabled"
#         if discord.version_info >= (1, 5, 0):
#             presence_intent = f"presence intent is {'enabled' if self.bot.intents.presences else 'disabled'}"
#             members_intent = f"members intent is {'enabled' if self.bot.intents.members else 'disabled'}"
#             summary.append(f"{message_cache}, {presence_intent} and {members_intent}.")
#         else:
#             guild_subscriptions = f"guild subscriptions are {'enabled' if self.bot._connection.guild_subscriptions else 'disabled'}"
#             summary.append(f"{message_cache} and {guild_subscriptions}.")
#         # pylint: enable=protected-access
#         # Show websocket latency in milliseconds
#         summary.append(f"Average websocket latency: {round(self.bot.latency * 1000, 2)}ms")
#         embed = discord.Embed(description="\n".join(summary))
#         await ctx.send(embed=embed)

# Everything here below is credit to Stella

EmojiSettings = namedtuple('EmojiSettings', 'start back forward end close')

class FakeEmote(discord.PartialEmoji):
    """
    Due to the nature of jishaku checking if an emoji object is the reaction, passing raw str into it will not work.
    Creating a PartialEmoji object is needed instead.
    """
    @classmethod
    def from_name(cls, name):
        emoji_name = re.sub("|<|>", "", name)
        a, name, id = emoji_name.split(":")
        return cls(name=name, id=int(id), animated=bool(a))

emote = EmojiSettings(
    start=FakeEmote.from_name("<a:thick_loading:793168593663164446>"),
    back=FakeEmote.from_name("<:PepePoint_flipped:798178551459348540>"),
    forward=FakeEmote.from_name("<:PepePoint:759934591590203423>"),
    end=FakeEmote.from_name("<:blobstop:749111017778184302>"),
    close=FakeEmote.from_name("<:redTick:596576672149667840>")
)
jishaku.paginators.EMOJI_DEFAULT = emote  # Overrides jishaku emojis

async def attempt_add_reaction(msg: discord.Message, reaction: Union[str, discord.Emoji]):
    """
    This is responsible for every add reaction happening in jishaku. Instead of replacing each emoji that it uses in
    the source code, it will try to find the corresponding emoji that is being used instead.
    """
    reacts = {
        "\N{WHITE HEAVY CHECK MARK}": "<a:snod:798165766888488991>",
        "\N{BLACK RIGHT-POINTING TRIANGLE}": "<a:thick_loading:793168593663164446>",
        "\N{HEAVY EXCLAMATION MARK SYMBOL}": "<a:sno:784149860726865930>",
        "\N{DOUBLE EXCLAMATION MARK}": "<a:sno:784149860726865930>",
        "\N{ALARM CLOCK}": emote.end
    }
    react = reacts[reaction] if reaction in reacts else reaction
    with contextlib.suppress(discord.HTTPException):
        return await msg.add_reaction(react)

jishaku.exception_handling.attempt_add_reaction = attempt_add_reaction

async def setup(bot):
    # await bot.add_cog(CustomDebugCog(bot=bot))
    pass