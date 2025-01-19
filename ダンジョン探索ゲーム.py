import pygame as pg
import random  # 迷路生成に必要


# 初期化処理・グローバル変数
scale_factor = 3
chip_s = int(24 * scale_factor)  # マップチップ基本サイズ
current_field = 'maze'  # 初期状態は迷路内
# 宝物リスト
# 宝箱の種類ごとに入手可能な宝物を定義
treasure_chests = {
    "golden_chest": ["ゴールドコイン", "魔法の指輪"],  # ゴールド宝箱の宝物
    "silver_chest": ["シルバーソード", "不思議なポーション"],  # シルバー宝箱の宝物
    "dragon_chest": ["ドラゴンの卵"],  # ドラゴン宝箱の宝物
}

# 売却額（宝物ごと）
treasure_prices = {
    "ゴールドコイン": 1000,
    "シルバーソード": 5000,
    "魔法の指輪": 3000,
    "ドラゴンの卵": 10000,
    "不思議なポーション": 1500,
}
# 買い物で購入可能なアイテムと価格
shop_items = {
    "シルバーチェストの鍵": 2000,   # 鍵を追加
    "ゴールドチェストの鍵": 8000   # 鍵を追加
}
# 袋 (Bag)
bag = {}
# プレイヤーの所持金
player_money = 0

print("=== ゲームの操作説明 ===")
print("W/A/S/D: 移動")
print("F: 休憩所へ移動 / 休憩所から戻る")
print("B: 袋の中身を表示")
print("V: 所持金の表示")
print("R: アイテムの売却")
print("G: アイテムの購入")
print("豪華な宝箱を開けるには鍵が必要")
print("======================")


