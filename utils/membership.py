from telegram import Bot
from telegram.error import TelegramError
from config import REQUIRED_CHANNELS


async def check_membership(bot: Bot, user_id: int) -> list[dict]:
    """
    Returns a list of channels the user has NOT joined.
    Empty list = user is a member of all required channels.
    """
    not_joined = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(channel["username"], user_id)
            if member.status in ("left", "kicked"):
                not_joined.append(channel)
        except TelegramError:
            # Can't check — treat as not joined (bot may not be admin yet)
            not_joined.append(channel)
    return not_joined
