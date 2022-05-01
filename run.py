import requests
import shapefile
import csv
import geopandas as gpd
from bs4 import BeautifulSoup
from urllib.parse import quote, urlencode


def run():
    all_stations, headings = get_station_list()
    filtered_stations = get_stations_by_city(
        all_stations, ["嘉義縣", "嘉義市", "臺南市"])
    create_shapefile(filtered_stations, headings)
    get_rain_monthly_data(filtered_stations, ["2019", "2020", "2021"])


def get_station_list():
    STATION_URL = "https://e-service.cwb.gov.tw/wdps/obs/state.htm#existing_station"
    # Get rain station list
    r = requests.get(STATION_URL)
    r.encoding = 'utf-8'
    if r.status_code == requests.codes.ok:
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find(id='existing_station').find(
            "table", attrs={"class": "download_html_table"})
        # The first tr contains the field names.
        headings = [th.get_text() for th in table.find("tr").find_all("th")]

        datasets = []
        for row in table.find_all("tr")[1:]:
            dataset = zip(headings, (td.get_text()
                          for td in row.find_all("td")))
            datasets.append(tuple(dataset))
    return datasets, headings


def get_stations_by_city(station_dataset, city_list):
    filtered_station_list = []
    for city in city_list:
        filtered = filter(lambda sta: sta[5][1] == city, station_dataset)
        filtered_station_list += list(filtered)
    return filtered_station_list


def create_shapefile(point_list, headings):
    SHP_FILENAME = "rain_station"
    point_list_noheading = [[coord[1] for coord in pair]
                            for pair in point_list]
    w = shapefile.Writer('./Data/' + SHP_FILENAME + '.shp', shapefile.POINT)
    for j in headings:
        w.field(j, 'C', '100')
    for i in point_list_noheading:
        w.point(float(i[3]), float(i[4]))
        w.record(*i)
        # w.save('./rain_station.shp')
    # create the PRJ file
    prj = open("./Data/%s.prj" % SHP_FILENAME, "w")
    epsg = 'GEOGCS["WGS 84",'
    epsg += 'DATUM["WGS_1984",'
    epsg += 'SPHEROID["WGS 84",6378137,298.257223563]]'
    epsg += ',PRIMEM["Greenwich",0],'
    epsg += 'UNIT["degree",0.0174532925199433]]'
    prj.write(epsg)
    prj.close()


def get_rain_monthly_data(station_list, year_list):
    YEAR_REPORT_URL = "https://e-service.cwb.gov.tw/HistoryDataQuery/YearDataController.do"
    for station in station_list:
        for year in year_list:
            payload = {'command': 'viewMain',
                       'station': station[0][1],
                       "stname": quote(str(station[1][1])),
                       "datepicker": year,
                       "altitude": station[2][1] + "m"}
            r = requests.get(YEAR_REPORT_URL, params=urlencode(payload))
            if r.status_code == requests.codes.ok:
                html = r.text
                soup = BeautifulSoup(html, "html.parser")
                table = soup.find(id='MyTable')
                headings = [th.get_text()
                            for th in table.find("tr", attrs={"class": "third_tr"}).find_all("th")]
                datasets = []
                for row in table.find_all("tr")[2:]:
                    dataset = zip(headings, (td.get_text()
                                             for td in row.find_all("td")))
                    datasets.append(tuple(dataset))
                datasets = filter(None, datasets)
                csv_filename = "%s_%s_%s" % (
                    station[5][1], station[0][1], year)
                save_dataset_to_file(datasets, headings, csv_filename)


def save_dataset_to_file(dataset, heading, filename):
    dataset_noheading = [[value[1] for value in d]
                         for d in dataset]
    with open('./Data/%s.csv' % filename, 'w', newline='') as f:
        write = csv.writer(f)
        write.writerow(heading)
        write.writerows(dataset_noheading)


def create_voronoi_shape(point_shp_filename="./Data/rain_station.shp",
                         boundary_shp_filename="./Data/reservior/reservior.shp"):
    gdf = gpd.read_file(point_shp_filename)
    gdf.head()

    boundary = gpd.read_file(boundary_shp_filename)


if __name__ == '__main__':
    run()
