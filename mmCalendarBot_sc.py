#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
A bot that set alarms for Miralos Morir Calendar
"""

import logging
import os
import random
import sys
import json
import requests
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

b_key = "1270963300:AAHcBmzi_uoMwj62p6MFgonsZ6QaqOtJPz0"
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Getting mode, so we could define run function for local and Heroku setup
#mode = os.getenv("MODE")
mode = "dev"
TOKEN = os.getenv("TOKEN")
if mode == "dev":
    TOKEN = b_key
    def run(updater):
        updater.start_polling()
elif mode == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        # Code from https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#heroku
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
else:
    logger.error("No MODE  specified!")
    sys.exit(1)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    update.message.reply_text('Hi! Use /set <seconds> to set a timer')


def alarm(context):
    """Send the alarm message."""
    job = context.job
    context.bot.send_message(job.context, text='Beep!')

def calendar_notif(context):
    """ Check Calendar for dates and notify"""
    job = context.job
    cites_url = "http://miralosmorserver.pythonanywhere.com/api/calendar/all"
    cites_req = requests.get(cites_url)
    cites_dict = cites_req.json()
    cites_hour = [c['start'] for c in cites_dict]
    cite_stamps = [datetime.strptime(h, '%Y-%m-%dT%H:%M:%S.000Z') for h in cites_hour]
    cite_stamps_corrected = [(h - timedelta(hours=3)) for h in cite_stamps]
    for i in range(len(cite_stamps_corrected)):
        if datetime.today().date() == cite_stamps_corrected[i].date():
            msg = "Hoy tenemos " + cites_dict[i]['title'] + "a las " + cite_stamps_corrected[i].strftime("%H:%M hs")
            context.bot.send_message(job.context, text=msg)

def calendar_group(dp):
    cites_url = "http://miralosmorserver.pythonanywhere.com/api/calendar/all"
    cites_req = requests.get(cites_url)
    cites_dict = cites_req.json()
    cites_hour = [c['start'] for c in cites_dict]
    cite_stamps = [datetime.strptime(h, '%Y-%m-%dT%H:%M:%S.000Z') for h in cites_hour]
    cite_stamps_corrected = [(h - timedelta(hours=3)) for h in cite_stamps]
    for i in range(len(cite_stamps_corrected)):
        if datetime.today().date() == cite_stamps_corrected[i].date():
            msg = "Hoy tenemos '" + cites_dict[i]['title'] + "' a las " + cite_stamps_corrected[i].strftime("%H:%M hs")
            dp.bot.sendMessage(chat_id='@miralosmoriralertas', text=msg)

def calendar_group_remainder(dp):
    cites_url = "http://miralosmorserver.pythonanywhere.com/api/calendar/all"
    cites_req = requests.get(cites_url)
    cites_dict = cites_req.json()
    cites_hour = [c['start'] for c in cites_dict]
    cite_stamps = [datetime.strptime(h, '%Y-%m-%dT%H:%M:%S.000Z') for h in cites_hour]
    cite_stamps_corrected = [(h - timedelta(hours=3)) for h in cite_stamps]
    for i in range(len(cite_stamps_corrected)):
        if datetime.today().date() == cite_stamps_corrected[i].date():
            if (cite_stamps[i] > datetime.now()) and (cite_stamps[i] < (datetime.now() + timedelta(hours=1))):
                msg = "Acordate que a las " + cite_stamps_corrected[i].strftime("%H:%M hs") + " tenemos '" + cites_dict[i]['title'] + "'"
                dp.bot.sendMessage(chat_id='@miralosmoriralertas', text=msg)
    

def set_timer(update, context):
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = int(context.args[0])
        if due < 0:
            update.message.reply_text('Sorry we can not go back to future!')
            return

        # Add job to queue and stop current one if there is a timer already
        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()
        new_job = context.job_queue.run_repeating(calendar_notif, interval = due, context=chat_id)
        context.chat_data['job'] = new_job

        update.message.reply_text('Timer successfully set!')

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <seconds>')


def unset(update, context):
    """Remove the job if the user changed their mind."""
    if 'job' not in context.chat_data:
        update.message.reply_text('You have no active timer')
        return

    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']

    update.message.reply_text('Timer successfully unset!')


def main(d_or_r):
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))
    #dp.add_handler(CommandHandler("set", set_timer,
     #                             pass_args=True,
      #                            pass_job_queue=True,
       #                           pass_chat_data=True))

    #dp.add_handler(CommandHandler("unset", unset, pass_chat_data=True))

    h = "2020-09-22T12:00:00.000Z"

    daily_cal = datetime.strptime(h, '%Y-%m-%dT%H:%M:%S.000Z')

    #dp.job_queue.run_daily(calendar_group, time=daily_cal)
    #dp.job_queue.run_repeating(calendar_group_remainder, interval=timedelta(minutes=55))

    msg = "mensaje de prueba"
    #dp.bot.sendMessage(chat_id='@miralosmoriralertas', text=msg)
    # Start the Bot
    if d_or_r == "daily":
        print("daily")
        calendar_group(dp)
    else:
        print("reminder")
        calendar_group_remainder(dp)

    #run(updater)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    #updater.idle()


if __name__ == '__main__':
    if  len(sys.argv) > 1:
        main(sys.argv[1])