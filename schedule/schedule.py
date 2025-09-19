from flask import Flask, render_template, request, jsonify, make_response
import json
from werkzeug.exceptions import NotFound

app = Flask(__name__)

PORT = 3202
HOST = '0.0.0.0'

with open('{}/databases/times.json'.format("."), "r") as jsf:
   schedule = json.load(jsf)["schedule"]

def write(movies):
    with open('{}/databases/times.json'.format("."), 'w') as f:
        full = {}
        full['times']=schedule
        json.dump(full, f)

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the Showtime service!</h1>"

@app.route("/schedule/<date>", methods=['GET'])
#testée
def get_schedule_bydate(date):
    for time in schedule:
        if str(time["date"]) == str(date):
            res = make_response(jsonify(time),200)
            return res
    return make_response(jsonify({"error":"Date not found"}),500)

@app.route("/schedule/movie/<movieid>", methods=['GET'])
#testée
def get_schedule_bymovieid(movieid):
    find_movie = False
    date_list = []
    for time in schedule:
        if str(movieid) in time["movies"]:
            find_movie = True
            date_list.append(time)
    if find_movie :
      res = make_response(jsonify(date_list),200)
      return res
    else: 
      return make_response(jsonify({"error":"Movie Id not found"}),500)

@app.route("/schedule/<date>/<movieid>", methods=['POST'])
#testée
def schedule_movie(date,movieid):
    for time in schedule:
         if str(time["date"]) == str(date):
            if str(movieid) in time["movies"]:
               return make_response(jsonify({"error":"The movie is already scheduled at this date"}),500)
            else: 
               time["movies"].append(str(movieid))
               write(schedule)
               res = make_response(jsonify({"message":"movie scheduled"}),200)
               return res
   #sinon, la date n'a pas ete trouve, il faut la rajouter
    schedule.append({"date": str(date), "movies": [str(movieid)] })
    write(schedule)
    res = make_response(jsonify({"message":"movie scheduled"}),200)
    return res

@app.route("/schedule/<date>/<movieid>", methods=['DELETE'])
#testée
def unschedule_movie(date, movieid):
    for time in schedule:
        if str(time["date"]) == str(date):
            time["movies"].remove(str(movieid))
            write(schedule)
            return make_response(jsonify(time),200)

    res = make_response(jsonify({"error":"movie ID not scheduled for this date"}),500)
    return 

"""
@app.route("/schedule/movie/<movieid>", methods=['DELETE'])
def del_movie_from_schedule(movieid):
    for time in schedule:
        if str(time["date"]) == str(date):
            time["movies"].remove(str(movieid))
            write(schedule)
            return make_response(jsonify(time),200)

    res = make_response(jsonify({"error":"movie ID not scheduled for this date"}),500)
    return 
"""

@app.route("/schedule/date/<date>", methods=['DELETE'])
def del_date_from_schedule(date, movieid):
    for time in schedule:
        if str(time["date"]) == str(date):
            schedule.remove(time)
            write(schedule)
            return make_response(jsonify(time),200)

    res = make_response(jsonify({"error":"date not found"}),500)
    return res

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
