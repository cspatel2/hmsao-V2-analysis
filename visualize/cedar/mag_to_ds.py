#%%
import pandas as pd
import xarray as xr

# Define your file paths
input_txt_file = "mag_kiruna.txt"
output_nc_file = "mag_kiruna.nc"

## Step 1: Find the table header line dynamically
header_line_index = 0
with open(input_txt_file, "r") as f:
    for i, line in enumerate(f):
        if "DATE" in line and "TIME" in line:
            header_line_index = i
            break

# Step 2: Read data using regex whitespace parsing
df = pd.read_csv(
    input_txt_file,
    skiprows=header_line_index,
    sep=r"\s+",
    engine="python",
)

# Step 3: Clean column names and drop the trailing empty '|' column
df.columns = df.columns.str.replace("|", "", regex=False).str.strip()
df = df.loc[:, df.columns != ""]  # <-- THIS FIXES THE EMPTY NAME VARIABLE

# Step 4: Combine DATE and TIME into a single UTC Timestamp
df["time"] = pd.to_datetime(
    df["DATE"] + " " + df["TIME"], errors="coerce"
).dt.tz_localize("UTC")

# Drop the legacy independent text columns
df = df.drop(columns=["DATE", "TIME","DOY"])

# Step 5: Convert DataFrame to an xarray Dataset indexed by time
df = df.set_index("time")
ds = xr.Dataset.from_dataframe(df)

# Step 6: Add metadata attributes
ds.time.attrs["standard_name"] = "time"
ds.time.attrs["long_name"] = "Coordinated Universal Time"

for var in ds.data_vars:
    if var != "DOY":
        ds[var].attrs["units"] = "nT"
        ds[var].attrs["long_name"] = f"Geomagnetic Field Component {var}"
    
ds = ds.assign_coords({"tstamp": ('time',[t.timestamp() for t in ds.time.values])})
ds = ds.swap_dims({"time": "tstamp"}).drop("time")

# Step 7: Export to NetCDF
ds.to_netcdf(output_nc_file)
print(f"Successfully created: {output_nc_file}")
print("Final Dataset Variables:", list(ds.data_vars))
# %%
