from flask import Blueprint, jsonify, request, session, redirect, url_for, send_file
from app.models.users import Users
from app.models.address import Address
from app.models.orders import Orders
from app.models.tickets import Tickets
from werkzeug.utils import secure_filename
from app import db
import os

# creates blueprint
api = Blueprint('api', __name__, url_prefix="/api")

# creates a path to attachments
UPLOAD_FOLDER = os.path.abspath("app/static/attachments")

#login route
@api.route('/login', methods=['POST'])
def login():
    #checks if the email and password is correct or is it empty
    try:
        email = request.json.get('email')
        password = request.json.get('password')

        query = f"(select * from users where email='{email}' and password='{password}');"
        if not all((email, password)):
            return jsonify({
                    'status': 'error',
                    'message': 'Both email and password are required!'
            }), 400
        user = db.engine.execute(query).first()

        if user:
            session["email"] = email
            session["user_id"] = user[0]
            return jsonify({
                "status": "success",
                "id": user[0]
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Not sure"
            }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

# logout route
@api.route("/logout", methods=["POST"])
def logout():
    #logouts from the database
    try:
        session["email"] = None
        session["user_id"] = None
        return jsonify(
            {
                "status": "success",
            }, 200
        )
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

#adds address to the database and add-address route
@api.route("/add-address", methods=["POST"])
def add_address():
    try:
        house_number = request.json.get("house_number")
        city = request.json.get("city")
        state = request.json.get("state")
        country = request.json.get("country")
        pin_code = request.json.get("pin_code")
        user_email = session.get("email")
        user_query = f"select * from users where email='{user_email}';"
        user = db.engine.execute(user_query).first()
        Address.create(user["id"], house_number, city, state, country, pin_code)
        return jsonify(
            {
                "status": "success",
            }, 201
        )
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

#create-order route and creates a new order in the batabase
@api.route("/create-order", methods=["POST"])
def create_order():
    try:
        user_email = session.get("email")
        user_query = f"select * from users where email='{user_email}';"
        user = db.engine.execute(user_query).first()
        product_id = request.json.get("product_id")
        address_id = request.json.get("address_id")
        amount = request.json.get("amount")
        Orders.create(user["id"], product_id, 1, address_id, amount)
        return jsonify(
            {
                "status": "success",
            }, 201
        )
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

# submit-help route and creates a new help ticket for the user 
@api.route("/submit-help", methods=["POST"])
def submit_help():
    title = request.form.get("title")
    description = request.form.get("description")
    attachment = request.files.get("attachment")
    if attachment:
        filename = secure_filename(attachment.filename)
        attachment.save(os.path.join(UPLOAD_FOLDER, filename))
    user_email = session.get("email")
    user_query = f"select * from users where email='{user_email}';"
    user = db.engine.execute(user_query).first()
    Tickets.create(user["id"], title, description, filename)
    return jsonify(
            {
                "status": "success",
            }, 201
        )

# app download route
@api.route("/download/<path:filename>")
def download(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

# search-order route and returns all orders that match the query parameter
@api.route("/search-order")
def search_order():
    order_id = request.args.get("order_id")
    user_email = session.get("email")
    user_query = f"select * from users where email='{user_email}';"
    user = db.engine.execute(user_query).first()
    order_query = f"(select p.image, p.name, o.amount from products p right join orders o on o.user_id={user['id']} and p.id=o.product_id and o.id={order_id});"
    order = db.engine.execute(order_query).all()
    orders = []
    for order_obj in order:
        if all((order_obj[0], order_obj[1], order_obj[2])):
            orders.append([order_obj[0], order_obj[1], order_obj[2]])
    return jsonify({
        "status": "success",
        "orders": orders
    }), 200

# execute route executes the code and engine
@api.route("/execute", methods=["POST"])
def execute():
    try:
        code = request.json.get("code")
        result = db.engine.execute(code).all()
        if len(result) == 0:
            return jsonify({
                "status": "no_result"
            }), 200
        else:
            keys, values = result[0].keys()._keys, []
            for result_obj in result:
                temp_values = []
                for result_value in result_obj:
                    temp_values.append(result_value)
                values.append(temp_values)
            return jsonify({
                "status": "success",
                "keys": keys,
                "values": values
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

# get-customer route returns customer information by id
@api.route("/get-customer")
def get_customer():
    try:
        customer_id = request.args.get("id")
        customer_query = f"select * from customers where id='{customer_id}';"
        customer_data = db.engine.execute(customer_query).first()
        if(customer_data):
            return jsonify({
                "status": "success",
            
            }), 200
        else:
            return jsonify({
                "status" : "error",
                "message" : "Customer not found"
            }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400