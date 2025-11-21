import argparse
from flask import Flask, request as f_request, jsonify, make_response

from model.api import MovieApiWrapper, ScheduleApiWrapper, UserApiWrapper
from model.db import BookingDatabaseConnector, BookingDatabaseConnectorJson, BookingDatabaseConnectorMongo

########################################################################################
#                                                                                      #
#                                    CONFIGURATION                                     #
#                                                                                      #
########################################################################################

# Storage
DEFAULT_JSON_DESTINATION = "./databases/bookings.json"
DEFAULT_MONGO_DESTINATION = "mongodb://root:example@localhost:27017/"

# Web app
PORT = 3201
HOST = '0.0.0.0'

# External services
DEFAULT_MOVIE_API_URL = "http://localhost:3200"
DEFAULT_SCHEDULE_API_URL = "http://localhost:3202"
DEFAULT_USER_API_URL = "http://localhost:3203"

# Responses
RESPONSES_403 = {"success": False, "message": "Unauthorized access"}

########################################################################################
#                                                                                      #
#                                  VARIABLES GLOBALES                                  #
#                                                                                      #
########################################################################################

app = Flask(__name__)
database : BookingDatabaseConnector = None
user_api : UserApiWrapper = None
movie_api : MovieApiWrapper = None
schedule_api : ScheduleApiWrapper = None

########################################################################################
#                                                                                      #
#                                FONCTIONS UTILITAIRES                                 #
#                                                                                      #
########################################################################################

def parse_args() -> None:
   """Parse command line arguments to choose data storage method and destination."""

   parser = argparse.ArgumentParser()
   parser.add_argument("-m", "--mongo", help="Choose mongodb as data storage", action="store_true")
   parser.add_argument("-j", "--json", help="Choose JSON file as data storage", action="store_true")
   parser.add_argument("--storage", help="Specify where the data is stored (either a json file or a mongo url)")
   parser.add_argument("--user-service-url", help="Specify the url of the user service", default=DEFAULT_USER_API_URL)
   parser.add_argument("--movie-service-url", help="Specify the url of the movie service", default=DEFAULT_MOVIE_API_URL)
   parser.add_argument("--schedule-service-url", help="Specify the url of the schedule service", default=DEFAULT_SCHEDULE_API_URL)

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

   global database, user_api, movie_api, schedule_api

   if args.mongo:
      database = BookingDatabaseConnectorMongo(destination)
   else:
      # Json by default
      database = BookingDatabaseConnectorJson(destination)

   user_api = UserApiWrapper(args.user_service_url)
   movie_api = MovieApiWrapper(args.movie_service_url)
   schedule_api = ScheduleApiWrapper(args.schedule_service_url)


def authorization_is_admin() -> bool:
   auth_value = f_request.headers.get('Authorization')
   if auth_value is None:
      return False
   return user_api.is_user_an_administrator(auth_value)


def authorization_is_admin_or_self(userid: str) -> bool:
   auth_value = f_request.headers.get('Authorization')
   if auth_value is None:
      return False
   return userid == auth_value or user_api.is_user_an_administrator(auth_value)

########################################################################################
#                                                                                      #
#                                        ROUTES                                        #
#                                                                                      #
########################################################################################

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the Booking service!</h1>"


@app.route("/bookings", methods=["GET"])
def route_get_bookings():
   if not authorization_is_admin():
      return make_response(jsonify(RESPONSES_403), 403)
   bookings = database.get_bookings()
   response_body = {
      "success": True,
      "message": "",
      "bookings": bookings
   }
   return make_response(jsonify(response_body), 200)


@app.route("/booking/<user_id>", methods=["GET"])
def route_get_bookings_by_user(user_id: str):
   if not authorization_is_admin_or_self(user_id):
      return make_response(jsonify(RESPONSES_403), 403)
   bookings = database.get_booking_by_user(user_id)
   response_body = {
      "success": True,
      "message": "",
      "userid": bookings["userid"],
      "dates": bookings["dates"]
   }
   return make_response(jsonify(response_body), 200)


