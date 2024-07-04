#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify, abort
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    restaurants_data = [restaurant.to_dict(only=('address', 'id', 'name')) for restaurant in restaurants]
    return jsonify(restaurants_data)

@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant(id):
    restaurant = db.session.query(Restaurant).get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    
    restaurant_data = restaurant.to_dict()
    restaurant_data["restaurant_pizzas"] = []
    
    for restaurant_pizza in restaurant.restaurant_pizzas:
        pizza_data = {
            "id": restaurant_pizza.id,
            "pizza_id": restaurant_pizza.pizza_id,
            "price": restaurant_pizza.price,
            "restaurant_id": restaurant_pizza.restaurant_id,
            "pizza": {
                "id": restaurant_pizza.pizza.id,
                "name": restaurant_pizza.pizza.name,
                "ingredients": restaurant_pizza.pizza.ingredients
            }
        }
        restaurant_data["restaurant_pizzas"].append(pizza_data)
    
    return jsonify(restaurant_data)

@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = db.session.query(Restaurant).get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    
    db.session.delete(restaurant)
    db.session.commit()
    return '', 204

@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    pizzas_data = [
        {
            "id": pizza.id,
            "ingredients": pizza.ingredients,
            "name": pizza.name
        } for pizza in pizzas
    ]
    return jsonify(pizzas_data)

@app.route('/restaurant_pizzas', methods=['POST'])
def add_restaurant_pizza():
    data = request.get_json()
    price = data.get('price')
    pizza_id = data.get('pizza_id')
    restaurant_id = data.get('restaurant_id')

    if not (price and pizza_id and restaurant_id):
        return make_response( {"errors": ["validation errors"]}, 400)

    try:
        new_restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
        db.session.add(new_restaurant_pizza)
        db.session.commit()

        restaurant = Restaurant.query.filter(Restaurant.id==restaurant_id).first()
        pizza = Pizza.query.filter(Pizza.id==pizza_id).first()
        response_data = {
            "id": new_restaurant_pizza.id,
            "price": new_restaurant_pizza.price,
            "pizza_id": new_restaurant_pizza.pizza_id,
            "restaurant_id": new_restaurant_pizza.restaurant_id,
            "pizza": {
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients
            },
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address
            }
        }
        return make_response(response_data, 201)
    except ValueError as e:
        return make_response( {"errors": ["validation errors"]}, 400)

if __name__ == "__main__":
    app.run(port=5555, debug=True)
