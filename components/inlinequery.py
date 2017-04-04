from uuid import uuid4

import emoji

import mdformat
from telegram import ParseMode

from telegram import InputTextMessageContent

from telegram import InlineQueryResultArticle

import const
import messages
import search
import util
from bot import _new_bots_text
from model import Bot, Category

# CONSTANTS
MAX_BOTS = 30
SEARCH_QUERY_MIN_LENGTH = 3
CONTRIBUTING_QUERIES = ['contributing', 'ctrbt']
EXAMPLES_QUERIES = ['example', 'examples']

def query_too_short_article():
    txt = '[I am a stupid, crazy fool.](https://www.youtube.com/watch?v=DLzxrzFCyOs)'
    return InlineQueryResultArticle(
        id=uuid4(),
        title=util.action_hint('Your search term must be at least {} characters long.'.format(SEARCH_QUERY_MIN_LENGTH)),
        input_message_content=InputTextMessageContent(message_text=txt,
                                                      parse_mode="Markdown",
                                                      disable_web_page_preview=True)
    )


def new_bots_article():
    # append new bots list to result
    msg_text = messages.PROMOTION_MESSAGE + '\n\n' + _new_bots_text()
    return InlineQueryResultArticle(
        id=uuid4(),
        title='🆕 New Bots',
        input_message_content=InputTextMessageContent(message_text=msg_text, parse_mode="Markdown"),
        description='Bots added in the last {} days.'.format(const.BOT_CONSIDERED_NEW),
        # thumb_url='http://www.colorcombos.com/images/colors/FF0000.png',
    )


def category_article(cat):
    bot_list = Bot.of_category(cat)
    txt = messages.PROMOTION_MESSAGE + '\n\n'
    txt += "There are *{}* bots in the category *{}*:\n\n".format(len(bot_list), str(cat))
    txt += '\n'.join([str(b) for b in bot_list])
    return InlineQueryResultArticle(
        id=uuid4(),
        title=emoji.emojize(cat.emojis, use_aliases=True) + cat.name,
        input_message_content=InputTextMessageContent(message_text=txt, parse_mode=ParseMode.MARKDOWN),
        description=cat.extra,
        # thumb_url='https://pichoster.net/images/2017/03/13/cfa5e29e29e772373242bc177a9e5479.jpg'
    )


def bot_article(b):
    # bots_with_description = [b for b in bot_list if b.description is not None]
    txt = '{} ▶️ {}'.format(messages.random_call_to_action(), b.detail_text)
    txt += '\n\n' + messages.PROMOTION_MESSAGE
    return InlineQueryResultArticle(
        id=uuid4(),
        title=b.str_no_md,
        input_message_content=InputTextMessageContent(message_text=txt, parse_mode=ParseMode.MARKDOWN),
        description=b.description if b.description else b.name if b.name else None,
        # thumb_url='http://www.colorcombos.com/images/colors/FF0000.png'
    )


def all_bot_results_article(lst, too_many_results):
    # bots_with_description = [b for b in bot_list if b.description is not None]
    txt = messages.PROMOTION_MESSAGE + '\n\n'
    txt += "{} one of these {} bots:\n\n".format(messages.random_call_to_action(), len(lst))
    txt += '\n'.join([str(b) for b in lst])
    return InlineQueryResultArticle(
        id=uuid4(),
        title='{} {} ʙᴏᴛ ʀᴇsᴜʟᴛs'.format(
            mdformat.smallcaps("Send"),
            len(lst)),
        input_message_content=InputTextMessageContent(message_text=txt, parse_mode=ParseMode.MARKDOWN)
        # description=b.description if b.description else b.name if b.name else None,
        # thumb_url='http://www.colorcombos.com/images/colors/FF0000.png'
    )


# def select_category_article():
#     txt = messages.PROMOTION_MESSAGE + '\n\n'
#     txt += util.action_hint(messages.SELECT_CATEGORY)
#     reply_markup = InlineKeyboardMarkup(_select_category_buttons())
#     return InlineQueryResultArticle(
#         id=uuid4(),
#         title="ᴀʟʟ ᴄᴀᴛᴇɢᴏʀɪᴇs",
#         input_message_content=InputTextMessageContent(message_text=txt,
#                                                       parse_mode=ParseMode.MARKDOWN),
#         reply_markup=reply_markup,
#     )

def inlinequery_handler(bot, update):
    query = update.inline_query.query.lower()
    results_list = list()

    input_given = len(query.strip()) > 0
    query_too_short = 0 < len(query.strip()) < SEARCH_QUERY_MIN_LENGTH

    too_many_results = False
    cat_results = []
    bot_results = []

    if input_given:
        # query category results
        cat_results = search.search_categories(query)

        if not query_too_short:
            # query bot results
            bot_results = list(search.search_bots(query))
            if len(bot_results) > MAX_BOTS:
                bot_results = bot_results[:MAX_BOTS]
                too_many_results = True

    # query for new bots
    if query == messages.NEW_BOTS_INLINEQUERY.lower() or query == 'new':
        results_list.append(new_bots_article())
        bot.answerInlineQuery(update.inline_query.id, results=results_list)
        return

    if query in CONTRIBUTING_QUERIES:
        results_list.append(InlineQueryResultArticle(
            id=uuid4(),
            title='Contributing',
            input_message_content=InputTextMessageContent(message_text=messages.CONTRIBUTING_MESSAGE,
                                                          parse_mode="Markdown"),
        ))
        bot.answerInlineQuery(update.inline_query.id, results=results_list)
        return

    if query in EXAMPLES_QUERIES:
        results_list.append(InlineQueryResultArticle(
            id=uuid4(),
            title='Examples',
            input_message_content=InputTextMessageContent(message_text=messages.EXAMPLES_MESSAGE,
                                                          parse_mode="Markdown"),
        ))
        bot.answerInlineQuery(update.inline_query.id, results=results_list)
        return

    invalid_search_term = query_too_short and not cat_results
    if invalid_search_term:
        results_list.append(query_too_short_article())

    results_available = cat_results or bot_results
    if results_available:
        if len(bot_results) > 1:
            results_list.append(all_bot_results_article(bot_results, too_many_results))
        for c in cat_results:
            results_list.append(category_article(c))
        for b in bot_results:
            results_list.append(bot_article(b))

        if len(bot_results) > 0:
            bot.answerInlineQuery(update.inline_query.id, results=results_list,
                                  switch_pm_text="See all results" if too_many_results else "Search in private chat",
                                  switch_pm_parameter=query)
        else:
            bot.answerInlineQuery(update.inline_query.id, results=results_list)
    else:
        results_list.append(new_bots_article())
        categories = Category.select_all()
        for c in categories:
            results_list.append(category_article(c))

        if invalid_search_term or not input_given:
            bot.answerInlineQuery(update.inline_query.id, results=results_list)
        else:
            bot.answerInlineQuery(update.inline_query.id, results=results_list,
                                  switch_pm_text="No results. Contribute a bot?",
                                  switch_pm_parameter='contributing')
