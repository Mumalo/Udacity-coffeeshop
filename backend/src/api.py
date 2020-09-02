import os
from flask import Flask, request, jsonify, abort
from sqlalchemy.exc import SQLAlchemyError
import json
# from flask_cors import CORS
import sys

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth
from .database.models import Drink

app = Flask(__name__)
print("Running flask app")
setup_db(app)
# CORS(app)

MAX_DRINKS_PER_PAGE = 10


def paginate_drinks(drinks):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * MAX_DRINKS_PER_PAGE
    end = start + MAX_DRINKS_PER_PAGE
    return drinks[start:end]


'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks", methods=["GET"])
def get_drinks(token):
    print("getting drinks")
    try:
        drinks = Drink.query.all()
        paginated_list = paginate_drinks(list(map(Drink.short, drinks)))
        return jsonify({
            'success': True,
            'drinks': paginated_list
        })
    except SystemError:
        abort(400)


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks-detail", methods=["GET"])
@requires_auth("get:drinks-detail")
def get_drink_detail(token):
    print("getting drinks detail")
    try:
        drinks = Drink.query.all()
        paginated = paginate_drinks(list(map(Drink.long, drinks)))
        return jsonify({
            'success': True,
            'drinks': paginated
        })
    except Exception:
        print(sys.exc_info())
        abort(400)


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def post_drink(token):
    new_drink_data = request.get_json()
    if new_drink_data and 'title' in new_drink_data and 'recipe' in new_drink_data:
        title, recipe = new_drink_data['title'], json.dumps(new_drink_data['recipe'])
        print(jsonify(new_drink_data['recipe']))
        try:
            new_drink = Drink(title=title, recipe=recipe)
            new_drink.insert()
            return jsonify({
                'success': True,
                'drinks:': new_drink.long()
            })
        except SQLAlchemyError:
            print(sys.exc_info())
            abort(400)
    abort(400)


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks/<int:id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def update_drink(token, id):
    drink = Drink.query.get(id)
    request_data = request.get_json()
    if not drink:
        print("no drink")
        abort(404)
    if 'title' in request_data:
        setattr(drink, 'title', request_data['title'])
    if 'recipe' in request_data:
        setattr(drink, 'recipe', json.dumps(request_data['recipe']))
    try:
        drink.update()
        return jsonify({
            'success': True,
            'drinks': list(drink.long())
        })
    except SQLAlchemyError:
        print(sys.exc_info())
        abort(400)
    except Exception:
        print(sys.exc_info())
        abort(400)


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks/<int:id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(token, id):
    print("deletimg drink")
    drink = Drink.query.get(id)
    if not drink:
        abort(404)
    try:
        Drink.delete(drink)
        return jsonify({
            'success': True,
            'id': id
        })
    except SQLAlchemyError:
        print(sys.exc_info())
        abort(400)


## Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above 
'''


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above 
'''


@app.errorhandler(AuthError)
def unauthorized(e):
    return jsonify(
        e.error,
    ), e.status_code
