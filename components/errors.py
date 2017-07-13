def no_library_support(bot, update):
    chat_id = update.effective_chat.id
    text = "This feature will be available very soon."
    bot.sendMessage(chat_id, text)
