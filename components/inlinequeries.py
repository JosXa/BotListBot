from collections import Iterable

import emoji
from typing import Dict, TypeVar
from uuid import uuid4

import captions
import const
import mdformat
import search
import util
from actions import *
from components import botlistchat, favorites
from dialog import messages
from flow.actionbutton import ActionButton
from flow.context import FlowContext
from models import Bot, Category, Favorite, Statistic, User
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResult, InlineQueryResultArticle, \
    InputTextMessageContent, ParseMode, Update
from telegram.ext import CallbackContext, Dispatcher

MAX_BOTS = 30
SEARCH_QUERY_MIN_LENGTH = 2
CONTRIBUTING_QUERIES = [const.DeepLinkingActions.CONTRIBUTING, 'ctrbt', 'contrib']
EXAMPLES_QUERIES = ['example', const.DeepLinkingActions.EXAMPLES]


# TODO:
class MessageBlueprint:
    pass


class MessageBuilder:
    def __init__(self, text):
        pass

    def render(self) -> MessageBlueprint:
        raise NotImplemented  # TODO


# ENDTODO


class ArticleBuilder:
    def __init__(self, title: str = None):
        self.title = title
        self.message_text: str = None
        self.parse_mode: ParseMode = None
        self.disable_web_page_preview: bool = True
        self._id = None

        # Data for custom values
        self.data: Dict = {}

    def render(self, result_action_id=None, callback_manager=None) -> InlineQueryResultArticle:
        if not self._id:
            if self.data:
                if not all((callback_manager, result_action_id)):
                    raise ValueError("If `data` is provided, the `result_action_id` and `callback_manager` arguments "
                                     "must be given in order to persist the values.")
                self._id = callback_manager.create_callback(result_action_id, self.data)
            else:
                self._id = str(uuid4())  # No callback necessary

        return InlineQueryResultArticle(
            action=self._id,
            title=self.title,
            input_message_content=InputTextMessageContent(
                message_text=self.message_text,
                parse_mode=self.parse_mode,
                disable_web_page_preview=self.disable_web_page_preview
            )
        )


Articles = TypeVar([ArticleBuilder, InlineQueryResult])


class ArticleContainer:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.results = None
        self.head = []
        self.footer = []

    @staticmethod
    def __make_list(articles):
        if not isinstance(articles, Iterable):
            articles = [articles]
        return articles

    def set_head(self, articles):
        self.head = self.__make_list(articles)

    def set_footer(self, articles):
        self.footer = self.__make_list(articles)

    def add_article(self, articles: Articles):
        self.results.append(articles)


def query_too_short_article():
    art = ArticleBuilder(
        title='Your search term must be at least {} characters long.'.format(SEARCH_QUERY_MIN_LENGTH)
    )
    art.message_text = '[I am a stupid, crazy fool.](https://www.youtube.com/watch?v=DLzxrzFCyOs)'
    art.parse_mode = 'markdown'
    return art


def new_bots_article():
    from components.explore import _new_bots_text
    msg_text = messages.PROMOTION_MESSAGE + '\n\n' + _new_bots_text()
    return InlineQueryResultArticle(
        action=uuid4(),
        title='🆕 New Bots',
        input_message_content=InputTextMessageContent(message_text=msg_text, parse_mode="Markdown"),
        description='Bots added since the last update',
        # thumb_url='http://www.colorcombos.com/images/colors/FF0000.png',
    )


def category_article(cat):
    cat_bots = Bot.of_category_without_new(cat)
    txt = messages.PROMOTION_MESSAGE + '\n\n'
    txt += "There are *{}* bots in the category *{}*:\n\n".format(len(cat_bots), str(cat))
    txt += '\n'.join([str(b) for b in cat_bots])
    return InlineQueryResultArticle(
        action=uuid4(),
        title=emoji.emojize(cat.emojis, use_aliases=True) + cat.name,
        input_message_content=InputTextMessageContent(message_text=txt,
                                                      parse_mode=ParseMode.MARKDOWN),
        description=cat.extra,
        # thumb_url='https://pichoster.net/images/2017/03/13/cfa5e29e29e772373242bc177a9e5479.jpg'
    )


