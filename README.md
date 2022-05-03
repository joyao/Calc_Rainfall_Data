# Calculate Rainfall Data

This script will automatically crawling data from CWB website, create voronoi polygon and calculate rainfall data.

## Environment Setup

### Windows

Since some package cannot automatically installed by pip, you have to get the following packages form [Unofficial Windows Binaries for Python Extension Packages](https://www.lfd.uci.edu/~gohlke/pythonlibs/).

-   Fiona-1.8.21-cp39-cp39-win_amd64.whl
-   GDAL-3.4.2-cp39-cp39-win_amd64.whl
-   Rtree-1.0.0-cp39-cp39-win_amd64.whl
-   Shapely-1.8.1.post1-cp39-cp39-win_amd64.whl

```cmd
pip install .\Fiona-1.8.21-cp39-cp39-win_amd64.whl
pip install .\GDAL-3.4.2-cp39-cp39-win_amd64.whl
pip install .\Rtree-1.0.0-cp39-cp39-win_amd64.whl
pip install .\Shapely-1.8.1.post1-cp39-cp39-win_amd64.whl
```

Install requirements packages

```cmd
pip install -r requirements.txt
```

## Run Script

```
python run.py
```

## Output Data

-   `rain_station.dbf/.prj/.shp/.shx`: Rain stations shapefile with station information attribute.
-   `voronoi_<timestemp>.cpg/.dbf/.prj/.shp/.shx`: The voronoi polygon of selected city area.
-   `voronoi_<timestemp>_final_<timestemp>.cpg/.dbf/.prj/.shp/.shx`: The voronoi polygon of reservior area.
-   `<CityName>_<StationID>.csv`: Rainfall data crawled from CWB website
-   `all_rainfall_data.json`: All rainfall data crawled from CWB website.
-   `rainfall_coronoi_all.cpg/.dbf/.prj/.shp/.shx`: The voronoi polygon of reservior area shapefile with all rainfall monthly attribute.
-   `rainfall_coronoi_all.csv`: Rainfall monthly data of reservior area.
-   `irrigation_rainfall_voronoi_all.cpg/.dbf/.prj/.shp/.shx`: The voronoi polygon of reservior area shapefile with irrigation rainfall monthly attribute.
-   `irrigation_rainfall_voronoi_all.csv`: Irrigation rainfall monthly data of reservior area.
