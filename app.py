from flask import Flask, request, jsonify
import xarray as xr
from data_loader import load_dataset
from flasgger import Swagger

app = Flask(__name__)
app.config["SWAGGER"] = {
    "title": "Xarray Flask API",
    "uiversion": 3,
}

swagger = Swagger(app)

ds = xr.open_dataset("weather_data.nc")

real_ds = load_dataset()

def _first_existing_var(dataset: xr.Dataset, candidates: list[str]) -> str | None:
    for name in candidates:
        if name in dataset.data_vars:
            return name
    return None

@app.route("/")
def home():
    """
    Health check.
    ---
    tags:
      - Health
    responses:
      200:
        description: Server is running
    """
    return "Flask server is running"


# Concept 1 — Dataset Structure
@app.route("/dataset-info", methods=["GET"])
def dataset_info():
    """
    Get dataset structure (dims/coords/variables) for `weather_data.nc`.
    ---
    tags:
      - Dataset (sample)
    responses:
      200:
        description: Dataset structure
    """
    return jsonify({
        "dimensions": list(ds.dims),
        "coordinates": list(ds.coords),
        "variables": list(ds.data_vars)
    })

# Concept 2 — DataArray
@app.route("/dataarray", methods=["GET"])
def dataarray():
    """
    Describe the `temperature` DataArray (name and dims).
    ---
    tags:
      - Dataset (sample)
    responses:
      200:
        description: DataArray description
    """

    temp = ds["temperature"]

    return jsonify({
        "name": temp.name,
        "dimensions": temp.dims
    })

# Concept 3 — Index Selection (isel)
@app.route("/index-temp", methods=["GET"])
def index_temp():
    """
    Get temperature by index selection (isel) at time=0.
    ---
    tags:
      - Temperature (sample)
    parameters:
      - name: lat_index
        in: query
        type: integer
        required: true
      - name: lon_index
        in: query
        type: integer
        required: true
    responses:
      200:
        description: Temperature value
    """
    print(request.args, "test")
    lat_index = int(request.args.get("lat_index"))
    lon_index = int(request.args.get("lon_index"))

    value = ds.temperature.isel(
        lat=lat_index,
        lon=lon_index,
        time=0
    ).values

    return jsonify({"temperature": float(value)})

# Concept 4 — Coordinate Selection (sel)
@app.route("/coordinate-temp", methods=["GET"])
def coordinate_temp():
    """
    Get temperature by coordinate selection (sel, nearest) at time=0.
    ---
    tags:
      - Temperature (sample)
    parameters:
      - name: lat
        in: query
        type: number
        format: float
        required: true
      - name: lon
        in: query
        type: number
        format: float
        required: true
    responses:
      200:
        description: Temperature value
    """

    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))

    temp = ds.temperature.sel(
        lat=lat,
        lon=lon,
        method="nearest"
    )

    return jsonify({
        "temperature": float(temp.isel(time=0))
    })

# Concept 5 — Time Selection
@app.route("/temperature-time", methods=["GET"])
def temperature_time():
    """
    Compute mean temperature for a given time slice.
    ---
    tags:
      - Temperature (sample)
    parameters:
      - name: date
        in: query
        type: string
        required: true
        description: Time coordinate value (must match dataset time encoding)
    responses:
      200:
        description: Mean temperature at that time
    """

    date = request.args.get("date")

    data = ds.temperature.sel(time=date)

    return jsonify({
        "mean_temp": float(data.mean())
    })

# Concept 6 — Region Selection (Geospatial Bounding Box)
@app.route("/region-temp", methods=["GET"])
def region_temp():
    """
    Compute average temperature over a lat/lon bounding box.
    ---
    tags:
      - Temperature (sample)
    parameters:
      - name: lat_min
        in: query
        type: number
        format: float
        required: true
      - name: lat_max
        in: query
        type: number
        format: float
        required: true
      - name: lon_min
        in: query
        type: number
        format: float
        required: true
      - name: lon_max
        in: query
        type: number
        format: float
        required: true
    responses:
      200:
        description: Average temperature in region
    """

    lat_min = float(request.args.get("lat_min"))
    lat_max = float(request.args.get("lat_max"))
    lon_min = float(request.args.get("lon_min"))
    lon_max = float(request.args.get("lon_max"))

    region = ds.temperature.sel(
        lat=slice(lat_min, lat_max),
        lon=slice(lon_min, lon_max)
    )

    return jsonify({
        "avg_temp": float(region.mean())
    })

# Concept 7 — Aggregations
@app.route("/global-mean", methods=["GET"])
def global_mean():
    """
    Compute global mean temperature across all dims.
    ---
    tags:
      - Temperature (sample)
    responses:
      200:
        description: Global mean temperature
    """

    value = ds.temperature.mean()

    return jsonify({
        "global_mean_temperature": float(value)
    })

# Concept 8 — Time Series
@app.route("/timeseries", methods=["GET"])
def timeseries():
    """
    Get temperature timeseries (nearest lat/lon).
    ---
    tags:
      - Temperature (sample)
    parameters:
      - name: lat
        in: query
        type: number
        format: float
        required: true
      - name: lon
        in: query
        type: number
        format: float
        required: true
    responses:
      200:
        description: Temperature timeseries
    """

    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))

    series = ds.temperature.sel(
        lat=lat,
        lon=lon,
        method="nearest"
    )

    values = series.values.tolist()

    return jsonify({
        "temperature_timeseries": values
    })

