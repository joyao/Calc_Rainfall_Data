import requests
import shapefile
import csv
import os
import time
import datetime
import json
import glob
import math
import geopandas as gpd
from bs4 import BeautifulSoup
from urllib.parse import quote, urlencode
from shapely.ops import unary_union
from geovoronoi import voronoi_regions_from_coords, points_to_coords


def run():
    YEAR_LIST = ["2019", "2020", "2021"]
    all_stations, headings = get_station_list()
    filtered_stations_city = get_stations_by_city(
        all_stations, ["嘉義縣", "嘉義市", "臺南市"])
    filtered_stations_year = get_stations_by_year(
        filtered_stations_city, YEAR_LIST)
    create_shapefile(filtered_stations_year, headings, "rain_station")
    voronoi_shp_file = create_voronoi_shape(point_shp_filename="./Data/rain_station.shp",
                                            boundary_shp_filename="./Data/county_moi/COUNTY_MOI_1090820_clip.shp")
    voronoi_reservior_shape_path = mask_voromoi_with_reservior(
        voronoi_shp_file)
    all_rain_data, rainfall_headings = get_rain_monthly_data(
        filtered_stations_year, YEAR_LIST)
    calc_rainfall(all_rain_data, rainfall_headings,
                  voronoi_reservior_shape_path, YEAR_LIST)
    calc_rainfall(all_rain_data, rainfall_headings,
                  voronoi_reservior_shape_path, YEAR_LIST, output_filename="irrigation_rainfall_voronoi_all", coefficient=1.0*0.17*0.89)


def get_station_list():
    STATION_URL = "https://e-service.cwb.gov.tw/wdps/obs/state.htm"
    # Get rain station list
    r = requests.get(STATION_URL)
    r.encoding = 'utf-8'
    if r.status_code == requests.codes.ok:
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find(
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


def get_stations_by_year(station_dataset, year_list):
    filtered_station_list = []
    for data in station_dataset:
        for year in year_list:
            data_start_year = datetime.datetime.strptime(
                data[7][1], '%Y/%m/%d').year
            if int(data_start_year) < int(year):
                # If have end date
                if data[8][1]:
                    data_end_year = datetime.datetime.strptime(
                        data[8][1], '%Y/%m/%d').year
                    if int(data_end_year) > int(year):
                        filtered_station_list += list((data, ))
                    break
                else:
                    filtered_station_list += list((data, ))
            else:
                print(data[0][1], data[7][1], data[8][1])
            break
    return filtered_station_list


def create_shapefile(point_list, headings, filename):
    point_list_noheading = [[coord[1] for coord in pair]
                            for pair in point_list]
    w = shapefile.Writer('./Data/' + filename + '.shp',
                         shapefile.POINT, encoding="utf8")
    for j in headings:
        w.field(j, 'C', '100')
    for i in point_list_noheading:
        w.point(float(i[3]), float(i[4]))
        w.record(*i)
    # create the PRJ file
    prj = open("./Data/%s.prj" % filename, "w")
    epsg = 'GEOGCS["WGS 84",'
    epsg += 'DATUM["WGS_1984",'
    epsg += 'SPHEROID["WGS 84",6378137,298.257223563]]'
    epsg += ',PRIMEM["Greenwich",0],'
    epsg += 'UNIT["degree",0.0174532925199433]]'
    prj.write(epsg)
    prj.close()


def get_rain_monthly_data(station_list, year_list, save_file=True):
    YEAR_REPORT_URL = "https://e-service.cwb.gov.tw/HistoryDataQuery/YearDataController.do"
    all_rain_data = {}
    headings = []
    existing_file_list = glob.glob("./Data/*.csv")
    for station in station_list:
        filtered = list(
            filter(lambda sta: station[0][1] in sta, existing_file_list))
        if filtered:
            with open(os.path.normpath(filtered[0]), newline='') as csvfile:
                rows = csv.reader(csvfile)
                headings = list(next(rows))
                all_rain_data[station[0][1]] = list(rows)
            continue
        datasets = []
        data_lists = []
        for year in year_list:
            payload = {'command': 'viewMain',
                       'station': station[0][1],
                       "stname": quote(str(station[1][1])),
                       "datepicker": year,
                       "altitude": station[2][1] + "m"}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
            }
            session = requests.Session()
            r = session.get(YEAR_REPORT_URL,
                            params=urlencode(payload),
                            headers=headers)
            if r.status_code == requests.codes.ok:
                html = r.text
                soup = BeautifulSoup(html, "html.parser")
                table = soup.find(id='MyTable')
                headings = ["Year"] + [th.get_text()
                                       for th in table.find("tr", attrs={"class": "third_tr"}).find_all("th")]
                for row in table.find_all("tr")[2:]:
                    data_list = [td.get_text() for td in row.find_all("td")]
                    data_list = list(filter(None, list(data_list)))
                    if data_list:
                        data_lists.append([year] + data_list)
                    dataset = zip(headings, (td.get_text()
                                             for td in row.find_all("td")))
                    dataset_noempty = tuple(filter(None, tuple(dataset)))
                    if dataset_noempty:
                        datasets.append((("Year", year), ) + dataset_noempty)
        datasets = filter(None, datasets)
        csv_filename = "%s_%s" % (station[5][1], station[0][1])
        save_dataset_to_file(datasets, headings, csv_filename)
        all_rain_data[station[0][1]] = data_lists
    if save_file:
        with open("./Data/all_rainfall_data.json", "w") as fp:
            json.dump(all_rain_data, fp)
    return all_rain_data, headings


