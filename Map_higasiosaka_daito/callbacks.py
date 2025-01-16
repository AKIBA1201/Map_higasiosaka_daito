# callbacks.py

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Output, Input
from layout import variable_options
from data_loader import load_municipality_data
import logging
import geopandas as gpd
from shapely.geometry import Point
import numpy as np

def register_callbacks(app):
    @app.callback(
        Output('mapPlot', 'figure'),
        [Input('city_selection', 'value'), Input('variable', 'value')]
    )
    def update_map(selected_cities, selected_var):
        logging.debug(f"update_map callback triggered with cities: {selected_cities}, selected_var: {selected_var}")
        print(f"update_map callback triggered with cities: {selected_cities}, selected_var: {selected_var}")
        
        if not selected_cities or not selected_var:
            logging.info("City or variable not selected. Returning empty figure.")
            print("City or variable not selected. Returning empty figure.")
            return go.Figure()
        
        try:
            # 選択された市が文字列の場合、リストに変換
            if isinstance(selected_cities, str):
                selected_cities = [selected_cities]
            
            data_list = []
            for city in selected_cities:
                data_city = load_municipality_data(city)
                data_list.append(data_city)
            
            # 全ての市のデータを結合
            data = pd.concat(data_list, ignore_index=True)
            
            # 選択された変数に対応するラベルを取得
            display_label = [k for k, v in variable_options.items() if v == selected_var][0]
            
            if 'city_town_key' not in data.columns:
                logging.error("Column 'city_town_key' not found in data.")
                print("Column 'city_town_key' not found in data.")
                return go.Figure()
            
            if data.geometry.isnull().all():
                logging.error("Geometry data is missing.")
                print("Geometry data is missing.")
                return go.Figure()
            
            # CRSの確認と変換
            if data.crs != "EPSG:4326":
                data = data.to_crs(epsg=4326)
                logging.info("Coordinate reference system transformed to EPSG:4326.")
                print("Coordinate reference system transformed to EPSG:4326.")
            
            # 選択された市のキーを作成（市名をソートして結合）
            sorted_cities = sorted(selected_cities)
            city_key = '・'.join(sorted_cities)
            print(f"Generated city_key: {city_key}")
            
            # 事前定義されたズームと中心位置の設定
            zoom_and_center_settings = {
                '大阪市鶴見区': {'zoom': 13.1, 'center_offset': {'lat': -0.00002, 'lon': -0.0004}},
                '大東市': {'zoom': 13.1, 'center_offset': {'lat': 0.001, 'lon': 0.006}},
                '大東市・東大阪市': {'zoom': 11.9, 'center_offset': {'lat': 0.004, 'lon': 0.006}},
                '門真市': {'zoom': 13.0, 'center_offset': {'lat': -0.002, 'lon': -0.0007}},
                '東大阪市': {'zoom': 12.4, 'center_offset': {'lat': -0.002, 'lon': 0.015}},
                '大阪市鶴見区・大東市・東大阪市・門真市': {'zoom': 10.8, 'center_offset': {'lat': 0.000, 'lon': 0.003}},
                # 必要に応じて他の組み合わせを追加
            }
            
            # 地図の中心とズームレベルの設定
            if city_key in zoom_and_center_settings:
                settings = zoom_and_center_settings[city_key]
                zoom = settings['zoom']
                center_offset = settings['center_offset']
                
                # 中心点の計算
                projected_data = data.to_crs(epsg=3857)  # Web Mercatorに変換
                centroid = projected_data.unary_union.centroid
                centroid = gpd.GeoSeries([centroid], crs="EPSG:3857").to_crs(epsg=4326).iloc[0]
                center = {
                    "lat": centroid.y + center_offset['lat'],
                    "lon": centroid.x + center_offset['lon']
                }
                print(f"Using predefined settings for {city_key}: zoom={zoom}, center={center}")
            else:
                # 動的に中心点とズームレベルを計算
                projected_data = data.to_crs(epsg=3857)  # Web Mercatorに変換
                centroid = projected_data.unary_union.centroid  # 全体の中心を計算
                centroid = gpd.GeoSeries([centroid], crs="EPSG:3857").to_crs(epsg=4326).iloc[0]
                center = {"lat": centroid.y, "lon": centroid.x}
                logging.debug(f"Map center calculated at: {center}")
                print(f"Map center calculated at: {center}")

                # ズームレベルの計算（データの範囲に基づく）
                bounds = projected_data.total_bounds  # [minx, miny, maxx, maxy]
                map_width = bounds[2] - bounds[0]
                map_height = bounds[3] - bounds[1]
                max_dimension = max(map_width, map_height)
                zoom = 21.3 - np.log(max_dimension)
                zoom = max(min(zoom, 15), 5)  # ズームレベルを5から15の範囲に制限
                logging.debug(f"Calculated zoom level: {zoom}")
                print(f"Calculated zoom level: {zoom}")
            
            # 地図の作成
            fig = px.choropleth_mapbox(
                data,
                geojson=data.__geo_interface__,
                locations='city_town_key',
                color=selected_var,
                featureidkey='properties.city_town_key',
                mapbox_style="open-street-map",
                center=center,
                zoom=zoom,
                opacity=0.5,
                labels={selected_var: display_label}
            )
            
            fig.update_traces(hovertemplate="<b>%{location}</b><br>" + display_label + ": %{z}<extra></extra>")
            fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
            logging.info("Map updated successfully.")
            print("Map updated successfully.")
            return fig
        except FileNotFoundError as e:
            logging.error(e)
            print(e)
            return go.Figure()
        except Exception as e:
            logging.exception("予期しないエラーが発生しました。")
            print("予期しないエラーが発生しました。")
            return go.Figure()
    
    @app.callback(
        Output('barPlot', 'figure'),
        [Input('mapPlot', 'clickData'), Input('city_selection', 'value')]
    )
    def update_bar(clickData, selected_cities):
        logging.debug("update_bar callback triggered.")
        print("update_bar callback triggered.")
        
        if not clickData or not selected_cities:
            logging.info("Insufficient data for bar plot. Returning empty figure.")
            print("Insufficient data for bar plot. Returning empty figure.")
            return {
                "data": [],
                "layout": go.Layout(
                    xaxis={"visible": False},
                    yaxis={"visible": False},
                    annotations=[
                        {
                            "text": "クリックで年齢層別人口の表示",
                            "xref": "paper",
                            "yref": "paper",
                            "showarrow": False,
                            "font": {
                                "size": 15
                            }
                        }
                    ]
                )
            }
        
        try:
            city_town_key = clickData['points'][0]['location']
            logging.info(f"Clicked city_town_key: {city_town_key}")
            print(f"Clicked city_town_key: {city_town_key}")
            
            if isinstance(selected_cities, str):
                selected_cities = [selected_cities]
            
            data_list = []
            for city in selected_cities:
                data_city = load_municipality_data(city)
                data_list.append(data_city)
            
            data = pd.concat(data_list, ignore_index=True)
        
            selected_town_data = data[data['city_town_key'] == city_town_key]
            logging.info(f"Updating bar plot for city_town_key: {city_town_key}")
            print(f"Updating bar plot for city_town_key: {city_town_key}")
        
            if selected_town_data.empty:
                logging.warning(f"No data found for city_town_key: {city_town_key}")
                print(f"No data found for city_town_key: {city_town_key}")
                return go.Figure()
        
            age_groups = [
                'age_0_4', 'age_5_9', 'age_10_14', 'age_15_19',
                'age_20_24', 'age_25_29', 'age_30_34', 'age_35_39',
                'age_40_44', 'age_45_49', 'age_50_54', 'age_55_59',
                'age_60_64', 'age_65_69', 'age_70_74', 'age_over_75'
            ]
            age_labels = [
                '0-4', '5-9', '10-14', '15-19',
                '20-24', '25-29', '30-34', '35-39',
                '40-44', '45-49', '50-54', '55-59',
                '60-64', '65-69', '70-74', '75以上'
            ]
        
            population_values = []
            actual_age_labels = []
            for ag, label in zip(age_groups, age_labels):
                if ag in selected_town_data.columns:
                    population = selected_town_data[ag].iloc[0]
                    population_values.append(population if not pd.isnull(population) else 0)
                    actual_age_labels.append(label)
                else:
                    population_values.append(0)
                    actual_age_labels.append(label)
        
            df = pd.DataFrame({'AgeGroup': actual_age_labels, 'Population': population_values})
            
            if '_' in city_town_key:
                city_name, town_name = city_town_key.split('_', 1)
            else:
                city_name = ''
                town_name = city_town_key
        
            fig = px.bar(df, x='AgeGroup', y='Population')
            fig.update_layout(
                title={
                    'text': f'{city_name}<br>{town_name}の年齢別人口',
                    'x': 0.5,
                    'y': 0.96,
                    'xanchor': 'center',
                    'font': {'size': 18}
                },
                xaxis_title='',
                yaxis_title='',
                xaxis_tickangle=45
            )
            logging.info("Bar plot updated successfully.")
            print("Bar plot updated successfully.")
            return fig
        
        except Exception as e:
            logging.exception("バープロットの更新中にエラーが発生しました。")
            print("バープロットの更新中にエラーが発生しました。")
            return go.Figure()
