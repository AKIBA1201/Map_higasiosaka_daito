# layout.py

import os
from dash import dcc, html

# 変数オプションの定義（そのまま）

variable_options = {
    # 生徒候補
    "男女20-39歳": "age_20_39",
    "男女小4-中3_10-14歳": "age_10_14",
    "男20-39歳": "male_age_20_39",
    "女20-39歳": "female_age_20_39",
    "男小4-中3_10-14歳": "male_age_10_14",
    "女小4-中3_10-14歳": "female_age_10_14",
    
    # 総人口関連
    "総人口": "population_total",
    "男性": "male_total",
    "女性": "female_total",

    # 年齢別
    "10歳未満": "age_under_10",
    "10-19歳": "age_10_19",
    "20-29歳": "age_20_29",
    "30-39歳": "age_30_39",
    "40-49歳": "age_40_49",
    "50-59歳": "age_50_59",
    "60-69歳": "age_60_69",
    "70-74歳": "age_70_74",
    "75歳以上": "age_over_75",

    # 男性の年齢別
    "男性 10歳未満": "male_age_under_10",
    "男性 10-19歳": "male_age_10_19",
    "男性 20-29歳": "male_age_20_29",
    "男性 30-39歳": "male_age_30_39",
    "男性 40-49歳": "male_age_40_49",
    "男性 50-59歳": "male_age_50_59",
    "男性 60-69歳": "male_age_60_69",
    "男性 70-74歳": "male_age_70_74",
    "男性 75歳以上": "male_age_over_75",

    # 女性の年齢別
    "女性 10歳未満": "female_age_under_10",
    "女性 10-19歳": "female_age_10_19",
    "女性 20-29歳": "female_age_20_29",
    "女性 30-39歳": "female_age_30_39",
    "女性 40-49歳": "female_age_40_49",
    "女性 50-59歳": "female_age_50_59",
    "女性 60-69歳": "female_age_60_69",
    "女性 70-74歳": "female_age_70_74",
    "女性 75歳以上": "female_age_over_75"
}

# スクリプトのディレクトリ（layout.pyが存在するディレクトリ）を取得
script_dir = os.path.dirname(os.path.abspath(__file__))

# dataディレクトリのパスを設定
data_dir = os.path.join(script_dir, 'data')

# dataディレクトリが存在するか確認
if not os.path.exists(data_dir):
    raise FileNotFoundError(f"データディレクトリが見つかりません: {data_dir}")

# ディレクトリ内のフォルダ名を取得（ファイルを除外）
city_list = [name for name in os.listdir(data_dir)
             if os.path.isdir(os.path.join(data_dir, name)) and not name.startswith('.')]

# ドロップダウンのオプションを生成
city_options = [{'label': city, 'value': city} for city in city_list]

# デフォルトで選択される都市名（必要に応じて変更）
default_cities = ['東大阪市', '大東市']

# デフォルト都市がcity_listに存在するか確認し、存在するもののみをデフォルト値に設定
default_cities = [city for city in default_cities if city in city_list]

# レイアウト構成
layout = html.Div([
    html.Div([
        dcc.Dropdown(
            id='city_selection',
            options=city_options,
            value=default_cities,  # デフォルト値をリストに
            placeholder="▼選択してください",
            style={'width': '90%'},
            multi=True  # 複数選択を有効にする
        ),

        dcc.Dropdown(
            id='variable',
            options=[
                {'label': k, 'value': v} for k, v in variable_options.items()
            ],
            value='age_20_39',  # デフォルト値を設定
            placeholder="▼選択してください",
            style={'width': '90%'}
        ),

        dcc.Graph(id='barPlot', style={'height': '640px', 'margin-left': '-50px'})
    ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top',}),

    html.Div([
        dcc.Graph(id='mapPlot', style={'height': '700px', 'width': '100%'})
    ], style={'width': '80%', 'display': 'inline-block', 'verticalAlign': 'top','margin-left': '-50px'})
])
