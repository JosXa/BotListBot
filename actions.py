import emoji
from dataclasses import dataclass
from typing import List, Union

import captions
from custemoji import Emoji
from flow.action import Action, ViewModel, ActionRepository
from models import Bot, Category, Favorite, Keyword, Suggestion, User


# region View Model


@dataclass
class BotViewModel(ViewModel):
    bot: Bot


@dataclass
class RemoveFavoriteModel(ViewModel):
    favorite: Favorite
    show_details: bool


@dataclass
class CategoryModel(ViewModel):
    category: Category


@dataclass
class BotCategoryModel(ViewModel):
    bot: Bot
    category: Category


@dataclass
class LayoutModel(ViewModel):
    value: str


@dataclass
class PaginationModel(ViewModel):
    page: int = 0


@dataclass
class PagedBotModel(PaginationModel, BotViewModel):
    pass


@dataclass
class UserModel(ViewModel):
    user: User


@dataclass
class RecommendAdminModel(BotViewModel):
    moderator: User


@dataclass
class NotificationModel(ViewModel):
    discreet: bool = False
    show_notification: bool = True
    show_alert: bool = False


@dataclass
class BotNotifyModel(NotificationModel, BotViewModel):
    pass


@dataclass
class RejectBotSubmissionModel(ViewModel):
    reason: str = None
    to_reject: Bot = None
    admin_user: User = None
    notify_submittant: bool = True
    verbose: bool = True


@dataclass
class BanModel(ViewModel):
    ban_state: bool


class BanEntityModel(BanModel):
    entity: Union[User, Bot]


@dataclass
class BooleanPropertyModel(ViewModel):
    value: bool


@dataclass
class EditBooleanBotPropertyModel(NotificationModel, BooleanPropertyModel, BotViewModel):
    pass


@dataclass
class SuggestionModel(ViewModel):
    suggestion: Suggestion
    page: int = 0
    bot_to_edit: Bot = None


@dataclass
class UpdateBotListModel(ViewModel):
    silent: bool
    resend: bool


@dataclass
class MessageLinkModel(ViewModel):
    chat_id: int
    message_id: int


@dataclass
class CallbackActionModel(ViewModel):
    next_action: Action


@dataclass
class BotCallbackActionModel(CallbackActionModel, BotViewModel):
    pass


@dataclass
class ButtonModel(ViewModel):
    back_button: bool


@dataclass
class BotKeywordModel(ViewModel):
    bot: Bot
    keyword: Keyword


@dataclass
class KeywordSuggestionModel(ViewModel):
    bot: Bot
    keyword: Keyword


@dataclass
class AddCustomFavoriteModel(ViewModel):
    username: str = None


@dataclass
class SearchQueryModel(ViewModel):
    query: str
    send_errors: bool = True


@dataclass
class ApproveBotsModel(PaginationModel):
    override_list: List[Bot] = None


# endregion


