import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# create coordinates
time = pd.date_range("2026-03-01", periods=5)
lat = [30, 31, 32]
lon = [75, 76, 77]

# create random data
temperature = np.random.rand(5,3,3)

print(temperature)
# create dataset
ds = xr.Dataset(
    {
        "temperature": (["time","lat","lon"], temperature)
    },
    coords={
        "time": time,
        "lat": lat,
        "lon": lon
    }
)
ds.temperature.isel(time=0).plot()
print(ds)
print(ds.temperature.sel(lat=31, lon=76))
plt.show()
