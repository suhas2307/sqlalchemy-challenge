from flask import Flask,jsonify
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine,func
import datetime as dt

app = Flask(__name__)

# Reflect the Hawaii database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

Base = automap_base()
Base.prepare(engine,reflect=True)

Measurement = Base.classes.measurement
Station = Base.classes.station

#Create index route
@app.route("/")
def index():
    return (
        f"Welcome to the Home page<br/>"
        f"The available routes are:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/2017-01-01<br/>"
        f"/api/v1.0/2017-01-01/2017-02-01"
    )

# Create precipation route
@app.route("/api/v1.0/precipitation")
def precipation():
    session = Session(engine)

    # Retrieve date and precipation values from Measurement table
    ppt_data = session.query(Measurement.date,Measurement.prcp).order_by(Measurement.date).all()
    session.close()

    # Convert the data for each date into a dictionary format
    ppt_list = []

    for date,prcp in ppt_data:
        ppt_dict={}
        ppt_dict[date] = prcp
        ppt_list.append(ppt_dict)

    return jsonify(ppt_list)

# Create stations route
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)

    stations = session.query(Station.id,Station.station,Station.name,Station.latitude,Station.longitude,Station.elevation).all()
    session.close()

    # Create a list of dictionaries to return the data
    station_list = []

    for id,station,name,lat,lng,elev in stations:
        station_dict = {}
        station_dict['id'] = id
        station_dict['station'] = station
        station_dict['name'] = name
        station_dict['lat'] = lat
        station_dict['lng'] = lng
        station_dict['elevation'] = elev
        station_list.append(station_dict)
    
    return jsonify(station_list)

# Create tobs route
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)

    # Find the most active station based on the entire dataset
    station = (session.query(Station.id,Station.station,func.count(Measurement.tobs))
    .filter(Station.station==Measurement.station)
    .group_by(Station.id,Station.station)
    .order_by(func.count(Measurement.tobs).desc())
    .first()
    )

    most_active_station = station[1]

    # Find the range of dates for which to query the data

    # get max date as a string from the Measurement table
    smax_date = session.query(func.max(Measurement.date)).scalar()
    # Convert smax_date into a date object
    max_date = dt.datetime.strptime(smax_date,'%Y-%m-%d').date()
    # Calculate the min date for retrieving last 12 months data
    min_date = max_date - dt.timedelta(days=365)

    # Retrieve the data to be returned
    most_active_station_data = (session.query(Measurement.date,Measurement.tobs)
    .filter(Measurement.station==most_active_station)
    .filter(Measurement.date >= min_date)
    .all()
    )

    session.close()

    # Jsonify the return
    return_list = []

    for date,tobs in most_active_station_data:
        return_dict={}
        return_dict[date] = tobs
        return_list.append(return_dict)
    
    return jsonify(return_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temp_analyis(start,end=None):
    start_date = dt.datetime.strptime(start,'%Y-%m-%d').date()

    session = Session(engine)

    if end is None:
        temp_data = (session.query(Measurement.date,func.min(Measurement.tobs),func.avg(Measurement.tobs),func.max(Measurement.tobs))
            .filter(Measurement.date >= start_date)
            .group_by(Measurement.date)
            .order_by(Measurement.date)
            .all()
        )
    else:
        end_date = dt.datetime.strptime(end,'%Y-%m-%d').date()

        temp_data = (session.query(Measurement.date,func.min(Measurement.tobs),func.avg(Measurement.tobs),func.max(Measurement.tobs))
            .filter(Measurement.date >= start_date,Measurement.date <= end_date)
            .group_by(Measurement.date)
            .order_by(Measurement.date)
            .all()
        )
    
    session.close()
    
    # Create a list to send a jsonified return
    temp_list = []

    for date,mintemp,avgtemp,maxtemp in temp_data:
        temp_dict = {}
        temp_dict['Date'] = date
        temp_dict['TMIN'] = mintemp
        temp_dict['TAVG'] = avgtemp
        temp_dict['TMAX'] = maxtemp
        temp_list.append(temp_dict)
    
    return jsonify(temp_list)

if __name__ == '__main__':
    app.run(debug=True)