class Actions(ActionRepository):
    # Basic
    DELETE_INLINE_RESULT = Action('delinline')
    REMOVE_KEYWORD = Action('remkw', model_type=BotKeywordModel)
    START = Action('start', commands='start')
    SEND_MAIN_MENU = Action('mainmenu', commands='menu')
    HELP = Action('help', caption=captions.HELP)

    # Contributions
    CONTRIBUTING = Action('contributing', caption=captions.CONTRIBUTING)

    # Exploring
    EXPLORE = Action('explore', caption=captions.EXPLORE, commands=['e', 'explore'])
    SEND_NEW_BOTS = Action('sendnewbots', caption=captions.NEW_BOTS)
    SEARCH = Action('search', commands=['s', 'search'], caption=captions.SEARCH)
    EXAMPLES = Action('examples', caption=captions.EXAMPLES)
    SELECT_CATEGORY = Action('selectcat', caption=captions.CATEGORIES, model_type=CallbackActionModel)
    SEND_CATEGORY = Action('sendcat', caption=captions.CATEGORIES, model_type=CategoryModel)
    REFRESH = Action('refresh', caption=captions.REFRESH, model_type=BotViewModel)
    SELECT_BOT_FROM_CATEGORY = Action(
        'selectbot',
        model_type=BotCategoryModel,
        caption=lambda model: '{}{}'.format(emoji.emojize(model.category.emojis, use_aliases=True), c.name))
    SEND_BOT_DETAILS = Action('botdetails', model_type=BotViewModel)

    # Favorites
    ADD_FAVORITE = Action('addnewfav', model_type=BotViewModel)
    ADD_TO_FAVORITES = Action('addfav', caption=captions.ADD_TO_FAVORITES, model_type=BotNotifyModel)
    TOGGLE_FAVORITES_LAYOUT = Action('favlayout')
    REMOVE_FAVORITE_MENU = Action('removefavmenu', captions.REMOVE_FAVORITE)
    REMOVE_FAVORITE = Action('remfav', model_type=RemoveFavoriteModel)
    SEND_FAVORITES = Action('sendfavlist', caption=captions.FAVORITES)
    ADD_ANYWAY = Action('addanyway', model_type=AddCustomFavoriteModel)

    # Moderation
    ADMIN_MENU = Action('adminmenu', caption=captions.ADMIN_MENU)
    APPROVE_REJECT_BOTS = Action('approvemenu', caption=captions.APPROVE_BOTS, model_type=ApproveBotsModel)
    ACCEPT_BOT = Action('acceptbot', model_type=BotViewModel)
    RECOMMEND_MODERATOR = Action('recommend-moderator', model_type=PagedBotModel)
    SELECT_MODERATOR = Action('selectmod', model_type=RecommendAdminModel)
    REJECT_BOT = Action('rejectbot', model_type=BotNotifyModel)
    BOT_ACCEPTED = Action('botaccepted', model_type=BotCategoryModel)
    CONFIRM_DELETE_BOT = Action('confirmdelete', model_type=BotViewModel, caption='Delete')
    DELETE_BOT = Action('delbot', model_type=BotViewModel, caption="Yes, delete it!")
    ACCEPT_SUGGESTION = Action('acceptsuggestion', model_type=SuggestionModel,
                               caption="{} Accept".format(Emoji.WHITE_HEAVY_CHECK_MARK))
    REJECT_SUGGESTION = Action('rejsuggestion', model_type=SuggestionModel, caption=Emoji.CROSS_MARK)
    CHANGE_SUGGESTION = Action('changesuggestion', model_type=SuggestionModel)
    SWITCH_APPROVALS_PAGE = Action('approvalspage', model_type=PaginationModel)
    SWITCH_SUGGESTIONS_PAGE = Action('suggestionspage', model_type=PaginationModel)
    DELETE_KEYWORD_SUGGESTION = Action('delkwsugg', model_type=KeywordSuggestionModel)

    # Botproperties
    APPLY_ALL_CHANGES = Action('applyall', model_type=BotViewModel, caption="🛃 Apply all changes")
    EDIT_BOT = Action('editbot', model_type=BotViewModel, caption=captions.EDIT_BOT)
    EDIT_BOT_SELECT_CAT = Action('editselectcat', model_type=BotViewModel)
    EDIT_BOT_CAT_SELECTED = Action('editbotcatselected', model_type=BotCategoryModel)
    EDIT_BOT_KEYWORDS = Action('editkwds', model_type=BotViewModel)
    EDIT_BOT_COUNTRY = Action('editcountry', model_type=BotViewModel)
    SET_COUNTRY = Action('setcountry', model_type=BotCategoryModel)
    EDIT_BOT_DESCRIPTION = Action('editdesc', model_type=BotViewModel)
    EDIT_BOT_EXTRA = Action('editextra', model_type=BotViewModel)
    EDIT_BOT_NAME = Action('editname', model_type=BotViewModel)
    EDIT_BOT_USERNAME = Action('editusername', model_type=BotViewModel)
    EDIT_BOT_INLINEQUERIES = Action('editilq', model_type=EditBooleanBotPropertyModel)
    EDIT_BOT_OFFICIAL = Action('editofficial', model_type=EditBooleanBotPropertyModel)
    EDIT_BOT_OFFLINE = Action('editoffline', model_type=EditBooleanBotPropertyModel)
    EDIT_BOT_SPAM = Action('editspam', model_type=EditBooleanBotPropertyModel)
    SET_KEYWORDS = Action('setkw', model_type=BotViewModel)
    ABORT_SETTING_KEYWORDS = Action('abortsetkw', model_type=BotViewModel)

    # BotList
    SEND_BOTLIST = Action('sendBL', model_type=UpdateBotListModel)
    RESEND_BOTLIST = Action('resendBL', model_type=UpdateBotListModel)

    # BotListChat
    PIN_MESSAGE = Action('pinmsg', model_type=MessageLinkModel)
    ADD_THANK_YOU = Action('addthx', model_type=MessageLinkModel)
    COUNT_THANK_YOU = Action('countthx')

    # Utilities
    SEND_BROADCAST = Action('sendbroadcast', commands=['bc', 'broadcast'])
    SET_NOTIFICATIONS = Action('setntfcs', model_type=BooleanPropertyModel)
    REMOVE_KEYBOARD = Action('remkb', commands='removekeyboard')
    DELETE_CONVERSATION = Action('delconv')

    # Internal, Statistics
    RECORD_STATS = Action('record_stats')
