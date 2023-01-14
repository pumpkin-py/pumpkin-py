import contextlib
import datetime
from typing import Callable, Dict, Optional, List

import discord
from discord.ext import commands

import pumpkin._tracing
from pumpkin.database.config import Config
from pumpkin.spamchannel.database import SpamChannel
from pumpkin.exceptions import SpamChannelException


config = Config.get()
_trace: Callable = pumpkin._tracing.register("pie_spamchannel")


class _SpamchannelManager:
    def __init__(self, *, time_limit: int, message_limit: int):
        self.time_limit = datetime.timedelta(minutes=time_limit)
        self.message_limit: int = message_limit

        self.cooldown: Dict[int, List[datetime.datetime]] = {}
        self.frozen: Dict[int, bool] = {}

    def _ensure_key(self, channel_id: int) -> None:
        """Make sure that the internal dictionaries know about the channel."""
        if channel_id not in self.cooldown:
            self.cooldown[channel_id] = []
        if channel_id not in self.frozen:
            self.frozen[channel_id] = False

    def _update_channel(self, channel_id: int) -> None:
        """Delete old timestamps from internal dictionaries."""
        if channel_id not in self.cooldown.keys():
            return

        now = datetime.datetime.now(datetime.timezone.utc)
        new_cooldown: List[datetime.datetime] = []
        for timestamp in self.cooldown[channel_id]:
            if (now - timestamp) <= self.time_limit:
                new_cooldown.append(timestamp)
        self.cooldown[channel_id] = new_cooldown

    def block_message(self, message: discord.Message) -> bool:
        """Check if the message can be sent to given channel.

        The redirection message is always sent, this function
        only returns boolean if the command should be invoked.

        Args:
            message: The command to be run.

        Returns:
            If the command should be run or not.
        """
        if type(message.channel) is not discord.TextChannel:
            _trace(f"Not TextChannel, but {type(message.channel).__name__}.")
            return False

        channel_id: int = message.channel.id
        self._ensure_key(channel_id)
        self._update_channel(channel_id)

        count: int = len(self.cooldown[channel_id])
        if count < self.message_limit and self.frozen[channel_id]:
            # Unlock the channel
            self.frozen[channel_id] = False
            _trace("Channel unlocked.")
        if count == self.message_limit and not self.frozen[channel_id]:
            # Lock the channel
            self.frozen[channel_id] = True
            _trace("Channel locked.")
        if count >= self.message_limit:
            # Any messages above message_limit won't be run,
            # and they should not count into the cooldown
            _trace("Allowed message queue size exceeded.")
            return True

        # Add the message timestamp to cooldown
        self.cooldown[channel_id].append(message.created_at)

        # Allow the command to be run
        _trace("Message added to message cooldown queue.")
        return False


_SPAMCHANNEL_MANAGER = _SpamchannelManager(time_limit=3, message_limit=3)


async def _run(ctx: commands.Context, hard: bool) -> bool:
    # Do not run in help
    if ctx.invoked_with == "help":
        return True

    if getattr(ctx.bot, "owner_id", 0) == ctx.author.id:
        _trace("Owner, invocation allowed.")
        return True
    if ctx.author.id in getattr(ctx.bot, "owner_ids", set()):
        _trace("Owners, invocation allowed.")
        return True

    if ctx.guild is None:
        _trace("Not in guild, invocation allowed.")
        return True

    spamchannels = SpamChannel.get_all(ctx.guild.id)
    if not spamchannels:
        # Allow the invocation if there are no spamchannels
        _trace("No spamchannels, invocation allowed.")
        return True

    if ctx.channel.id in [c.channel_id for c in spamchannels]:
        # Allow the invocation if message's channel is spamchannel
        _trace("In spamchannel, invocation allowed.")
        return True

    primary: Optional[SpamChannel] = None
    with contextlib.suppress(IndexError):
        primary = [s for s in spamchannels if s.primary][0]
    if not primary:
        primary = spamchannels[0]

    await ctx.send(
        "<@{user}> 👉 <#{channel}>".format(
            user=ctx.author.id, channel=primary.channel_id
        )
    )

    if hard:
        # Don't return 'False', because that triggers
        # 'You don't have permission' message. They do, but they've invoked
        # a command that is only allowed in spam channel.
        _trace("Command blocked [hard limit].")
        raise SpamChannelException(ctx.message)

    if _SPAMCHANNEL_MANAGER.block_message(ctx.message):
        # Don't return 'False', because that triggers
        # 'You don't have permission' message. They do, but they've already
        # exceeded their spam channel message limit.
        _trace("Command blocked [soft limit].")
        raise SpamChannelException(ctx.message)

    _trace("Invocation allowed.")
    return True


async def spamchannel_soft(ctx: commands.Context) -> bool:
    """Allow a few commands, then block."""
    return await _run(ctx, hard=False)


async def spamchannel_hard(ctx: commands.Context) -> bool:
    """Do not allow running this command outside of spam channel."""
    return await _run(ctx, hard=True)
