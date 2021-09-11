#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Basic example for a bot that uses inline keyboards. For an in-depth explanation, check out
 https://git.io/JOmFw.
"""
import datetime
import logging
import os
import random
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

data_folder = 'data/'
n_questions = 3
questions = {}
for folder in os.listdir(data_folder):
    questions[folder] = {}
    for filename in os.listdir(os.path.join(data_folder, folder)):
        questions[folder][filename.rsplit( ".", 1 )[ 0 ]] = os.path.join(data_folder, folder, filename)


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Countries", callback_data='category:countries'),
            InlineKeyboardButton("Fruits", callback_data='category:fruits')
        ],
    ]

    context.user_data.update({
        'username': update.message.from_user.username,
        'points': 0,
        'step': 0,
        'category': None,
        'options': None,
        'correct': None,
        'start_time': None
    })

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(f'{{ Greetings {update.message.from_user.username}, do you want to be a millionaire?}}')
    update.message.reply_text('{Select Category}', reply_markup=reply_markup)
    # update.message.reply_photo(photo=img, reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    action, value = query.data.split(':')
    if action == 'category':
        context.user_data.update({
            'category': value,
            'start_time': time.time(),
        })
        # query.edit_message_reply_markup()  # text(text=f"Selected option: {query.data}")
        query.delete_message()  # text(text=f"Selected option: {query.data}")
        query.message.reply_text('{Start game message %s}' % value)
        get_question_data(context.user_data['category'], query.message, context)
    elif action == 'answer':
        query.edit_message_reply_markup()
        if value == context.user_data['correct']:
            query.message.reply_text('{correct answer %s}' % value)
            context.user_data['points'] += 1
            if context.user_data['points'] == n_questions:
                total_time = time.time() - context.user_data['start_time']
                query.message.reply_text('{you won, your time: %s}' % datetime.timedelta(seconds=int(total_time)))
            else:
                query.message.reply_text('{you have %d points}' % context.user_data['points'])
                get_question_data(context.user_data['category'], query.message, context)
        else:
            query.message.reply_text('{Wrong answer %s, you lost}' % value)
    else:
        query.message.reply_text('Wrong action')


def get_question_data(category, message, context):
    category_data = questions[category]
    options = random.sample(list(category_data.keys()), 4)

    correct = options[random.randint(0, 3)]
    context.user_data.update({
        'options': options,
        'correct': correct
    })
    keyboard = [InlineKeyboardButton(option.capitalize(), callback_data=f'answer:{option}') for option in options]
    with open(category_data[correct], 'rb') as f:
        message.reply_photo(photo=f.read(), reply_markup=InlineKeyboardMarkup([keyboard[:2], keyboard[2:]]))





def help_command(update: Update, context: CallbackContext) -> None:
    """Displays info on how to use the bot."""
    update.message.reply_text("Use /start to test this bot.")


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    token = os.getenv('TG_TOKEN')
    assert token, "Telegram token is not provided"
    updater = Updater(token)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