def save_dataset_to_file(dataset, heading, filename):
    dataset_noheading = [[value[1] for value in d]
                         for d in dataset]
    with open('./Data/%s.csv' % filename, 'w', newline='') as f:
        write = csv.writer(f)
        write.writerow(heading)
        write.writerows(dataset_noheading)


def create_voronoi_shape(point_shp_filename="./Data/rain_station.shp",
                         boundary_shp_filename="./Data/county_moi/COUNTY_MOI_1090820_clip.shp",
                         voronoi_shp_filename="./Data/voronoi_%s.shp" % time.strftime("%Y%m%d%H%M%S", time.localtime())):
    #  boundary_shp_filename="./Data/reservior/reservior_clip.shp"):
    gdf = gpd.read_file(point_shp_filename, encoding='utf8')
    gdf = gdf.to_crs(epsg=3826)
    gdf.head()

    boundary = gpd.read_file(boundary_shp_filename, encoding='utf8')
    boundary = boundary.to_crs(epsg=3826)
    gdf_proj = gdf.to_crs(boundary.crs)
    boundary_shape = unary_union(boundary.geometry)
    coords = points_to_coords(gdf_proj.geometry)

    # Calculate Voronoi Regions
    try:
        region_polys, region_pts = voronoi_regions_from_coords(
            coords, boundary_shape)
        attr_list = []
        for i in region_pts:
            number = region_pts[i][0]
            attr_list.append(gdf_proj["站號"][number])
        gs = gpd.GeoSeries(region_polys)
        d = {'StationID': attr_list, 'geometry': gs}
        gdf = gpd.GeoDataFrame(d, crs="EPSG:3826")
        gdf['Area'] = gdf['geometry'].area
        gdf.to_file(voronoi_shp_filename)
    except:
        timestemp = time.strftime("%Y%m%d%H%M%S", time.localtime())
        clip_shp_path = "%s_%s.shp" % (
            os.path.splitext(gdf)[0] + "_clip", timestemp)
        clip_shapefile(
            point_shp_filename, boundary_shp_filename, clip_shp_path)
        create_voronoi_shape(
            clip_shp_path, boundary_shp_filename, voronoi_shp_filename)
    return voronoi_shp_filename


def mask_voromoi_with_reservior(voromoi_shp_path, reservior_shp_path="./Data/reservior/reservior_clip.shp"):
    timestemp = time.strftime("%Y%m%d%H%M%S", time.localtime())
    final_voronoi_shape_path = "%s_%s.shp" % (
        os.path.splitext(voromoi_shp_path)[0] + "_final", timestemp)
    clip_shapefile(
        voromoi_shp_path, reservior_shp_path, final_voronoi_shape_path)
    return final_voronoi_shape_path


def clip_shapefile(gdf, mask, output_name):
    shp = gpd.read_file(gdf).to_crs(epsg=3826)
    mask_shp = gpd.read_file(mask).to_crs(epsg=3826)
    clip_shp = gpd.clip(shp, mask_shp)
    clip_shp['Area'] = clip_shp['geometry'].area
    clip_shp.to_file(output_name)
    return output_name


def calc_rainfall(all_rain_data, heading, voronoi_shp_path, year_list, month_list=list(range(1, 13)), output_filename="rainfall_voronoi_all", coefficient=1.0):
    RESULT_FILENAME = "rainfall_voronoi_all"
    RESULT_FILENAME_IRRIGATION = "irrigation_rainfall_voronoi_all"
    csv_sum_rainfall = []
    data = all_rain_data
    if isinstance(all_rain_data, str):
        with open(all_rain_data) as json_file:
            data = json.load(json_file)
    voronoi_shp = gpd.read_file(voronoi_shp_path).to_crs(epsg=3826)

    precp_index = heading.index("Precp")
    for year in year_list:
        station_precp_yearly_sum_attr = []
        station_precp_monthly_sum_attr = {}
        count = 0
        for item in voronoi_shp["StationID"]:
            station_id = item
            filtered = list(filter(
                lambda sta: int(sta[0]) == int(year) and int(sta[1]) in month_list, data[station_id]))
            rainfall_precp = [float(mon[precp_index])
                              for mon in filtered]

            count_month = 0
            for month in month_list:
                rainfall_precp_monthly = rainfall_precp[count_month] * \
                    voronoi_shp["Area"][count]*1*math.pow(10, -6)*coefficient
                count_month += 1
                if str(month) not in station_precp_monthly_sum_attr.keys():
                    station_precp_monthly_sum_attr[str(month)] = []
                station_precp_monthly_sum_attr[str(month)].append(
                    rainfall_precp_monthly)

            rainfall_precp_sum = sum(rainfall_precp) * \
                voronoi_shp["Area"][count]*1*math.pow(10, -6)*coefficient
            station_precp_yearly_sum_attr.append(rainfall_precp_sum)
            count += 1
        for month in month_list:
            voronoi_shp['%s_%s' %
                        (year, str(month))] = station_precp_monthly_sum_attr[str(month)]
            csv_sum_rainfall.append(["%s_%s" % (year, str(month)), sum(
                station_precp_monthly_sum_attr[str(month)])])
        voronoi_shp['%s' % year] = station_precp_yearly_sum_attr
        csv_sum_rainfall.append(["%s" % (year), sum(
            station_precp_yearly_sum_attr)])
    voronoi_shp.to_file("./Data/%s.shp" % output_filename)
    with open('./Data/%s.csv' % output_filename, 'w', newline='') as f:
        write = csv.writer(f)
        write.writerows(csv_sum_rainfall)


if __name__ == '__main__':
    run()
