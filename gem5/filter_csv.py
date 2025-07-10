import pandas as pd

# 入力ファイルと出力ファイルのパス
input_csv = './data.csv'
output_csv = './filtered_data.csv' # フィルタリングされたデータが保存される新しいファイル

try:
    # data.csv を読み込む
    df = pd.read_csv(input_csv)

    # フィルタリング条件を設定
    # 'Core Number' が 8 または 16
    # かつ 'L1 Cache Size (KB)' が 8 または 16
    filtered_df = df[
        (df['Core Number'].isin([8, 16])) &
        (df['L1 Cache Size (KB)'].isin([8, 16]))
    ]

    # フィルタリングされたデータを新しいCSVファイルに保存
    filtered_df.to_csv(output_csv, index=False)

    print(f"フィルタリングされたデータを '{output_csv}' に保存しました。")
    print(f"抽出された行数: {len(filtered_df)}")

except FileNotFoundError:
    print(f"エラー: '{input_csv}' が見つかりません。ファイルパスを確認してください。")
except Exception as e:
    print(f"データの処理中にエラーが発生しました: {e}")