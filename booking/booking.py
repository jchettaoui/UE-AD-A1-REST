from flask import Flask, render_template, request, jsonify, make_response
import requests
import json
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

########################################################################################
#                                                                                      #
#                                      CONSTANTES                                      #
#                                                                                      #
########################################################################################

PORT = 3201
HOST = '0.0.0.0'

MOVIE_API = "http://localhost:3200"
SCHEDULE_API = "http://localhost:3202"

DATE_REGEX = ""

########################################################################################
#                                                                                      #
#                                      APP SETUP                                       #
#                                                                                      #
########################################################################################

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app = Flask(__name__)
app.url_map.converters['regex'] = RegexConverter

with open('{}/databases/bookings.json'.format("."), "r") as jsf:
   bookings = json.load(jsf)

########################################################################################
#                                                                                      #
#                                FONCTIONS UTILITAIRES                                 #
#                                                                                      #
########################################################################################

def get_booking_by_user(user_id):
   for user_booking in bookings:
      if user_booking["userid"] == user_id:
         return user_booking
   return None

def get_booking_by_user_and_date(user_id, date):
   user_booking = get_booking_by_user(user_id)
   if user_booking is None:
      return None, None
   for booking_date in user_booking["dates"]:
      if booking_date["date"] == date:
         return user_booking, booking_date
   return None, None

def get_booking(user_id, date, movie_id):
   user_booking, booking_date = get_booking_by_user_and_date(user_id, date)
   if user_booking is None:
      return None, None
   if movie_id in booking_date["movies"]:
      return user_booking, booking_date
   return None, None

def save_bookings(new_bookings: dict) -> None:
   with open('{}/databases/bookings.json'.format("."), "w") as jsf:
      json.dump(new_bookings, jsf, indent=2)

########################################################################################
#                                                                                      #
#                                        ROUTES                                        #
#                                                                                      #
########################################################################################

# @app.route('/<regex("[abcABC0-9]{4,6}"):uid>-<slug>/')

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the Booking service!</h1>"


@app.route('/booking/<user_id>/<date>/<movie_id>', methods=["POST"])
def route_user_create_booking(user_id: str, date: str, movie_id: str):

   # check if movie exists
   movie_exists = requests.get(MOVIE_API+f"/movies/{movie_id}")
   if movie_exists.status_code != 200:
      return make_response(jsonify({"error":"Movie not found", "movie_id": movie_id}), 404)

   # check if schedule exist
   screening_exists = requests.get(SCHEDULE_API+f"/schedule/{date}/{movie_id}")
   if screening_exists.status_code != 200:
      return make_response(jsonify({"error":"Screening not found", "date": date}), 404)
   
   # check if the user already has a booking for this movie
   for user in bookings:
      if str(user["userid"]) == user_id:
         for book_date in user["dates"]:
            if book_date["date"] == date:
               # pas de vérification si le film est déjà réservé. On suppose qu'un client peut acheter plusieurs tickets.
               book_date["movies"].append(movie_id)
               break
         else:
            user["dates"].append({
               "date": date,
               "movies": [movie_id]
            })
         break
   else:
      bookings.append({
         "userid": user_id,
         "dates": [
            {
               "date": date,
               "movies": [movie_id]
            }
         ]
      })
   
   save_bookings(bookings)

   return make_response(jsonify({
         "message":"Booking created", 
         "userid": user_id,
         "date": date,
         "movie_id": movie_id
         }), 201)


@app.route('/booking/<user_id>/<date>/<movie_id>', methods=["GET"])
def route_user_read_booking(user_id: str, date: str, movie_id: str):

   for user in bookings:
      if user["userid"] == user_id:
         for book_date in user["dates"]:
            if book_date["date"] == date:
               if movie_id in book_date["movies"]:
                  movie_details = requests.get(MOVIE_API+f"/movies/{movie_id}")
                  response_data = {
                        "message":"Booking found.", 
                        "date": date,
                     }
                  if movie_details.status_code != 200:
                     response_data["movie"] = {"movie_id": movie_id, "error":"Unable to get movie details"}
                  else:
                     response_data["movie"] = movie_details.json()
                  return make_response(jsonify(response_data))
    
   return make_response(jsonify({"error":"Booking not found"}), 404)

@app.route('/booking/<user_id>/<date>/<movie_id>', methods=["DELETE"])
def route_user_delete_booking(user_id: str, date: str, movie_id: str):
   user_booking, date_booking = get_booking(user_id, date, movie_id)
   if date_booking is None:
      return make_response(jsonify({"error":"Booking not found"}), 404)
   
   if len(date_booking["movies"]) == 1:
      user_booking["dates"].remove(date_booking)
   else:
      date_booking["movies"].remove(movie_id)

   save_bookings(bookings)
   return make_response(jsonify({"message":"Booking deleted", "date": date, "movie_id": movie_id}))


if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
