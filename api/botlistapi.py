import datetime
import random

import markdown
import os
from flask import Flask, request, jsonify, send_from_directory
from flask import Markup
from flask_autodoc.autodoc import Autodoc
from gevent.wsgi import WSGIServer
from peewee import fn

import settings
from model import Bot
from model import Category
from model.apiaccess import APIAccess


def md2html(text):
    text = str(text)
    import textwrap
    res = Markup(markdown.markdown(
        textwrap.dedent(text),
        [
            'markdown.extensions.codehilite',
            'markdown.extensions.nl2br',
            'markdown.extensions.extra',
            'markdown.extensions.admonition'
        ], extension_configs={
            'markdown.extensions.codehilite': {
                'noclasses': True,
                'pygments_style': 'colorful'
            }
        }))
    return res


app = Flask(__name__, static_url_path='/doc')
app.jinja_env.filters['markdown'] = md2html

auto = Autodoc(app)


# Disabled until security issues are figured out
# admin = Admin(app, name='botlist', template_mode='bootstrap3')
#
# admin.add_view(ModelView(Bot))
# admin.add_view(ModelView(Category))
# admin.add_view(ModelView(Channel))
# admin.add_view(ModelView(Favorite))
# admin.add_view(ModelView(Group))
# admin.add_view(ModelView(Suggestion))


# TODO: doesn't work
# app.config['APPLICATION_ROOT'] = '/botlist/api/v1'

def start_server():
    http_server = WSGIServer((settings.API_URL, settings.API_PORT), app)
    return http_server.serve_forever()


def _error(message):
    return jsonify({
        'error': message,
        'url': request.url
    })


@app.route('/submit', methods=['POST'])
@auto.doc()
def submit():
    if not request.is_json:
        res = _error('MimeType must be application/json.')
        res.status_code = 400
        return res

    content = request.get_json()
    try:
        access = APIAccess.get(APIAccess.token == content.get('token'))
    except APIAccess.DoesNotExist:
        res = _error('The access token is invalid.')
        res.status_code = 401
        return res

    username = content.get('username')
    if username is None or not isinstance(username, str):
        res = _error('You must supply a username.')
        res.status_code = 400
        return res

    # insert `@` if omitted
    username = '@' + username if username[0] != '@' else username

    try:
        Bot.get(Bot.username == username)
        res = _error('The bot {} is already in the BotList.'.format(username))
        res.status_code = 409
        return res
    except Bot.DoesNotExist:
        b = Bot(username=username)

    name = content.get('name')
    description = content.get('description')
    inlinequeries = content.get('inlinequeries')

    try:
        if name:
            if isinstance(name, str):
                b.name = name
            else:
                raise AttributeError('The name field must be a string.')
        if description:
            if isinstance(description, str):
                b.description = description
            else:
                raise AttributeError('The description field must be a string.')
        if inlinequeries:
            if isinstance(inlinequeries, bool):
                b.inlinequeries = inlinequeries
            else:
                raise AttributeError('The inlinequeries field must be a boolean.')
    except Exception as e:
        res = _error(str(e))
        res.status_code = 400
        return res

    b.date_added = datetime.date.today()
    b.submitted_by = access.user
    b.approved = False

    b.save()
    res = jsonify({
        'success': '{} was submitted for approval.'.format(b)
    })
    res.status_code = 201
    return res


@app.route('/bots', methods=['GET'])
@app.route('/bots/<int:page>', methods=['GET'])
@auto.doc()
def bots_endpoint(page=1):
    """
    Return bots from the BotList.

    Use the url parameters `url` or `username` to perform a search on the BotList.
    The @-character in usernames can be omitted.

    :param page: The page to display
    :return: All bots (paginated) or the search result if url parameters were used.
    """
    if request.method == 'GET':
        results = list()
        if len(request.args) > 0:
            # return bots matching the request arguments (after ?)
            id_arg = request.args.get('id', None)
            username_arg = request.args.get('username', None)

            if id_arg:
                results = Bot.select().where(Bot.id == id_arg).limit(1)
            elif username_arg:
                # allow for omitting the `@` in the username
                results = Bot.select().where(
                    (Bot.username == username_arg) | (Bot.username == '@' + username_arg)).limit(1)

            data = results[0].serialize

            if data:
                res = jsonify({
                    'search_result': data,
                    'meta': {'url': request.url}
                })
                res.status_code = 200
            else:
                res = _error('No bot found with your search parameters.')
                res.status_code = 404
            return res

        else:
            # return all bots (paginated)
            per_page = 50
            results = Bot.select().paginate(page, per_page)

            data = [i.serialize for i in results]

            if data:
                res = jsonify({
                    'bots': data,
                    'meta': {'page': page, 'per_page': per_page, 'page_url': request.url}
                })
                res.status_code = 200
            else:
                res = _error('No bots found.')
                res.status_code = 500
            return res


@app.route('/offline', methods=['POST'])
@auto.doc()
def set_offline():
    pass


@app.route('/categories', methods=['GET'])
@auto.doc()
def categories_endpoint():
    """
    Returns all categories of the BotList.
    """
    if request.method == 'GET':
        query = Category.select_all()
        data = [i.serialize for i in query]

        if data:
            res = jsonify({
                'categories': data,
                'meta': {'url': request.url}
            })
            res.status_code = 200
        else:
            res = _error('No categories found.')
            res.status_code = 500
        return res


@app.route('/random', methods=['GET'])
@auto.doc()
def random_bot():
    """
    Returns a random bot from the BotList. By default, only "interesting" bots with description and tags are shown.
    Use the parameter `?all=True` to receive _all_ possible choices.
    """
    show_all = bool(request.args.get("all", False))

    if show_all:
        random_bot = Bot.select().order_by(fn.Random()).limit(1)[0]
    else:
        random_bot = random.choice(Bot.explorable_bots())
    data = random_bot.serialize

    if data:
        res = jsonify({
            'search_result': data,
            'meta': {'url': request.url}
        })
        res.status_code = 200
    else:
        res = _error("No bot found.")
    return res

@app.route('/thumbnail/<username>.jpeg', methods=['GET'])
@auto.doc()
def thumbnail(username):
    if username[0] != '@':
        username = '@' + username
    try:
        item = Bot.by_username(username)
    except Bot.DoesNotExist:
        item = None
    if not item:
        return _error("There is no bot in the BotList with the username {}.".format(username))
    if not os.path.exists(item.thumbnail_file):
        return _error("Sorry, we don't have a thumbnail for this bot.")

    path, file = os.path.split(item.thumbnail_file)
    return send_from_directory(path, file)

@app.route('/')
def documentation():
    return auto.html(
        template='autodoc.html',
        title='BotListBot API',
        author='JosXa',
    )


if __name__ == '__main__':
    app.run(debug=True)
