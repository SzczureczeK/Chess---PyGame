from settings import *
import pygame as pg
import numpy as np
import time

# TO DO:
# - Detect a check mate conditions
# - Add the ability to save a game, create a save button at the bottom of the screen
# - Add the ability to load a game
# - Add a starting screen, which will ask whether to start a new or load a game
# - Optimize the moving and beating mechanics of the Rook


class Button(pg.sprite.Sprite):

    def __init__(self, game, x, y, w, h, text, type):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.image = pg.Surface((w, h))
        self.rect = self.image.get_rect()
        self.font = pg.font.SysFont("Arial", 28)
        self.is_selected = False
        self.is_hovered = False
        self.image.fill(BEIGE)
        self.color = BEIGE
        self.type = type
        self.text = text
        self.rect.x = x
        self.rect.y = y
        self.height = h
        self.width = w
        self.x = x
        self.y = y

    def update(self):
        self.rect.x, self.rect.y = self.x, self.y

        if self.is_hovered: self.image.fill(LIGHTGREY)
        elif self.is_selected: self.image.fill(LIGHTGREY)
        else: self.image.fill(self.color)

        self.textSurf = self.font.render(self.text, 1, BLACK)
        W, H = self.textSurf.get_width(), self.textSurf.get_height()
        self.image.blit(self.textSurf, [self.width/2 - W/2, self.height/2 - H/2])


class Tile(pg.sprite.Sprite):
    def __init__(self, game, x, y, color):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.font = pg.font.SysFont("Arial", 64)
        self.rect = self.image.get_rect()
        self.image.fill(color)
        self.show_coordinates = False
        self.is_occupied = False
        self.is_selected = False
        self.is_hovered = False
        self.piece = None
        self.color = color
        self.game = game
        self.x = x
        self.y = y

    def update(self):
        self.rect.x, self.rect.y = self.x * TILESIZE, self.y * TILESIZE

        if self.is_hovered: self.image.fill(LIGHTGREY)
        elif self.is_selected: self.image.fill(LIGHTGREY)
        else: self.image.fill(self.color)

        if self.show_coordinates:
            self.textSurf = self.font.render(f"[{self.x}, {self.y}]", 1, RED)
            W, H = self.textSurf.get_width(), self.textSurf.get_height()
            self.image.blit(self.textSurf, [TILESIZE/2 - W/2, TILESIZE/2 - H/2])


class Piece(pg.sprite.Sprite):
    def __init__(self, game, x, y, color):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.image = pg.Surface((TILESIZE*0.8, TILESIZE*0.8),pg.SRCALPHA)
        self.font = pg.font.SysFont("Arial", 64)
        self.rect = self.image.get_rect()
        self.color = color
        self.game = game
        self.x = x
        self.y = y

    def update(self):
        self.rect.x, self.rect.y = (self.x * TILESIZE), (self.y * TILESIZE)

    def blit_piece_image(self, graphic):
        graphic_rect = graphic.get_rect()
        blit_x = (TILESIZE - graphic_rect.width) // 2
        blit_y = (TILESIZE - graphic_rect.height) // 2

        self.image.blit(graphic, (blit_x, blit_y))

    def get_piece_image(self, piece):
        # Load the image and convert it to a format with alpha channel
        piece_img_path = f"images/{self.color}_{piece}.png"
        original_piece_img = pg.image.load(piece_img_path).convert_alpha()
        # Determine the scale factor to make the piece fit within the tile,
        # leaving some padding for visual appeal. E.g., 80% of TILESIZE.
        scale_factor = 0.8
        scaled_width, scaled_height = int(TILESIZE * scale_factor), int(TILESIZE * scale_factor)
        # Scale the image
        scaled_piece_img = pg.transform.scale(original_piece_img, (scaled_width, scaled_height))

        return scaled_piece_img