# PlayerCharacterクラスの定義
class PlayerCharacter:

  # コンストラクタ
  def __init__(self, init_pos, img_path):
    self.pos = pg.Vector2(init_pos)
    self.size = pg.Vector2(24, 32) * scale_factor
    self.dir = 2
    img_raw = pg.image.load(img_path)
    self.__img_arr = []
    for i in range(4):
      self.__img_arr.append([])
      for j in range(3):
        p = pg.Vector2(24 * j, 32 * i)
        tmp = img_raw.subsurface(pg.Rect(p, (24, 32)))
        tmp = pg.transform.scale(tmp, self.size)
        self.__img_arr[i].append(tmp)
      self.__img_arr[i].append(self.__img_arr[i][1])

    # 移動アニメーション関連
    self.is_moving = False  # 移動処理中は True になるフラグ
    self.__moving_vec = pg.Vector2(0, 0)  # 移動方向ベクトル
    self.__moving_acc = pg.Vector2(0, 0)  # 移動微量の累積

  def turn_to(self, dir):
    self.dir = dir

  def move_to(self, vec):
    self.is_moving = True
    self.__moving_vec = vec.copy()
    self.__moving_acc = pg.Vector2(0, 0)
    self.update_move_process()

  def update_move_process(self):
    assert self.is_moving
    self.__moving_acc += self.__moving_vec * 9
    if self.__moving_acc.length() >= chip_s:
      self.pos += self.__moving_vec
      self.is_moving = False

  def get_dp(self):
    dp = self.pos * chip_s - pg.Vector2(0, 12) * scale_factor
    if self.is_moving:  # キャラ状態が「移動中」なら
      dp += self.__moving_acc  # 移動微量の累積値を加算
    return dp

  def get_img(self, frame):
    return self.__img_arr[self.dir][frame // 6 % 4]

# ワープタイルリストを初期化
warp_tiles = []

# 黒のタイル取得関数
def get_black_tiles(maze):
  black_tiles = []
  for y in range(len(maze)):
    for x in range(len(maze[0])):
      if maze[y][x] == 0:
        black_tiles.append(pg.Vector2(x, y))  # タイルの位置を追加
  return black_tiles

# ゲームループを含むメイン処理
def main():

  # 初期化処理
  pg.init()
  pg.display.set_caption('ダンジョン')
  map_s = pg.Vector2(18, 9)     # マップの横・縦の配置数
  disp_w = int(chip_s * map_s.x)
  disp_h = int(chip_s * map_s.y)
  screen = pg.display.set_mode((disp_w, disp_h))
  clock = pg.time.Clock()
  font = pg.font.Font(None, 15)
  frame = 0
  exit_flag = False
  exit_code = '000'
  start_time = pg.time.get_ticks()  # ゲーム開始時の時間を取得
  chest_images = {
      "golden_chest": pg.image.load('./data/img/takarabako.png').convert_alpha(),
      "silver_chest": pg.image.load('./data/img/takarabako_2.png').convert_alpha(),
      "dragon_chest": pg.image.load('./data/img/takarabako_3.png').convert_alpha(),
  }
  # 宝箱ごとに必要な鍵を定義
  chest_keys = {
      "silver_chest": "シルバーチェストの鍵",
      "dragon_chest": "ゴールドチェストの鍵"
  }

  # タイル画像の読み込み
  white_tile_img = pg.image.load('./data/img/yougan.png').convert()
  black_tile_img = pg.image.load('./data/img/renga.png').convert()
  warp_tile_img = pg.image.load('./data/img/block_koori.png').convert_alpha()
  reset_tile_img = pg.image.load('./data/img/kaidan_down.png').convert_alpha()
  # 現在のフィールド管理変数
  current_field = 'maze'  # 初期状態は迷路内
  # フォント設定（ゲームクリア表示用）
  clear_font = pg.font.Font(None, 72)  # 72pxの大きなフォント
  time_font = pg.font.Font(None, 36)  # タイム表示用の36pxフォント

  # グリッド設定
  grid_c = '#bbbbbb'

  # 自キャラ移動関連
  cmd_move = -1  # 移動コマンドの管理変数
  m_vec = [
      pg.Vector2(0, -1),
      pg.Vector2(1, 0),
      pg.Vector2(0, 1),
      pg.Vector2(-1, 0)
  ]  # 移動コマンドに対応したXYの移動量

  # 自キャラの生成・初期化
  reimu = PlayerCharacter((2, 3), './data/img/reimu.png')

  # 迷路生成関数
  def generate_maze(width, height):
    maze = [[1 for _ in range(width)] for _ in range(height)]
    stack = []
    start_pos = (random.randint(0, height - 1), random.randint(0, width - 1))
    maze[start_pos[0]][start_pos[1]] = 0
    stack.append(start_pos)

    while stack:
      current = stack[-1]
      neighbors = []

      # 隣接タイルを調べる
      for dr, dc in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
        neighbor = (current[0] + dr, current[1] + dc)
        if (0 <= neighbor[0] < height) and (0 <= neighbor[1] < width) and (maze[neighbor[0]][neighbor[1]] == 1):
          if sum(1 for n in [(neighbor[0] + dr2, neighbor[1] + dc2) for dr2, dc2 in [(0, -1), (1, 0), (0, 1), (-1, 0)]] if 0 <= n[0] < height and 0 <= n[1] < width and maze[n[0]][n[1]] == 0) == 1:
            neighbors.append(neighbor)

      if neighbors:
        chosen = random.choice(neighbors)
        maze[chosen[0]][chosen[1]] = 0
        stack.append(chosen)
      else:
        stack.pop()

    return maze

  class Item:

    def __init__(self, position, chest_type):
      self.position = position
      self.collected = False
      self.chest_type = chest_type  # 宝箱の種類
      self.message_shown = False   # メッセージが表示済みかを管理

    def draw(self, screen):
      if not self.collected:
        # 宝箱の種類に対応した画像を描画
        screen.blit(chest_images[self.chest_type],
                    (self.position.x * chip_s, self.position.y * chip_s))

  # 行き止まりを見つける関数

  def get_dead_end_tiles(maze):
    dead_ends = []
    for y in range(len(maze)):
      for x in range(len(maze[0])):
        if maze[y][x] == 0:  # 通路タイル（黒タイル）の場合
          # 隣接するタイルの数をカウント
          neighbors = sum(
              1 for dy, dx in [(0, -1), (1, 0), (0, 1), (-1, 0)]
              if 0 <= y + dy < len(maze) and 0 <= x + dx < len(maze[0]) and maze[y + dy][x + dx] == 0
          )
          if neighbors == 1:  # 隣接する黒タイルが1つだけなら行き止まり
            dead_ends.append(pg.Vector2(x, y))
    return dead_ends

  # ワープタイルを配置する関数
  def place_warp_tiles(maze, num_warp_tiles=1):
    global warp_tiles  # グローバル変数を使用する
    dead_end_tiles = get_dead_end_tiles(maze)  # 行き止まりタイルを取得
    if len(dead_end_tiles) < num_warp_tiles:
      num_warp_tiles = len(dead_end_tiles)  # 行き止まりタイルが足りない場合に調整
    warp_tiles = [(int(tile.x), int(tile.y))
                  for tile in random.sample(dead_end_tiles, num_warp_tiles)]

  # リセットタイルを配置する関数
  def place_reset_tile(maze):
    dead_end_tiles = get_dead_end_tiles(maze)  # 行き止まりタイルを取得
    if dead_end_tiles:  # 行き止まりタイルが存在する場合
        # ワープタイルの位置を除外
      dead_end_tiles = [tile for tile in dead_end_tiles if (
          int(tile.x), int(tile.y)) not in warp_tiles]
      if dead_end_tiles:  # ワープタイル以外の行き止まりがある場合
        reset_tile_pos = random.choice(dead_end_tiles)  # ランダムに選択
        return (int(reset_tile_pos.x), int(reset_tile_pos.y))
    return None

  # アイテム配置
  def place_items(maze, num_items):
    dead_end_tiles = get_dead_end_tiles(maze)  # 行き止まりタイルを取得
    items = []

    if len(dead_end_tiles) < num_items:
      num_items = len(dead_end_tiles)  # 行き止まりタイルが足りない場合

    chest_types = list(treasure_chests.keys())  # 宝箱の種類リスト

    for _ in range(num_items):
      position = random.choice(dead_end_tiles)  # ランダムな行き止まりタイルを選択
      chest_type = random.choice(chest_types)  # ランダムな宝箱の種類を選択
      items.append(Item(position, chest_type))  # 宝箱を生成
      dead_end_tiles.remove(position)  # 同じ行き止まりに複数配置しないように

    return items

  # アイテム収集チェック関数
  def check_item_collection(reimu, items):
    global current_field  # グローバル変数を明示的に参照
    if current_field != 'maze':  # フィールドが迷路でない場合は何もしない
      return False

    for item in items:
      if not item.collected and reimu.pos == item.position:  # 位置が一致する場合
        required_key = chest_keys.get(item.chest_type)  # 必要な鍵を取得

        # ゴールデンチェストは鍵チェックをスキップ
        if item.chest_type == "golden_chest":
          required_key = None

        # 鍵が必要かつ所持していない場合
        if required_key and required_key not in bag:
          if not item.message_shown:  # メッセージがまだ表示されていない場合
            print(f"この宝箱を開けるには「{required_key}」が必要です！")
            item.message_shown = True  # メッセージを表示済みに設定
          return False  # 宝箱を開けられない

        # 宝箱を開ける処理
        item.collected = True  # アイテムを収集
        possible_treasures = treasure_chests[item.chest_type]
        treasure = random.choice(possible_treasures)  # ランダムな宝物を選択
        if treasure in bag:
          bag[treasure] += 1  # 既に所持している場合は個数を増やす
        else:
          bag[treasure] = 1  # 新しい宝物の場合は1個から

        print(
            f"宝箱から「{treasure}」を入手しました！（現在の所持数: {bag[treasure]}）")
        return True  # アイテムを収集した
    return False  # 収集しなかった

  # 迷路を生成place_warp_tiles(maze)  # ワープタイルを配置
  maze = generate_maze(int(map_s.x), int(map_s.y))
  place_warp_tiles(maze)  # ワープタイルを配置
  reset_tile = place_reset_tile(maze)  # リセットタイルを配置

  # ワープタイルと対応する休憩所の位置を明確にリンク
  warp_to_rest_link = {
      'maze_to_rest': warp_tiles[0],  # 迷路から休憩所に行くワープタイル
      'rest_to_maze': pg.Vector2(*warp_tiles[0])  # 休憩所から戻るワープタイル
  }

  # タイル描写
  def draw_maze(screen, maze):
    for y in range(len(maze)):
      for x in range(len(maze[y])):
        pos = (x * chip_s, y * chip_s)
        if maze[y][x] == 1:  # 白タイル
          screen.blit(white_tile_img, pos)
        elif (x, y) in warp_tiles:  # ワープタイル
          screen.blit(warp_tile_img, pos)
        elif (x, y) == reset_tile:  # リセットタイル
          screen.blit(reset_tile_img, pos)
        else:  # 黒タイル
          screen.blit(black_tile_img, pos)

  # 休憩場フィールド
  rest_area = [[0 for _ in range(5)] for _ in range(5)]  # 全て黒タイル
  rest_player_start_pos = pg.Vector2(2, 2)  # 休憩場の中心位置

  black_tiles = get_black_tiles(maze)  # 黒のタイル位置を取得

  # アイテムの数
  num_items = 4
  items = place_items(maze, num_items)  # アイテムを配置

  # プレイヤーキャラクターの初期位置
  if black_tiles:
    start_pos = random.choice(black_tiles)  # ランダムに黒のタイルを選択
  else:
    start_pos = (2, 3)  # 黒のタイルがなければデフォルト位置

  reimu = PlayerCharacter(start_pos, './data/img/reimu.png')  # プレイヤーキャラを初期化

  # タイルの状態を確認する関数
  # 現在のフィールドによって異なる迷路の構造を判定
  def is_valid_move(maze, pos):
    if (0 <= pos.y < len(maze)) and (0 <= pos.x < len(maze[0])):
      return maze[int(pos.y)][int(pos.x)] == 0  # 0が黒色タイル
    return False

  def sell_treasures():
    global bag, player_money  # 袋（宝物リスト）と所持金を使用

    if not bag:  # 袋が空の場合
      print("袋は空です。売却できる宝物がありません。")
      return

    print("=== 売却メニュー ===")
    for i, (treasure, count) in enumerate(bag.items(), start=1):
      price_per_item = treasure_prices.get(treasure, 0)  # 売却額を取得
      print(f"{i}. {treasure}: {count}個 (1個 {price_per_item}G)")
    print("===================")

    try:
      # 売却する宝物を選択
      choice = int(input("売却する宝物の番号を選んでください (キャンセル: 0): "))
      if choice == 0:
        print("売却をキャンセルしました。")
        return

      # 選択された宝物の名前を取得
      treasure_name = list(bag.keys())[choice - 1]
      max_count = bag[treasure_name]

      # 売却する個数を選択
      sell_count = int(input(f"{treasure_name}を何個売りますか？ (最大: {max_count}): "))
      if sell_count <= 0 or sell_count > max_count:
        print("無効な売却個数です。")
        return

      # 売却処理
      sell_price = sell_count * treasure_prices.get(treasure_name, 0)
      bag[treasure_name] -= sell_count
      if bag[treasure_name] == 0:
        del bag[treasure_name]  # 所持数が0になったら削除

      player_money += sell_price  # 所持金を増加
      print(f"{treasure_name}を{sell_count}個売却しました！ 売却額: {sell_price}G")
      print(f"現在の所持金: {player_money}G")

    except (ValueError, IndexError):
      print("無効な入力です。")

  # 買い物メニューの関数
  def shop_menu():
    global player_money, bag  # 所持金と袋を操作するためグローバル変数を使用
    print("=== ショップメニュー ===")
    for i, (item, price) in enumerate(shop_items.items(), start=1):
      print(f"{i}. {item}: {price}G")
    print("===================")

    try:
      # アイテムを選択
      choice = int(input("購入するアイテムの番号を選んでください (キャンセル: 0): "))
      if choice == 0:
        print("買い物をキャンセルしました。")
        return

      # 選択されたアイテムの名前と価格を取得
      item_name, item_price = list(shop_items.items())[choice - 1]

      # 購入処理
      if player_money >= item_price:
        player_money -= item_price  # 所持金を減らす
        if item_name in bag:
          bag[item_name] += 1  # 既に所持している場合は個数を増やす
        else:
          bag[item_name] = 1  # 初めて購入する場合は1個から
        print(f"{item_name}を購入しました！ 現在の所持金: {player_money}G")
      else:
        print("所持金が足りません！")

    except (ValueError, IndexError):
      print("無効な入力です。")

  # ゲームループ
  while not exit_flag:

    # キー状態の取得
    key = pg.key.get_pressed()

    # 休憩所から迷路に戻る処理を優先的に実行
    if current_field == 'rest' and key[pg.K_f]:  # Fキーが押された場合
      current_field = 'maze'  # フィールドを迷路に切り替え
      reimu.pos = warp_to_rest_link['rest_to_maze']  # 対応する迷路の位置に移動

    # システムイベントの検出
    for event in pg.event.get():
      if event.type == pg.QUIT:  # ウィンドウ[X]の押下
        exit_flag = True
        exit_code = '001'

      # 袋の中身を表示
      if event.type == pg.KEYDOWN and event.key == pg.K_b:
        print("袋の中身：")
        if bag:  # 袋に何か入っている場合
          for treasure, count in bag.items():
            print(f"- {treasure}: {count}個")
        else:  # 袋が空の場合
          print("袋は空っぽです。")

      # 売却メニューを開く
      if event.type == pg.KEYDOWN and event.key == pg.K_r:
        sell_treasures()

      if event.type == pg.KEYDOWN and event.key == pg.K_v:  # Mキーが押された場合
        print(f"現在の所持金: {player_money}G")

      # ショップメニューを開く
      if event.type == pg.KEYDOWN and event.key == pg.K_g:
        if current_field == 'rest':  # 現在のフィールドが休憩場の場合のみ
          shop_menu()
        else:
          print("買い物は休憩場でしかできません！")

    # キー状態の取得
    key = pg.key.get_pressed()
    cmd_move = -1
    cmd_move = 0 if key[pg.K_w] else cmd_move
    cmd_move = 1 if key[pg.K_d] else cmd_move
    cmd_move = 2 if key[pg.K_s] else cmd_move
    cmd_move = 3 if key[pg.K_a] else cmd_move

    # 現在のフィールドに応じたプレイヤーの位置切り替え処理
    if not reimu.is_moving:
      for item in items:
        if reimu.pos != item.position:
          item.message_shown = False  # プレイヤーが宝箱の位置から離れた場合にリセット
      if cmd_move != -1:
        reimu.turn_to(cmd_move)
        af_pos = reimu.pos + m_vec[cmd_move]

        if current_field == 'maze':  # 迷路内
          # リセットタイルの位置を安全に確認
          if not isinstance(reset_tile, (tuple, list)) or len(reset_tile) != 2:
            raise ValueError(f"リセットタイルの形式が不正です: {reset_tile}")
          # リセットタイルを踏んだ場合
          if af_pos == pg.Vector2(*reset_tile):

            # 新しい迷路を生成
            maze = generate_maze(int(map_s.x), int(map_s.y))
            place_warp_tiles(maze)  # 新しいワープタイルを配置

            # ワープタイルのデータを更新
            if warp_tiles:  # 迷路から休憩所へのリンクを更新
              warp_to_rest_link['maze_to_rest'] = warp_tiles[0]
              warp_to_rest_link['rest_to_maze'] = pg.Vector2(
                  *warp_tiles[0])  # 休憩所から戻るリンクを更新

            # 新しいリセットタイルを配置
            reset_tile = place_reset_tile(maze)

            # キャラクターの新しい初期位置を設定
            black_tiles = get_black_tiles(maze)  # 移動可能なタイルを取得
            if black_tiles:
              new_start_pos = random.choice(black_tiles)  # 黒タイルからランダムに選択
              reimu.pos = pg.Vector2(new_start_pos)  # キャラクターを新しい位置に移動

            # 宝箱（アイテム）の再配置
            items = place_items(maze, num_items)  # 再度アイテムを配置

          if is_valid_move(maze, af_pos):
            # ワープタイルを踏んだ場合
            if af_pos == pg.Vector2(*warp_to_rest_link['maze_to_rest']):
              current_field = 'rest'  # 休憩所に切り替え
              reimu.pos = rest_player_start_pos  # プレイヤーを休憩所の中心に移動
            else:
              reimu.move_to(m_vec[cmd_move])
        elif current_field == 'rest':  # 休憩所内
          if key[pg.K_f]:  # Fキーを押した場合
            current_field = 'maze'  # 迷路に切り替え
            reimu.pos = warp_to_rest_link['rest_to_maze']  # 対応する迷路の位置へ移動
          elif is_valid_move(rest_area, af_pos):  # 通常移動
            reimu.move_to(m_vec[cmd_move])

    # 背景描画
    screen.fill(pg.Color('WHITE'))  # 全画面を白でクリア

    # 現在のフィールドに応じた描画
    if current_field == 'maze':
      draw_maze(screen, maze)  # 迷路を描画
    elif current_field == 'rest':
      draw_maze(screen, rest_area)  # 休憩場を描画

    # グリッド
    for x in range(0, disp_w, chip_s):  # 縦線
      pg.draw.line(screen, grid_c, (x, 0), (x, disp_h))
    for y in range(0, disp_h, chip_s):  # 横線
      pg.draw.line(screen, grid_c, (0, y), (disp_w, y))

    # キャラが移動中ならば、移動アニメ処理の更新
    if reimu.is_moving:
      reimu.update_move_process()

    # 自キャラの描画
    screen.blit(reimu.get_img(frame), reimu.get_dp())

    # アイテムを描画
    for item in items:
      item.draw(screen)

    # アイテムの収集チェック
    if check_item_collection(reimu, items):
      if check_item_collection(reimu, items):
        print("")

    # クリアタイムを初期化
    clear_time = 0.0

  # クリア条件
    # クリア条件のチェック
    if player_money >= 30000:  # 所持金が30000G以上の場合
        # クリア時に経過時間を計算
      clear_time = (pg.time.get_ticks() - start_time) / 1000  # 秒単位に変換

      # 画面に「クリア」とタイムを表示
      screen.fill(pg.Color('BLACK'))  # 背景を黒くする

      # 大きなフォントで「クリア」を表示
      clear_text = clear_font.render(
          "Congratulation!GameClear!", True, pg.Color('WHITE'))
      screen.blit(clear_text, (disp_w / 2 -
                  clear_text.get_width() / 2, disp_h / 2 - 50))

      # タイムを表示
      time_text = time_font.render(
          f"time: {clear_time:.2f}sec", True, pg.Color('WHITE'))
      screen.blit(
          time_text, (disp_w / 2 - time_text.get_width() / 2, disp_h / 2 + 20))

      # 所持金を表示
      money_text = time_font.render(
          f"money: {player_money}G", True, pg.Color('WHITE'))
      screen.blit(money_text, (disp_w / 2 -
                  money_text.get_width() / 2, disp_h / 2 + 60))

      # 画面更新と一定時間待機
      pg.display.update()
      pg.time.wait(5000)  # 10秒間待機

      print(f"ゲームクリア！ 所持金: {player_money}G、クリアタイム: {clear_time:.2f}秒")
      exit_flag = True  # ゲームを終了する

    # 所持金を表示
    progress_text = font.render(
        f"money: {player_money}G / 30000G", True, 'WHITE')
    screen.blit(progress_text, (10, 30))  # 適切な位置に表示

    # フレームカウンタの描画
    frame += 1
    frm_str = f'{frame:05}'
    screen.blit(font.render(frm_str, True, 'WHITE'), (10, 10))
    screen.blit(font.render(f'{reimu.pos}', True, 'WHITE'), (10, 20))

    # 画面の更新と同期
    pg.display.update()
    clock.tick(30)

    # 画面の更新と同期
  if all(item.collected for item in items):
    # クリア条件が満たされた場合、クリアタイムを表示
    clear_time_text = font.render(f'クリアタイム: {clear_time:.2f}秒', True, 'BLACK')
    screen.blit(clear_time_text, (10, 40))  # 適切な座標に表示
    # 袋の中身を表示
    print("クリア時の袋の中身：")
    for treasure, count in bag.items():
      print(f"- {treasure} :{count}個")

  # ゲームループ [ここまで]
  pg.quit()
  return exit_code

if __name__ == "__main__":
  code = main()
  print(f'プログラムを「コード{code}」で終了しました。')
