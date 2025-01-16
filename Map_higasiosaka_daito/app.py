# app.py

from dash import Dash  # Dashフレームワークをインポート。Webアプリケーションの作成に使用される
import webbrowser       # デフォルトのWebブラウザを操作するためのモジュール
from threading import Timer  # スレッドを使用して時間ベースの操作を可能にするモジュール
import logging          # ログを出力するためのモジュール。デバッグや問題のトラッキングに役立つ
import socket           # ネットワーク操作用モジュール。IPアドレスやポートの管理に利用可能

# loggingモジュールを使ってログの出力形式とレベル設定
# logging.DEBUGでデバッグ用の詳細なログを出力
# format='%(levelname)s:%(message)s'でログのフォーマット指定
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

# Dashアプリ全体を管理する土台を作成
app = Dash(__name__)

# 他のファイルからlayoutとcallbacksをインポート
from layout import layout
from callbacks import register_callbacks

# アプリのレイアウトを設定
app.layout = layout

# コールバック関数の登録
register_callbacks(app)

# defでget_local_ipという関数を作成
# hostnameにsocketモジュールでgethostname()関数を使いコンピュータ名を格納
# returnでsocketモジュールgethostbyname()を使い格納したhostnameのIPアドレスを返す
def get_local_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

# サーバー起動設定
# このファイルが直接実行されたときだけ処理を実行するという条件。他ファイルからのインポート無効
if __name__ == '__main__':
    # ポート番号を設定
    port = 8041
    # さっき作成した関数を使いIPアドレスを格納
    local_ip = get_local_ip()
    # Timerモジュールで1秒後に実行。webbrowserモジュールでwebブラウザで指定したURLを開く
    # fで文字列の中に変数を{}で埋め込めるように。.start()でタイマー開始
    Timer(1, lambda: webbrowser.open(f'http://{local_ip}:{port}')).start()
    # try～exceptでエラーが発生するかもしれないコードを実行する形にし、エラー時クラッシュせずにエラー文表示
    try:
        # IPアドレスを含むアドレスの表示
        logging.info(f"Dash is running on http://{local_ip}:{port}/")
        # app.run_serverはDashアプリ起動メソッド
        # host='0.0.0.0'で同じネットワーク内デバイスからもアクセス可能に
        # さっき入力したポート番号で実行
        # デバッグモードONにする。その際のサーバーのリロード機能を無効にして二重起動を防ぐ場合はuse_reloader=False
        app.run_server(host='0.0.0.0', port=port, debug=True, use_reloader=False)
    # OSErrorが発生した時にその情報をeに格納
    except OSError as e:
        # ログにエラーの詳細を記録（例: "サーバー起動エラー: [Errno 98] Address already in use"）
        logging.error(f"サーバー起動エラー: {e}")
        # コンソールにエラー内容を表示（リアルタイムで確認可能）
        print(f"サーバー起動エラー: {e}")
        # ログに「別のポート番号を試すように」と解決策を記録
        logging.info("別のポート番号を試してください。")
        # コンソールに「別のポート番号を試してください」と解決策を表示
        print("別のポート番号を試してください。")