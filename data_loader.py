import xarray as xr

def load_dataset():

    ds = xr.open_mfdataset(
        "datasets/*.nc",
        combine="by_coords",
        chunks={"time":10}
    )

    return ds