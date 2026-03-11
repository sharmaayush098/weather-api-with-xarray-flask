import xarray as xr
import numpy as np
import pandas as pd
import os

os.makedirs("datasets", exist_ok=True)

lat = np.linspace(20,40,30)
lon = np.linspace(70,90,30)

for i in range(8, 11):

    time = pd.date_range(f"2026-03-{i+1}", periods=24, freq="h")

    temperature = 15 + 10*np.random.rand(24,30,30)
    humidity = 50 + 20*np.random.rand(24,30,30)

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

    ds.to_netcdf(f"datasets/weather_day{i+1}.nc")