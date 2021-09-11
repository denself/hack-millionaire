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
from typing import Optional

from emoji import emojize

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, CallbackQuery, Message
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

from utils.leader_board import store_result_of_user, print_n_sorted_users_with_min_time

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

j = None
data_folder = 'data/'
n_questions = 3
snoop_tresh = 0.8
questions = {}
for folder in os.listdir(data_folder):
    questions[folder] = {}
    for filename in os.listdir(os.path.join(data_folder, folder)):
        questions[folder][filename.rsplit( ".", 1 )[ 0 ]] = os.path.join(data_folder, folder, filename)


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton("Question [1/10]", callback_data='category:fruits')]]

    context.user_data.update({
        'username': update.message.from_user.username,
        'points': 0,
        'step': 0,
        'category': None,
        'options': None,
        'correct': None,
        'start_time': None,
        'hints': {
            '50': '⚖️50/50',
            'snoop': '☎️Call',
            'hint': '🔁 Change'
        }
    })

    reply_markup = InlineKeyboardMarkup(keyboard)

    # TODO: replace welcome video; add "Question [1/10]" button
    with open(os.path.join(data_folder, 'videos', 'win.mp4'), 'rb') as f:
        update.message.reply_video(f.read(), reply_markup=reply_markup)

    # update.message.reply_text('{Select Category}')
    # update.message.reply_photo(photo=img, reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query: Optional[CallbackQuery] = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user_class is needed
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
        query.message.reply_text('Question [1/10]')
        get_question_data(context.user_data['category'], query.message, context)
    elif action == 'answer':
        # query.edit_message_reply_markup()
        query.delete_message()
        if value == context.user_data['correct']:
            query.message.reply_text('{correct answer %s}' % value)
            context.user_data['points'] += 1
            if context.user_data['points'] == n_questions:
                total_time = int(time.time() - context.user_data['start_time'])
                store_result_of_user(update.callback_query.from_user.username, total_time)
                # http://www.unicode.org/emoji/charts/full-emoji-list.html
                query.message.reply_text(emojize(":party_popper:", use_aliases=True) + ', your time: %s seconds' % datetime.timedelta(seconds=total_time))
                print_n_sorted_users_with_min_time(query.message)
            else:
                with open(os.path.join(data_folder, 'videos', 'win.mp4'), 'rb') as f:
                    # TODO: add button "Question [2/10]"
                    query.message.reply_video(f.read())

                get_question_data(context.user_data['category'], query.message, context)
                # TODO: additional video before question 10
                # TODO: additional video after final answer
                # TODO: add message "hiring.reface.ai"
        else:
            with open(os.path.join(data_folder, 'videos', 'wrong.mp4'), 'rb') as f:
                # TODO: add button "Try Again"
                keyboard = [[InlineKeyboardButton("Try Again", callback_data='category:fruits')]]
                query.message.reply_video(f.read(), reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == 'help':
        if value == '50':
            context.user_data['hints'].pop('50')
            options = [[None]]
            while context.user_data['correct'] not in list(zip(*options))[-1]:
                options = random.sample(context.user_data['options'], 2)
            context.user_data['options'] = options
            keyboard = [InlineKeyboardButton(letter.capitalize() + '. ' + option.capitalize(),
                                             callback_data=f'answer:{option}') for letter, option in
                        sorted(context.user_data['options'])]
            hints = [InlineKeyboardButton(value, callback_data=f'help:{key}') for key, value in context.user_data['hints'].items()]
            query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([keyboard[:1], keyboard[1:], hints]))
        elif value == 'snoop':
            context.user_data['hints'].pop('snoop')
            query.edit_message_reply_markup()

            weights = [0.8 if v == context.user_data['correct'] else 0.1 for k, v in context.user_data['options']]
            hint = random.choices(context.user_data['options'], weights)[0][0]
            video_name = f'{hint.capitalize()}.mp4'

            keyboard = [InlineKeyboardButton(letter.capitalize() + '. ' + option.capitalize(),
                                             callback_data=f'answer:{option}') for letter, option in
                        context.user_data['options']]
            hints = [InlineKeyboardButton(value, callback_data=f'help:{key}') for key, value in context.user_data['hints'].items()]
            # hint_name = os.listdir(os.path.join(data_folder, 'hints', 'abcd'))
            with open(os.path.join(data_folder, 'hints', 'abcd', video_name), 'rb') as f:
                query.message.reply_video(f.read(), reply_markup=InlineKeyboardMarkup([keyboard[:2], keyboard[2:], hints]))
        elif value == 'hint':
            context.user_data['hints'].pop('hint')
            query.edit_message_reply_markup()

            keyboard = [InlineKeyboardButton(letter.capitalize() + '. ' + option.capitalize(),
                                             callback_data=f'answer:{option}') for letter, option in
                        context.user_data['options']]
            hints = [InlineKeyboardButton(value, callback_data=f'help:{key}') for key, value in context.user_data['hints'].items()]
            category_data = questions[context.user_data['category']]
            with open(category_data[context.user_data['correct']], 'rb') as f:
                query.message.reply_photo(photo=f.read(), reply_markup=InlineKeyboardMarkup([keyboard[:2], keyboard[2:], hints]))

    else:
        query.message.reply_text('Wrong action')


def get_question_data(category, message, context):
    category_data = questions[category]
    options = random.sample(list(category_data.keys()), 4)

    correct = options[random.randint(0, 3)]
    context.user_data.update({
        'options': list(zip('abcd', options)),
        'correct': correct
    })
    keyboard = [InlineKeyboardButton(letter.capitalize() + '. ' + option.capitalize(),
                                     callback_data=f'answer:{option}') for letter, option in context.user_data['options']]
    hints = [InlineKeyboardButton(value, callback_data=f'help:{key}') for key, value in context.user_data['hints'].items()]
    # reply_keyboard = [['50 / 50', 'Call Snoop', 'Get a Hint']]
    # message.reply_text(
    #     'Guess What is it?',
    #     reply_markup=ReplyKeyboardMarkup(
    #         reply_keyboard, one_time_keyboard=True, input_field_placeholder='Need Help?'
    #     ),
    # )
    with open(category_data[correct], 'rb') as f:
        message.reply_photo(photo=f.read(), reply_markup=InlineKeyboardMarkup([keyboard[:2], keyboard[2:], hints]))


def help_command(update: Update, context: CallbackContext) -> None:
    """Displays info on how to use the bot."""
    update.message.reply_text("Use /start to test this bot.")


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    token = os.getenv('TG_TOKEN')
    assert token, "Telegram token is not provided"
    updater = Updater(token)
    global j
    j = updater.job_queue

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user_class presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
