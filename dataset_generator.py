import xarray as xr
import numpy as np
import pandas as pd

lat = np.linspace(20,40,20)
lon = np.linspace(70,90,20)
time = pd.date_range("2025-03-8", periods=10)

temperature = 15 + 10*np.random.rand(10,20,20)
humidity = 50 + 20*np.random.rand(10,20,20)

ds = xr.Dataset(
    {
        "temperature": (["time","lat","lon"], temperature),
        "humidity": (["time","lat","lon"], humidity)
    },
    coords={
        "time": time,
        "lat": lat,
        "lon": lon
    }
)

ds.to_netcdf("weather_data.nc")