# Concept 9 — Groupby
@app.route("/monthly-average", methods=["GET"])
def monthly_avg():
    """
    Compute monthly mean temperature (groupby time.month).
    ---
    tags:
      - Temperature (sample)
    responses:
      200:
        description: Monthly mean array
    """

    result = ds.temperature.groupby("time.month").mean()

    return jsonify({
        "monthly_mean": result.values.tolist()
    })

# Concept 5 — Time Selection Convert to pandas
@app.route("/to-pandas", methods=["GET"])
def to_pandas():
    """
    Convert a single time-slice to a pandas DataFrame and return first rows as JSON.
    ---
    tags:
      - Dataset (sample)
    responses:
      200:
        description: JSON records (head)
    """

    df = ds.temperature.isel(time=0).to_dataframe().reset_index()

    return df.head().to_json(orient="records")


# Concept: dataset structure
@app.route("/dataset-metadata", methods=["GET"])
def metadata():
    """
    Get dataset structure (dims/coords/variables) for the `real_ds` dataset.
    ---
    tags:
      - Dataset (real)
    responses:
      200:
        description: Dataset structure
    """

    return jsonify({
        "dimensions": list(real_ds.dims),
        "coordinates": list(real_ds.coords),
        "variables": list(real_ds.data_vars)
    })

# Concept: geospatial coordinate selection
@app.route("/realtemperature", methods=["GET"])
def real_temperature():
    """
    Get temperature from `real_ds` at nearest lat/lon (time=0).
    ---
    tags:
      - Temperature (real)
    parameters:
      - name: lat
        in: query
        type: number
        format: float
        required: true
      - name: lon
        in: query
        type: number
        format: float
        required: true
    responses:
      200:
        description: Temperature value
    """

    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))

    temp = real_ds.temperature.sel(
        lat=lat,
        lon=lon,
        method="nearest"
    )

    value = float(temp.isel(time=0))

    return jsonify({
        "temperature": value
    })


# Concept: time dimension
@app.route("/realtimeseries", methods=["GET"])
def real_timeseries():
    """
    Get temperature timeseries from `real_ds` at nearest lat/lon.
    ---
    tags:
      - Temperature (real)
    parameters:
      - name: lat
        in: query
        type: number
        format: float
        required: true
      - name: lon
        in: query
        type: number
        format: float
        required: true
    responses:
      200:
        description: Temperature timeseries
    """

    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))

    series = real_ds.temperature.sel(
        lat=lat,
        lon=lon,
        method="nearest"
    )

    return jsonify({
        "values": series.values.tolist()
    })

@app.route("/realtime-weather", methods=["GET"])
def realtime_weather():
    """
    Get "real-time" weather values (nearest lat/lon; optionally at a given time).

    Notes:
    - This API reads from the xarray dataset(s) you have locally (not a live upstream feed).
    - Your current dataset only contains `temperature` and `humidity`. Wind/pressure will be null until present.
    ---
    tags:
      - Weather (real)
    parameters:
      - name: lat
        in: query
        type: number
        format: float
        required: true
      - name: lon
        in: query
        type: number
        format: float
        required: true
      - name: time
        in: query
        type: string
        required: false
        description: Optional time coordinate value; if omitted uses the latest time in the dataset
    responses:
      200:
        description: Weather at nearest point
    """
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    time_value = request.args.get("time")

    ds_for_read = real_ds

    selection = ds_for_read.sel(lat=lat, lon=lon, method="nearest")

    if "time" in selection.coords:
        if time_value:
            selection = selection.sel(time=time_value)
        else:
            selection = selection.isel(time=-1)

    temp_var = _first_existing_var(ds_for_read, ["temperature", "temp", "t2m", "air_temperature"])
    hum_var = _first_existing_var(ds_for_read, ["humidity", "rh", "relative_humidity", "q"])
    wind_var = _first_existing_var(ds_for_read, ["wind", "wind_speed", "windspeed", "u10", "v10"])
    pres_var = _first_existing_var(ds_for_read, ["pressure", "pres", "msl", "mean_sea_level_pressure", "sp"])

    def maybe_value(var_name: str | None):
        if not var_name:
            return None
        value = selection[var_name]
        if getattr(value, "size", 1) != 1:
            value = value.mean()
        return float(value.values)

    payload = {
        "requested": {"lat": lat, "lon": lon, "time": time_value},
        "nearest": {
            "lat": float(selection["lat"].values) if "lat" in selection.coords else None,
            "lon": float(selection["lon"].values) if "lon" in selection.coords else None,
            "time": str(selection["time"].values) if "time" in selection.coords else None,
        },
        "data": {
            "temperature": maybe_value(temp_var),
            "humidity": maybe_value(hum_var),
            "wind": maybe_value(wind_var),
            "pressure": maybe_value(pres_var),
        },
        "available_variables": list(ds_for_read.data_vars),
    }

    return jsonify(payload)

@app.route("/region-average", methods=["GET"])
def region_average():
    """
    Compute average temperature over a lat/lon bounding box (sample dataset).
    ---
    tags:
      - Temperature (sample)
    parameters:
      - name: lat_min
        in: query
        type: number
        format: float
        required: true
      - name: lat_max
        in: query
        type: number
        format: float
        required: true
      - name: lon_min
        in: query
        type: number
        format: float
        required: true
      - name: lon_max
        in: query
        type: number
        format: float
        required: true
    responses:
      200:
        description: Average temperature in region
    """

    lat_min = float(request.args.get("lat_min"))
    lat_max = float(request.args.get("lat_max"))
    lon_min = float(request.args.get("lon_min"))
    lon_max = float(request.args.get("lon_max"))

    region = ds.temperature.sel(
        lat=slice(lat_min,lat_max),
        lon=slice(lon_min,lon_max)
    )

    return jsonify({
        "avg_temperature": float(region.mean())
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
