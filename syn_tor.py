import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.ndimage import gaussian_filter
import imageio.v2 as imageio
import os

# === Load and merge ERA5 datasets ===
files = ["sl.nc", "sl2.nc", "pl.nc", "pl2.nc"]
datasets = [xr.open_dataset(f).drop_vars(['number', 'expver'], errors='ignore') for f in files]
ds = xr.merge(datasets)

# Fix time coordinate
if 'valid_time' in ds:
    ds = ds.rename({'valid_time': 'time'})
    ds = ds.assign_coords(time=pd.to_datetime(ds['time'].values, unit='s'))

# === Load tornado reports ===
df1 = pd.read_csv("230331_rpts_filtered_torn.csv")
df2 = pd.read_csv("230401_rpts_torn.csv")
df1['source_date'] = '2023-03-31'
df2['source_date'] = '2023-04-01'
df = pd.concat([df1, df2], ignore_index=True)

df['datetime'] = pd.to_datetime(
    df['source_date'] + ' ' + df['Time'].astype(str).str.zfill(4),
    format='%Y-%m-%d %H%M',
    errors='coerce'
)
df = df[df['Lat'].notna() & df['Lon'].notna()]

# === Define time range ===
start_time = pd.Timestamp("2023-03-31T18:00:00")
end_time = pd.Timestamp("2023-04-02T00:00:00")
hours = pd.date_range(start=start_time, end=end_time, freq='1H', inclusive='left')

# === Define variable configurations ===
variables = {
    'z300': {
        'data': lambda t: gaussian_filter(ds['z'].sel(pressure_level=300, time=t, method='nearest') / 98.0665, sigma=1.0),
        'cmap': 'YlGnBu_r',
        'levels': np.linspace(880, 1000, 41),
        'label': "Geopotential Height (dam)",
        'title': "300 hPa Geopotential Height",
        'contours': True
    },
    'wind300': {
        'data': lambda t: gaussian_filter(np.sqrt(
            ds['u'].sel(pressure_level=300, time=t, method='nearest')**2 +
            ds['v'].sel(pressure_level=300, time=t, method='nearest')**2), sigma=1.0),
        'cmap': 'plasma',
        'levels': np.linspace(20, 90, 36),
        'label': "Wind Speed (m/s)",
        'title': "300 hPa Wind Speed",
        'contours': False
    },
    'vort500': {
        'data': lambda t: gaussian_filter(ds['vo'].sel(pressure_level=500, time=t, method='nearest') * 1e5, sigma=1.0),
        'cmap': 'RdBu_r',
        'levels': np.linspace(-40, 40, 21),
        'label': "Absolute Vorticity (10⁻⁵ s⁻¹)",
        'title': "500 hPa Vorticity",
        'contours': False
    },
    'temp850': {
        'data': lambda t: gaussian_filter(ds['t'].sel(pressure_level=850, time=t, method='nearest') - 273.15, sigma=1.0),
        'cmap': 'RdYlBu_r',
        'levels': np.linspace(-20, 30, 26),
        'label': "Temperature (°C)",
        'title': "850 hPa Temperature",
        'contours': False
    },
    'cape': {
        'data': lambda t: gaussian_filter(ds['cape'].sel(time=t, method='nearest'), sigma=1.5),
        'cmap': 'plasma',
        'levels': np.linspace(0, 3000, 31),
        'label': "Surface CAPE (J/kg)",
        'title': "Surface CAPE",
        'contours': False
    },
}

# === Generate plots and GIFs ===
for varname, props in variables.items():
    frame_files = []
    for current_time in hours:
        data = props['data'](current_time)
        df_cumulative = df[(df['datetime'] >= start_time) & (df['datetime'] <= current_time)]

        fig = plt.figure(figsize=(16, 9))
        ax = plt.axes(projection=ccrs.LambertConformal())
        ax.set_extent([-125, -66.5, 24, 50], crs=ccrs.PlateCarree())

        ax.add_feature(cfeature.STATES.with_scale('50m'), edgecolor='black')
        ax.add_feature(cfeature.BORDERS, linestyle='--')
        ax.add_feature(cfeature.COASTLINE)

        cf = ax.contourf(ds['longitude'], ds['latitude'], data,
                         levels=props['levels'], cmap=props['cmap'], extend='both',
                         transform=ccrs.PlateCarree())

        if props.get('contours', False):
            cs = ax.contour(ds['longitude'], ds['latitude'], data,
                            levels=np.arange(880, 1000 + 6, 6), colors='black',
                            linewidths=1.0, transform=ccrs.PlateCarree())
            ax.clabel(cs, inline=1, fontsize=10, fmt="%.0f")

        plt.scatter(df_cumulative['Lon'], df_cumulative['Lat'],
                    c='#d62728', edgecolors='black', linewidths=0.2, s=30,
                    alpha=0.8, transform=ccrs.PlateCarree(), label='Tornado Reports', zorder=10)

        plt.title(f"{props['title']} with SPC Tornado Reports\nThrough {current_time:%HZ %b %d}", fontsize=14)
        cbar = plt.colorbar(cf, ax=ax, orientation='vertical', pad=0.02)
        cbar.set_label(props['label'])
        plt.legend(loc='upper right')
        plt.tight_layout()

        filename = f"{varname}_torn_{current_time:%Y%m%d_%H}.png"
        plt.savefig(filename, dpi=150)
        frame_files.append(filename)
        plt.close()

    gif_name = f"{varname}_torn_animation.gif"
    with imageio.get_writer(gif_name, mode='I', duration=0.9, loop=0) as writer:
        for file in frame_files:
            image = imageio.imread(file)
            writer.append_data(image)
    print(f"✅ {varname.upper()} GIF saved as {gif_name}")

