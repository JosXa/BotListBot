from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

import util
from const import CallbackActions


def manage_subscription(bot, update):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if util.is_group_message(update):
        admins = bot.get_chat_administrators(chat_id)
        if user_id not in admins:
            bot.send_failure(chat_id, "Sorry, but only Administrators of this group are allowed "
                                                    "to manage subscriptions.")
            return

    text = "Would you like to be notified when new bots arrive at the @BotList?"
    buttons = [[
        InlineKeyboardButton(util.success("Yes"),
                             callback_data=util.callback_for_action(CallbackActions.SET_NOTIFICATIONS,
                                                                    {'value': True})),
        InlineKeyboardButton("No", callback_data=util.callback_for_action(CallbackActions.SET_NOTIFICATIONS,
                                                                          {'value': False}))]]
    reply_markup = InlineKeyboardMarkup(buttons)
    msg = util.send_md_message(bot, chat_id, text, reply_markup=reply_markup)
    return ConversationHandler.END
