'''
核心
'''
import tkinter as tk
import os
import bena
import anne
from protractor import PROTRACTOR

if __name__ == "__main__":
    bena.load_character_names()
    bena.load_enemy_names()
    #bena.load_buff_template_data()
    #PROTRACTOR.load_directory("buff_template",bena.BUFF_TEMPLATE_DATA)
    bena.load_roguelike_topic_table()
    PROTRACTOR.load_directory("rogue_item",bena.ROGUELIKE_TOPIC_TABLE)
    PROTRACTOR.open()