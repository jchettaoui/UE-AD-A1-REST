import argparse
from flask import Flask, request, jsonify, make_response

from model.api import UserApiWrapper
from model.db import ActorDatabaseConnector, ActorDatabaseJsonConnector, ActorDatabaseMongoConnector, MovieDatabaseConnector, MovieDatabaseJsonConnector, MovieDatabaseMongoConnector

########################################################################################
#                                                                                      #
#                                    CONFIGURATION                                     #
#                                                                                      #
########################################################################################

# Storage
DEFAULT_JSON_MOVIE_DESTINATION = "./databases/movies.json"
DEFAULT_JSON_ACTOR_DESTINATION = "./databases/actors.json"
DEFAULT_MONGO_DESTINATION = "mongodb://root:example@localhost:27017/"

# Web app
PORT = 3200
HOST = '0.0.0.0'

# External services
MOVIE_API = "http://localhost:3200"
SCHEDULE_API = "http://localhost:3202"
USER_API = "http://localhost:3203"

# Responses
RESPONSES_403 = {"success": False, "message": "Unauthorized access"}

########################################################################################
#                                                                                      #
#                                  VARIABLES GLOBALES                                  #
#                                                                                      #
########################################################################################

app = Flask(__name__)
database_movie : MovieDatabaseConnector = None
database_actor : ActorDatabaseConnector = None
user_api = UserApiWrapper(USER_API)

#######################################################################################
#                                                                                     #
#                                 FONCTIONS UTILITAIRES                               #
#                                                                                     #
#######################################################################################

def parse_args() -> None:
   """Parse command line arguments to choose data storage method and destination."""

   parser = argparse.ArgumentParser()
   parser.add_argument("-m", "--mongo", help="Choose mongodb as data storage", action="store_true")
   parser.add_argument("-j", "--json", help="Choose JSON file as data storage", action="store_true")
   parser.add_argument("--storage_movies", help="Specify where the movies data is stored (either a json file or a mongo url)")
   parser.add_argument("--storage_actors", help="Specify where the actors data is stored (either a json file or a mongo url)")

   args = parser.parse_args()

   if not args.mongo and not args.json:
      print("Please select a data storage method when starting the app : \n\tJSON : -j \n\tMongoDB : -m\nYou can also specify the storage destination with the flag '--storage'")
      exit(1)

   if args.mongo and args.json:
      print("You can only choose one data storage method !")
      exit(1)

   destination_movies = ""
   if not args.storage_movies:
      print("No storage_movies destination found. Using default value :", end="")
      if args.mongo:
         print(DEFAULT_MONGO_DESTINATION)
         destination_movies = DEFAULT_MONGO_DESTINATION
      else:
         # Json by default
         print(DEFAULT_JSON_MOVIE_DESTINATION)
         destination_movies = DEFAULT_JSON_MOVIE_DESTINATION
   else:
      destination_movies = args.storage_movies

   destination_actors = ""
   if not args.storage_actors:
      print("No storage_actors destination found. Using default value :", end="")
      if args.mongo:
         print(DEFAULT_MONGO_DESTINATION)
         destination_actors = DEFAULT_MONGO_DESTINATION
      else:
         # Json by default
         print(DEFAULT_JSON_ACTOR_DESTINATION)
         destination_actors = DEFAULT_JSON_ACTOR_DESTINATION
   else:
      destination_actors = args.storage_actors

   global database_movie
   global database_actor

   if args.mongo:
      database_movie = MovieDatabaseMongoConnector(destination_movies)
      database_actor = ActorDatabaseMongoConnector(destination_actors)
   else:
      # Json by default
      database_movie = MovieDatabaseJsonConnector(destination_movies)
      database_actor = ActorDatabaseJsonConnector(destination_actors)


def authorization_is_admin() -> bool:
   auth_value = request.headers.get('Authorization')
   if auth_value is None:
      return False
   return user_api.is_user_an_administrator(auth_value)

#######################################################################################
#                                                                                     #
#                                        ROUTES                                       #
#                                                                                     #
#######################################################################################

# root message
@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Movie service!</h1>",200)


@app.route("/movies/<movie_id>", methods=["GET"])
def get_movie_by_id(movie_id: str):
    movie = database_movie.get_movie_by_id(movie_id)
    if movie is None:
        response_body = {
            "success": False,
            "message": "Movie not found",
            "error_field": "movie_id",
            "error_value": movie_id
        }
        return make_response(jsonify({"error":"Movie ID not found"}), 404)
    response_body = {
        "success": True,
        "message": "Movie found",
        "movie": movie
    }
    return make_response(jsonify(response_body), 200)


@app.route("/moviesbytitle", methods=["GET"])
def get_movie_by_title():
    if request.args:
        req = request.args
        movie = database_movie.get_movie_by_title(str(req["title"]))
        if movie is not None:
            return make_response(jsonify(movie), 200)
    return make_response(jsonify({"error":"Movie title not found"}), 404)


@app.route("/movies/<movie_id>", methods=["POST"])
def route_add_movie(movie_id: str):
    if not authorization_is_admin():
       return make_response(jsonify(RESPONSES_403), 403)

    if database_movie.get_movie_by_id(movie_id) is not None:
        return make_response(jsonify({"error":"Movie ID already exists"}), 400)
    req = request.get_json()
    database_movie.add_movie(req)
    return make_response(jsonify({"message":"Movie added"}), 200)


@app.route("/movies/<movie_id>/<rate>", methods=["PUT"])
def route_edit_movie_rate(movie_id: str, rate: float):
    if not authorization_is_admin():
       return make_response(jsonify(RESPONSES_403), 403)
    
    movie = database_movie.get_movie_by_id(movie_id)
    if movie is None:
        return make_response(jsonify({"error":"Movie not found"}), 404)

    try:
        movie["rating"] = float(rate)
    except ValueError:
        return make_response(jsonify({"error":"Invalid rating"}), 400)
    database_movie.update_movie(movie_id, movie)
    return make_response(jsonify(movie), 200)


@app.route("/movies/<movie_id>", methods=["DELETE"])
def route_delete_movie(movie_id: str):
    if not authorization_is_admin():
       return make_response(jsonify(RESPONSES_403), 403)
    
    movie = database_movie.get_movie_by_id(movie_id)
    if movie is None:
        return make_response(jsonify({"error":"Movie title not found"}), 404)
    database_movie.delete_movie_by_id(movie_id)
    return make_response(jsonify(movie), 200)

########################################################################################
#                                                                                      #
#                                      DEMARRAGE                                       #
#                                                                                      #
########################################################################################

if __name__ == "__main__":
    parse_args()
    print("Server running in port %s"%(PORT))
    app.run(host=HOST, port=PORT)
