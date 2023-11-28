import numpy as np
import random 
import pygame as p
from pygame.constants import MOUSEBUTTONDOWN
import sys
import copy
import time
import json
import os.path

p.init()
width = 1200
height = 800 
FPS =60
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)
PURPLE = (255,0,255)
BROWN = (139,131,120)
TAN = (250,235,215)

font = p.font.SysFont(None, 36)
clock = p.time.Clock()
screen = p.display.set_mode((width, height))
p.display.set_caption("Backgammon")
screen.fill(TAN)

class Board:
    # Initial board fed into players
    # 1s represent red, 2s represent black
    def __init__(self):
        self.board = [[],[1,1],[], [],[],[],[2,2,2,2,2], [],[2,2,2],[],[],[],[1,1,1,1,1],\
            [2,2,2,2,2],[],[],[],[1,1,1],[], [1,1,1,1,1], [],[],[],[],[2,2],[]]
        
class Player:
    # Player class, comp/human built into one
    def __init__(self, color, board=None):
        self.win=False
        if board == None:
            self.board = Board().board
        else:
            self.board = board
        self.color = color
        self.Red_Pieces = {}
        self.Black_Pieces = {}
        self.populate_Dict(self.board)
        self.take_off=False    
        self.temp_boards = []
        self.final_boards = []
        self.replica_board = copy.deepcopy(self.board)    
        self.Red_Copy = copy.deepcopy(self.Red_Pieces)
        self.Black_Copy = copy.deepcopy(self.Black_Pieces)
        self.doubles = False        
        self.on_rail = False
        self.can_remove = False
        self.furthest_piece = None
        self.dice = []
        self.count = 0        
        self.Red_Piece_Coords = {k: [] for k in range(26)}
        self.Black_Piece_Coords = {k: [] for k in range(26)}
        self.stored_boards = []
        self.stored_boards.append(self.board)
        self.moves = []
        self.buffer = 50
        self.draw_board()
        self.draw_pieces()                
    
    def win_check(self):
        if self.color=='red':
            piece = 1
        else:
            piece = 2
        for x in self.board:
            if piece in x:
                return False 
        self.win=True
        return True

    def generate_random_board(self):
        # Random board generator for reinforcement learning testing
        board = [[] for _ in range(26)]
        # 15 pieces per player
        for _ in range(15):
            can_insert = False
            while can_insert==False:
                red = random.randint(1,24)
                black = random.randint(1,24)
                if red !=black:
                    if 2 not in board[red] and 1 not in board[black]:
                        board[red].append(1)
                        board[black].append(2)
                        can_insert=True 
        return board 

    def Can_remove(self):
        # Determines if pieces can be moved off of board
        self.can_remove=False
        self.furthest_piece=None  
        if self.color=='red':
            s = sorted([x for x in self.Red_Pieces])            
            if len(s)>0:
                if min(s)>=19:
                    self.can_remove=True                
                    self.furthest_piece = min(s)                   
        if self.color=='black':
            s = sorted([x for x in self.Black_Pieces])          
            if len(s)>0:
                if max(s)<=6:
                    self.can_remove=True                
                    self.furthest_piece = max(s)                     
        return     

    def redraw(self):
        # Redraws board, for movement updates based on update board and piece positions
        screen.fill(TAN)
        self.draw_board()
        self.populate_Dict(self.board)
        self.draw_pieces()

    def draw_board(self):
        # Draws the board
        start_x, start_y = self.buffer,self.buffer 
        end_x = width-self.buffer
        end_y = height-self.buffer        
        p.draw.line(screen, BLACK, (start_x, start_y), (end_x, start_y))
        p.draw.line(screen, BLACK, (start_x, end_y), (end_x, end_y))
        p.draw.line(screen, BLACK, (start_x, start_y), (start_x, end_y))
        p.draw.line(screen, BLACK, (end_x, start_y), (end_x, end_y))
        x_gap = (end_x-start_x)/15
        for i in range(15):
            p.draw.line(screen, BLACK, (start_x+i*x_gap, start_y), (start_x+i*x_gap, end_y))
        p.draw.rect(screen,BROWN,(start_x,start_y,x_gap,end_y-start_y))
        p.draw.rect(screen,BROWN,(start_x+x_gap*7,start_y,x_gap,end_y-start_y))
        p.draw.rect(screen,BROWN,(start_x+x_gap*14,start_y,x_gap+1,end_y-start_y))                

    def draw_pieces(self):
        # Draws pieces, maps coordinates to color dictionaries for user interactions
        start_x, start_y = self.buffer,self.buffer 
        end_x = width-self.buffer
        end_y = height-self.buffer
        x_gap = (end_x-start_x)/15   
        c_size = (x_gap/2)-8        
        top_half = self.board[0:13]
        bottom_half = self.board[13:]
        bottom_half = bottom_half[::-1]
        count = 0
        for i in range(len(top_half)):
            val = top_half[i]                                   
            if len(val)>0:
                if i >6:
                    i = i+1
                x_coord = start_x + x_gap*i + .5*x_gap
                current_y = start_y+ c_size
                inner_count = 0
                for _ in range(len(val)):
                    y_coord = current_y
                    if 1 in val:
                        # append the left, right, top, bottom of piece
                        self.Red_Piece_Coords[count].append((x_coord-c_size, x_coord+c_size,y_coord-c_size,y_coord+c_size))
                        color = RED
                    else:
                        self.Black_Piece_Coords[count].append((x_coord-c_size, x_coord+c_size,y_coord-c_size,y_coord+c_size))
                        color = BLACK
                    p.draw.circle(screen, color, (x_coord,y_coord), c_size)
                    if inner_count <5:
                        current_y+=c_size*2 -2
                    if inner_count>4:
                        img = font.render(f'{inner_count+1}', True, WHITE)
                        screen.blit(img, (x_coord-c_size/2,y_coord))    
                        overlap = font.render(None, 0, TAN)
                        screen.blit(overlap, (x_coord-c_size/2,y_coord))
                    inner_count+=1
            count+=1        
        count = 25
        for i in range(len(bottom_half)):
            val = bottom_half[i]
            if len(val)>0:
                if i >6:
                    i = i+1
                x_coord = start_x + x_gap*i + .5*x_gap
                current_y = end_y - c_size
                inner_count = 0
                for _ in range(len(val)):
                    y_coord = current_y
                    if 1 in val:
                        self.Red_Piece_Coords[count].append((x_coord-c_size, x_coord+c_size,y_coord-c_size,y_coord+c_size))
                        color = RED
                    else:
                        self.Black_Piece_Coords[count].append((x_coord-c_size, x_coord+c_size,y_coord-c_size,y_coord+c_size))
                        color = BLACK

                    p.draw.circle(screen, color, (x_coord,y_coord), c_size)
                    if inner_count <5:
                        current_y-=c_size*2 -2
                    if inner_count>4:
                        img = font.render(f'{inner_count+1}', True, WHITE)
                        screen.blit(img, (x_coord-c_size/2,y_coord))    
                        overlap = font.render(None, 0, TAN)
                        screen.blit(overlap, (x_coord-c_size/2,y_coord))
                    inner_count+=1
            count-=1

    def rail_check(self):
        # Determines if player has a piece on the rail
        # To be used to force players to take off rail before moving elsewhere
        self.on_rail=False
        if self.color == 'red':            
            if 0 in self.Red_Pieces:
                self.on_rail = True
                return self.Red_Pieces[0]
            else:
                return 0
        if self.color =='black':
            if 25 in self.Black_Pieces:
                self.on_rail = True
                return self.Black_Pieces[25]
            else:
                return 0
            
    def roll(self):
        # For doubles, 2 sets of the same value will be used
        # If not doubles, 2 combinations of same roll will be used
        die_1 = random.randint(1,6)
        die_2 = random.randint(1,6)
        if die_1 == die_2:
            self.doubles = True
            for _ in range(2):                
                self.dice.append([die_1,die_2])
        else:
            self.doubles = False
            self.dice = [[die_1,die_2],[die_2,die_1]]            
        return

    def clear_dict(self):
        # Clears player's piece dictionary
        if self.color =='red':
            self.Red_Pieces = {}
        elif self.color=='black':
            self.Black_Pieces = {}

    def populate_Dict(self, board):
        # Populates the piece dictionary for both red and black
        for slot,val in enumerate(board):
            if 1 in val:
                self.Red_Pieces[slot]=len(val)
            elif 2 in val:
                self.Black_Pieces[slot]=len(val)                

    def blocked(self,spot):
        # checks if a spot is blocked for a given color
        if self.color == 'red':
            opp_pieces = self.Black_Pieces
        else:
            opp_pieces = self.Red_Pieces
        if spot in opp_pieces and opp_pieces[spot]>1:
            return True
        return False          
    
    def spot_open(self, spot):
        # Checks if a spot is open        
        if self.color =='red':
            if self.blocked(spot)==False and spot<25:
                return True
        if self.color =='black':
            if self.blocked(spot)==False and spot>0:                         
                return True
    
    def spot_open_furthest(self,spot):
        if self.color=='red':
            if self.blocked(spot)==False:                
                return True                 
        if self.color=='black':
            if self.blocked(spot)==False:                
                return True                       
    def calc_moves(self,start,die):
        # Calculates moves from a starting position for a given die
        moves = []
        if self.color =='red':
            end = start + die
            if self.furthest_piece!=None and self.furthest_piece+die>=25:                                   
                self.clear_dict()
                self.populate_Dict(self.board)
                if self.Red_Pieces!= {}:
                    self.furthest_piece = min([x for x in self.Red_Pieces])                    
                    self.board[self.furthest_piece].remove(1)
                    self.take_off=True
                    self.off_board = self.board
                self.redraw()
                self.clear_dict()
                self.populate_Dict(self.board)                                  
                return            
        elif self.color =='black':
            end = start-die
            if self.furthest_piece!=None and self.furthest_piece-die<=0:                    
                self.clear_dict()
                self.populate_Dict(self.board)
                if self.Black_Pieces!={}:
                    self.furthest_piece = max([x for x in self.Black_Pieces])                    
                    self.board[self.furthest_piece].remove(2)
                    self.take_off=True
                    self.off_board = self.board
                self.redraw()
                self.clear_dict()
                self.populate_Dict(self.board)                 
                return        
        if self.spot_open(end)==True:                
            moves.append(end)        
        return moves

    def move(self,board,start,end):
        # Moves a piece for a given board from start to end position
        if self.spot_open(end)==True:            
            p = board[start].pop()
            if board[start]==[]:
                if self.color=='red':
                    del self.Red_Pieces[start]
                elif self.color=='black':
                    del self.Black_Pieces[start]    
            if self.color=='red':
                if 2 in board[end]:
                    board[0].append(p)                                      
                else:
                    board[end].append(p)
            if self.color=='black':
                if 1 in board[end]:                                       
                    board[25].append(p)                    
                else:
                    board[end].append(p)            
            return board            
    
    def find_Board_states(self,board,die):
        # Finds all board states using a starting board state and die
        self.clear_dict()
        self.populate_Dict(board)
        if self.color =='red':
            Pieces = sorted([x for x in self.Red_Pieces.keys()])
        else:
            Pieces = sorted([x for x in self.Black_Pieces.keys()])        
        Possible_Boards = []        
        for piece in Pieces:
            Moves = self.calc_moves(piece,die)
            if self.win==True or self.take_off==True:
                break            
            if Moves!=[]:
                temp_board = copy.deepcopy(board)   
                self.move(temp_board,piece,Moves[0])
                Possible_Boards.append(temp_board)        
        return Possible_Boards

    def Non_rail_non_doubles_states(self):
        # Creates board states for non double rolls using non rail starting board states
        die_1 = self.dice[0][0]
        die_2 = self.dice[0][1]        
        Original = copy.deepcopy(self.board)
        die_1_boards = self.find_Board_states(self.board,die_1)
        die_2_boards = self.find_Board_states(self.board, die_2)
        States = []
        for board in die_1_boards:    
            second_boards = self.find_Board_states(board, die_2)
            for x in second_boards:
                States.append(x)        
        self.clear_dict()
        self.populate_Dict(Original)
        for board_2 in die_2_boards:    
            second_boards = self.find_Board_states(board_2, die_1)
            for x in second_boards:
                if x not in States:
                    States.append(x)                    
        self.stored_boards=States
        return

    def Non_rail_doubles_states(self,die=None):
        #Recurive function to find all board states for doubles or other cases        
        if self.count ==4:
            return       
        if die==None:
            die = self.dice[0][0]
        Boards = []        
        for board in self.stored_boards:
            self.clear_dict()
            next_boards = self.find_Board_states(board, die)
            for x in next_boards:
                if x not in Boards:
                    Boards.append(x)
        self.stored_boards = Boards
        self.count+=1
        self.Non_rail_doubles_states()
    
    def Rail_Non_Doubles(self):
        #Moves a non double roll with piece(s) starting on rail 
        if self.color =='red':
            Start = 0
            Count = self.Red_Pieces[0]
        elif self.color=='black':
            Start = 25
            Count = self.Black_Pieces[25]
        if Count>=2:
            for die in self.dice[0]:
                moves = self.calc_moves(Start,die)
                if moves!=[]:
                   self.move(self.board,Start,moves[0])
            return        
        
        Temporary_Stored_Boards = []        
        if Count ==1:
            for die in self.dice[0]:                
                for x in self.dice[0]:
                    if x!=die:
                        other = x  
                moves = self.calc_moves(Start,die)
                if moves!=[]:
                   self.move(self.board,Start,moves[0])
                   self.stored_boards.clear()
                   self.stored_boards.append(self.board)
                   self.count = 3
                   self.Non_rail_doubles_states(die=other)                   
                   for board in self.stored_boards:
                    if board not in Temporary_Stored_Boards:
                        Temporary_Stored_Boards.append(board)
                self.stored_boards.clear()
                self.board = self.replica_board
                self.populate_Dict(self.board)                           
            self.stored_boards = Temporary_Stored_Boards
            return

    def Rail_Doubles(self):
        # Finds board states when doubles are rolled with pieces on rail
        Die = self.dice[0][0]
        if self.color =='red':
            Start = 0
            End = Start+Die 
            Count = self.Red_Pieces[0]
        elif self.color=='black':
            Start = 25
            End = Start-Die
            Count = self.Black_Pieces[25]
        if Count >=4:
            if self.calc_moves(Start,Die)!=[]:
                for _ in range(4):
                    self.move(self.board,Start,End)
                return             
        elif Count <4:
            if self.calc_moves(Start,Die)!=[]:
                for _ in range(Count):
                    self.move(self.board,Start,End)
                    self.count+=1
                self.stored_boards.clear()                    
                self.stored_boards.append(self.board)
                self.Non_rail_doubles_states()
    
    def Random_Move(self,reinforced=False,File=None,Func=None):
        # Random move based on board state from computer        
        self.roll()
        self.rail_check()
        self.Can_remove()
        if self.on_rail==False:
            if self.doubles==False:
                self.Non_rail_non_doubles_states()                
            else:
                self.Non_rail_doubles_states()                
        elif self.on_rail==True:
            if self.doubles==False:
                self.Rail_Non_Doubles()
            else:
                self.Rail_Doubles()        
        if self.take_off==True:
            self.board = self.off_board
            if self.win_check()==True:
                self.board = Board().board
                self.redraw()
                return                    
        elif self.stored_boards == []:            
            self.board = self.replica_board
            self.redraw()
            return 
        elif self.take_off==False and self.stored_boards!=[]:
            if reinforced==False:
                self.board = self.stored_boards[random.randint(0,len(self.stored_boards)-1)] 
            else:
                self.board =  self.reinforced_test(File,Func, self.stored_boards)                   
        self.redraw()                
        return
        
    def distance_to_piece(self,p_1,p_2):
        # Finds absolute distance from p_1 to p_2        
        return abs(p_1-p_2)     

    def record_eval(self, File,L1, L2,increment=1,decrement=1,lr=.2):
    # Records evaluation for given json file based on list of board representations
    # check if file exists in directory
        if os.path.isfile(File)==False:
            with open(File, "w") as f:
                json.dump({}, f)       
        with open(File) as file:    
            Eval = json.load(file)                    
        for val in L1:
            if val not in Eval:
                Eval[val]=increment
            else:
                Eval[val]+=lr*increment
        for val2 in L2:
            if val2 not in Eval:
                Eval[val2]=-1*decrement
            else:
                Eval[val2]-=lr*decrement
        with open(File, 'w') as fp:
            json.dump(Eval, fp)
        return  
            
    def reinforced_test(self, File, func, boards,thresh=0):
        # reinforced learning using board evaluation function
        # This function is built into player's random move function as alternative
        with open(File) as file:    
            Stored_Info = json.load(file)
        Keys = [x for x in Stored_Info]        
        # Altering this val , is the selection criteria for choosing moves,
        # Setting it at 0 forces choice to be positive, or random
        
        Final_Board = None
        for board in boards:
            output = func(board)            
            if output in Keys:
                if Stored_Info[output]>thresh:
                    Final_Board=board 
                    thresh = Stored_Info[output]        
        if Final_Board==None:            
            return boards[random.randint(0,len(boards)-1)]       
        else:            
            return Final_Board
            
    def pip_differential(self):
        count = 0
        opp_count = 0
        if self.color=='red':
            for pos,Count in self.Red_Pieces.items():
                count += (25-pos)*Count
            for pos,Count in self.Black_Pieces.items():
                opp_count += pos*Count
        elif self.color=='black':
            for pos,Count in self.Black_Pieces.items():
                count +=pos*Count
            for pos,Count in self.Red_Pieces.items():
                opp_count += (25-pos)*Count        
        diff = opp_count-count
        pip_dict = {-100:-3, -60:-2,-30:-1,30:1, 60:2, 100:3}
        pips = sorted([int(x) for x in pip_dict.keys()])
        idx = 0
        for x in pips:
            if diff >x:                
                idx +=1
            else:
                break
        return pip_dict[pips[idx-1]]
    def Eval_Board_New(self,board):
        if self.can_remove == False:
            self.clear_dict()
            self.populate_Dict(board)
            blocks = 0
            singles = 0
            if self.color == 'red':
                pieces = copy.deepcopy(self.Red_Pieces)                                          
            else:
                pieces = copy.deepcopy(self.Black_Pieces)                
            for v in pieces.values():
                if v >1:
                    blocks +=1
                else:
                    singles +=1
            return str([blocks,singles])        

    def Matrix_Eval_Board_4(self, board):
        # Using pip differential function, block differential, and rail count differential
        # To populate an array of [0,0,0] into for example [1,2,1], etc...to evaluate a given
        # board state, in order to feed various boards and save various board states, 
        # to be incremented and decremented at the end game and stored for reinforcement learning
        if self.can_remove == False:
            self.clear_dict()
            self.populate_Dict(board)
            Output =  [0,0,0]
            blocks = 0
            if self.color == 'red':
                pieces = copy.deepcopy(self.Red_Pieces)
                opp_pieces = copy.deepcopy(self.Black_Pieces)
                rail_count = len(self.board[25])-len(self.board[0])                
            elif self.color == 'black':
                pieces = copy.deepcopy(self.Black_Pieces)
                opp_pieces = copy.deepcopy(self.Red_Pieces)
                rail_count = len(self.board[0])-len(self.board[25])               
            
            for v in pieces.values():
                if v >1:
                    blocks +=1
            for v in opp_pieces.values():
                if v>1:
                    blocks -=1

            Output[0]=self.pip_differential()
            Output[1]=blocks
            Output[2]=rail_count
            return str(Output)