class Knight(Piece):

    def __init__(self, game, x, y, color):
        super().__init__(game, x, y, color)
        # Blit the scaled piece graphic onto the Knight's main image surface.
        # We blit it centered, so calculate the top-left corner.
        self.piece_graphic = self.get_piece_image('knight')
        self.blit_piece_image(self.piece_graphic)

    def get_valid_moves(self, piece, position, board, player_move):

        valid_moves = []
        valid_beating_moves = []

        move_matrix = [[-2,-1], [-1,-2], [1,-2], [2, -1],
                       [2,1], [1,2], [-1,2], [-2,1]]

        for matrix in move_matrix:
            # Handles out of index errors. Making sure the moves are not outside the board
            if any(n < 0 or n > 7 for n in [matrix[0]+piece[0], matrix[1]+piece[1]]):
                continue
            # Get the tile object at the predicted move coordinates
            tile = board[matrix[0]+piece[0]][matrix[1]+piece[1]]
            # If the tile contains a piece that is not the players colour, add the coordinates
            # of that tile to valid_beating_moves
            if tile.is_occupied and tile.piece.color != player_move:
                valid_beating_moves.append(np.add(piece, [matrix[0], matrix[1]]).tolist())
            # If the tile is not occupied, add the coordinates of the tile to valid_moves
            if not tile.is_occupied:
                valid_moves.append(np.add(piece, [matrix[0], matrix[1]]).tolist())

        return valid_moves, valid_beating_moves


class Pawn(Piece):

    def __init__(self, game, x, y, color):
        super().__init__(game, x, y, color)
        self.color = color
        self.is_first_move = True
        self.piece_graphic = self.get_piece_image('pawn')
        self.blit_piece_image(self.piece_graphic)

    def get_valid_moves(self, piece, position, board, player_move):

        valid_moves = []
        valid_beating_moves = []

        # The beating matrix varies depending on the colour of the piece
        # A white piece, on the right hand side of the board, can only
        # take another piece diagonally to the left, opposite is true
        # for black pieces.

        if self.color == "black":
            beating_matrix = [[1,-1],[1,1]]
            # On first move, a pawn can move one or two
            # tiles in their respective direction. On any
            # subsequent move, it can only move one tile at
            # a time
            if self.is_first_move:
                move_matrix = [[1,0], [2,0]]
            else: move_matrix = [[1,0]]

        if self.color == "white":
            beating_matrix = [[-1,1],[-1,-1]]
            if self.is_first_move:
                move_matrix = [[-1,0],[-2,0]]
            else: move_matrix = [[-1,0]]

        # Since the pawn can only move one tile in its respective direction, (left or right)
        # but can take a piece diagonally, this requires a seperate moving and beating matrix lists
        for matrix in move_matrix:
            if any(n < 0 or n > 7 for n in [matrix[0]+piece[0], matrix[1]+piece[1]]):
                valid_moves = []
            elif not board[matrix[0]+piece[0]][matrix[1]+piece[1]].piece:
                valid_moves.append(np.add(piece, [matrix[0], matrix[1]]).tolist())

        for matrix in beating_matrix:
            if any(n < 0 or n > 7 for n in [matrix[0]+piece[0], matrix[1]+piece[1]]):
                continue
            elif board[matrix[0]+piece[0]][matrix[1]+piece[1]].piece:
                if board[matrix[0]+piece[0]][matrix[1]+piece[1]].piece.color != player_move:
                    valid_beating_moves.append(np.add(piece, [matrix[0], matrix[1]]).tolist())

        return valid_moves, valid_beating_moves


