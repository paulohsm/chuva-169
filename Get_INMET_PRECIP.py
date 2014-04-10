# -*- coding: utf-8 -*-

# Pay attention for ### NOT USED ### functions

import psycopg2
import csv
import numpy as np
from scipy.interpolate import griddata
import datetime as dt
import matplotlib.pyplot as plt
import netCDF4 as nc

# Get one instant of INMET observational hourly precipitation 
def Get_INMET_HOURLY_PRECIP(pcp_date):
    host = "fauno"
    bd   = "func"
    user = "consulta"
    pwrd = "funceme"
    query = "SELECT dse_estacao, " \
            "       ST_AsEWKT(est_geom::geometry), " \
            "       dse_valor" \
            "  FROM pcd.dado_sensor, pcd.estacao" \
            " WHERE dse_sensor = 22" \
            "   AND dse_data = %s " \
            "   AND dse_estacao BETWEEN 394 AND 909 " \
            "   AND est_codigo = dse_estacao" \
            " ORDER BY dse_estacao;"
    conn = psycopg2.connect(host=host, database=bd, user=user, password=pwrd)
    cur  = conn.cursor()
    cur.execute(query, [pcp_date])
    precip_data = cur.fetchall()
    return precip_data

# Separate fields of Precip list and format Lon,Lat
def Format_Data(prec_list):
    cod = []
    lon = []
    lat = []
    val = []
    for row in prec_list:
        lonlat = row[1].split("(")[1].split(" ")[0:2]
        cod.append(int(row[0]))
        lon.append(float(lonlat[0]))
        lat.append(float(lonlat[1]))
        val.append(float(row[2]))
    return(cod, lon, lat, val)
    
# Set CSV file name and write data
def Save_CSV(csv_date, cod, lon, lat, val):
    csv_fn = csv_date[0:10]+'-'+csv_date[11:13]+csv_date[14:16]+'_INMET-PRECIP.csv'
    csv_file = open(csv_fn, 'w')
    csv_out = csv.writer(csv_file, delimiter=';')
    for r in range(len(cod)):
        csv_out.writerow([cod[r], lon[r], lat[r], val[r]])

### NOT USED ###
# Interpolate scattered precip to regular grid
def Grid_Prec(lon, lat, val):
    nx = 111 #155
    ny = 114 #115
    minlon = -51.713
    maxlon = -26.963
    minlat = -18.712
    maxlat =   6.713
    lons = np.linspace(minlon, maxlon, nx)
    lats = np.linspace(minlat, maxlat, ny)
    gx, gy = np.meshgrid(lons, lats)
    gprec = griddata((lon,lat),val,(gx,gy),method='cubic')
    return gprec

### NOT USED ###
# Iterate over 7 days to do the tasks above for every hour
# Time interval is from 2014-03-27 00:00 to 2017-04-03 00:00
def Make_CSV_Files():
    base_date = dt.datetime(2014, 03, 27)
    hrs_range = 169
    date_list = [ base_date + dt.timedelta(hours=x) for x in range(0,hrs_range) ]
    gridded_precip = []
    for date in date_list:
        curr_date = date.strftime("%Y-%m-%d %H:%M")
        curr_data = Get_INMET_HOURLY_PRECIP(curr_date)
        c_cod, c_lon, c_lat, c_val = Format_Data(curr_data)
        Save_CSV(curr_date, c_cod, c_lon, c_lat, c_val)
        gridded_precip.append(Grid_Prec(c_lon, c_lat, c_val))

### NOT USED ###
# Grid data and save in NETCDF format
def Make_NC_Gridded():
    nx = 111 #155
    ny = 114 #115
    minlon = -51.713
    maxlon = -26.963
    minlat = -18.712
    maxlat =   6.713
    lons = np.linspace(minlon, maxlon, nx)
    lats = np.linspace(minlat, maxlat, ny)
    gx, gy = np.meshgrid(lons, lats)
    tdate = '2014-03-31 05:00'
    tdata = Get_INMET_HOURLY_PRECIP(tdate)
    tcod, tlon, tlat, tval = Format_Precip(tdata)
    gprec = griddata((tlon,tlat),tval,(gx,gy),method='cubic') 
    #print np.shape(np.meshgrid(lons, lats))
    #print np.shape(np.ndarray(lons, lats))
    #print [tlon,tlat]
    #print np.shape(gprec)
    plt.contourf(gx, gy, gprec)
    plt.show()

# Save data in CSV format, interpolate it to regular grid and save as NetCDF
def Make_All_Files():
    # output grid dimensions
    nx, ny, nt = (111, 114, 169)
    # start time of time series
    base_date = dt.datetime(2014, 03, 27)
    date_list = [ base_date + dt.timedelta(hours=x) for x in range(0,nt) ]
    # horizontal axis/grid
    minlon, maxlon = (-51.713, -26.963)
    minlat, maxlat = (-18.712,   6.713)
    lons = np.linspace(minlon, maxlon, nx)
    lats = np.linspace(minlat, maxlat, ny)
    gx, gy = np.meshgrid(lons, lats)
    # variable to store the complete dataset
    #gridded_data = np.empty([nt,ny,nx], dtype=float)
    # create netCDF file from scratch, add data dimensions
    ncfile = nc.Dataset('chuva169_INMET.nc','w')
    time_dim = ncfile.createDimension('time', 0)
    lat_dim = ncfile.createDimension('lat', ny)
    lon_dim = ncfile.createDimension('lon', nx)
    # netCDF data axes variables
    time = ncfile.createVariable('time', 'f4', ('time',))
    time.units = 'hours since ' + base_date.strftime("%Y-%m-%d %H:%M")
    time.standard_name = 'time'
    time[:] = range(nt)
    lat = ncfile.createVariable('lat', 'f4', ('lat',))
    lat.units = 'degrees_north'
    lat.standard_name = 'latitude'
    lat[:] = lats
    lon = ncfile.createVariable('lon', 'f4', ('lon',))
    lon.units = 'degrees_east'
    lon.standard_name = 'longitude'
    lon[:] = lons
    # the variable interests us: gridded precipitation
    gpcp = ncfile.createVariable('prec', 'f4', ('time','lat','lon'))
    gpcp.units = 'mm'
    gpcp.standard_name = 'hourly_precipitation'
    l = 0
    for date in date_list:
        curr_date = date.strftime("%Y-%m-%d %H:%M")
        curr_data = Get_INMET_HOURLY_PRECIP(curr_date)
        c_cod, c_lon, c_lat, c_val = Format_Data(curr_data)
        Save_CSV(curr_date, c_cod, c_lon, c_lat, c_val)
	gpcp[l,:,:] = griddata((c_lon,c_lat),c_val,(gx,gy),method='linear')
        l = l + 1
    # writing data
    ncfile.close()


#Make_CSV_Files()
#Make_NC_Gridded()
Make_All_Files()
