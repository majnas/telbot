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

import os
import logging
from typing import Any, Dict, Tuple
from telegram.constants import ParseMode

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext
)
from dataclasses import dataclass
from typing import List
from db import RDB
import re
import utils

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# State definitions for top level conversation
STATISTICS, HOWMUCH, SELECT_ACTION, STOPPING, REPORT, DESC, SPENDER, DELREC = map(chr, range(8))

# Different constants for this example
DB, TEAMS = map(chr, range(8, 10))


@dataclass
class Team:
    name_farsi: str
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

TEAMS_DEFAULT.append(Team("مجید", "Majid", "Majid", "Safoura", 3, "Majid+", "Majid-", "🚗"))
TEAMS_DEFAULT.append(Team("محمد", "Mammad", "Mammad", "Saba", 3, "Mammad+", "Mammad-",  "🚙"))
TEAMS_DEFAULT.append(Team("حسین", "Hossein", "Hossein", "Parisa", 2, "Hossein+", "Hossein-","🏎️"))
TEAMS_DEFAULT.append(Team("عارف", "Aref", "Aref", "Nafise", 2, "Aref+", "Aref-", "🚕"))
TEAMS_DEFAULT.append(Team("مسعود", "Masoud", "Masoud", "Mahshid", 2, "Masoud+", "Masoud-", "🚛"))

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
    # Create an instance of RecordsDB
    db = RDB('records.db')
    context.user_data[DB] = db

    keyboard = [["Report"],
                ["New"],
                ["Delete"],
                ["Done"],]
    await update.message.reply_text(
        '<b>چکار میخوای بکنی؟\n</b>',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True, is_persistent=True))

    context.user_data[TEAMS] = TEAMS_DEFAULT
    context.user_data["records"] = []
    return SELECT_ACTION



async def update_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    if update.message.text != "New":
        update_teams(context.user_data[TEAMS], update.message.text)

    keyboard = [[t.minustext, str(t.n), t.addtext] for t in context.user_data[TEAMS]]
    keyboard += [["Done"]]

    await update.message.reply_text(
        '<b>تعداد افراد هر تیم👫\n</b>',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True, is_persistent=True))

    return STATISTICS


async def delete_record(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    await update.message.reply_text(text=f"<b>کدوم ردیف رو میخوای حذف کنی؟</b>\n", parse_mode='HTML')
    return DELREC


async def spender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    keyboard = [[t.name] for t in context.user_data[TEAMS]]

    await update.message.reply_text(
        '<b>کی خرج کرده؟\n</b>',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True, is_persistent=True),
    )
    return SPENDER


async def desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    spender = update.message.text
    if spender not in [t.name for t in context.user_data[TEAMS]]:
        spender = context.user_data['spender']
    context.user_data['spender'] = spender
    spender_farsi = next(team.name_farsi for team in context.user_data[TEAMS] if team.name == spender)
    context.user_data['spender_farsi'] = spender_farsi
    await update.message.reply_text(text=f"<b>{spender_farsi} جان خرج چی کردی؟</b>\n", parse_mode='HTML')

    return DESC


async def howmuch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    desc = update.message.text
    context.user_data['desc'] = desc
    spender_farsi = context.user_data['spender_farsi']
    await update.message.reply_text(text=f"<b>{spender_farsi} جان چقدر خرج کردی؟</b>\n", parse_mode='HTML')

    return HOWMUCH


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    await update.message.reply_text("مراقب خودت باش خوشگله 😉")

    # Close the connection
    context.user_data[DB].close_connection()

    return STOPPING


async def which_record(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    idx = int(update.message.text) + 1
    # Insert a new record
    context.user_data[DB].delete_record_by_index(idx)
    logger.info(f"{user.first_name}: deleted record with idx={idx-1}")

    return await report(update, context)


async def store(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Report conversation from InlineKeyboardButton."""
    user = update.message.from_user
    
    spender = context.user_data['spender']
    desc = context.user_data['desc']
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

        context.user_data[DB].insert_record(user.first_name, 
                                            spender, 
                                            howmuch, 
                                            cost_per_person, 
                                            desc, 
                                            "cid", 
                                            rezhesab_dict)
    logger.info(f"{user.first_name}: {spender} spend {howmuch}$ for {desc}")

    return await report(update, context)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    table = context.user_data[DB].get_table_as_string()

    # https://stackoverflow.com/questions/49345960/how-do-i-send-tables-with-telegram-bot-api
    # update.message.reply_text(f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)
    await update.message.reply_text(f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)
    # or use markdown
    # await update.message.reply_text(f'```{table}```', parse_mode=ParseMode.MARKDOWN_V2)
    utils.create_pdf_with_text("report.pdf", table)
    utils.create_txt("report.txt", table.get_string())
    return await pdf(update, context)

async def pdf(update: Update, context: CallbackContext) -> None:
    pdf_file_path = 'report.pdf'
    await context.bot.send_document(chat_id=update.message.chat_id, document=open(pdf_file_path, 'rb'))

    pdf_file_path = 'report.txt'
    await context.bot.send_document(chat_id=update.message.chat_id, document=open(pdf_file_path, 'rb'))

    # pdf_file_path = 'report.png'
    # await context.bot.send_document(chat_id=update.message.chat_id, document=open(pdf_file_path, 'rb'))

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
                            MessageHandler(filters.Regex(r'^Delete$'), delete_record),
                            MessageHandler(filters.Regex(r'^Done$'), stop)],

            STATISTICS: [MessageHandler(filters.Regex(r'^(?!Done).*$'), update_statistics),
                         MessageHandler(filters.Regex(r'^Done$'), spender)],

            SPENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, desc)],
            DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, howmuch)],

            HOWMUCH: [MessageHandler(filters.Regex(re.compile(r'^\d+(\.\d+)?$')), store),
                      MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r'^\d+$'), howmuch)],

            DELREC: [MessageHandler(filters.Regex(r'^\d+$'), which_record)],

            STOPPING: [CommandHandler("start", start)],
        },
        fallbacks=[CommandHandler("stop", stop)],
    )


    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