class Rook(Piece):

    def __init__(self, game, x, y, color):
        super().__init__(game, x, y, color)
        self.color = color
        self.piece_graphic = self.get_piece_image('rook')
        self.blit_piece_image(self.piece_graphic)

    @staticmethod
    def get_valid_moves(piece, position, board, player_move):

        valid_moves = []
        valid_beating_moves = []

        rows = []
        cols = []

        # Generate the row and column at point of intersection
        # of the Rooks position
        for i in range(8):
            rows.append([i,piece[1]])
            cols.append([piece[0], i])

        # Iterate through tiles to the right of the piece position
        # If the tile is empty, add it to valid moves
        # If a piece is found on the tile and if it is the
        # opponents piece, add it to valid_beating_moves lists
        # and stop.

        for pos in rows[piece[0]+1:]:
            tile = board[pos[0]][pos[1]]
            if tile.piece:
                if tile.piece.color != player_move:
                    valid_beating_moves.append(pos)
                break
            valid_moves.append(pos)

        # Iterate through tiles to the left of the piece position
        # If the tile is empty, add it to valid moves
        # If a piece is found on the tile and if it is the
        # opponents piece, add it to valid_beating_moves lists
        # and stop.
        for pos in reversed(rows[:piece[0]]):
            tile = board[pos[0]][pos[1]]
            if tile.piece:
                if tile.piece.color != player_move:
                    valid_beating_moves.append(pos)
                break
            valid_moves.append(pos)

        # Iterate through tiles below the piece position
        # If the tile is empty, add it to valid moves
        # If a piece is found on the tile and if it is the
        # opponents piece, add it to valid_beating_moves lists
        # and stop.
        for pos in cols[piece[1]+1:]:
            tile = board[pos[0]][pos[1]]
            if tile.piece:
                if tile.piece.color != player_move:
                    valid_beating_moves.append(pos)
                break
            valid_moves.append(pos)

        # Iterate through tiles above the piece position
        # If the tile is empty, add it to valid moves.
        # If a piece is found on the tile and if it is the
        # opponents piece, add it to valid_beating_moves lists
        # and stop.
        for pos in reversed(cols[:piece[1]]):
            tile = board[pos[0]][pos[1]]
            if tile.piece:
                if tile.piece.color != player_move:
                    valid_beating_moves.append(pos)
                break
            valid_moves.append(pos)

        return valid_moves, valid_beating_moves


class Bishop(Piece):

    def __init__(self, game, x, y, color):
        super().__init__(game, x, y, color)
        self.color = color
        self.piece_graphic = self.get_piece_image('bishop')
        self.blit_piece_image(self.piece_graphic)

    @staticmethod
    def get_valid_moves(piece, position, board, player_move):

        valid_moves = []
        valid_beating_moves = []

        # Lists containing diagonal lines that intersect the pieces current position
        d1 = []
        d2 = []

        # Get all the tiles diagonally from the piece position
        for x in range(8):
            y = x + (piece[1]-piece[0])
            y2 = (x*-1) +(piece[1]+piece[0])
            if (0 <= y < 8):
                d1.append([x, y])
            if (0 <= y2 < 8):
                d2.append([x, y2])

        start_index = d1.index(piece)
        for pos in d1[start_index+1:]:
            tile = board[pos[0]][pos[1]]
            if tile.piece:
                if tile.piece.color != player_move:
                    valid_beating_moves.append(pos)
                break
            valid_moves.append(pos)

        for pos in reversed(d1[:start_index]):
            tile = board[pos[0]][pos[1]]
            if tile.piece:
                if tile.piece.color != player_move:
                    valid_beating_moves.append(pos)
                break
            valid_moves.append(pos)

        start_index = d2.index(piece)
        for pos in d2[start_index+1:]:
            tile = board[pos[0]][pos[1]]
            if tile.piece:
                if tile.piece.color != player_move:
                    valid_beating_moves.append(pos)
                break
            valid_moves.append(pos)

        for pos in reversed(d2[:start_index]):
            tile = board[pos[0]][pos[1]]
            if tile.piece:
                if tile.piece.color != player_move:
                    valid_beating_moves.append(pos)
                break
            valid_moves.append(pos)

        return valid_moves, valid_beating_moves


