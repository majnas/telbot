import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,
                      InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler, filters)

from icecream import ic
from dataclasses import dataclass
from typing import List

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

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

TEAMS: List[Team] = []
TEAMS.append(Team("Majid", "Majid", "Safoura", 3, "Majid+", "Majid-", "🚗"))
TEAMS.append(Team("Mammad", "Mammad", "Saba", 3, "Mammad+", "Mammad-",  "🚙"))
TEAMS.append(Team("Hossein", "Hossein", "Parisa", 2, "Hossein+", "Hossein-","🏎️"))
TEAMS.append(Team("Aref", "Aref", "Nafise", 2, "Aref+", "Aref-", "🚕"))
TEAMS.append(Team("Masoud", "Masoud", "Mahshid", 2, "Masoud+", "Masoud-", "🚛"))

def update_teams(text: str)-> None:
    for team in TEAMS:
        if text == team.addtext:
            team.n += 1 
        elif text == team.minustext:
            team.n -= 1

# Define states
STATISTICS, SPENDER, AMOUNT, SUMMARY = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their preferred car type."""
    reply_keyboard = [[t.minustext, str(t.n), t.addtext] for t in TEAMS]
    reply_keyboard += [["Apply"]]

    await update.message.reply_text(
        '<b>Set statistics\n</b>',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True, is_persistent=True),
    )

    return STATISTICS


async def statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Apply":
        # user = update.message.from_user
        # context.user_data['car_type'] = update.message.text
        # logger.info('Car type of %s: %s', user.first_name, update.message.text)

        reply_keyboard = [[t.name] for t in TEAMS]

        await update.message.reply_text(
            '<b>Who spend money?\n</b>',
            parse_mode='HTML',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True, is_persistent=True),
        )
        return SPENDER
    else:
        ic(update.message.text)
        update_teams(text=update.message.text)
        reply_keyboard = [[t.minustext, str(t.n), t.addtext] for t in TEAMS]
        reply_keyboard += [["Apply"]]

        await update.message.reply_text(
            '<b>Set statistics\n</b>',
            parse_mode='HTML',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True, is_persistent=True),
        )
        return STATISTICS
        

async def spender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ic(update.message.text)
    context.user_data['spender'] = update.message.text
    await update.message.reply_text(text='<b>Please type in the mileage (e.g., 50000):</b>', parse_mode='HTML')
    return AMOUNT


async def amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ic("amount")
    context.user_data['amount'] = update.message.text
    ic(update.message.text)
    ic(context.user_data)
    # print report
    # Inform user and transition to summary
    # await update.message.reply_text('<b>Photo uploaded successfully.\n'
    #                                 'Let\'s summarize your selections.</b>',
    #                                 parse_mode='HTML'
    # )
    await summary(update, context)  # Proceed to summary
    

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Summarizes the user's selections and ends the conversation, including the uploaded image."""
    selections = context.user_data
    # Construct the summary text
    summary_text = (f"<b>Here's what you told me about your car:\n</b>"
                    f"<b>Spender:</b> {selections.get('spender')}\n"
                    f"<b>Amount:</b> {selections.get('amount')}\n"
                    f"<b>Photo:</b> {'Uploaded' if 'car_photo' in selections else 'Not provided'}")

    chat_id = update.effective_chat.id
    # If no photo was uploaded, just send the summary text
    await context.bot.send_message(chat_id=chat_id, text=summary_text, parse_mode='HTML')
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text('Bye! Hope to talk to you again soon.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END



def main() -> None:
    """Run the bot."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN = os.getenv("TOKEN")

    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            STATISTICS: [MessageHandler(filters.TEXT & ~filters.COMMAND, statistics)],
            SPENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, spender)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount)],
            SUMMARY: [MessageHandler(filters.ALL, summary)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    # Handle the case when a user sends /start but they're not in a conversation
    application.add_handler(CommandHandler('start', start))

    application.run_polling()


if __name__ == '__main__':
    main()