#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using nested ConversationHandlers.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
from typing import Any, Dict, Tuple
from telegram.constants import ParseMode

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from icecream import ic
from dataclasses import dataclass
from typing import List
from db import RDB


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# State definitions for top level conversation
NEW_RECORD, STATISTICS, HOWMUCH, DESCRIBING_SELF = map(chr, range(4))
# State definitions for second level conversation
SELECTING_LEVEL, SELECTING_GENDER = map(chr, range(4, 6))
# State definitions for descriptions conversation
SELECTING_FEATURE, TYPING = map(chr, range(6, 8))
# Meta states
STOPPING, REPORT = map(chr, range(8, 10))
# mystates
REPORT, EXPORT = map(chr, range(10, 12))
# Shortcut for ConversationHandler.END
END = ConversationHandler.END

# Different constants for this example
(
    DB,
    SELECT_ACTION,
    SPENDER,
    DONE,   
    TEAMS,
    PARENTS,
    CHILDREN,
    SELF,
    GENDER,
    MALE,
    FEMALE,
    AGE,
    NAME,
    START_OVER,
    FEATURES,
    CURRENT_FEATURE,
    CURRENT_LEVEL,
) = map(chr, range(13, 30))


@dataclass
class Team:
    name: str
    dad: str
    mon: str
    n: 2
    addtext: str
    minustext: str
    icon: None
    def __str__(self) -> str:
        return f"{self.name} {self.n}"


@dataclass
class Record:
    idx: int
    uid: str
    user: str
    spender: str
    houmuch: float


TEAMS_DEFAULT: List[Team] = []
TEAMS_DEFAULT.append(Team("مجید", "مجید", "صفورا", 3, "مجید+", "مجید-", "🚗"))
TEAMS_DEFAULT.append(Team("محمد", "محمد", "صبا", 3, "محمد+", "محمد-", "🚛"))
TEAMS_DEFAULT.append(Team("حسین", "حسین", "پریسا", 2, "حسین+", "حسین-","🏎️"))
TEAMS_DEFAULT.append(Team("عارف", "عارف", "نفیسه", 2, "عارف+", "عارف-", "🚕"))
TEAMS_DEFAULT.append(Team("مسعود", "مسعود", "مهشید", 2, "مسعود+", "مسعود-", "🚛"))


def update_teams(teams: dict, text: str)-> None:
    for team in teams:
        if text == team.addtext:
            team.n += 1 
        elif text == team.minustext:
            team.n -= 1

        if team.n < 0:
            team.n = 0

# Top level conversation callbacks
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select an action: Adding parent/child or show data."""
    ic("start")

    # Create an instance of RecordsDB
    db = RDB('records.db')
    context.user_data[DB] = db

    keyboard = [["Report"],
                ["New"],
                ["Done"]]
    await update.message.reply_text(
        '<b>چکار میخوای بکنی؟\n</b>',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True, is_persistent=True))

    context.user_data[TEAMS] = TEAMS_DEFAULT
    context.user_data["records"] = []
    return SELECT_ACTION



async def update_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    ic("update_statistics")
    if update.message.text != "New":
        update_teams(context.user_data[TEAMS], update.message.text)

    # [ic(t) for t in context.user_data[TEAMS]]

    keyboard = [[t.minustext, str(t.n), t.addtext] for t in context.user_data[TEAMS]]
    keyboard += [["Done"]]

    await update.message.reply_text(
        '<b>تعداد افراد هر تیم👫\n</b>',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True, is_persistent=True))

    return STATISTICS


async def spender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    ic("spender")
    keyboard = [[t.name] for t in context.user_data[TEAMS]]

    await update.message.reply_text(
        '<b>کی خرج کرده؟\n</b>',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True, is_persistent=True),
    )
    return SPENDER


async def howmuch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    ic("howmuch")
    ic(update.message.text)
    ic(context.user_data)

    spender = update.message.text
    if spender not in [t.name for t in context.user_data[TEAMS]]:
        spender = context.user_data['spender']
    context.user_data['spender'] = spender
    await update.message.reply_text(text=f"<b>{spender} جان چقدر خرج کردی؟</b>\n", parse_mode='HTML')

    return HOWMUCH


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ic("stop")
    """End Conversation by command."""
    await update.message.reply_text("مراقب خودت باش خوشگله 😉")

    # Close the connection
    context.user_data[DB].close_connection()

    return STOPPING


# async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     ic("end")
#     """End conversation from InlineKeyboardButton."""
#     await update.callback_query.answer()

#     text = "See you around!"
#     await update.callback_query.edit_message_text(text=text)

#     return END


async def store(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ic("store")
    """Report conversation from InlineKeyboardButton."""
    user = update.message.from_user
    ic(user)
    
    spender = context.user_data['spender']
    howmuch = float(update.message.text)

    # Insert a new record
    if howmuch != 0:
        n = sum([t.n for t in context.user_data[TEAMS]])
        cost_per_person = howmuch / n
        rezhesab_dict = {}
        rezhesab_dict[spender] = 0
        for t in context.user_data[TEAMS]:
            if t.name != spender:
                team_cost = t.n * cost_per_person
                rezhesab_dict[t.name] = -team_cost
                rezhesab_dict[spender] += team_cost

        context.user_data[DB].insert_record(user.first_name, spender, howmuch, "cid", rezhesab_dict)

    await report(update, context)


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ic("report")
    table = context.user_data[DB].get_table_as_string()

    # https://stackoverflow.com/questions/49345960/how-do-i-send-tables-with-telegram-bot-api
    # update.message.reply_text(f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)
    # await update.message.reply_text(f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)
    # or use markdown
    await update.message.reply_text(f'```{table}```', parse_mode=ParseMode.MARKDOWN_V2)
    return STOPPING


def main() -> None:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN = os.getenv("TOKEN")

    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_ACTION: [MessageHandler(filters.Regex(r'^Report$'), report),
                            MessageHandler(filters.Regex(r'^New$'), update_statistics),
                            MessageHandler(filters.Regex(r'^Done$'), stop)],

            STATISTICS: [MessageHandler(filters.Regex(r'^(?!Done).*$'), update_statistics),
                         MessageHandler(filters.Regex(r'^Done$'), spender)],

            SPENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, howmuch)],

            HOWMUCH: [MessageHandler(filters.Regex(r'^\d+$'), store),
                      MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r'^\d+$'), howmuch)],

            STOPPING: [CommandHandler("start", start)],
        },
        fallbacks=[CommandHandler("stop", stop)],
    )


    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
