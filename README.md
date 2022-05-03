# Calculate Rainfall Data

This script will automatically crawling data from CWB website, create voronoi polygon and calculate rainfall data.

## Environement Setup

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
