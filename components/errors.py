from telegram import Update
from telegram.ext import CallbackContext


def no_library_support(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = "This feature will be available very soon."
    context.bot.sendMessage(chat_id, text)