class King(Piece):

    def __init__(self, game, x, y, color):
        super().__init__(game, x, y, color)
        self.color = color
        self.piece_graphic = self.get_piece_image('king')
        self.blit_piece_image(self.piece_graphic)

    def get_valid_moves(self, piece, position, board, player_move):

        valid_moves = []
        valid_beating_moves = []

        move_matrix = [[1,1], [1,-1], [-1,1], [-1,-1],
                       [0,1], [0,-1], [1,0], [-1,0]]

        for matrix in move_matrix:
            if any(n < 0 or n > 7 for n in [matrix[0]+piece[0], matrix[1]+piece[1]]):
                continue
            tile = board[matrix[0]+piece[0]][matrix[1]+piece[1]]
            if not tile.is_occupied:
                valid_moves.append(np.add(piece, [matrix[0], matrix[1]]).tolist())
            elif tile.piece.color != player_move:
                valid_beating_moves.append(np.add(piece, [matrix[0], matrix[1]]).tolist())

        return valid_moves, valid_beating_moves


class Queen(Piece):

    def __init__(self, game, x, y, color):
        super().__init__(game, x, y, color)
        self.color = color
        self.piece_graphic = self.get_piece_image('queen')
        self.blit_piece_image(self.piece_graphic)

    def get_valid_moves(self, piece, position, board, player_move):

        # Since the queen combines the movement mechanics of both Rook and Bishop
        # The get_valid_moves methods of the two pieces can be repurposed and combined
        # to get the valid moves for the Queen piece.
        return [a + b for a, b in zip(Rook.get_valid_moves(piece, position, board, player_move),
                                      Bishop.get_valid_moves(piece, position, board, player_move))]


