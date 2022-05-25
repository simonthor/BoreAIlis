import os
import sys
# TODO change this to where you have the CDF reader installed
os.environ["CDF_LIB"] = "/home/simon/installers/cdf38_1-dist/lib"

from spacepy import datamodel
import aacgmv2
import scipy.interpolate as spi
import numpy as np
from datetime import datetime
import glob


def cart2pol(x, y):
    r = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y, x)
    phi[phi < 0] += 2*np.pi
    return r, phi


def main(dirname):
    print(dirname)
    data_sources = glob.glob(dirname)
    for data_source in data_sources:
        fn_nodir = data_source.split('/')[-1]
        fn_noext = fn_nodir[:fn_nodir.rfind('.')]
        # TODO change this directory to wherever you want to save the files
        fn_export = f"/mnt/f/Simon DL research/processed/{fn_noext}.h5"
        if os.path.exists(fn_export):
            print(f"Skipping {fn_export}")
            continue
        
        print(f"Begin processing {data_source}", end="\r")
        images, times = data_to_grid_image(data_source)
        if np.any(datamodel.dmarray(images, dtype=float) < 0):
            print(f"non-positive values found for {data_source}")
        if len(images) <= 0:
            print(f"No valid images found for {data_source}")
            continue

        data = datamodel.SpaceData()
        data['image'] = datamodel.dmarray(images, dtype=float)
        data['time'] = datamodel.dmarray(times, dtype=datetime)
        
        datamodel.toHDF5(fn_export, data)
        del images
        del times
        del data
        print(f"Finished {fn_noext}")

def data_to_grid_image(data_source):
    data = datamodel.fromCDF(data_source)

    images = []
    times = []

    for i, (im, lat, lon, dt) in enumerate(zip(data['Image_Counts_Clean'], data['Geo_Lat'], data['Geo_Lon'], data['Epoch'])):
        max_lat = 30
        mask = (0 <= im) & (0 <= lon) & (0 <= lat)
        if mask.sum() < 5000:
            #print(f"Warning: Only {mask.sum()} pixels passed 1st selection at {dt}. Skipping.")
            continue
        (lat_c, lon_c, _) = aacgmv2.convert_latlon_arr(lat[mask], lon[mask], 0, dt)
        
        lat_m = 90 - lat_c
        nan_mask = ~np.isnan(lat_c) & ~np.isnan(lat_m) & (lat_m <= max_lat + 5)

        if nan_mask.sum() < 5000:
            #print(f"Warning: Only {nan_mask.sum()} pixels passed 2nd selection at {dt}. Skipping.")
            continue
        
        lat_m = lat_m[nan_mask]
        
        lon_c = lon_c[nan_mask]
        lon_m = aacgmv2.convert_mlt(lon_c, dt, m2a=False)
        lon_m = lon_m / 24 *2*np.pi

        im_cropped = im[mask][nan_mask]

        npoints = 80
        axis = np.linspace(-max_lat, max_lat, npoints)
        X, Y = np.meshgrid(axis, axis)
        interpolate = spi.LinearNDInterpolator(np.c_[lat_m, lon_m], im_cropped)
        R, Phi = cart2pol(X, Y)
        colors = np.zeros(R.shape)
        colors[R <= max_lat] = interpolate(R[R <= max_lat], Phi[R <= max_lat])
        # Set images that have negative and nan values (maybe because of bad interpolation?) to 0.
        colors[colors < 0] = 0
        colors[np.isnan(colors)] = 0
        images.append(colors)
        times.append(dt)

    return images, times

if __name__ == '__main__':
    profile = False
    if profile:
        import cProfile
        import pstats
        import io

        with cProfile.Profile() as pr:
            main(sys.argv[1])
            
        sortby = pstats.SortKey.CUMULATIVE
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        with open('profiling.log', 'w') as f:
            print(s.getvalue(), file=f)
    else:
        main(sys.argv[1])