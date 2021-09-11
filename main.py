#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Basic example for a bot that uses inline keyboards. For an in-depth explanation, check out
 https://git.io/JOmFw.
"""
import csv
import logging
import os
import random
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

from file_utils import find_image

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

j = None
data_folder = 'data/'
n_questions = 10
snoop_tresh = 0.8

with open(os.path.join(data_folder, 'countries', 'questions.csv')) as f:
    questions = list(csv.reader(f, delimiter='\t'))


def start(update: Update, context: CallbackContext) -> None:

    keyboard = [[InlineKeyboardButton("Question [1/10]", callback_data='question:start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    with open(os.path.join(data_folder, 'videos', '0-hello.mp4'), 'rb') as f:
        update.message.reply_video(f.read(), reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query: Optional[CallbackQuery] = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user_class is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    action, value = query.data.split(':')
    if action == 'question':
        query.delete_message()
        if value == 'start':
            context.user_data.update({
                'username': query.message.from_user.username,
                'points': 0,
                'options': None,
                'correct': None,
                'hints': {
                    '50': '⚖️50/50',
                    'snoop': '☎️Call',
                    'hint': '🔁 Change'
                }
            })
        # query.message.reply_text('Question [%d/10]' % (context.user_data['points']+1))
        get_question_data(query.message, context)
    elif action == 'answer':
        query.delete_message()
        # Answer correct
        if value == context.user_data['correct']:
            context.user_data['points'] += 1

            # Final answer
            if context.user_data['points'] == n_questions:

                keyboard = [[InlineKeyboardButton("Try Again", callback_data='question:start')],
                            [InlineKeyboardButton("Claim Prize", url='https://hey.reface.ai/hiring/')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                with open(os.path.join(data_folder, 'videos', '10-win.mp4'), 'rb') as f:
                    query.message.reply_video(f.read(), reply_markup=reply_markup)
            # Other answer
            else:
                if context.user_data['points'] + 1 == n_questions:
                    keyboard = [[InlineKeyboardButton("Final Question",
                                                      callback_data='question:next')]]
                else:
                    keyboard = [[InlineKeyboardButton("Question [%d/10]" % (context.user_data['points'] + 1),
                                                      callback_data='question:next')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                with open(os.path.join(data_folder, 'videos', '%d.mp4' % context.user_data['points']), 'rb') as f:
                    query.message.reply_video(f.read(), reply_markup=reply_markup)

                # with open(os.path.join(data_folder, 'videos', '10-win.mp4'), 'rb') as f:
                #     query.message.reply_video(f.read())

                # TODO: additional video before question 10
                # TODO: add message "hiring.reface.ai" with bitly
        # Answer Wrong
        else:
            with open(os.path.join(data_folder, 'videos', 'wrong.mp4'), 'rb') as f:
                keyboard = [[InlineKeyboardButton("Try Again", callback_data='question:start')]]
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
            query.delete_message()

            keyboard = [InlineKeyboardButton(letter.capitalize() + '. ' + option.capitalize(),
                                             callback_data=f'answer:{option}') for letter, option in
                        context.user_data['options']]
            hints = [InlineKeyboardButton(value, callback_data=f'help:{key}') for key, value in context.user_data['hints'].items()]
            with open(find_image(os.path.join(data_folder, 'countries/images'), context.user_data['correct'], True), 'rb') as f:
                query.message.reply_photo(photo=f.read(), reply_markup=InlineKeyboardMarkup([keyboard[:2], keyboard[2:], hints]))

    else:
        query.message.reply_text('Wrong action')


def get_question_data(message, context):
    choices = random.choice(questions)
    correct = choices[0]
    print(correct)
    options = [correct, *random.sample(choices[1:], k=3)][:4]
    random.shuffle(options)

    context.user_data.update({
        'options': list(zip('abcd', options)),
        'correct': correct
    })
    keyboard = [InlineKeyboardButton(letter.capitalize() + '. ' + option.capitalize(),
                                     callback_data=f'answer:{option}') for letter, option in context.user_data['options']]
    hints = [InlineKeyboardButton(value, callback_data=f'help:{key}') for key, value in context.user_data['hints'].items()]

    with open(find_image(os.path.join(data_folder, 'countries/images'), context.user_data['correct']), 'rb') as f:
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
