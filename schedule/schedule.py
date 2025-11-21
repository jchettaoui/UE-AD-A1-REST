import argparse

from flask import Flask, request, jsonify, make_response

from model.api import MovieApiWrapper, UserApiWrapper
from model.db import ScheduleDatabaseConnector, ScheduleDatabaseJsonConnector, ScheduleDatabaseMongoConnector

########################################################################################
#                                                                                      #
#                                    CONFIGURATION                                     #
#                                                                                      #
########################################################################################

# Storage
DEFAULT_JSON_DESTINATION = "./databases/times.json"
DEFAULT_MONGO_DESTINATION = "mongodb://root:example@localhost:27017/"

# Web app
PORT = 3202
HOST = '0.0.0.0'

# External services
DEFAULT_MOVIE_API_URL = "http://localhost:3200"
DEFAULT_USER_API_URL = "http://localhost:3203"

# Responses
RESPONSES_403 = {"success": False, "message": "Unauthorized access"}

########################################################################################
#                                                                                      #
#                                  VARIABLES GLOBALES                                  #
#                                                                                      #
########################################################################################

app = Flask(__name__)
database : ScheduleDatabaseConnector = None
user_api : UserApiWrapper = None
movie_api : MovieApiWrapper = None

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
    parser.add_argument("--storage", help="Specify where the data is stored (either a json file or a mongo url)")
    parser.add_argument("--user-service-url", help="Specify the url of the user service", default=DEFAULT_USER_API_URL)
    parser.add_argument("--movie-service-url", help="Specify the url of the movie service", default=DEFAULT_MOVIE_API_URL)

    args = parser.parse_args()

    if not args.mongo and not args.json:
        print("Please select a data storage method when starting the app : \n\tJSON : -j \n\tMongoDB : -m\nYou can also specify the storage destination with the flag '--storage'")
        exit(1)

    if args.mongo and args.json:
        print("You can only choose one data storage method !")
        exit(1)

    destination = ""
    if not args.storage:
        print("No storage destination found. Using default value :", end="")
        if args.mongo:
            print(DEFAULT_MONGO_DESTINATION)
            destination = DEFAULT_MONGO_DESTINATION
        else:
            # Json by default
            print(DEFAULT_JSON_DESTINATION)
            destination = DEFAULT_JSON_DESTINATION
    else:
        destination = args.storage

    global database, user_api, movie_api

    if args.mongo:
        database = ScheduleDatabaseMongoConnector(destination)
    else:
        # Json by default
        database = ScheduleDatabaseJsonConnector(destination)

    user_api = UserApiWrapper(args.user_service_url)
    movie_api = MovieApiWrapper(args.movie_service_url)


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

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the Showtime service!</h1>"


@app.route("/schedule/<date>", methods=['GET'])
def get_schedule_bydate(date: str):
    schedule = database.get_schedule_by_date(date)
    if schedule is None:
        return make_response(jsonify({"error":"Date not found"}),404)

    return make_response(jsonify(schedule), 200)


@app.route("/schedule/movie/<movieid>", methods=['GET'])
def get_schedule_bymovieid(movieid):
    schedule = database.get_schedule_by_movieid(movieid)
    if schedule is None:
        return make_response(jsonify({"error":"Date not found"}),404)

    return make_response(jsonify(schedule), 200)
    

@app.route("/schedule/<date>/<movie_id>", methods=["GET"])
def is_movie_scheduled(date: str, movie_id: str):
    schedules = database.get_schedule_by_movieid(movie_id)
    for s in schedules:       
        if s["date"] == date:
            return make_response(jsonify({"message":"Yes, the movie is scheduled at this date.", "date":date, "movie_id": movie_id}), 200)
    return make_response(jsonify({"message":"No, this movie isn't scheduled at this date.", "date":date, "movie_id": movie_id}), 404)


@app.route("/schedule/<date>/<movieid>", methods=['POST'])
def schedule_movie(date, movieid):
    if not authorization_is_admin():
        return make_response(jsonify(RESPONSES_403), 403)

    schedule_added = database.add_movie_to_date(date, movieid)
    if schedule_added is None:
        database.add_date_to_schedule({"date": date, "movies": [movieid]})
    return make_response(jsonify({"message":"movie scheduled", "schedule": schedule_added}), 201)


@app.route("/schedule/<date>/<movieid>", methods=['DELETE'])
def unschedule_movie(date, movieid):
    if not authorization_is_admin():
        return make_response(jsonify(RESPONSES_403), 403)

    unscheduled = database.delete_movie_from_date(date, movieid)
    if unscheduled is None:
        return make_response(jsonify({"error":"movie ID not scheduled for this date"}),404)
    return make_response(jsonify({"message":"movie unscheduled", "schedule": unscheduled}),200)


@app.route("/schedule/movie/<movieid>", methods=['DELETE'])
def del_movie_from_schedule(movieid):
    if not authorization_is_admin():
        return make_response(jsonify(RESPONSES_403), 403)

    deleted = database.delete_movie_from_schedule(movieid)
    if deleted is None:
        return make_response(jsonify({"error":"movie ID not scheduled"}), 400)
    return make_response(jsonify(deleted), 200)


@app.route("/schedule/date/<date>", methods=['DELETE'])
def del_date_from_schedule(date):
    if not authorization_is_admin():
        return make_response(jsonify(RESPONSES_403), 403)

    deleted = database.delete_date_from_schedule(date)
    if deleted is None:
       return make_response(jsonify({"error":"date not found"}),500)

    return make_response(jsonify(deleted), 200)

########################################################################################
#                                                                                      #
#                                      DEMARRAGE                                       #
#                                                                                      #
########################################################################################

if __name__ == "__main__":
   parse_args()
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)