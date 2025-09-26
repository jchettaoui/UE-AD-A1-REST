from flask import Flask, request, jsonify, make_response
import json
import sys
from werkzeug.exceptions import NotFound

app = Flask(__name__)

PORT = 3200
HOST = '0.0.0.0'

with open('{}/databases/movies.json'.format("."), 'r') as jsf:
    movies = json.load(jsf)["movies"]
    print(movies)

def write(movies):
    with open('{}/databases/movies.json'.format("."), 'w') as f:
        full = {}
        full['movies']=movies
        json.dump(full, f, indent=2)

# root message
@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Movie service!</h1>",200)

@app.route("/json", methods=["GET"])
def get_json():
    return make_response(jsonify(movies), 200)

@app.route("/movies/<movie_id>", methods=["GET"])
def get_movie_by_id(movie_id: str):
    for movie in movies:
        if movie_id == str(movie["id"]):
            return make_response(jsonify(movie), 200)
    return make_response(jsonify({"error":"Movie ID not found"}), 404)

@app.route("/moviesbytitle", methods=["GET"])
def get_movie_by_title():
    if request.args:
        req = request.args
        for movie in movies:
            if str(req["title"]) == str(movie["title"]):
                return make_response(jsonify(movie), 200)
    return make_response(jsonify({"error":"Movie title not found"}), 404)


@app.route("/movies/<movie_id>", methods=["POST"])
def route_add_movie(movie_id: str):
    req = request.get_json()
    for movie in movies:
        if movie_id == str(movie["id"]):
            return make_response(jsonify({"error":"Movie ID already exists"}), 400)
    movies.append(req)
    write(movies)
    return make_response(jsonify({"message":"Movie added"}), 200)


@app.route("/movies/<movie_id>/<rate>", methods=["PUT"])
def route_edit_movie_rate(movie_id: str, rate: float):
    for movie in movies:
        if movie_id == str(movie["id"]):
            movie["rate"] = rate
            write(movies)
            return make_response(jsonify(movie), 200)
    return make_response(jsonify({"error":"Movie title not found"}), 404)


@app.route("/movies/<movie_id>", methods=["DELETE"])
def route_delete_movie(movie_id: str):
    for movie in movies:
        if movie_id == str(movie["id"]):
            movies.remove(movie)
            write(movies)
            return make_response(jsonify(movie), 200)
    return make_response(jsonify({"error":"Movie title not found"}), 404)



if __name__ == "__main__":
    #p = sys.argv[1]
    print("Server running in port %s"%(PORT))
    app.run(host=HOST, port=PORT)
