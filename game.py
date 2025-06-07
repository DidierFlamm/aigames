# -*- coding: utf-8 -*-
"""
Created on Mon May 12 09:38:44 2025

@author: did

exemple : https://www.codingame.com/multiplayer/bot-programming/tic-tac-toe
 
"""

#TODO: permettre List[str] ou Tuple[str, ...] dans get_winner() pour gérer des victoires multiples, si le jeu le permet.
#TODO: créer 1_vs_all : self.all_against_ref_player = True + définir self.reference_player dans l'init de classe et le passer dans l'appel de best move : best_move = self.get_best_move(state=self.state, player=self.player, reference_player=self.reference_player, all_against_ref_player=self.all_against_ref_player, max_depth=max_depth) 
#TODO: créer run_multi avec self.all_against_ref_player = False

from typing import List, TypeVar, Generic, Any
from abc import ABC, abstractmethod
from copy import deepcopy
from time import time
import datetime
import os
import json
import random
from colorama import Fore, Style
from player import PlayerManagerUI
from minimax import Minimax
from tkinter import Tk, filedialog


#NOTE: State a un type libre qui pourra être spécifié lors de la création d'une sous-classe
StateType = TypeVar("StateType")



class Game(ABC, Generic[StateType]): #signifie que la classe Game est générique sur le type StateType
    
    def __init__(self, initial_state: StateType, all_against_ref_player: bool):
        """
        Initialise une nouvelle instance de jeu.
        
        Paramètres :
        - initial_state : L'état initial du jeu (par exemple : plateau vide, position de départ…).
                          Une copie profonde sera faite pour protéger cet état d'origine.
        - all_against_ref_player : Booléen déterminant la stratégie utilisée par l'algorithme Minimax :
            - True  : Minimax classique, où un joueur considère tous les autres comme adversaires
                      et essaie de maximiser son propre score en minimisant celui des autres.
            - False : Minimax "selfish", où chaque joueur maximise indépendamment son propre score
                      sans chercher à minimiser celui des autres (utile dans les jeux à plusieurs joueurs
                      avec stratégies plus individualistes).
    
        Attributs internes créés :
        - self.initial_state : Copie profonde de l'état initial, utilisée pour initialiser le jeu.
        - self.starting_player : Joueur qui commence la partie actuelle. Peut changer lors des redémarrages
                                 (par exemple pour alterner les joueurs au début de chaque partie).
        - self.state : état courant du jeu (copie profonde de initial_state).
        - self.current_player : joueur courant actif dans le tour en cours.
        - self.scores : Dictionnaire des scores de l'ensemble des parties jouées (clé = nom de joueur ou 'draw' ; valeur = nombre de victoires du joueur ou de matchs nuls pour "draw").
        - self.game_number : nombre de parties jouées
        - self.game : liste des événements et états successifs d'une partie (liste de dict),
                         remplie par 'run' si l'option 'save_log' est activée.
        - self.games : liste des parties jouées (list de dict)
                 
        Comportement :
        - self.initial_state est deepcopié pour s'assurer de conserver la configuration de base.
        """
        
        self.initial_state = deepcopy(initial_state)  
        self.starting_player = None
        self.all_against_ref_player = all_against_ref_player
        self.reference_player= None            # à définir lors de la création des joueurs pour les jeux multi avec self.all_against_ref == True
        self.max_depth = None                  # max_depth sera initialisé par la méthode start()
        self.log = None                        # log sera initialisé par la méthode start()
        self.nb_players = None                 # nb_players ne doit être défini que si le nb de players est imposé. Sinon, il doit rester None et sera géré par la méthode start() avec une variable locale
        self.state = deepcopy(initial_state)    
        self.current_player = None          
        self.scores = {}                       
        self.game_number = 0                   # on initialise la 1ère game à 0 pour être cohérent avec le comptage python
        self.game = []
        self.games = []
        self.players = []                      # Liste pour stocker tous les joueurs de la partie (humains et bots)
        self.bot_move_fns= {}                # Dictionnaire des functions utiles pour créer des bots {fn_name : fn}
        self.managerUI = PlayerManagerUI(self)     # Objet permettant le management des joueurs (création, modification, suppression...)
        self.minimax = Minimax(self)
        
        #créé les 2 bots best et random et les ajoute à la liste de bots
        self.bot_move_fns["minimax_best_move"] = self.minimax.get_best_move  #ajoute best_move
        self.bot_move_fns["random_move"] = self.get_random_move  #ajoute random_bot
        

        
        
    def __str__(self):
        info = [
            f"Game {self.__class__.__name__} #{self.game_number}",
            f"Starting player: {self.starting_player}",
            f"Current player: {self.current_player}",
            f"Scores: {self.scores}",
            "Current state:",
            self.state_to_str(self.state)
        ]
        return "\n".join(info)
    
    def start(self, max_depth: int = None, log: bool = False, nb_players: int = None):
        """
        Fonction lancée juste après l'initialisation
        Permet de définir certains paramètres optionnels spécifiques à la partie :
            -max_depth
            -log
            -nb_players
        Permet de créer les players et executer run()
        Par défaut: 
            - affiche un message de bienvenue et le message issu de print_help
            - demande le nb de joueurs si non précisé
            - lance PlayerManagerUI pour la création des nouveaux joueurs via UI
            - définit le 1er joueur créé comme starting_player
            - execute run() 
        """
        
        print("\nWelcome in", self.__class__.__name__, "!\n")
        
        self.max_depth = max_depth
        self.log = log
        
        self.print_help()
        print("")
        
        #si self.nb_players est défini, on l'utilise en priorité
        if self.nb_players: nb_players = self.nb_players
        
        # si self.nb_players n'est pas défini et nb_players non plus, on demande de le préciser :
        if not nb_players:
            while True:
                try:
                    nb_players = int(input("Select number of players: "))
                    if nb_players <= 0:
                        print("Please enter a positive number.")
                        continue
                    break
                except ValueError:
                    print("Invalid input. Please enter a valid integer.")
        
        if len(self.players)>nb_players:
            raise ValueError(f"Too many players: expected {nb_players}, got {len(self.players)}.")
        
        #on créé autant de nouveaux joueurs que nécessaire (en tenant compte des joueurs créée éventuellement pendant l'init)
        while len(self.players) < nb_players:
            self.managerUI.new_player()
        
        #affichage des joueurs créés pour vérification
        for player in self.players:
            print(player)
        print("")
        
        #définition du starting player
        self.starting_player = self.players[0]
        
        #run !
        self.run()
    
    @abstractmethod
    def state_to_str(self, state: StateType) -> str:
        """
        Retourne une représentation textuelle (string) de l'état du jeu donné.
        Cette méthode doit être implémentée par les sous-classes.
        """
        
    def symbol_to_colored_symbol(self, symbol: str, players: List[Any]) -> str:
        """ 
        Retourne le symbole colorisé du symbole selon les couleurs définies dans players
        Peut être utilisé pour définir print_colored_state
        """
        sym_to_pla = {player.symbol : player for player in players}
        
        player = sym_to_pla.get(symbol, None)
        
        try:
            return self.get_colored_symbol(player)
        except:
            return symbol
        
    def get_colored_symbol(self, player) -> str:
        """
        Transforme le symbole du joueur en une f-string du symbole coloré.
        
        Exemple :
            player = player_1
            let player_1.symbol = "X"
            → f"\x1b[31mX{Style.RESET_ALL}"
    
        Retour :
            str : f-string du symbole coloré selon la couleur du joueur.
        """
        
        color_name = player.color.upper()                    #par exemple color_name = RED
        try: 
            color = getattr(Fore, color_name)                #par exemple: color = Fore.RED
        except:
            color = Fore.RESET                               #gère l'erreur si la couleur est inconnu                         
        return f"{color}{player.symbol}{Style.RESET_ALL}"
    
    def get_colored_name(self, player) -> str:
        """
        Retourne une f-string du nom coloré.
        
        Exemple :
            symbol = "Player_1"
            → f"\x1b[31mPlayer_1{Style.RESET_ALL}"
    
        Retour :
            str : f-string du symbole coloré selon la couleur du joueur correspondant.
        """
        color_name = player.color.upper()                    #par exemple color_name = RED
        try: 
            color = getattr(Fore, color_name)                #par exemple: color = Fore.RED
        except:
            color = Fore.RESET                               #gère l'erreur si la couleur est inconnu                         
        return f"{color}{player.name}{Style.RESET_ALL}"

    
    
    def print_state_from_str(self, state_str : str) -> None:
        """
        Affiche de façon esthétique l'état du jeu.
        A adapter en fonction du jeu et de son StateType
        Par défaut, effectue un simple print de state après transformation par state_to_str.
        Utilisé pour les replays (car players n'est pas accessible pour coloriser)
        """
        
        print(state_str)
        
    def print_colored_state(self, state, players) -> None:
        """ 
        Affiche l'état du jeu en colorisant les symboles selon la liste des players'
        Utilisé pendant le déroulement du jeu
        Par défaut, transforme state en state_str et le print via print_state_from_str (sans utiliser de couleur)
        """
        
        state_str = self.state_to_str(state)
        
        self.print_state_from_str(state_str)
        

    def print_help(self) -> None:
        """
        Affiche le guide d'utilisation du jeu.
        
        Cette méthode peut être surchargée dans chaque sous-classe pour fournir
        un message personnalisé à destination de l'utilisateur.
        Par défaut, elle affiche des instructions générales.
        """
        print("How to play:")
        print("- Enter a move (e.g., a number or coordinate depending on the game),")
        print("  or press [Enter] without typing anything to let the AI play for you.")
        print("- Type '?' or 'help' at any time to display these instructions again.")
    

    @abstractmethod                                   
    def is_terminal(self, state: StateType) -> bool:
        """
        Vérifie si l'état du jeu est terminal (victoire, défaite ou match nul).
        NB : peut éventuellement faire intervenir des fonctions comme get_winner(state),
        """
        

    @abstractmethod
    def get_score_by_symbol(self, state: StateType, reference_player: str, depth: int) -> int:
        """
        Calcule et retourne le score de l'état du jeu pour le joueur spécifié.
        Utilisé pour évaluer les positions terminales.
        """
        
    
    @abstractmethod
    def get_heuristic_by_symbol(self, state: StateType, reference_player_symbol: str, depth: int) -> int:
        """
        Évalue un état de jeu non terminal en attribuant un score heuristique.
        Utilisé pour évaluer les positions non terminales en cas de dépassement de max_depth
        """
        

    @abstractmethod
    def get_possible_moves(self, state: StateType) -> List[str]:
        """
        Retourne la liste des mouvements possibles dans l'état donné.
        """
        

    @abstractmethod
    def apply_move(self, state: StateType, move: str, player: str)-> StateType:
        """
        Applique le mouvement du joueur sur l'état du jeu et retourne le nouvel état.
        """
        
    
    def get_next_player(self, player):
        """
        Retourne le joueur suivant dans l'ordre de jeu, parmi les joueurs in_game
        """
        in_game_players = [_player for _player in self.players if _player.in_game == True]
        current_index = in_game_players.index(player)
        next_player = in_game_players[(current_index+1)%len(in_game_players)]
        return next_player
    
    def get_next_player_by_symbol(self, symbol: str)-> str:
        """
        Retourne le symbole suivant dans l'ordre de jeu, parmi les joueurs in_game
        """
        in_game_symbols = [_player.symbol for _player in self.players if _player.in_game == True]
        current_index = in_game_symbols.index(symbol)
        next_symbol = in_game_symbols[(current_index+1)%len(in_game_symbols)]
        return next_symbol
        
    @abstractmethod
    def get_winner_by_symbol(self, state: StateType) -> str | None:
        """
        Retourne le vainqueur ou None si il n'y en a pas.
        """
        
    def get_player_by_symbol(self, symbol:str):
        """
        Retourne le joueur correspondant au symbole ou None si inconnu
        """
        symbol_to_player = {player.symbol : player for player in self.players}
        return symbol_to_player.get(symbol)
    
    def early_pruning_hook(self, state, depth, value, max_depth=None, reference_player=None) -> bool:
        """
        Hook d’élagage précoce (early pruning) à surcharger si besoin selon la logique propre à chaque jeu.
        
        Par défaut, cette fonction ne déclenche aucun élagage et retourne toujours False.
        
        Elle peut être redéfinie dans une sous-classe pour arrêter l’exploration d’une branche 
        lorsqu’un critère de "non-pertinence" ou de "coût trop élevé" est détecté.
    
        Paramètres :
        - state : L'état actuel du jeu
        - depth : La profondeur actuelle dans l'arbre
        - value : La valeur estimée de cette branche jusqu'ici
        - max_depth : (optionnel) Profondeur limite, si définie
        - reference_player : (optionnel) Peut être utile dans des stratégies ciblant un joueur
    
        Retourne :
        - True si l’exploration doit s’arrêter prématurément pour cette branche
        - False sinon (comportement par défaut)
        
        Exemple de surcharge :
        ```python
        def early_pruning(self, state, depth, value, max_depth=None, reference_player=None):
            # Arrêt si heuristique très défavorable dès un faible niveau
            return value < -100 and depth < 2
        ```
        """
        return False
    
    def get_random_move(self, state, **kwargs) -> str:
        """ 
        Retourne un move choisi au hasard parmi les moves possibles
        **kwargs permet de le rendre compatible avec best_move

        """
        moves = self.get_possible_moves(state)
        return random.choice(moves)
    
    def get_human_move(self, state, player, **kwargs) -> str:
        """
        Demande le move du joueur en cours via input, vérifie et retourne le move
        **kwargs permet de le rendre compatible avec best_move

        """
        
        current_colored_symbol = self.get_colored_symbol(player)
        
        move = input(f"{player.name} : {current_colored_symbol} – Your turn ! Move or '?' for help ➤ ")
        
        moves = self.get_possible_moves(state)
            
        if move == "?" or move == "help":
            print("")
            self.print_help()
            print("")
            return self.get_human_move(state, player)
            
        elif move not in moves:
            print(f"'{move}' is not a valid move! Choose among: {', '.join(moves)}")
            return self.get_human_move(state, player)
        else:
            return move
    
    def run(self, max_depth: int = None):
        if len(self.players)==1: 
            self.run_solo(max_depth)
        elif len(self.players)==2: 
            self.run_1_vs_1(max_depth)
        elif self.all_against_ref_player:
            self.run_1_vs_all(max_depth)
        else:
            self.run_multi(max_depth)
    
    def run_1_vs_1(self, max_depth: int = None):
        
        """
        si save_log est activé, met à jour l'historique des évenements et états successifs du jeu avec:
            - une ligne pour l'évenement start avec les paramètres starting_player, max_depth ainsi que le datetime du début de la partie
            - une ligne par chaquen évenement move :
                - 'player' : identifiant du joueur ayant joué (ex: "X", 1, etc.)
                - 'action' : coup joué (format dépendant du jeu, ex: (row, col))
                - 'state' : copie de l'état du jeu juste après ce coup (type variable selon le jeu)
                - 'duration' : le temps en ms si le coup a été déterminé par IA ou None sinon
            - une ligne pour l'évenement end avec les paramètres status, winner le cas échéant et le datetime de fin de la partie et la durée totale
        """
                       
        def play_turn():
            
            if self.log: t_start = time()
            
            #get move (attention à la signature des fonctions passés à player.move_fn car elles doivent être compatibles avec les kwargs ci-dessous
            move = self.current_player.move_fn(state = self.state, player= self.current_player, reference_player= self.current_player, all_against_ref_player= self.all_against_ref_player, max_depth=self.max_depth)
            
            #Affiche le bot si move
            if self.current_player.is_bot: print(self.get_colored_name(self.current_player), "plays", move)

            
            
            
            #apply move
            self.state = self.apply_move(self.state, move, self.current_player)
            self.print_colored_state(self.state, self.players)
            #log move
            if self.log:
                duration = int(1000 * (time() - t_start))
                self.game.append({
                "event": "move",
                "player": self.current_player.symbol,
                "action": move,
                "state": self.state_to_str(self.state),
                "duration_ms": duration
            })
            #next player to current
            self.current_player = self.get_next_player(self.current_player)
        
    
        def handle_end_of_game(start_time):
            winner_symbol = self.get_winner_by_symbol(self.state)
            if winner_symbol:
                winner = self.get_player_by_symbol(winner_symbol)
                print(f"{self.get_colored_name(winner)} wins !")
                self.scores[winner_symbol] = self.scores.get(winner_symbol, 0) + 1
            else:
                print("It's a draw !")
                self.scores["draw"] = self.scores.get("draw", 0) + 1
                
                 
            if self.log:
                #log l'event end
                end_time = datetime.datetime.now()
                duration = int((end_time - start_time).total_seconds() * 1000)
                self.game.append({
                    "event": "end",
                    "winner": winner_symbol,
                    "status": "win" if winner_symbol else "draw",
                    "datetime": end_time.isoformat(timespec='milliseconds')
                })
                #ajoute game dans games
                self.games.append({
                    "game_number": self.game_number,
                    "starting_player": self.starting_player.symbol,
                    "duration_ms": duration,
                    "score": self.scores.copy(),
                    "events": self.game
                })
                #reset game pour la prochaine partie
                self.game = []
    
            #print scores
            print("\nScore :")
            for player in self.players:
                print(f"\t{self.get_colored_name(player)} : {self.scores.get(player.symbol, 0)}")
            
            if self.scores.get('draw',0) != 0:
                print(f"\tdraws : {self.scores.get('draw',0)}")   #et on termine par draws si il y en a
        
        
        
        
        self.current_player = self.starting_player
        
        while True:   #boucle infinie sur les nouvelles parties (tant que l'utilisateur ne quitte pas)
            
            start_time=None
            #log l'event start
            if self.log:
                start_time = datetime.datetime.now()
                self.game.append({
                "event": "start",
                "datetime": start_time.isoformat(timespec='milliseconds')
                })
            
            #print le début de partie
            print("Game", self.game_number)
            print(f"{self.current_player.name} : {self.get_colored_symbol(self.current_player)} starts")
            self.print_colored_state(self.state, self.players)
            
            #boucle sur chaque tour d'une partie jusqu'à un état terminal
            while not self.is_terminal(self.state): 
                play_turn()
               
            #atteinte de l'état terminal => fonction dédiée   
            handle_end_of_game(start_time)
                     
                        #si play again, on continue sur une nouvelle partie     
            if input("\nPress [enter] to play again, or any other key to quit ➤ ") == "": 
                self.state = deepcopy(self.initial_state)
                self.starting_player = self.get_next_player(self.starting_player)
                self.current_player = self.starting_player
                self.game_number+=1
                continue
            else:       #sinon on détermine le final winner, on save log, on print la fin de partie et quitte
                final_winner_symbols = self.get_final_winner_symbols()
                if self.log:
                    self.save_log(max_depth, final_winner_symbols)
                                    
                if final_winner_symbols :
                    final_winner = self.get_player_by_symbol(final_winner_symbols)
                    if final_winner:                                                           # en cas d'égalité de victoire, final winner retourne None
                        print('\nFinal winner is', self.get_colored_name(final_winner), "!!")
                    else : 
                        print("\nIt's a tie between", final_winner_symbols, "!")
                else:
                    print("\nIt's a tie with only draws.")
                
                print("\nGood bye !")
                return
    
    def get_final_winner_symbols(self)-> str:
        """
        Retourne le symbole du joueur ayant le score le + plus élevé
        Retourne None si il n'y a que des matchs nuls
        En cas d'égalité, retourne les symboles des joueurs vainqueurs séparés par '&''
        """
        scores_without_draw = {k: v for k, v in self.scores.items() if k != "draw"}
    
        if not scores_without_draw:
            return None  # Que des matchs nuls, aucun gagnant
    
        max_score = max(scores_without_draw.values())
        winners_symbols = [symbol for symbol, score in scores_without_draw.items() if score == max_score]
    
        return " & ".join(sorted(winners_symbols)) # Si plusieurs gagnants, on les joint avec " & "               
    
    def save_log(self, max_depth, final_winner):
        """
        Sauvegarde les données de la session dans un fichier JSON.
        Le fichier est nommé selon le nom de la classe et l’horodatage de fin de partie.
        """
        
        start_iso_datetime = self.games[0]["events"][0]["datetime"]
        end_iso_datetime = self.games[-1]["events"][-1]["datetime"]
        
        total_duration = int((datetime.datetime.fromisoformat(end_iso_datetime) - datetime.datetime.fromisoformat(start_iso_datetime)).total_seconds())
        
        players_list = []
        for player in self.players:
            players_list.append({"name":player.name, "symbol":player.symbol, "color":player.color, "stats":player.stats, "is_bot":player.is_bot, "move_fn_class": player.move_fn.__self__.__class__.__name__, "move_fn_name": player.move_fn.__name__})
        
        
        session_info = {
            "game_class": self.__class__.__name__,
            "all_against_ref_player": self.all_against_ref_player,
            "total_games": len(self.games),
            "max_depth": max_depth,
            "initial_state": self.state_to_str(self.initial_state),
            "players": players_list,
            "final_winner": final_winner,
            "final_score": self.scores,
            "start_datetime": start_iso_datetime,
            "end_datetime": end_iso_datetime,
            "total_duration_s": total_duration,
            "games": self.games                                               
            }
        
        
        class_name = self.__class__.__name__
    
        # Créer le dossier dédié : game_logs/<NomClasse> 
        folder_path = os.path.join("game_logs", class_name)
        os.makedirs(folder_path, exist_ok=True) # Crée récursivement le dossier si besoin
    
        # Récupérer la date/heure actuelle pour le nom du fichier
        timestamp = datetime.datetime.now().isoformat(timespec='seconds').replace(":", "-")
        filename = f"{class_name}_{timestamp}.json"
        filepath = os.path.join(folder_path, filename)
    
        # Sauvegarde JSON
        with open(filepath, "w") as f:
            json.dump(session_info, f, indent=2)
            
        print(f"💾 Game successfully saved to '{filename}'")
        
    def replay(self, file_path: str = None) -> None:
        
        #Load JSON from a given file path or via a file dialog if None.
    
    
        if file_path and os.path.isfile(file_path):
            path = file_path
        else:
            root = Tk()
            root.withdraw()  # Ne pas afficher la fenêtre principale
            path = filedialog.askopenfilename(
                title="Choose JSON file",
                filetypes=[("JSON files", "*.json")],
            )
            root.destroy()
    
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    log = json.load(f)
            except Exception as e:
                print(f"[red]Error loading JSON file {path}: {e}[/red]")
                return
        else:
            return
        
        filename = os.path.basename(path)
        
        print("File:", filename)
        print("Game:", log["game_class"])
        self.print_state_from_str(log["initial_state"])
        print(f"\n{len(log["players"])} players:\n") 
        for player in log['players']:
            print("\t" + player['name'])
            print("\t\tsymbol:", player['symbol'])
            print("\t\tcolor:", player['color'])
            print("\t\tbot: ", player['is_bot'],"\n")
        print(log["total_games"],"games:")
        for game in log['games']:
            print("\n=== game", game["game_number"],"===\n")
            for event in game["events"][1:-1]:
                print("\t"+event["player"],"plays", event["action"])
                self.print_state_from_str(event['state'])
            print(f"\nwinner: {game["events"][-1]["winner"]}")
            print(f"score: {game["score"]}")
        print("\nFinal winner is", log["final_winner"])