import datetime
from flask import Flask, request, jsonify
from flask import abort
from flask.ext.admin import Admin
from flask.ext.admin.contrib.peewee import ModelView
from peewee import SelectQuery

from model import Bot
from model import Category
from flask_autodoc import Autodoc

from model import Channel
from model import Favorite
from model import Group
from model import Suggestion
from model import User
from model.apiaccess import APIAccess
from gevent.wsgi import WSGIServer

app = Flask(__name__)
auto = Autodoc(app)
admin = Admin(app, name='botlist', template_mode='bootstrap3')

admin.add_view(ModelView(Bot))
admin.add_view(ModelView(Category))
admin.add_view(ModelView(Channel))
admin.add_view(ModelView(Favorite))
admin.add_view(ModelView(Group))
admin.add_view(ModelView(Suggestion))

app.config['APPLICATION_ROOT'] = '/botlist/api/v1'


# Open inceptionhosting ports for me:
# 2601-2620

def start_server():
    http_server = WSGIServer(('', 8080), app)
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


@app.route('/')
def documentation():
    return auto.html()


if __name__ == '__main__':
    app.run(debug=True)
