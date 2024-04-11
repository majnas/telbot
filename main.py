import os
import telegram.ext
from dotenv import load_dotenv
from icecream import ic

load_dotenv()
TOKEN = os.getenv("TOKEN")

def start(update, context):
    update.message.reply_text("Hello Regent Guys!")

def help(update, context):
    update.message.reply_text(
        """
        Hello Regent Guys!
        /start - to start
        /help - to get help
        /newrec - new records
        /report - get report
        """
    )

def new(update, context):
    # Get the username or display name of the user who sent the command
    user_name = update.effective_user.username or update.effective_user.first_name
    update.message.reply_text(f"{user_name} is requesting a new number. Please enter a number:")

def get_number(update, context):
    user_name = update.effective_user.username or update.effective_user.first_name
    try:
        number = int(update.message.text)
        update.message.reply_text(f"{user_name} entered: {number}")
    except ValueError:
        update.message.reply_text("Please enter a valid number.")

updater = telegram.ext.Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(telegram.ext.CommandHandler('start', start))
dispatcher.add_handler(telegram.ext.CommandHandler('help', help))
dispatcher.add_handler(telegram.ext.CommandHandler('new', new))

# Add a message handler to capture the number from the user
dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.text & ~telegram.ext.Filters.command, get_number))

updater.start_polling()
updater.idle()
