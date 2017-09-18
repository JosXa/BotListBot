import json
import logging
import re
import traceback
from pprint import pprint

from telegram.ext import CallbackQueryHandler
from telegram.ext import ChosenInlineResultHandler
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import Filters
from telegram.ext import InlineQueryHandler
from telegram.ext import MessageHandler
from telegram.ext import RegexHandler

import captions
import settings
import util
from components import botlistchat, help, favorites, admin, basic, botproperties, botlist, broadcasts, explore
from components import contributions
from components import eastereggs
from components import inlinequeries
from components.basic import all_handler
from components.explore import show_new_bots, send_bot_details, select_category, send_category
from components.misc import access_token, set_notifications
from components.misc import t3chnostats
from components.search import search_handler, search_query
from const import CallbackActions, BotStates
from dialog import messages
from lib import InlineCallbackHandler
from misc import manage_subscription
from model import Keyword
from model import Statistic
from model import User, Category, Bot, Favorite, Country, Suggestion

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


def callback_router(bot, update, chat_data, user_data, job_queue):
    obj = json.loads(str(update.callback_query.data))
    user = User.from_update(update)

    try:
        if 'a' in obj:
            action = obj['a']

            # BOTLISTCHAT
            if action == CallbackActions.DELETE_CONVERSATION:
                botlistchat.delete_conversation(bot, update, chat_data)
            # HELP
            elif action == CallbackActions.HELP:
                help.help(bot, update)
            elif action == CallbackActions.CONTRIBUTING:
                help.contributing(bot, update)
            elif action == CallbackActions.EXAMPLES:
                help.examples(bot, update)
            # BASIC QUERYING
            elif action == CallbackActions.SELECT_CATEGORY:
                select_category(bot, update, chat_data)
            elif action == CallbackActions.SELECT_BOT_FROM_CATEGORY:
                category = Category.get(id=obj['id'])
                send_category(bot, update, chat_data, category)
            elif action == CallbackActions.SEND_BOT_DETAILS:
                item = Bot.get(id=obj['id'])
                send_bot_details(bot, update, chat_data, item)
            # FAVORITES
            elif action == CallbackActions.TOGGLE_FAVORITES_LAYOUT:
                value = obj['v']
                favorites.toggle_favorites_layout(bot, update, value)
            elif action == CallbackActions.ADD_FAVORITE:
                favorites.add_favorite_handler(bot, update)
            elif action == CallbackActions.REMOVE_FAVORITE_MENU:
                favorites.remove_favorite_menu(bot, update)
            elif action == CallbackActions.REMOVE_FAVORITE:
                to_remove = Favorite.get(id=obj['id'])
                bot_details = to_remove.bot
                to_remove.delete_instance()
                if obj.get('details'):
                    send_bot_details(bot, update, chat_data, bot_details)
                else:
                    favorites.remove_favorite_menu(bot, update)
            elif action == CallbackActions.SEND_FAVORITES_LIST:
                favorites.send_favorites_list(bot, update)
            elif action == CallbackActions.ADD_ANYWAY:
                favorites.add_custom(bot, update, obj['u'])
            elif action == CallbackActions.ADD_TO_FAVORITES:
                details = obj.get('details')
                discreet = obj.get('discreet', False) or details
                item = Bot.get(id=obj['id'])
                favorites.add_favorite(bot, update, item, callback_alert=discreet)
                if details:
                    send_bot_details(bot, update, chat_data, item)
            # ACCEPT/REJECT BOT SUBMISSIONS
            elif action == CallbackActions.APPROVE_REJECT_BOTS:
                custom_approve_list = [Bot.get(id=obj['id'])]
                admin.approve_bots(bot, update, override_list=custom_approve_list)
            elif action == CallbackActions.ACCEPT_BOT:
                to_accept = Bot.get(id=obj['id'])
                admin.edit_bot_category(bot, update, to_accept, CallbackActions.BOT_ACCEPTED)
                # Run in x minutes, giving the moderator enough time to edit bot details
                job_queue.run_once(lambda b, job:
                                   botlistchat.notify_group_submission_accepted(b, job, to_accept),
                                   settings.BOT_ACCEPTED_IDLE_TIME * 60)
            elif action == CallbackActions.RECOMMEND_MODERATOR:
                bot_in_question = Bot.get(id=obj['id'])
                admin.recommend_moderator(bot, update, bot_in_question, obj['page'])
            elif action == CallbackActions.SELECT_MODERATOR:
                bot_in_question = Bot.get(id=obj['bot_id'])
                moderator = User.get(id=obj['uid'])
                admin.share_with_moderator(bot, update, bot_in_question, moderator)
                admin.approve_bots(bot, update, obj['page'])
            elif action == CallbackActions.REJECT_BOT:
                to_reject = Bot.get(id=obj['id'])
                notification = obj.get('ntfc', True)
                admin.reject_bot_submission(bot, update, to_reject, verbose=False, notify_submittant=notification)
                admin.approve_bots(bot, update, obj['page'])
            elif action == CallbackActions.BOT_ACCEPTED:
                to_accept = Bot.get(id=obj['bid'])
                category = Category.get(id=obj['cid'])
                admin.accept_bot_submission(bot, update, to_accept, category)
            elif action == CallbackActions.COUNT_THANK_YOU:
                new_count = obj.get('count', 1)
                basic.count_thank_you(bot, update, new_count)
            # ADD BOT
            # elif action == CallbackActions.ADD_BOT_SELECT_CAT:
            #     category = Category.get(id=obj['id'])
            #     admin.add_bot(bot, update, chat_data, category)
            # EDIT BOT
            elif action == CallbackActions.EDIT_BOT:
                to_edit = Bot.get(id=obj['id'])
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_SELECT_CAT:
                to_edit = Bot.get(id=obj['id'])
                admin.edit_bot_category(bot, update, to_edit)
            elif action == CallbackActions.EDIT_BOT_CAT_SELECTED:
                to_edit = Bot.get(id=obj['bid'])
                cat = Category.get(id=obj['cid'])
                botproperties.change_category(bot, update, to_edit, cat)
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_COUNTRY:
                to_edit = Bot.get(id=obj['id'])
                botproperties.set_country_menu(bot, update, to_edit)
            elif action == CallbackActions.SET_COUNTRY:
                to_edit = Bot.get(id=obj['bid'])
                if obj['cid'] == 'None':
                    country = None
                else:
                    country = Country.get(id=obj['cid'])
                botproperties.set_country(bot, update, to_edit, country)
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_DESCRIPTION:
                to_edit = Bot.get(id=obj['id'])
                botproperties.set_text_property(bot, update, chat_data, 'description', to_edit)
            elif action == CallbackActions.EDIT_BOT_EXTRA:
                to_edit = Bot.get(id=obj['id'])
                botproperties.set_text_property(bot, update, chat_data, 'extra', to_edit)
            elif action == CallbackActions.EDIT_BOT_NAME:
                to_edit = Bot.get(id=obj['id'])
                botproperties.set_text_property(bot, update, chat_data, 'name', to_edit)
            elif action == CallbackActions.EDIT_BOT_USERNAME:
                to_edit = Bot.get(id=obj['id'])
                botproperties.set_text_property(bot, update, chat_data, 'username', to_edit)
            # elif action == CallbackActions.EDIT_BOT_KEYWORDS:
            #     to_edit = Bot.get(id=obj['id'])
            #     botproperties.set_keywords_init(bot, update, chat_data, to_edit)
            elif action == CallbackActions.APPLY_ALL_CHANGES:
                to_edit = Bot.get(id=obj['id'])
                admin.apply_all_changes(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_INLINEQUERIES:
                to_edit = Bot.get(id=obj['id'])
                value = bool(obj['value'])
                botproperties.toggle_value(bot, update, 'inlinequeries', to_edit, value)
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_OFFICIAL:
                to_edit = Bot.get(id=obj['id'])
                value = bool(obj['value'])
                botproperties.toggle_value(bot, update, 'official', to_edit, value)
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_OFFLINE:
                to_edit = Bot.get(id=obj['id'])
                value = bool(obj['value'])
                botproperties.toggle_value(bot, update, 'offline', to_edit, value)
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_SPAM:
                to_edit = Bot.get(id=obj['id'])
                value = bool(obj['value'])
                botproperties.toggle_value(bot, update, 'spam', to_edit, value)
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.CONFIRM_DELETE_BOT:
                to_delete = Bot.get(id=obj['id'])
                botproperties.delete_bot_confirm(bot, update, to_delete)
            elif action == CallbackActions.DELETE_BOT:
                to_edit = Bot.get(id=obj['id'])
                botproperties.delete_bot(bot, update, to_edit)
                send_category(bot, update, to_edit.category)
            elif action == CallbackActions.ACCEPT_SUGGESTION:
                suggestion = Suggestion.get(id=obj['id'])
                suggestion.apply()
                admin.approve_suggestions(bot, update, page=obj['page'])
            elif action == CallbackActions.REJECT_SUGGESTION:
                suggestion = Suggestion.get(id=obj['id'])
                suggestion.delete_instance()
                admin.approve_suggestions(bot, update, page=obj['page'])
            elif action == CallbackActions.CHANGE_SUGGESTION:
                suggestion = Suggestion.get(id=obj['id'])
                botproperties.change_suggestion(bot, update, suggestion, page_handover=obj['page'])
            elif action == CallbackActions.SWITCH_SUGGESTIONS_PAGE:
                page = obj['page']
                admin.approve_suggestions(bot, update, page)
            elif action == CallbackActions.SWITCH_APPROVALS_PAGE:
                admin.approve_bots(bot, update, page=obj['page'])
            elif action == CallbackActions.SET_NOTIFICATIONS:
                set_notifications(bot, update, obj['value'])
            elif action == CallbackActions.NEW_BOTS_SELECTED:
                show_new_bots(bot, update, chat_data, back_button=True)
            elif action == CallbackActions.ABORT_SETTING_KEYWORDS:
                to_edit = Bot.get(id=obj['id'])
                admin.edit_bot(bot, update, chat_data, to_edit)
            # SENDING BOTLIST
            elif action == CallbackActions.SEND_BOTLIST:
                silent = obj.get('silent', False)
                re_send = obj.get('re', False)
                botlist.send_botlist(bot, update, resend=re_send, silent=silent)
            elif action == CallbackActions.RESEND_BOTLIST:
                botlist.send_botlist(bot, update, resend=True)
            # BROADCASTING
            elif action == 'send_broadcast':
                broadcasts.send_broadcast(bot, update, user_data)
            elif action == 'pin_message':
                broadcasts.pin_message(bot, update, obj['mid'])
            elif action == 'add_thank_you':
                basic.add_thank_you_button(bot, update, obj['cid'], obj['mid'])
            # EXPLORING
            elif action == CallbackActions.EXPLORE_NEXT:
                explore.explore(bot, update, chat_data)
    except Exception as e:
        traceback.print_exc()

        # get the callback action in plaintext
        actions = dict(CallbackActions.__dict__)
        a = next(k for k, v in actions.items() if v == obj.get('a'))
        util.send_md_message(bot, settings.ADMINS[0],
                             "Exception in callback query for {}:\n{}\n\nWith CallbackAction {}\n\nWith data:\n{}".format(
                                 user.markdown_short,
                                 util.escape_markdown(e),
                                 util.escape_markdown(a),
                                 util.escape_markdown(str(obj))
                             ))
    finally:
        bot.answerCallbackQuery(update.callback_query.id)
        return ConversationHandler.END


def forward_router(bot, update, chat_data):
    text = update.message.text

    # match first username in forwarded message
    try:
        username = re.match(settings.REGEX_BOT_IN_TEXT, text).groups()[0]
        if username == '@' + settings.SELF_BOT_NAME:
            return  # ignore

        item = Bot.get(Bot.username == username)

        send_bot_details(bot, update, chat_data, item)

    except (AttributeError, Bot.DoesNotExist):
        pass  # no valid username in forwarded message


def reply_router(bot, update, chat_data):
    text = update.message.reply_to_message.text

    if text == messages.ADD_FAVORITE:
        query = update.message.text
        favorites.add_favorite_handler(bot, update, query)
    elif text == messages.SEARCH_MESSAGE:
        query = update.message.text
        search_query(bot, update, chat_data, query)

    # BOTPROPERTIES
    bot_properties = ['description', 'extra', 'name', 'username']
    try:
        partition = text.partition(messages.BOTPROPERTY_STARTSWITH)
    except AttributeError as e:
        print("An exception has been raised for partitioning the text in reply_to_message (reply_router):")
        print(e)
        pprint(update.message.reply_to_message.to_dict())
        return  # raise DispatcherHandlerStop # TODO
    if partition[1] != '':
        bot_property = next(p for p in bot_properties if partition[2].startswith(p))
        # Reply for setting a bot property
        botproperties.set_text_property(bot, update, chat_data, bot_property)
        return  # raise DispatcherHandlerStop # TODO
    elif text == messages.BAN_MESSAGE:
        query = update.message.text
        admin.ban_handler(bot, update, query, True)
    elif text == messages.UNBAN_MESSAGE:
        query = update.message.text
        admin.ban_handler(bot, update, query, False)


def register(dp):
    keywords_handler = ConversationHandler(
        entry_points=[
            InlineCallbackHandler(CallbackActions.EDIT_BOT_KEYWORDS,
                                  botproperties.set_keywords_init,
                                  serialize=lambda data: dict(to_edit=Bot.get(id=data['id'])),
                                  pass_chat_data=True)
        ],
        states={
            BotStates.SENDING_KEYWORDS: [
                MessageHandler(Filters.text, botproperties.add_keyword, pass_chat_data=True),
                InlineCallbackHandler(CallbackActions.REMOVE_KEYWORD,
                                      botproperties.remove_keyword,
                                      serialize=lambda data: dict(
                                          to_edit=Bot.get(id=data['id']),
                                          keyword=Keyword.get(id=data['kwid'])
                                      ),
                                      pass_chat_data=True)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(callback_router, pass_chat_data=True, pass_user_data=True, pass_job_queue=True)
        ],
        per_user=True,
        allow_reentry=False

    )

    dp.add_handler(keywords_handler)

    broadcasting_handler = ConversationHandler(
        entry_points=[
            InlineCallbackHandler('broadcast', broadcasts.broadcast, pass_user_data=True),
            CommandHandler("broadcast", broadcasts.broadcast, pass_user_data=True),
            CommandHandler("bc", broadcasts.broadcast, pass_user_data=True)
        ],
        states={
            BotStates.BROADCASTING: [
                MessageHandler(Filters.text, broadcasts.broadcast_preview, pass_user_data=True),
            ],
        },
        fallbacks=[],
        per_user=True,
        per_chat=False,
        allow_reentry=True
    )
    dp.add_handler(broadcasting_handler)

    dp.add_handler(CallbackQueryHandler(callback_router, pass_chat_data=True, pass_user_data=True, pass_job_queue=True))
    dp.add_handler(CommandHandler(('cat', 'category', 'categories'), select_category, pass_chat_data=True))
    dp.add_handler(CommandHandler(('s', 'search'), search_handler, pass_args=True, pass_chat_data=True))

    dp.add_handler(MessageHandler(Filters.reply, reply_router, pass_chat_data=True), group=0)
    dp.add_handler(MessageHandler(Filters.forwarded, forward_router, pass_chat_data=True))

    dp.add_handler(CommandHandler("admin", admin.menu))
    dp.add_handler(CommandHandler("a", admin.menu))

    # admin menu
    dp.add_handler(RegexHandler(captions.APPROVE_BOTS + '.*', admin.approve_bots))
    dp.add_handler(RegexHandler(captions.APPROVE_SUGGESTIONS + '.*', admin.approve_suggestions))
    dp.add_handler(RegexHandler(captions.PENDING_UPDATE + '.*', admin.pending_update))
    dp.add_handler(RegexHandler(captions.SEND_BOTLIST, admin.prepare_transmission, pass_chat_data=True))
    dp.add_handler(RegexHandler(captions.FIND_OFFLINE, admin.send_offline))
    dp.add_handler(RegexHandler(captions.SEND_CONFIG_FILES, admin.send_runtime_files))
    dp.add_handler(RegexHandler(captions.SEND_ACTIVITY_LOGS, admin.send_activity_logs))

    # main menu
    dp.add_handler(RegexHandler(captions.ADMIN_MENU, admin.menu))
    dp.add_handler(RegexHandler(captions.REFRESH, admin.menu))
    dp.add_handler(RegexHandler(captions.CATEGORIES, select_category, pass_chat_data=True))
    dp.add_handler(RegexHandler(captions.EXPLORE, explore.explore, pass_chat_data=True))
    dp.add_handler(RegexHandler(captions.FAVORITES, favorites.send_favorites_list))
    dp.add_handler(RegexHandler(captions.NEW_BOTS, show_new_bots, pass_chat_data=True))
    dp.add_handler(RegexHandler(captions.SEARCH, search_handler, pass_chat_data=True))
    dp.add_handler(RegexHandler(captions.CONTRIBUTING, help.contributing))
    dp.add_handler(RegexHandler(captions.EXAMPLES, help.examples))
    dp.add_handler(RegexHandler(captions.HELP, help.help))

    dp.add_handler(RegexHandler("^/edit\d+$", admin.edit_bot, pass_chat_data=True), group=1)
    dp.add_handler(CommandHandler('reject', admin.reject_bot_submission))
    dp.add_handler(CommandHandler('rej', admin.reject_bot_submission))

    dp.add_handler(CommandHandler('new', contributions.new_bot_submission, pass_args=True, pass_chat_data=True))
    dp.add_handler(RegexHandler('.*#new.*', contributions.new_bot_submission, pass_chat_data=True), group=1)
    dp.add_handler(CommandHandler('offline', contributions.notify_bot_offline, pass_args=True))
    dp.add_handler(RegexHandler('.*#offline.*', contributions.notify_bot_offline), group=1)
    dp.add_handler(CommandHandler('spam', contributions.notify_bot_spam, pass_args=True))
    dp.add_handler(RegexHandler('.*#spam.*', contributions.notify_bot_spam), group=1)
    dp.add_handler(RegexHandler('^{}$'.format(settings.REGEX_BOT_ONLY), send_bot_details, pass_chat_data=True))

    dp.add_handler(CommandHandler('help', help.help))
    dp.add_handler(CommandHandler(("contribute", "contributing"), help.contributing))
    dp.add_handler(CommandHandler("examples", help.examples))
    dp.add_handler(CommandHandler("rules", help.rules))

    dp.add_handler(CommandHandler(("addfav", "addfavorite"), favorites.add_favorite_handler, pass_args=True))
    dp.add_handler(CommandHandler(("f", "fav", "favorites"), favorites.send_favorites_list))

    dp.add_handler(CommandHandler(("e", "explore"), explore.explore, pass_chat_data=True))
    dp.add_handler(CommandHandler("official", explore.show_official))

    dp.add_handler(CommandHandler('ban', lambda bot, update, args: admin.ban_handler(
        bot, update, args, True), pass_args=True))
    dp.add_handler(CommandHandler('unban', lambda bot, update, args: admin.ban_handler(
        bot, update, args, False), pass_args=True))
    dp.add_handler(CommandHandler('t3chno', t3chnostats))
    dp.add_handler(CommandHandler('random', eastereggs.send_random_bot))
    dp.add_handler(CommandHandler('easteregg', eastereggs.send_next, pass_args=True))

    dp.add_handler(CommandHandler("subscribe", manage_subscription))
    dp.add_handler(CommandHandler("newbots", show_new_bots, pass_chat_data=True))

    dp.add_handler(CommandHandler("accesstoken", access_token))

    dp.add_handler(CommandHandler(('log', 'logs'), admin.send_activity_logs))
    dp.add_handler(CommandHandler(('debug', 'analysis', 'ana', 'analyze'),
                                  lambda bot, update: admin.send_activity_logs(bot, update, Statistic.ANALYSIS)))
    dp.add_handler(CommandHandler('info', lambda bot, update: admin.send_activity_logs(bot, update, Statistic.INFO)))
    dp.add_handler(
        CommandHandler('detailed', lambda bot, update: admin.send_activity_logs(bot, update, Statistic.DETAILED)))
    dp.add_handler(
        CommandHandler(('warn', 'warning'), lambda bot, update: admin.send_activity_logs(bot, update, Statistic.WARN)))
    dp.add_handler(
        CommandHandler('important', lambda bot, update: admin.send_activity_logs(bot, update, Statistic.IMPORTANT)))

    dp.add_handler(MessageHandler(Filters.text, lambda bot, update: botlistchat.text_message_logger(bot, update, log)),
                   group=99)

    dp.add_handler(ChosenInlineResultHandler(inlinequeries.chosen_result, pass_chat_data=True))
    dp.add_handler(InlineQueryHandler(inlinequeries.inlinequery_handler, pass_chat_data=True))
    dp.add_handler(MessageHandler(Filters.all, all_handler, pass_chat_data=True), group=98)
