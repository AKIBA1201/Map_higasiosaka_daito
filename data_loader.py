# data_loader.py

import os
import pandas as pd
import geopandas as gpd
import logging
from shapely.ops import unary_union

def load_municipality_data(municipality_name):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(BASE_DIR, "data")
    
    logging.debug(f"Loading data for municipality: {municipality_name}")
    print(f"Loading data for municipality: {municipality_name}")
    
    # data直下のCSVファイルを指定
    pop_file = os.path.join(data_dir, "tblT001082C27.csv")
    try:
        # CSVファイルを読み込み（1行目を無視して2行目を列名として設定）
        population_data = pd.read_csv(pop_file, encoding='shift_jis', skiprows=1, dtype=str)
        print(f"Raw column names: {population_data.columns.tolist()}")

        # 2行目の Unnamed: 2 と Unnamed: 3 を CITY_NAME, S_NAME に変更
        population_data.rename(columns={'Unnamed: 2': 'CITY_NAME', 'Unnamed: 3': 'S_NAME'}, inplace=True)
        print(f"Cleaned column names: {population_data.columns.tolist()}")

        # 列名から「総数」「歳」などの不要な文字とスペースを削除
        population_data.columns = (
            population_data.columns
            .str.replace(r'総数|歳', '', regex=True)  # 総数や歳を削除
            .str.replace('〜', '～')  # 全角チルダを波ダッシュに統一
            .str.replace(' ', '')      # 余分なスペースを削除
            .str.strip()                # 前後の空白を削除
        )

        # 必要な列が揃っているか確認
        required_columns = ['CITY_NAME', 'S_NAME']
        missing_columns = [col for col in required_columns if col not in population_data.columns]
        if missing_columns:
            raise KeyError(f"必要な列が見つかりません: {missing_columns}")

        # 特定の市区町村データをフィルタリング
        population_data = population_data[population_data['CITY_NAME'].str.contains(municipality_name, na=False, case=False)]

        # 数値データの前処理
        numeric_cols = population_data.columns.drop(['CITY_NAME', 'S_NAME'])
        # '-' や 'X' を NaN に置換し、数値型に変換
        population_data[numeric_cols] = population_data[numeric_cols].replace({'-': None, 'X': None}).apply(pd.to_numeric, errors='coerce')
        # NaN を 0 に置換
        population_data[numeric_cols] = population_data[numeric_cols].fillna(0)
        print("数値データの前処理を行いました。")

        # 年齢別変数の生成（重要な値）
        age_columns = {
            'age_0_4': ['０～４'],
            'age_5_9': ['５～９'],
            'age_10_14': ['１０～１４'],
            'age_15_19': ['１５～１９'],
            'age_20_24': ['２０～２４'],
            'age_25_29': ['２５～２９'],
            'age_30_34': ['３０～３４'],
            'age_35_39': ['３５～３９'],
            'age_40_44': ['４０～４４'],
            'age_45_49': ['４５～４９'],
            'age_50_54': ['５０～５４'],
            'age_55_59': ['５５～５９'],
            'age_60_64': ['６０～６４'],
            'age_65_69': ['６５～６９'],
            'age_70_74': ['７０～７４'],
            'age_over_75': ['７５以上'],
            'male_age_under_10': ['男０～４', '男５～９'],
            'male_age_10_14': ['男１０～１４'],
            'male_age_10_19': ['男１０～１４', '男１５～１９'],
            'male_age_20_29': ['男２０～２４', '男２５～２９'],
            'male_age_20_39': ['男２０～２４', '男２５～２９', '男３０～３４', '男３５～３９'],
            'male_age_30_39': ['男３０～３４', '男３５～３９'],
            'male_age_40_49': ['男４０～４４', '男４５～４９'],
            'male_age_50_59': ['男５０～５４', '男５５～５９'],
            'male_age_60_69': ['男６０～６４', '男６５～６９'],
            'male_age_70_74': ['男７０～７４'],
            'male_age_over_75': ['男７５以上'],
            'female_age_under_10': ['女０～４', '女５～９'],
            'female_age_10_14': ['女１０～１４'],
            'female_age_10_19': ['女１０～１４', '女１５～１９'],
            'female_age_20_29': ['女２０～２４', '女２５～２９'],
            'female_age_20_39': ['女２０～２４', '女２５～２９', '女３０～３４', '女３５～３９'],
            'female_age_30_39': ['女３０～３４', '女３５～３９'],
            'female_age_40_49': ['女４０～４４', '女４５～４９'],
            'female_age_50_59': ['女５０～５４', '女５５～５９'],
            'female_age_60_69': ['女６０～６４', '女６５～６９'],
            'female_age_70_74': ['女７０～７４'],
            'female_age_over_75': ['女７５以上'],
            'age_under_10': ['０～４', '５～９'],
            'age_10_19': ['１０～１４', '１５～１９'],
            'age_20_29': ['２０～２４', '２５～２９'],
            'age_20_39': ['２０～２４', '２５～２９', '３０～３４', '３５～３９'],
            'age_30_39': ['３０～３４', '３５～３９'],
            'age_40_49': ['４０～４４', '４５～４９'],
            'age_50_59': ['５０～５４', '５５～５９'],
            'age_60_69': ['６０～６４', '６５～６９'],
        }

        for new_col, cols in age_columns.items():
            # 存在しない列を除外
            existing_cols = [col for col in cols if col in population_data.columns]
            if existing_cols:
                population_data[new_col] = population_data[existing_cols].sum(axis=1)
            else:
                population_data[new_col] = 0  # 存在しない場合は0を代入
        print("年齢別変数を生成しました。")

        logging.debug(f"Final population_data columns: {population_data.columns.tolist()}")
        print(f"Final population_data columns: {population_data.columns.tolist()}")

    except FileNotFoundError:
        error_msg = f"Population data file not found: {pop_file}"
        logging.error(error_msg)
        print(error_msg)
        raise FileNotFoundError(error_msg)
    except KeyError as e:
        error_msg = f"人口データの読み込み中にエラーが発生しました: {e}"
        logging.error(error_msg)
        print(error_msg)
        raise e
    except Exception as e:
        error_msg = f"人口データの読み込み中にエラーが発生しました: {e}"
        logging.error(error_msg)
        print(error_msg)
        raise e

    # シェイプファイルの読み込み
    try:
        # シェイプファイルが存在するサブディレクトリ
        shape_dir = os.path.join(data_dir, municipality_name)
        if not os.path.isdir(shape_dir):
            logging.error(f"シェイプファイルのディレクトリが見つかりません: {shape_dir}")
            print(f"シェイプファイルのディレクトリが見つかりません: {shape_dir}")
            raise FileNotFoundError(f"シェイプファイルのディレクトリが見つかりません: {shape_dir}")

        # フォルダ内のシェイプファイルを自動的に検出
        shapefiles = [file for file in os.listdir(shape_dir) if file.endswith('.shp') and not file.startswith('~$')]
        if not shapefiles:
            logging.error(f"No shapefiles found in {shape_dir}")
            print(f"No shapefiles found in {shape_dir}")
            raise FileNotFoundError(f"No shapefiles found in {shape_dir}")

        if len(shapefiles) == 1:
            shapefile_name = shapefiles[0]
            shape_file_path = os.path.join(shape_dir, shapefile_name)
            logging.info(f"Found shapefile: {shapefile_name}")
            print(f"Found shapefile: {shapefile_name}")

        else:
            # 複数のシェイプファイルが存在する場合
            shapefile_name = shapefiles[0]
            shape_file_path = os.path.join(shape_dir, shapefile_name)
            logging.warning(f"Multiple shapefiles found in {shape_dir}. Using the first one: {shapefile_name}")
            print(f"Multiple shapefiles found in {shape_dir}. Using the first one: {shapefile_name}")

        try:
            map_data_town = gpd.read_file(shape_file_path, encoding='utf-8')
        except UnicodeDecodeError:
            map_data_town = gpd.read_file(shape_file_path, encoding='shift_jis')

        # CRSをEPSG:4326に変換
        if map_data_town.crs != "EPSG:4326":
            map_data_town = map_data_town.to_crs(epsg=4326)
            logging.info("CRSをEPSG:4326に変換しました。")
            print("CRSをEPSG:4326に変換しました。")

        logging.debug(f"Shapefile data columns: {map_data_town.columns.tolist()}")
        print(f"Shapefile data columns: {map_data_town.columns.tolist()}")
        
        # 'S_NAME'列が存在するか確認
        if 'S_NAME' not in map_data_town.columns:
            logging.error("'S_NAME'列がシェイプファイルに存在しません。")
            print("'S_NAME'列がシェイプファイルに存在しません。")
            raise KeyError("'S_NAME'列がシェイプファイルに存在しません。")

        # 重複している地名を取得
        duplicated_names = map_data_town[map_data_town['S_NAME'].duplicated(keep=False)]['S_NAME'].unique()
        print(f"重複している地名: {duplicated_names}")

        if len(duplicated_names) > 0:
            # 重複地名のデータを抽出
            filtered_shape_data = map_data_town[map_data_town['S_NAME'].isin(duplicated_names)]

            # 'AREA'列が存在するか確認（存在しない場合は計算）
            if 'AREA' not in filtered_shape_data.columns:
                filtered_shape_data['AREA'] = filtered_shape_data.geometry.area

            # 重複地名ごとにポリゴン結合と最大AREAのカラム情報を維持
            def aggregate_data(group):
                # 最大AREAを持つ行を基準にする
                max_area_row = group.loc[group['AREA'].idxmax()]
                # ポリゴンを結合
                merged_geometry = unary_union(group.geometry)
                # 最大AREA行のカラム情報をコピーし、ポリゴンを置き換える
                aggregated_data = max_area_row.copy()
                aggregated_data.geometry = merged_geometry
                aggregated_data['KIGO_E'] = 'E1'  # 固定値
                return aggregated_data

            # S_NAME ごとにグループ化して処理
            merged_geometries = filtered_shape_data.groupby('S_NAME').apply(aggregate_data)
            merged_shape_data = gpd.GeoDataFrame(merged_geometries, geometry='geometry', crs=map_data_town.crs)

            # 重複データを削除して結合後データだけを保持
            map_data_town = map_data_town[~map_data_town['S_NAME'].isin(duplicated_names)]  # 重複地名を除外
            map_data_town = pd.concat([map_data_town, merged_shape_data], ignore_index=True)  # 結合後のデータを追加
            print("重複ポリゴンを結合しました。")

        else:
            print("重複する地名はありません。")

    except Exception as e:
        logging.error(f"シェイプファイルの読み込み中にエラーが発生しました: {e}")
        print(f"シェイプファイルの読み込み中にエラーが発生しました: {e}")
        raise e

    # マージ用の列を探す
    possible_merge_columns = ['city_name', 'cityname', 'city', 'sityo_name', 'municipality']
    map_data_town.columns = map_data_town.columns.str.lower()
    merge_left_on_city = next((col for col in possible_merge_columns if col in map_data_town.columns), None)

    possible_merge_columns_town = ['s_name', 'moji', 'name', '町名']
    merge_left_on_town = next((col for col in possible_merge_columns_town if col in map_data_town.columns), None)

    if not merge_left_on_city or not merge_left_on_town:
        logging.error(f"シェイプファイル内にマージ用の列が見つかりませんでした ({municipality_name})")
        print(f"シェイプファイル内にマージ用の列が見つかりませんでした ({municipality_name})")
        print(f"利用可能な列名: {map_data_town.columns.tolist()}")
        raise KeyError("マージ用の列がシェイプファイルに存在しません。")

    try:
        # 数字を統一するための関数を定義
        def zenkaku_to_hankaku(text):
            if isinstance(text, str):
                return text.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
            return text

        kanji_numbers = {
            '0': '零', '1': '一', '2': '二', '3': '三', '4': '四',
            '5': '五', '6': '六', '7': '七', '8': '八', '9': '九',
            '10': '十', '11': '十一', '12': '十二', '13': '十三', '14': '十四',
            '15': '十五', '16': '十六', '17': '十七', '18': '十八', '19': '十九',
            '20': '二十'
        }

        def arabic_to_kanji_converter(text):
            if isinstance(text, str):
                for num, kanji in sorted(kanji_numbers.items(), key=lambda x: -len(x[0])):
                    text = text.replace(num + '丁目', kanji + '丁目')
                return text
            return text

        # 町名と市名の前処理（全角・半角、スペース、数字の統一）
        def preprocess_name(name):
            if pd.isnull(name):
                return ''
            name = str(name)
            name = name.strip()
            name = name.replace('　', '')  # 全角スペースを削除
            name = name.replace(' ', '')   # 半角スペースを削除
            name = zenkaku_to_hankaku(name)  # 全角数字を半角数字に変換
            name = arabic_to_kanji_converter(name)  # 半角数字を漢数字に変換
            return name.lower()

        # シェイプファイルの市名と町名を前処理
        map_data_town[merge_left_on_city] = map_data_town[merge_left_on_city].apply(preprocess_name)
        map_data_town[merge_left_on_town] = map_data_town[merge_left_on_town].apply(preprocess_name)
        map_data_town['city_town_key'] = map_data_town[merge_left_on_city] + '_' + map_data_town[merge_left_on_town]

        # 人口データの市名と町名を前処理
        population_data['CITY_NAME'] = population_data['CITY_NAME'].apply(preprocess_name)
        population_data['S_NAME'] = population_data['S_NAME'].apply(preprocess_name)
        population_data['city_town_key'] = population_data['CITY_NAME'] + '_' + population_data['S_NAME']

        # マージ
        map_data_town = map_data_town.merge(population_data, on='city_town_key', how='left')
        logging.debug(f"After merge, map_data_town columns: {map_data_town.columns.tolist()}")
        print(f"After merge, map_data_town columns: {map_data_town.columns.tolist()}")
    except Exception as e:
        logging.error(f"データのマージ中にエラーが発生しました: {e}")
        print(f"データのマージ中にエラーが発生しました: {e}")
        raise e

    # マージ後の欠損値確認
    if 'age_20_39' in map_data_town.columns:
        missing = map_data_town['age_20_39'].isnull().sum()
        print(f"マージ後のage_20_39の欠損値数: {missing}")
        if missing > 0:
            logging.warning(f"マージ後に{missing}件のage_20_39の欠損値が発生しました。")
            print(f"マージ後に{missing}件のage_20_39の欠損値が発生しました。")

            # 一致していないcity_town_keyの確認（オプション）
            unmatched = map_data_town[map_data_town['age_20_39'].isnull()]['city_town_key'].unique()
            print("一致していない市区町村と町名の組み合わせ:", unmatched)
            logging.debug(f"一致していない市区町村と町名の組み合わせ: {unmatched}")
    else:
        print("age_20_39列が存在しません。")

    logging.info("データのマージが完了しました。")
    print("データのマージが完了しました。")

    logging.debug(f"Final map_data_town columns: {map_data_town.columns.tolist()}")
    print(f"Final map_data_town columns: {map_data_town.columns.tolist()}")

    return map_data_town