Red_wins = 0
Black_wins = 0
Red_Moves = []
Black_Moves = []
board = None
running = True
Games = 0

while running:    
    if Games ==1000:
        print(Red_wins/Black_wins)                            
        break
    
    clock.tick(FPS)    
    for event in p.event.get():
        if event.type == p.QUIT:
            sys.exit()
    
    P1 = Player('red',board)
    # P1.Random_Move(reinforced=True,File='Scores_10.json',Func=P1.Matrix_Eval_Board_4)
    P1.Random_Move()

    # print(P1.stored_boards)    
    board = P1.board
    conversion = P1.Eval_Board_New(board)
    # prevent breaking in end-game
    if conversion!=None:
        Red_Moves.append(conversion)

    if P1.win==True:
        P1.record_eval('Scores_11.json', Red_Moves, Black_Moves)                       
        Red_wins+=1
        Games +=1
        print(f'Red Wins : {Red_wins}, Black Wins:{Black_wins}')
        Red_Moves.clear()
        Black_Moves.clear()
        # Generates randomized board on the restart
        board = P1.generate_random_board()
 
    P2 = Player('black',board)      
    P2.Random_Move()
    board = P2.board
    conversion = P2.Eval_Board_New(board)
    if conversion!=None:
        Black_Moves.append(conversion)

    if P2.win==True:
        P2.record_eval('Scores_11.json', Black_Moves, Red_Moves)               
        Black_wins+=1
        Games+=1 
        print(f'Red Wins : {Red_wins}, Black Wins:{Black_wins}')                                                   
        Red_Moves.clear()
        Black_Moves.clear()
        board = P2.generate_random_board()     
        
    #  Optional Time parameter to view changing board states
    # time.sleep(.5)       
    p.display.flip()