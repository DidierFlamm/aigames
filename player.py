#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 19 10:54:31 2025

@author: did
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Any
from colorama import Fore




class Player:
    """
    Represents a human player by default.
    
    Attributes:
        game (Game)
        name (str): Player's name.
        symbol (str): Player's symbol (single character).
        color (str): Player's display color.
        stats (dict): Additional player characteristics.
        is_bot (bool): True if player is a bot, False if human (default).
        
    Internal attributes created:
        in_game (bool)
        move_fn : 
    """
    
    _counter = 0 # Compteur de joueurs humains créés
    
    def __init__(self, game: 'Game', name: str = None, symbol: str = None, color: str = None, stats: dict = None, is_bot : bool = False):
        
        if not is_bot: Player._counter += 1 # Incrémente le compteur uniquement si ce n’est pas un bot
        
        self.game = game
        
        
        # Générer un suffixe : _counter jusqu'à 9 puis A, B, etc...
        suffix = (str(Player._counter) if Player._counter < 10 
            else chr(ord('A') + Player._counter - 10))                  #exemple, pour counter = 10, on obtient chr(65 + 0) → 'A', etc....
        
        self.name = name if name else f"Player_{suffix}"
        self.symbol = symbol if symbol else suffix
        
        
        self.color = color if color else "default"
        self.stats = stats if stats else {}
        self.is_bot = is_bot
        self.in_game = True  # Le joueur est actif au début de la partie
        self.move_fn = self.game.get_human_move

    def __str__(self):
        """
        Représentation lisible de l’objet Player pour le débogage.
        """
        type_str = "Bot" if self.is_bot else "Human"
        try:
            color_code = getattr(Fore, self.color.upper())
        except AttributeError:
            color_code = ""
        
        colored_symbol = f"{color_code}{self.symbol}{Fore.RESET}"
        return f"<{type_str} {self.name} | symbol: '{colored_symbol}', color: '{self.color}', stats: {self.stats}>"
            

class Bot(Player):
    
    """
    Bot player subclass with a move strategy.

    Attributes:
        game (Game)
        move_fn (Callable[[Any], str]): Function to decide the bot's move.
        name (str): Player's name.
        symbol (str): Player's symbol (single character).
        color (str): Player's display color.
        stats (dict): Additional player characteristics.      
    """

    _counter = 0  # Compteur pour les bots

    def __init__(self, game: 'Game', move_fn: Callable[[Any], str], name: str = None, symbol: str = None, color: str = None, stats: dict = None):
        
        Bot._counter += 1
        name = name if name else f"bot_{chr(96 + Bot._counter)}"            #convertit le counter en lettre minuscule (96 + 1 -> 'a')
        symbol = symbol if symbol else chr(96 + Bot._counter)      
        super().__init__(game, name, symbol, color, stats, is_bot = True)   #appeler super.init après avoir défini name et symbole mais avant move_fn 
        self.move_fn = move_fn
        