class Chess:
    def __init__(self):
        # initialize game window, etc
        pg.init()
        self.clock = pg.time.Clock()
        pg.display.set_caption(TITLE)
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.number_of_black_moves = 0
        self.number_of_white_moves = 0
        self.tile_to_move_to = None
        self.clicked_piece = None
        self.player_move = "black"
        self.captured_whites = []
        self.captured_blacks = []
        self.running = True
        self.check = None
        self.white_king = None
        self.black_king = None

    def new(self):
        # start a new game
        self.board = [[],[],[],[],[],[],[],[]]
        self.all_sprites = pg.sprite.Group()
        self.pieces = pg.sprite.Group()
        self.tiles = pg.sprite.Group()
        self.buttons = pg.sprite.Group()
        self.start_time = pg.time.get_ticks()

        self.coordinates_button = Button(self, 5, HEIGHT-65, 200, 60, "Show Coordinates", "coordinates")
        self.buttons.add(self.coordinates_button)
        self.save_button = Button(self, 210, HEIGHT-65, 200, 60, "Save Game", "save")
        self.build_board()

        # Order of pieces in columns 0 and 7
        pieces = [Rook, Knight, Bishop, King, Queen, Bishop, Knight, Rook]

        # Places pieces on the board
        for y, piece in enumerate(pieces):
            self.place_piece(Pawn, 1, y, "black")
            self.place_piece(Pawn, 6, y, "white")
            self.place_piece(piece, 0, y, "black")
            self.place_piece(piece, 7, y, "white")

    def place_piece(self, piece, x, y, color):
        self.piece = piece(self, x, y, color)
        self.pieces.add(self.piece)
        self.board[x][y].piece = self.piece
        if piece is King and color == "black":
            self.black_king = self.piece
        if piece is King and color == "white":
            self.white_king = self.piece

    def build_board(self):
        # Colours of the board
        colors = [None, BEIGE, BROWN]
        step = 1
        for x in range(8):
            step *= -1
            for y in range(8):
                if x % 2 == 0:
                    if y in (0,2):
                        self.tile = Tile(self, y, x, colors[step])
                        self.board[y].append(self.tile)
                    elif y == 6:
                        self.tile = Tile(self, y, x, colors[step])
                        self.board[y].append(self.tile)
                    else:
                        self.tile = Tile(self, y, x, colors[step])
                        self.board[y].append(self.tile)
                else:
                    if y == 1:
                        self.tile = Tile(self, y, x, colors[step])
                        self.board[y].append(self.tile)
                    elif y in (5,7):
                        self.tile = Tile(self, y, x, colors[step])
                        self.board[y].append(self.tile)
                    else:
                        self.tile = Tile(self, y, x, colors[step])
                        self.board[y].append(self.tile)
                self.tiles.add(self.tile)
                step *= -1

    def move_pieces(self, piece, tile):
        # Move the pieces on the self.board array

        piece_position = [piece.x, piece.y]
        tile_position = [tile.x, tile.y]

        piece.x, piece.y = tile_position[0], tile_position[1]

        self.board[tile_position[0]][tile_position[1]].piece = piece
        self.board[piece_position[0]][piece_position[1]].piece = None

        # Deselect both tiles and update their piece, is_selected and is_occupied states
        # To reflect the updated board.
        self.tile_to_move_to.is_selected = False
        self.tile_to_move_to.is_occupied = True
        self.clicked_piece.is_selected = False
        self.clicked_piece.is_occupied = False

        # Reset the selected tiles
        self.tile_to_move_to = None
        self.clicked_piece = None

        if self.player_move == "black":
            self.number_of_black_moves += 1
            self.player_move = "white"
        else:
            self.number_of_white_moves += 1
            self.player_move = "black"

    def is_check(self):
        # Check whether black king is under direct attack - check
        # Check whether white king is under direct attack - check
        # If any opponents pieces have the kings position in their
        # valid_beating_moves array, return true.

        black_king_pos = [self.black_king.x, self.black_king.y]
        white_king_pos = [self.white_king.x, self.white_king.y]

        for piece in self.pieces:
            piece_pos = [piece.x, piece.y]
            # Use the piece's own color to calculate its valid beats
            _, valid_beats = piece.get_valid_moves(piece_pos, None, self.board, piece.color)

            if piece.color == "white" and black_king_pos in valid_beats: return "black"
            if piece.color == "black" and white_king_pos in valid_beats: return "white"

        return None

    def run(self):
        # Game Loop
        self.playing = True
        currently_hovered_tile = None
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()

            self.mouse_pos = pg.mouse.get_pos()

            tile = None

            for sprite in self.all_sprites.sprites():
                # Check if the mouse position is inside the sprite's rectangle
                if sprite.rect.collidepoint(self.mouse_pos):
                    tile = sprite
                    break

            # Determine which tile to apply the hover over effect.
            if tile:
                if tile != currently_hovered_tile:
                    if currently_hovered_tile:
                        currently_hovered_tile.is_hovered = False
                    tile.is_hovered = True
                    currently_hovered_tile = tile
            else:
                if currently_hovered_tile:
                    currently_hovered_tile.is_hovered = False
                    currently_hovered_tile = None

            # Perform selected piece movement
            if self.tile_to_move_to:
                piece = self.clicked_piece.piece
                piece_position = [piece.x, piece.y]
                move_position = [self.tile_to_move_to.x, self.tile_to_move_to.y]

                valid_moves, valid_beats = piece.get_valid_moves(piece_position, move_position,
                                                                 self.board, self.player_move)
                # Perform capturing move
                if move_position in valid_beats:
                    captured_piece = self.board[move_position[0]][move_position[1]].piece
                    captured_piece.kill()
                    if self.player_move == "black":
                        self.captured_whites.append(captured_piece)
                    else:
                        self.captured_blacks.append(captured_piece)
                    self.move_pieces(piece, self.tile_to_move_to)
                    self.check = self.is_check()
                # Perform regular movev
                elif move_position in valid_moves:
                    if type(piece) is Pawn:
                        piece.is_first_move = False
                    self.move_pieces(piece, self.tile_to_move_to)
                    self.check = self.is_check()
                # Deselect all selected pieces and tiles
                else:
                    self.tile_to_move_to.is_selected = False
                    self.tile_to_move_to = None
                    self.clicked_piece.is_selected = False
                    self.clicked_piece = None

    def draw_text(self, x, y, text, text_size, color):
        font = pg.font.SysFont("Arial", text_size)
        self.textSurf = font.render(text, 1, color)
        W, H = self.textSurf.get_width(), self.textSurf.get_height()
        self.screen.blit(self.textSurf, [x - W/2, y - H/2])

    def update(self):
        # Game Loop - Update
        self.all_sprites.update()

        milli_passed = pg.time.get_ticks() - self.start_time
        seconds = (milli_passed // 1000) % 60
        minutes = (milli_passed // 60000) % 60
        self.time_elapsed = f"{minutes:02}:{seconds:02}"

    def events(self):
        # Game Loop - events
        for event in pg.event.get():
            # check for closing window
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            if event.type == pg.MOUSEBUTTONUP:
                pos = pg.mouse.get_pos()

                # First tile to be selected must be the current players piece
                if not self.tile_to_move_to:
                    clicked_sprites = [s for s in self.all_sprites if s.rect.collidepoint(pos)]
                    sprite = clicked_sprites[0]
                    if type(sprite) is Button:
                        if sprite.is_selected:
                            sprite.is_selected = False
                        else:
                            sprite.is_selected = True
                        if sprite.type == "save":
                            pass
                        if sprite.type == "coordinates":
                            for tile in self.tiles:
                                tile.show_coordinates = sprite.is_selected
                    elif clicked_sprites[0].piece and not self.clicked_piece:
                        if clicked_sprites[0].piece.color == self.player_move:
                            self.clicked_piece = clicked_sprites[0]
                            self.clicked_piece.is_selected = True

                    # Second tile to be selected must be an empty tile
                    if self.clicked_piece:
                        clicked_tile = [s for s in self.tiles if s.rect.collidepoint(pos)]
                        if clicked_tile[0] != self.clicked_piece:
                            self.tile_to_move_to = clicked_tile[0]
                            self.tile_to_move_to.is_selected = True

    def draw(self):
        # Game Loop draw
        self.screen.fill(DARKGREY)
        self.all_sprites.draw(self.screen)
        self.draw_text(160, 1050, f"caputred whites: {len(self.captured_whites)}", 32, BEIGE)
        self.draw_text(WIDTH-160, 1050, f"caputred blacks: {len(self.captured_blacks)}", 32, BEIGE)
        self.draw_text(WIDTH/2, 1080, f"{self.player_move}'s Turn", 54, BEIGE)
        if self.check in ("black", "white"):
            self.draw_text(WIDTH/2, 1130, f"{self.check} is in CHECK", 56, RED)
        self.draw_text(WIDTH/2, 1040, f"Time: {self.time_elapsed}", 24, BEIGE)

        # Draw minature captured white pieces on the bottom of the screen.
        # Scale the image
        scale_factor = 0.3
        scaled_width, scaled_height = int(TILESIZE * scale_factor), int(TILESIZE * scale_factor)
        i, x, y = 0, 0, 1070
        for captured_piece in self.captured_whites:
            if i > 7:
                i, x, y = 0, 0, y+40
            scaled_piece_img = pg.transform.scale(captured_piece.piece_graphic, (scaled_width, scaled_height))
            self.screen.blit(scaled_piece_img, (x+(scaled_width*i), y))
            i+= 1

        # Draw minature captured black pieces on the bottom of the screen.
        i, x, y = 0, WIDTH-(8*scaled_width), 1070
        for captured_piece in self.captured_blacks:
            if i > 7:
                i, x, y = 0, WIDTH-(8*scaled_width), y+40
            scaled_piece_img = pg.transform.scale(captured_piece.piece_graphic, (scaled_width, scaled_height))
            self.screen.blit(scaled_piece_img, (x+(scaled_width*i), y))
            i+= 1

        # *after* drawing everything, flip the display
        pg.display.flip()

g = Chess()
while g.running:
    g.new()
    g.run()

pg.quit()
