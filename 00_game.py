import pygame as pg
import random  # 迷路生成に必要


# 初期化処理・グローバル変数
scale_factor = 3
chip_s = int(24 * scale_factor)  # マップチップ基本サイズ


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
    self.__moving_acc += self.__moving_vec * 6
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

# ゲームループを含むメイン処理
def main():

  # 初期化処理
  pg.init()
  pg.display.set_caption('ぼくのかんがえたさいきょうのげーむ II')
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
  item_img = pg.image.load('./data/img/takarabako.png').convert_alpha()
  # タイル画像の読み込み
  white_tile_img = pg.image.load('./data/img/yougan.png').convert()
  black_tile_img = pg.image.load('./data/img/renga.png').convert()

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

  # マップの描画関数
  def draw_maze(screen, maze):
    for y in range(len(maze)):
      for x in range(len(maze[y])):
        if maze[y][x] == 1:  # 白タイル
          screen.blit(white_tile_img, (x * chip_s, y * chip_s))
        else:  # 黒タイル
          screen.blit(black_tile_img, (x * chip_s, y * chip_s))

  # 黒のタイル取得関数を追加
  def get_black_tiles(maze):
    black_tiles = []
    for y in range(len(maze)):
      for x in range(len(maze[0])):
        if maze[y][x] == 0:
          black_tiles.append(pg.Vector2(x, y))  # タイルの位置を追加
    return black_tiles

  class Item:

    def __init__(self, position):
      self.position = position
      self.collected = False

    def draw(self, screen):
      if not self.collected:
        screen.blit(item_img, (self.position.x *
                    chip_s, self.position.y * chip_s))

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

  # アイテム配置
  def place_items(maze, num_items):
    dead_end_tiles = get_dead_end_tiles(maze)  # 行き止まりタイルを取得
    items = []

    if len(dead_end_tiles) < num_items:
      num_items = len(dead_end_tiles)  # 行き止まりタイルが足りない場合

    for _ in range(num_items):
      position = random.choice(dead_end_tiles)  # ランダムな行き止まりタイルを選択
      items.append(Item(position))
      dead_end_tiles.remove(position)  # 同じ行き止まりに複数配置しないように

    return items

  # アイテム収集チェック関数

  def check_item_collection(reimu, items):
    for item in items:
      if not item.collected and reimu.pos == item.position:  # 位置が一致する場合
        item.collected = True  # アイテムを収集
        return True  # アイテムを収集した
    return False  # 収集しなかった

  tile_size = 32  # タイルのサイズ
  maze_width, maze_height = 10, 10  # 迷路のサイズ
  maze = generate_maze(int(map_s.x), int(map_s.y))  # 迷路を生成
  black_tiles = get_black_tiles(maze)  # 黒のタイル位置を取得

  # アイテムの数
  num_items = 3
  items = place_items(maze, num_items)  # アイテムを配置

  # プレイヤーキャラクターの初期位置
  if black_tiles:
    start_pos = random.choice(black_tiles)  # ランダムに黒のタイルを選択
  else:
    start_pos = (2, 3)  # 黒のタイルがなければデフォルト位置

  reimu = PlayerCharacter(start_pos, './data/img/reimu.png')  # プレイヤーキャラを初期化

  # タイルの状態を確認する関数
  def is_valid_move(maze, pos):
    if (0 <= pos.y < len(maze)) and (0 <= pos.x < len(maze[0])):
      return maze[int(pos.y)][int(pos.x)] == 0  # 0が黒色タイル
    return False

  # ゲームループ
  while not exit_flag:

    # システムイベントの検出
    for event in pg.event.get():
      if event.type == pg.QUIT:  # ウィンドウ[X]の押下
        exit_flag = True
        exit_code = '001'

    # キー状態の取得
    key = pg.key.get_pressed()
    cmd_move = -1
    cmd_move = 0 if key[pg.K_w] else cmd_move
    cmd_move = 1 if key[pg.K_d] else cmd_move
    cmd_move = 2 if key[pg.K_s] else cmd_move
    cmd_move = 3 if key[pg.K_a] else cmd_move

    # 背景描画
    screen.fill(pg.Color('WHITE'))

    # 迷路を描画
    draw_maze(screen, maze)

    # 移動コマンドの処理
    if not reimu.is_moving:
      if cmd_move != -1:
        reimu.turn_to(cmd_move)
        af_pos = reimu.pos + m_vec[cmd_move]  # 移動(仮)した座標

        # 有効な移動なら移動指示
        if is_valid_move(maze, af_pos):
          reimu.move_to(m_vec[cmd_move])

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
      print("アイテムを収集しました！")

  # クリア条件
    # クリアタイムを初期化
    clear_time = 0.0

  # クリア条件
    if all(item.collected for item in items):
      # クリア時に経過時間を計算
      clear_time = (pg.time.get_ticks() - start_time) / 1000  # 秒単位に変換

    # 画面に「クリア」とタイムを表示
      screen.fill(pg.Color('BLACK'))  # 背景を黒くする

    # 大きなフォントで「クリア」を表示
      clear_font = pg.font.Font(None, 72)  # 72pxの大きなフォント
      clear_text = clear_font.render("Clear!", True, pg.Color('WHITE'))
      screen.blit(clear_text, (disp_w / 2 -
                               clear_text.get_width() / 2, disp_h / 2 - 50))

    # タイムを表示
      time_font = pg.font.Font(None, 36)  # 36pxのフォント
      time_text = time_font.render(
          f"time: {clear_time:.2f}sec", True, pg.Color('WHITE'))
      screen.blit(time_text, (disp_w / 2 -
                              time_text.get_width() / 2, disp_h / 2 + 20))

    # 画面更新と一定時間待機
      pg.display.update()
      pg.time.wait(3000)  # 3秒間待機

      print(f"すべてのアイテムを集めました！ゲームクリア！クリアタイム: {clear_time:.2f}秒")  # ターミナルにも表示
      exit_flag = True  # ゲームを終了する

    # フレームカウンタの描画
    frame += 1
    frm_str = f'{frame:05}'
    screen.blit(font.render(frm_str, True, 'BLACK'), (10, 10))
    screen.blit(font.render(f'{reimu.pos}', True, 'BLACK'), (10, 20))

    # 画面の更新と同期
    pg.display.update()
    clock.tick(30)

  # ゲームループ [ここまで]
  pg.quit()
  return exit_code

if __name__ == "__main__":
  code = main()
  print(f'プログラムを「コード{code}」で終了しました。')