class PlayerManagerUI:
    """
    Classe qui ouvre une fenêtre Tkinter pour créer un joueur humain ou un bot.
    
    Arguments:
    - game: instance de Game à laquelle ajouter le joueur créé.
    
    Usage:
    managerUI = PlayerManagerUI(game)
    bot     = managerUI.new_player(move_fn=fonction_IA)  # Pour un bot
    player = managerUI.new_player()  # Pour un humain
    """
    
    def __init__(self, game: 'Game'):
        
        self.game = game
        self.player = None

    def new_player(self, 
               symbol: str = "",
               color: str = "default"
               ) -> Player:
        self.root = tk.Tk()
        self.root.title("New Player")
    
        self.root.attributes('-topmost', True) #pour éviter que la fenetre soit cachée derriere les fenetres actives de l'utilisateur
        self.root.update()
    
        # Variables
        self.player_type = tk.StringVar(value="Human")
        self.name_var = tk.StringVar()
        self.symbol_var = tk.StringVar(value=symbol)
        self.color_var = tk.StringVar(value=color)
        self.move_fn_var = tk.StringVar(value = list(self.game.bot_move_fns.keys())[0])  # valeur par défaut ou vide
        self.stats_entries = []
    
        # Interface
        
            #type en ligne 0
        ttk.Label(self.root, text="Type:").grid(row=0, column=0, padx=5, pady=5)
        type_combo = ttk.Combobox(self.root, textvariable=self.player_type, values=["Human", "Bot"])
        type_combo.grid(row=0, column=1, padx=5)
        
        
            # move_fn en ligne 1 (cachée au départ)
        ttk.Label(self.root, text="Move:").grid(row=1, column=0, padx=5, pady=5)
        self.move_fn_combo = ttk.Combobox(self.root, textvariable=self.move_fn_var, 
                                           values=list(self.game.bot_move_fns.keys()))  
        self.move_fn_combo.grid(row=1, column=1, padx=5)
        self.move_fn_combo.grid_remove()  # cache la Combobox au départ
    
            # name en ligne 2
        ttk.Label(self.root, text="Name:").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(self.root, textvariable=self.name_var).grid(row=2, column=1, padx=5)
    
            #symbol en ligne 3
        ttk.Label(self.root, text="Symbol:").grid(row=3, column=0, padx=5, pady=5)
        ttk.Entry(self.root, textvariable=self.symbol_var).grid(row=3, column=1, padx=5)
    
            #color en ligne 4
        self.color_label = ttk.Label(self.root, text="Color:")
        self.color_label.grid(row=4, column=0, pady=5)
        colors = ['', 'black', 'blue', 'cyan', 'green', 'magenta', 'red', 'white', 'yellow']
        self.color_combo = ttk.Combobox(self.root, textvariable=self.color_var, values=colors, width=15)
        self.color_combo.grid(row=4, column=1)
        

            # Frame Stats en ligne 5
        self.stats_frame = ttk.LabelFrame(self.root, text="Stats")
        self.stats_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
        self.add_stats_row()
        self.btn_add_stat = ttk.Button(self.stats_frame, text="Add stat", command=self.add_stats_row)
        self.btn_add_stat.grid(row=99, column=1, columnspan=3, pady=5)
    
            # Bouton Create en ligne 6
        ttk.Button(self.root, text="Create", command=self.create_player).grid(row=6, column=0, columnspan=2, padx=30, pady=10, sticky='ew')
    
        # --- Listener sur color pour modifier la couleur du label Color ---
        def on_color_change(*args):
            color = self.color_var.get()
            try:
                self.color_label.configure(foreground=color)
            except tk.TclError:
                pass  # ignore les couleurs invalides 
        self.color_var.trace_add("write", on_color_change) #ajout du listener
        on_color_change() # Appel manuel au démarrage pour màj la couleur
    
        # --- Listener sur player_type pour afficher/cacher la combobox move_fn---
        def on_player_type_change(*args):
            if self.player_type.get() == "Bot":
                self.move_fn_combo.grid()  # affiche la Combobox
            else:
                self.move_fn_combo.grid_remove()  # cache la Combobox
        self.player_type.trace_add('write', on_player_type_change) #ajout du listener
        on_player_type_change() # Appel manuel au démarrage pour afficher ou non
        
        
        # création de la fenetre en mainloop
        self.root.mainloop()
        
        # retourne le joueur si besoin de le stocker dans une variable
        return self.player

    

    
    def add_stats_row(self):
        """
        Exécutée au moment du click sur le bouton Add Stat
        Ajoute une ligne de saisie dans la section Stats : deux Entry pour clé et valeur.
        """
        
        row = len(self.stats_entries)
        key_var = tk.StringVar()
        val_var = tk.StringVar()
        # On décale les colonnes pour laisser une marge de chaque côté (colonnes 1 et 2)
        ttk.Entry(self.stats_frame, textvariable=key_var, width=10).grid(row=row, column=1, padx=15)
        ttk.Label(self.stats_frame, text=":").grid(row=row, column=2)
        ttk.Entry(self.stats_frame, textvariable=val_var, width=10).grid(row=row, column=3, padx=15)
        self.stats_entries.append((key_var, val_var))

    def create_player(self):
        """
        Executée au moment du click sur create
        Récupère les données du formulaire, valide, puis crée un Player ou un Bot.
        
        Si Bot, vérifie que move_fn est fourni.
        """
        
        name = self.name_var.get()
        symbol = self.symbol_var.get()
        color = self.color_var.get()
        move_fn = self.move_fn_var.get()

        if len(symbol) > 1:
            messagebox.showerror("Invalid Symbol", "The symbol must be a single character or none.")
            return

        stats = {k.get(): v.get() for k, v in self.stats_entries if k.get()}
        
        if self.player_type.get() == "Bot":
            if not move_fn:  # vide ou None
                messagebox.showerror("Error", "You must select a move function for a Bot.")
                return
            self.player = Bot(self.game, self.game.bot_move_fns[move_fn], name, symbol, color, stats)
        else:
            self.player = Player(self.game, name, symbol, color, stats, is_bot = False)
            
        # le player est ajouté à la liste des joueurs de game 
        self.game.players.append(self.player)

        self.root.destroy()







if __name__ == "__main__":
    
    # Exemple d’utilisation avec un jeu fictif
    
    class Game():
        def __init__(self):
            self.players = [] # Liste pour stocker tous les joueurs (humains et bots)
            self.bot_move_fns = {"fn1" : lambda : "fonction 1", "fn2" : lambda : "fonction 2"}
    
    my_game = Game()
  
    
    manager = PlayerManagerUI(my_game)    # Créateur lié à l’instance my_game
    
    new_player = manager.new_player()        # Création d’un new_player
