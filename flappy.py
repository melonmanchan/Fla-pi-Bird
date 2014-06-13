#!/usr/bin/env python
# -*- coding: utf-8 -*-

import curses
import numpy as np
import time
import serial
import sys
import random

C_TICKSPEED = 0.7
C_PLAYER_XPOS = 4
C_PIPE_TICK = 4
C_PIPE_HOLE_SIZE = 3

class Player:
    def __init__(self):
        self.height = 4
        self.isDead = False
        self.isJumpingNextFrame = False
        
    def handle_player_movement(self):
        if self.isJumpingNextFrame == True:
            if self.height > 0:
                self.height-= 1
        else:
            self.height += 1
        self.isJumpingNextFrame = False

        if self.height == 9:
            self.height = 8
            self.isDead = True
        
class Game:
    def __init__(self):
        self.ticks = 0
        self.score = 0
        self.port = self.open_port()
        self.gameMap = self.initialize_world()
        self.player = Player()
        self.gameMap[self.player.height, C_PLAYER_XPOS] = 1
        self.timer = time.time()
        
        self.inputPoller = curses.initscr()
        curses.noecho()
        self.inputPoller.nodelay(1)
        
        self.add_pipe()
        
    def open_port(self):
        s = serial.Serial()
        s.baudrate = 9600
        s.timeout = 0
        s.port = "/dev/ttyAMA0"

        try:
            s.open()
        except serial.SerialException, e:
            sys.stderr.write("could not open port %r: %s\n" % (s.port, e))
            sys.exit(1)
        
        s.write("$$$ALL,OFF\r")
        return s

    def initialize_world(self):
        return np.zeros((9, 14))

    def main_loop(self):
        deltaTimer = time.time()
        if not self.player.isJumpingNextFrame:
            self.player.isJumpingNextFrame = self.handle_input()
            
        if deltaTimer - self.timer > C_TICKSPEED:
            self.timer = time.time()
            self.update()
            self.draw()
            curses.flushinp()
    
    def update(self):
        self.ticks += 1
            
        self.gameMap[self.player.height, C_PLAYER_XPOS] = 0
        
        self.player.handle_player_movement()
        self.check_pipe_collisions()
        self.check_for_death()
        ## Roll map one step to the left
        self.gameMap = np.roll(self.gameMap,13,axis=1)
        self.gameMap[:,-1] = 0
        self.gameMap[self.player.height, C_PLAYER_XPOS] = 1

        if self.ticks % C_PIPE_TICK == 0:
            self.add_pipe()
            if self.ticks > 8:
                self.score += 1
        
    def draw(self):
        ##print np.array_str(self.gameMap)
        ## Get transposition of game map, remove non-digit characters and draw.
        frameString = np.array_str(self.gameMap.T)
        frameString = filter(lambda x: x.isdigit(), frameString)
        self.port.write("$$$F" + frameString + "\r" )

    def check_pipe_collisions(self):
        if self.gameMap[self.player.height, C_PLAYER_XPOS + 1] == 1:
            self.player.isDead = True
            
    def check_for_death(self):
        if self.player.isDead == True:
            self.port.write("$$$ALL,OFF\r")
            self.port.write("ded, score: " + str(self.score))
            curses.flushinp()
            curses.endwin()
            sys.exit(0)
    
    def add_pipe(self):
        self.gameMap[0:9, 13] = 1
        hole = random.randint(C_PIPE_HOLE_SIZE,8)
        self.gameMap[hole-C_PIPE_HOLE_SIZE:hole,13] = 0
        
    def handle_input(self):
        c = self.inputPoller.getch()
        if c >1 :
             return True
        else:
            return False
    
def main():
    game = Game()
    while True:
        game.main_loop()
    
if __name__ == '__main__':
    main()