def bot_article(b):
    txt = '{} ➡️ {}'.format(messages.rand_call_to_action(), b.detail_text)
    txt += '\n\n' + messages.PROMOTION_MESSAGE
    buttons = [
        [
            ActionButton(Actions.ADD_TO_FAVORITES, view_data=BotNotifyModel(bot=b, discreet=True)),
            ActionButton(Actions.EDIT_BOT, view_data=BotNotifyModel(bot=b), switch_inline_current_chat=b.username)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    return InlineQueryResultArticle(
        action=uuid4(),
        title=b.str_no_md,
        input_message_content=InputTextMessageContent(message_text=txt,
                                                      parse_mode=ParseMode.MARKDOWN),
        description=b.description if b.description else b.name if b.name else None,
        reply_markup=reply_markup
        # thumb_url='http://www.colorcombos.com/images/colors/FF0000.png'
    )


def all_bot_results_article(lst, too_many_results):
    txt = messages.PROMOTION_MESSAGE + '\n\n'
    txt += "{} one of these {} bots:\n\n".format(messages.rand_call_to_action(), len(lst))
    txt += '\n'.join([str(b) for b in lst])
    return InlineQueryResultArticle(
        action=uuid4(),
        title='{} {} ʙᴏᴛ ʀᴇsᴜʟᴛs'.format(
            mdformat.smallcaps("Send"),
            len(lst)),
        input_message_content=InputTextMessageContent(message_text=txt[:4096],
                                                      parse_mode=ParseMode.MARKDOWN)
        # description=b.description if b.description else b.name if b.name else None,
        # thumb_url='http://www.colorcombos.com/images/colors/FF0000.png'
    )


def favorites_article(user):
    fav_list = Favorite.select_all(user)
    text = favorites._favorites_categories_md(fav_list) + '\n\n' + messages.PROMOTION_MESSAGE
    return InlineQueryResultArticle(
        action=uuid4(),
        title=captions.FAVORITES,
        input_message_content=InputTextMessageContent(message_text=text,
                                                      parse_mode="Markdown"),
    )


def hint_article(msg, reply_markup, key):
    return InlineQueryResultArticle(
        action=uuid4(),
        title=key.replace('#', '').capitalize() + ' hint',
        input_message_content=InputTextMessageContent(
            message_text=msg,
            parse_mode="Markdown",
            disable_web_page_preview=True
        ),
        reply_markup=reply_markup
    )


def inlinequery_handler(update: Update, context: FlowContext):
    query = update.inline_query.query.lower()

    # TODO: remove or enhance eventually, this is potentially very spammy
    # Statistic.of(update, 'inlinequery', '"{}"'.format(query), Statistic.DETAILED)

    user = User.from_update(update)
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
        context.bot.answerInlineQuery(update.inline_query.id, results=results_list)
        return

    if query in CONTRIBUTING_QUERIES:
        results_list.append(InlineQueryResultArticle(
            action=uuid4(),
            title='Contributing',
            input_message_content=InputTextMessageContent(message_text=messages.CONTRIBUTING,
                                                          parse_mode="Markdown"),
        ))
        context.bot.answerInlineQuery(update.inline_query.id, results=results_list, cache_time=600)
        return

    if query in EXAMPLES_QUERIES:
        results_list.append(InlineQueryResultArticle(
            action=uuid4(),
            title='Examples',
            input_message_content=InputTextMessageContent(message_text=messages.EXAMPLES,
                                                          parse_mode="Markdown"),
        ))
        context.bot.answerInlineQuery(update.inline_query.id, results=results_list, cache_time=600)
        return

    if query in (const.DeepLinkingActions.RULES, '#rules'):
        results_list.append(InlineQueryResultArticle(
            action=uuid4(),
            title='@BotListChat Rules',
            input_message_content=InputTextMessageContent(message_text=messages.BOTLISTCHAT_RULES,
                                                          parse_mode="Markdown",
                                                          disable_web_page_preview=True),
        ))
        context.bot.answerInlineQuery(update.inline_query.id, results=results_list, cache_time=600)
        return

    if query == const.DeepLinkingActions.FAVORITES and user.has_favorites:
        results_list.append(favorites_article(user))
        context.bot.answerInlineQuery(update.inline_query.id, results=results_list, cache_time=0,
                                      is_personal=True)
        return

    msg, reply_markup, key = botlistchat.get_hint_message_and_markup(query)
    if msg is not None:
        results_list.append(hint_article(msg, reply_markup, key))
        context.bot.answerInlineQuery(update.inline_query.id, results=results_list, cache_time=600)
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
            context.bot.answerInlineQuery(update.inline_query.id, results=results_list,
                                          switch_pm_text="See all results" if too_many_results else "Search in private chat",
                                          switch_pm_parameter=util.encode_base64(query), cache_time=0,
                                          is_personal=True)
        else:
            context.bot.answerInlineQuery(update.inline_query.id, results=results_list, cache_time=0,
                                          is_personal=True)
    else:
        if user.has_favorites:
            results_list.append(favorites_article(user))
        results_list.append(new_bots_article())
        categories = Category.select_all()
        for c in categories:
            results_list.append(category_article(c))

        if invalid_search_term or not input_given:
            context.bot.answerInlineQuery(update.inline_query.id, results=results_list, cache_time=0,
                                          is_personal=True)
        else:
            context.bot.answerInlineQuery(update.inline_query.id, results=results_list,
                                          switch_pm_text="No results. Contribute a bot?",
                                          switch_pm_parameter='contributing', cache_time=0,
                                          is_personal=True)