@app.route("/booking/<user_id>/<date>", methods=["GET"])
def route_get_bookings_by_user_and_date(user_id: str, date: str):
   if not authorization_is_admin_or_self(user_id):
      return make_response(jsonify(RESPONSES_403), 403)
   
   response_body = {
      "success": False,
      "message": "",
      "date": date,
      "movies": []
   }

   bookings = database.get_booking_by_user_and_date(user_id, date)
   if bookings is None:
      response_body["message"] = "No booking found"
      return make_response(jsonify(response_body), 200)
   
   details = f_request.args.get('details')
   if details == "yes":
      for movie_id in bookings["movies"]:
         movie_details = movie_api.get_movie_by_id(movie_id)
         if movie_details.status_code != 200:
            response_body["movies"].append({"id": movie_id})
         else:
            response_body["movies"].append(movie_details.json()["movie"])
   else:
      response_body["movies"] = bookings["movies"]
   response_body["success"] = True

   return make_response(jsonify(response_body), 200)


@app.route('/booking/<user_id>/<date>/<movie_id>', methods=["GET"])
def route_user_read_booking(user_id: str, date: str, movie_id: str):
   if not authorization_is_admin_or_self(user_id):
      return make_response(jsonify(RESPONSES_403), 403)

   response_body = {
      "success": False,
      "message": "",
   }
   
   booking_exists = database.get_booking_by_user_and_date(user_id, date)
   if booking_exists is None:
      response_body["message"] = "Booking not found"
      return make_response(jsonify(response_body), 404)
   
   response_body["success"] = True
   response_body["date"] = booking_exists["date"]
   
   movie_details = movie_api.get_movie_by_id(movie_id)
   if movie_details.status_code != 200:
      response_body["movie"] = {"id": movie_id}
      response_body["message"] = "Booking found but enabled to get movie info"
   else:
      response_body["movie"] = movie_details.json()["movie"]
      response_body["message"] = "Booking found"

   return make_response(jsonify(response_body), 200)


@app.route('/booking/<user_id>/<date>/<movie_id>', methods=["POST"])
def route_user_create_booking(user_id: str, date: str, movie_id: str):
   if not authorization_is_admin_or_self(user_id):
      return make_response(jsonify(RESPONSES_403), 403)

   response_body = {
      "success": False,
      "message": "",
   }

   # check if movie exists
   movie_exists = movie_api.get_movie_by_id(movie_id)
   if movie_exists.status_code != 200:
      response_body["message"] = "Movie not found"
      response_body["error_field"] = "movie_id"
      response_body["error_value"] = movie_id
      return make_response(jsonify(response_body), 404)

   # check if schedule exist
   screening_exists = schedule_api.is_movie_scheduled(date, movie_id)
   if screening_exists.status_code != 200:
      response_body["message"] = "Screening not found"
      response_body["error_field"] = "date"
      response_body["error_value"] = date
      return make_response(jsonify(response_body), 404)
   
   new_booking = database.add_booking(user_id, date, movie_id)
   response_body["success"] = new_booking is not None
   response_body["message"] = "Booking created"
   response_body["date"] = new_booking["date"]
   response_body["movies"] = new_booking["movies"]

   return make_response(jsonify(response_body), 201)


@app.route('/booking/<user_id>/<date>/<movie_id>', methods=["DELETE"])
def route_user_delete_booking(user_id: str, date: str, movie_id: str):
   if not authorization_is_admin_or_self(user_id):
      return make_response(jsonify(RESPONSES_403), 403)

   response_body = {
      "success": False,
      "message": "",
   }
   
   deleted_booking = database.delete_booking(user_id, date, movie_id)
   if deleted_booking is None:
      response_body["message"] = "Booking not found"
      return make_response(jsonify(response_body), 404)

   response_body["success"] = True
   response_body["message"] = "Booking deleted"
   response_body["date"] = deleted_booking["date"]
   response_body["movies"] = deleted_booking["movies"]

   return make_response(jsonify(response_body), 200)


if __name__ == "__main__":
   parse_args()
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
