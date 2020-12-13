from typing import Optional

from telegram import (
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ParseMode,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
    Update,
    TelegramError,
)
from telegram.ext import ConversationHandler, run_async

from botlistbot import appglobals
from botlistbot import captions
from botlistbot import const
from botlistbot import search
from botlistbot import settings
from botlistbot import util
from botlistbot.components import basic, botlistchat
from botlistbot.components.botlistchat import get_hint_data
from botlistbot.components.explore import send_bot_details
from botlistbot.dialog import messages
from botlistbot.helpers import try_delete_after
from botlistbot.models import User


def search_query(bot, update: Update, chat_data, query, send_errors=True):
    cid: int = update.effective_chat.id
    user: User = User.from_update(update)
    is_admin: bool = cid in settings.MODERATORS
    replied_to_message_id: Optional[int] = util.original_reply_id(update)
    is_suggestion_by_other: bool = (
        update.effective_chat and update.effective_chat.id == settings.BOTLISTCHAT_ID
    )

    results = search.search_bots(query)

    reply_markup = (
        ReplyKeyboardMarkup(basic.main_menu_buttons(is_admin), resize_keyboard=True)
        if util.is_private_message(update)
        else None
    )
    if results:
        if len(results) == 1:
            update.effective_message.delete()
            if is_suggestion_by_other:
                header = f"{user.markdown_short} found the following bot for you:"
            else:
                header = "I found the following bot for you:"
            return send_bot_details(
                bot, update, chat_data, results[0], header_msg=header
            )
        too_many_results = len(results) > settings.MAX_SEARCH_RESULTS

        bots_list = ""
        if cid in settings.MODERATORS:  # private chat with moderator
            # append edit buttons
            bots_list += "\n".join(
                ["{} — /edit{} 🛃".format(b, b.id) for b in list(results)[:100]]
            )
        else:
            bots_list += "\n".join(
                [str(b) for b in list(results)[: settings.MAX_SEARCH_RESULTS]]
            )
        bots_list += "\n…" if too_many_results else ""
        bots_list = messages.SEARCH_RESULTS.format(
            bots=bots_list,
            num_results=len(results),
            plural="s" if len(results) > 1 else "",
            query=query,
        )

        if util.is_group_message(update) and not update.message.reply_to_message:
            try:
                bot.formatter.send_message(
                    update.effective_user.id,
                    bots_list,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True,
                )
                reply_markup, callback = botlistchat.append_restricted_delete_button(
                    update, chat_data, InlineKeyboardMarkup([[]])
                )
                msg = bot.formatter.send_message(
                    update.effective_chat.id,
                    f"Hey {user.plaintext}, let's not annoy the others. I sent you the search results "
                    f"[in private chat](https://t.me/{settings.SELF_BOT_NAME}).",
                    disable_web_page_preview=True,
                    reply_markup=reply_markup,
                )
                callback(msg)
                update.effective_message.delete()
            except TelegramError:
                hint_msg, hint_reply_markup, _ = get_hint_data("#private")
                bot.formatter.send_message(
                    update.effective_chat.id,
                    hint_msg,
                    reply_markup=hint_reply_markup,
                    reply_to_message_id=update.effective_message.id,
                    disable_web_page_preview=True,
                )
            return ConversationHandler.END

        if is_suggestion_by_other and replied_to_message_id:
            bots_list = f"{user.markdown_short} suggests to search and {bots_list}"

        bot.formatter.send_message(
            update.effective_chat.id,
            bots_list,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            reply_to_message_id=replied_to_message_id,
        )
        update.effective_message.delete()
    else:
        if send_errors:
            callback = None
            if util.is_group_message(update):
                reply_markup, callback = botlistchat.append_restricted_delete_button(
                    update, chat_data, InlineKeyboardMarkup([[]])
                )
            msg = update.message.reply_text(
                util.failure(
                    "Sorry, I couldn't find anything related "
                    "to *{}* in the @BotList. /search".format(
                        util.escape_markdown(query)
                    )
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup,
            )
            if callback:
                callback(msg)

    return ConversationHandler.END


@run_async
def search_handler(bot, update, chat_data, args=None):
    if args:
        search_query(bot, update, chat_data, " ".join(args))
    else:
        # no search term
        if util.is_group_message(update):
            action = const.DeepLinkingActions.SEARCH
            sent_msg = update.message.reply_text(
                "Please use the search command with arguments, inlinequeries or continue in private. "
                "Example: `/search awesome bot`",
                quote=True,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔎 Search inline", switch_inline_query_current_chat=""
                            ),
                            InlineKeyboardButton(
                                captions.SWITCH_PRIVATE,
                                url="https://t.me/{}?start={}".format(
                                    settings.SELF_BOT_NAME, action
                                ),
                            ),
                        ]
                    ]
                ),
            )
            try_delete_after(
                appglobals.job_queue, [sent_msg, update.effective_message], delay=10
            )
        else:
            update.message.reply_text(
                messages.SEARCH_MESSAGE, reply_markup=ForceReply(selective=True)
            )
    return ConversationHandler.END
