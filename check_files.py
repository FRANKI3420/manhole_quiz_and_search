import os

def delete_non_jpg_files(directory):
    # 許可する拡張子
    valid_extensions = ('.jpg', '.jpeg')
    
    if not os.path.exists(directory):
        print(f"エラー: {directory} フォルダが見つかりません。")
        return

    # 削除対象のリストを作成
    targets = []
    for filename in os.listdir(directory):
        ext = os.path.splitext(filename)[1].lower()
        file_path = os.path.join(directory, filename)
        
        # 拡張子が対象外かつ、ファイルであること
        if ext not in valid_extensions and os.path.isfile(file_path):
            targets.append(filename)

    if not targets:
        print("削除対象のファイル（非JPG）は見つかりませんでした。")
        return

    # 対象を表示
    print(f"以下の {len(targets)} 件のファイルを削除します:")
    for name in targets:
        print(f"  - {name}")

    # 最終確認
    confirm = input("\n本当に削除しますか？ (y/n): ")
    if confirm.lower() == 'y':
        for name in targets:
            try:
                os.remove(os.path.join(directory, name))
                print(f"削除完了: {name}")
            except Exception as e:
                print(f"削除失敗: {name} - {e}")
        print("\nすべての削除処理が完了しました。")
    else:
        print("\nキャンセルしました。")

if __name__ == "__main__":
    delete_non_jpg_files("manhole_images")