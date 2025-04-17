import pymongo
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ClashRoyaleAnalytics:
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client['clashroyale']
        self.players = self.db['players']
        self.battles = self.db['battles']
        
    # Consultas originais
    def win_loss_percentage_by_card(self, card_name, start_date, end_date):
        """Consulta 1: Porcentagem de vitórias/derrotas com uma carta específica"""
        pipeline = [
            {"$match": {
                "battleTime": {"$gte": start_date, "$lte": end_date},
                "$or": [
                    {"team.0.cards.name": card_name},
                    {"team.1.cards.name": card_name}
                ]
            }},
            {"$project": {
                "playerTag": 1,
                "team": 1,
                "won": {
                    "$cond": {
                        "if": {"$eq": ["$team.0.crowns", 3]},
                        "then": "team0",
                        "else": "team1"
                    }
                },
                "used_card": {
                    "$cond": {
                        "if": {"$in": [card_name, "$team.0.cards.name"]},
                        "then": "team0",
                        "else": "team1"
                    }
                }
            }},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "wins": {
                    "$sum": {
                        "$cond": [{"$eq": ["$won", "$used_card"]}, 1, 0]
                    }
                }
            }},
            {"$project": {
                "win_percentage": {"$multiply": [{"$divide": ["$wins", "$total"]}, 100]},
                "loss_percentage": {"$subtract": [100, {"$multiply": [{"$divide": ["$wins", "$total"]}, 100]}]}
            }}
        ]
        
        result = list(self.battles.aggregate(pipeline))
        return result[0] if result else {"win_percentage": 0, "loss_percentage": 0}

    def high_winrate_decks(self, min_win_percentage, start_date, end_date):
        """Consulta 2: Decks com alta taxa de vitória"""
        pipeline = [
            {"$match": {
                "battleTime": {"$gte": start_date, "$lte": end_date}
            }},
            {"$project": {
                "deck": "$team.0.cards.name",
                "won": {"$eq": ["$team.0.crowns", 3]}
            }},
            {"$group": {
                "_id": "$deck",
                "total": {"$sum": 1},
                "wins": {"$sum": {"$cond": ["$won", 1, 0]}}
            }},
            {"$project": {
                "deck": "$_id",
                "win_percentage": {"$multiply": [{"$divide": ["$wins", "$total"]}, 100]}
            }},
            {"$match": {
                "win_percentage": {"$gt": min_win_percentage}
            }},
            {"$sort": {"win_percentage": -1}}
        ]
        
        return list(self.battles.aggregate(pipeline))

    def loss_count_by_combo(self, card_combo, start_date, end_date):
        """Consulta 3: Derrotas com um combo específico de cartas"""
        pipeline = [
            {"$match": {
                "battleTime": {"$gte": start_date, "$lte": end_date},
                "team.0.cards.name": {"$all": card_combo}
            }},
            {"$project": {
                "lost": {"$ne": ["$team.0.crowns", 3]}
            }},
            {"$group": {
                "_id": None,
                "loss_count": {"$sum": {"$cond": ["$lost", 1, 0]}}
            }}
        ]
        
        result = list(self.battles.aggregate(pipeline))
        return result[0]['loss_count'] if result else 0

    def wins_with_card_underdog(self, card_name, trophy_diff_percent, start_date, end_date):
        """Consulta 4: Vitórias com carta X quando o vencedor tem menos troféus"""
        pipeline = [
            {"$match": {
                "battleTime": {"$gte": start_date, "$lte": end_date},
                "duration": {"$lt": 120},  # Menos de 2 minutos
                "team.1.towersDestroyed": {"$gte": 2}  # Perdedor derrubou 2+ torres
            }},
            {"$project": {
                "winner": {
                    "$cond": {
                        "if": {"$eq": ["$team.0.crowns", 3]},
                        "then": {"tag": "$team.0.tag", "trophies": "$team.0.startTrophies"},
                        "else": {"tag": "$team.1.tag", "trophies": "$team.1.startTrophies"}
                    }
                },
                "loser": {
                    "$cond": {
                        "if": {"$ne": ["$team.0.crowns", 3]},
                        "then": {"tag": "$team.0.tag", "trophies": "$team.0.startTrophies"},
                        "else": {"tag": "$team.1.tag", "trophies": "$team.1.startTrophies"}
                    }
                },
                "winner_deck": {
                    "$cond": {
                        "if": {"$eq": ["$team.0.crowns", 3]},
                        "then": "$team.0.cards.name",
                        "else": "$team.1.cards.name"
                    }
                }
            }},
            {"$match": {
                "$expr": {
                    "$lt": [
                        "$winner.trophies",
                        {"$multiply": ["$loser.trophies", (100 - trophy_diff_percent) / 100]}
                    ]
                },
                "winner_deck": card_name
            }},
            {"$count": "win_count"}
        ]
        
        result = list(self.battles.aggregate(pipeline))
        return result[0]['win_count'] if result else 0

    def best_card_combos(self, combo_size, min_win_percentage, start_date, end_date):
        """Consulta 5: Melhores combos de cartas de tamanho N"""
        # Esta é uma versão simplificada - análise de combos pode ser complexa
        pipeline = [
            {"$match": {
                "battleTime": {"$gte": start_date, "$lte": end_date}
            }},
            {"$project": {
                "cards": "$team.0.cards.name",
                "won": {"$eq": ["$team.0.crowns", 3]}
            }},
            {"$unwind": "$cards"},
            {"$group": {
                "_id": "$cards",
                "win_rate": {"$avg": {"$cond": ["$won", 1, 0]}}
            }},
            {"$match": {
                "win_rate": {"$gt": min_win_percentage / 100}
            }},
            {"$sort": {"win_rate": -1}},
            {"$limit": combo_size}
        ]
        
        return list(self.battles.aggregate(pipeline))

    # Consultas extras
    def most_used_cards(self, start_date, end_date):
        """Consulta Extra 1: Cartas mais usadas"""
        pipeline = [
            {"$match": {
                "battleTime": {"$gte": start_date, "$lte": end_date}
            }},
            {"$unwind": "$team"},
            {"$unwind": "$team.cards"},
            {"$group": {
                "_id": "$team.cards.name",
                "usage_count": {"$sum": 1}
            }},
            {"$sort": {"usage_count": -1}},
            {"$limit": 10}
        ]
        
        return list(self.battles.aggregate(pipeline))

    def player_win_rates(self, min_battles=10):
        """Consulta Extra 2: Taxa de vitória por jogador"""
        pipeline = [
            {"$group": {
                "_id": "$playerTag",
                "total_battles": {"$sum": 1},
                "wins": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$team.0.crowns", 3]},
                            1,
                            0
                        ]
                    }
                }
            }},
            {"$match": {
                "total_battles": {"$gte": min_battles}
            }},
            {"$project": {
                "win_rate": {"$divide": ["$wins", "$total_battles"]},
                "total_battles": 1
            }},
            {"$sort": {"win_rate": -1}}
        ]
        
        return list(self.battles.aggregate(pipeline))

    def card_win_rates_by_arena(self, arena, start_date, end_date):
        """Consulta Extra 3: Taxa de vitória por carta em uma arena específica"""
        pipeline = [
            {"$match": {
                "battleTime": {"$gte": start_date, "$lte": end_date},
                "arena.name": arena
            }},
            {"$unwind": "$team"},
            {"$unwind": "$team.cards"},
            {"$group": {
                "_id": "$team.cards.name",
                "total_uses": {"$sum": 1},
                "wins": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$team.crowns", 3]},
                            1,
                            0
                        ]
                    }
                }
            }},
            {"$project": {
                "win_rate": {"$divide": ["$wins", "$total_uses"]},
                "total_uses": 1
            }},
            {"$sort": {"win_rate": -1}},
            {"$limit": 10}
        ]
        
        return list(self.battles.aggregate(pipeline))


class AnalyticsGUI:
            def __init__(self, root, db):
                self.root = root
                self.db = db
                self.setup_ui()
                
            def setup_ui(self):
                self.root.title("Clash Royale Analytics")
                self.root.geometry("1000x700")
                
                # Notebook para abas
                self.notebook = ttk.Notebook(self.root)
                self.notebook.pack(fill='both', expand=True)
                
                # Aba para consultas principais
                self.main_queries_tab = ttk.Frame(self.notebook)
                self.notebook.add(self.main_queries_tab, text="Consultas Principais")
                self.setup_main_queries_tab()
                
                # Aba para consultas extras
                self.extra_queries_tab = ttk.Frame(self.notebook)
                self.notebook.add(self.extra_queries_tab, text="Consultas Extras")
                self.setup_extra_queries_tab()
                
                # Área de resultados
                self.result_frame = ttk.LabelFrame(self.root, text="Resultados")
                self.result_frame.pack(fill='both', expand=True, padx=5, pady=5)
                
                self.result_text = scrolledtext.ScrolledText(self.result_frame, height=10)
                self.result_text.pack(fill='both', expand=True, padx=5, pady=5)
                
            def setup_main_queries_tab(self):
                # Consulta 1
                ttk.Label(self.main_queries_tab, text="1. Porcentagem de vitórias/derrotas com carta específica").grid(row=0, column=0, sticky='w', padx=5, pady=5)
                
                self.card_name_var = tk.StringVar()
                ttk.Entry(self.main_queries_tab, textvariable=self.card_name_var, width=20).grid(row=0, column=1, padx=5, pady=5)
                
                ttk.Label(self.main_queries_tab, text="Data início:").grid(row=0, column=2, padx=5, pady=5)
                self.start_date_var1 = tk.StringVar(value="2024-01-01")
                ttk.Entry(self.main_queries_tab, textvariable=self.start_date_var1, width=10).grid(row=0, column=3, padx=5, pady=5)
                
                ttk.Label(self.main_queries_tab, text="Data fim:").grid(row=0, column=4, padx=5, pady=5)
                self.end_date_var1 = tk.StringVar(value="2024-12-31")
                ttk.Entry(self.main_queries_tab, textvariable=self.end_date_var1, width=10).grid(row=0, column=5, padx=5, pady=5)
                
                ttk.Button(self.main_queries_tab, text="Executar", command=self.execute_query1).grid(row=0, column=6, padx=5, pady=5)
                
                # Consulta 2
                ttk.Label(self.main_queries_tab, text="2. Decks com alta taxa de vitória (%)").grid(row=1, column=0, sticky='w', padx=5, pady=5)
                
                self.min_win_percentage_var = tk.DoubleVar(value=60.0)
                ttk.Entry(self.main_queries_tab, textvariable=self.min_win_percentage_var, width=5).grid(row=1, column=1, padx=5, pady=5)
                
                ttk.Label(self.main_queries_tab, text="Data início:").grid(row=1, column=2, padx=5, pady=5)
                self.start_date_var2 = tk.StringVar(value="2024-01-01")
                ttk.Entry(self.main_queries_tab, textvariable=self.start_date_var2, width=10).grid(row=1, column=3, padx=5, pady=5)
                
                ttk.Label(self.main_queries_tab, text="Data fim:").grid(row=1, column=4, padx=5, pady=5)
                self.end_date_var2 = tk.StringVar(value="2024-12-31")
                ttk.Entry(self.main_queries_tab, textvariable=self.end_date_var2, width=10).grid(row=1, column=5, padx=5, pady=5)
                
                ttk.Button(self.main_queries_tab, text="Executar", command=self.execute_query2).grid(row=1, column=6, padx=5, pady=5)
                
                # Consulta 3
                ttk.Label(self.main_queries_tab, text="3. Derrotas com combo de cartas").grid(row=2, column=0, sticky='w', padx=5, pady=5)
                
                self.card_combo_var = tk.StringVar()
                ttk.Entry(self.main_queries_tab, textvariable=self.card_combo_var, width=30).grid(row=2, column=1, columnspan=2, padx=5, pady=5)
                
                ttk.Label(self.main_queries_tab, text="Data início:").grid(row=2, column=3, padx=5, pady=5)
                self.start_date_var3 = tk.StringVar(value="2024-01-01")
                ttk.Entry(self.main_queries_tab, textvariable=self.start_date_var3, width=10).grid(row=2, column=4, padx=5, pady=5)
                
                ttk.Label(self.main_queries_tab, text="Data fim:").grid(row=2, column=5, padx=5, pady=5)
                self.end_date_var3 = tk.StringVar(value="2024-12-31")
                ttk.Entry(self.main_queries_tab, textvariable=self.end_date_var3, width=10).grid(row=2, column=6, padx=5, pady=5)
                
                ttk.Button(self.main_queries_tab, text="Executar", command=self.execute_query3).grid(row=2, column=7, padx=5, pady=5)
                
                # Consulta 4
                ttk.Label(self.main_queries_tab, text="4. Vitórias com carta X quando vencedor tem menos troféus (%)").grid(row=3, column=0, sticky='w', padx=5, pady=5)
                
                self.card_name_var4 = tk.StringVar()
                ttk.Entry(self.main_queries_tab, textvariable=self.card_name_var4, width=20).grid(row=3, column=1, padx=5, pady=5)
                
                self.trophy_diff_var = tk.DoubleVar(value=15.0)
                ttk.Entry(self.main_queries_tab, textvariable=self.trophy_diff_var, width=5).grid(row=3, column=2, padx=5, pady=5)
                
                ttk.Label(self.main_queries_tab, text="Data início:").grid(row=3, column=3, padx=5, pady=5)
                self.start_date_var4 = tk.StringVar(value="2024-01-01")
                ttk.Entry(self.main_queries_tab, textvariable=self.start_date_var4, width=10).grid(row=3, column=4, padx=5, pady=5)
                
                ttk.Label(self.main_queries_tab, text="Data fim:").grid(row=3, column=5, padx=5, pady=5)
                self.end_date_var4 = tk.StringVar(value="2024-12-31")
                ttk.Entry(self.main_queries_tab, textvariable=self.end_date_var4, width=10).grid(row=3, column=6, padx=5, pady=5)
                
                ttk.Button(self.main_queries_tab, text="Executar", command=self.execute_query4).grid(row=3, column=7, padx=5, pady=5)
                
                # Consulta 5
                ttk.Label(self.main_queries_tab, text="5. Melhores combos de N cartas com vitória > Y%").grid(row=4, column=0, sticky='w', padx=5, pady=5)
                
                self.combo_size_var = tk.IntVar(value=3)
                ttk.Entry(self.main_queries_tab, textvariable=self.combo_size_var, width=3).grid(row=4, column=1, padx=5, pady=5)
                
                self.min_win_percentage_var5 = tk.DoubleVar(value=60.0)
                ttk.Entry(self.main_queries_tab, textvariable=self.min_win_percentage_var5, width=5).grid(row=4, column=2, padx=5, pady=5)
                
                ttk.Label(self.main_queries_tab, text="Data início:").grid(row=4, column=3, padx=5, pady=5)
                self.start_date_var5 = tk.StringVar(value="2024-01-01")
                ttk.Entry(self.main_queries_tab, textvariable=self.start_date_var5, width=10).grid(row=4, column=4, padx=5, pady=5)
                
                ttk.Label(self.main_queries_tab, text="Data fim:").grid(row=4, column=5, padx=5, pady=5)
                self.end_date_var5 = tk.StringVar(value="2024-12-31")
                ttk.Entry(self.main_queries_tab, textvariable=self.end_date_var5, width=10).grid(row=4, column=6, padx=5, pady=5)
                
                ttk.Button(self.main_queries_tab, text="Executar", command=self.execute_query5).grid(row=4, column=7, padx=5, pady=5)
                
            def setup_extra_queries_tab(self):
                # Consulta Extra 1
                ttk.Label(self.extra_queries_tab, text="Extra 1. Cartas mais usadas").grid(row=0, column=0, sticky='w', padx=5, pady=5)
                
                ttk.Label(self.extra_queries_tab, text="Data início:").grid(row=0, column=1, padx=5, pady=5)
                self.start_date_var_e1 = tk.StringVar(value="2024-01-01")
                ttk.Entry(self.extra_queries_tab, textvariable=self.start_date_var_e1, width=10).grid(row=0, column=2, padx=5, pady=5)
                
                ttk.Label(self.extra_queries_tab, text="Data fim:").grid(row=0, column=3, padx=5, pady=5)
                self.end_date_var_e1 = tk.StringVar(value="2024-12-31")
                ttk.Entry(self.extra_queries_tab, textvariable=self.end_date_var_e1, width=10).grid(row=0, column=4, padx=5, pady=5)
                
                ttk.Button(self.extra_queries_tab, text="Executar", command=self.execute_extra_query1).grid(row=0, column=5, padx=5, pady=5)
                
                # Consulta Extra 2
                ttk.Label(self.extra_queries_tab, text="Extra 2. Taxa de vitória por jogador (min. batalhas)").grid(row=1, column=0, sticky='w', padx=5, pady=5)
                
                self.min_battles_var = tk.IntVar(value=10)
                ttk.Entry(self.extra_queries_tab, textvariable=self.min_battles_var, width=5).grid(row=1, column=1, padx=5, pady=5)
                
                ttk.Button(self.extra_queries_tab, text="Executar", command=self.execute_extra_query2).grid(row=1, column=2, padx=5, pady=5)
                
                # Consulta Extra 3
                ttk.Label(self.extra_queries_tab, text="Extra 3. Taxa de vitória por carta na arena").grid(row=2, column=0, sticky='w', padx=5, pady=5)
                
                self.arena_var = tk.StringVar(value="Arena 12")
                ttk.Entry(self.extra_queries_tab, textvariable=self.arena_var, width=10).grid(row=2, column=1, padx=5, pady=5)
                
                ttk.Label(self.extra_queries_tab, text="Data início:").grid(row=2, column=2, padx=5, pady=5)
                self.start_date_var_e3 = tk.StringVar(value="2024-01-01")
                ttk.Entry(self.extra_queries_tab, textvariable=self.start_date_var_e3, width=10).grid(row=2, column=3, padx=5, pady=5)
                
                ttk.Label(self.extra_queries_tab, text="Data fim:").grid(row=2, column=4, padx=5, pady=5)
                self.end_date_var_e3 = tk.StringVar(value="2024-12-31")
                ttk.Entry(self.extra_queries_tab, textvariable=self.end_date_var_e3, width=10).grid(row=2, column=5, padx=5, pady=5)
                
                ttk.Button(self.extra_queries_tab, text="Executar", command=self.execute_extra_query3).grid(row=2, column=6, padx=5, pady=5)
            
            # Métodos para executar as consultas
            def execute_query1(self):
                card_name = self.card_name_var.get()
                start_date = self.start_date_var1.get()
                end_date = self.end_date_var1.get()
                
                if not card_name:
                    messagebox.showerror("Erro", "Por favor, insira o nome de uma carta")
                    return
                    
                try:
                    result = self.db.win_loss_percentage_by_card(card_name, start_date, end_date)
                    self.display_result(f"Porcentagem de vitórias/derrotas com a carta {card_name}:\n"
                                    f"Vitórias: {result.get('win_percentage', 0):.2f}%\n"
                                    f"Derrotas: {result.get('loss_percentage', 0):.2f}%")
                except Exception as e:
                    messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
            
            def execute_query2(self):
                min_win_percentage = self.min_win_percentage_var.get()
                start_date = self.start_date_var2.get()
                end_date = self.end_date_var2.get()
                
                try:
                    results = self.db.high_winrate_decks(min_win_percentage, start_date, end_date)
                    output = "Decks com alta taxa de vitória:\n"
                    for res in results:
                        output += f"\nDeck: {', '.join(res['_id'])}\n"
                        output += f"Taxa de vitória: {res.get('win_percentage', 0):.2f}%\n"
                        output += f"Total de partidas: {res.get('total', 0)}\n"
                    
                    self.display_result(output)
                except Exception as e:
                    messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
            
            def execute_query3(self):
                card_combo = [card.strip() for card in self.card_combo_var.get().split(',')]
                start_date = self.start_date_var3.get()
                end_date = self.end_date_var3.get()
                
                if not card_combo or not any(card_combo):
                    messagebox.showerror("Erro", "Por favor, insira um combo de cartas (separado por vírgulas)")
                    return
                    
                try:
                    loss_count = self.db.loss_count_by_combo(card_combo, start_date, end_date)
                    self.display_result(f"Total de derrotas com o combo {', '.join(card_combo)}: {loss_count}")
                except Exception as e:
                    messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
            
            def execute_query4(self):
                card_name = self.card_name_var4.get()
                trophy_diff = self.trophy_diff_var.get()
                start_date = self.start_date_var4.get()
                end_date = self.end_date_var4.get()
                
                if not card_name:
                    messagebox.showerror("Erro", "Por favor, insira o nome de uma carta")
                    return
                    
                try:
                    win_count = self.db.wins_with_card_underdog(card_name, trophy_diff, start_date, end_date)
                    self.display_result(f"Vitórias com a carta {card_name} quando o vencedor tinha {trophy_diff}% menos troféus: {win_count}")
                except Exception as e:
                    messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
            
            def execute_query5(self):
                combo_size = self.combo_size_var.get()
                min_win_percentage = self.min_win_percentage_var5.get()
                start_date = self.start_date_var5.get()
                end_date = self.end_date_var5.get()
                
                try:
                    results = self.db.best_card_combos(combo_size, min_win_percentage, start_date, end_date)
                    output = f"Melhores combos de {combo_size} cartas (vitória > {min_win_percentage}%):\n"
                    for res in results:
                        output += f"\nCarta: {res['_id']}\n"
                        output += f"Taxa de vitória: {res.get('win_rate', 0)*100:.2f}%\n"
                    
                    self.display_result(output)
                except Exception as e:
                    messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
            
            def execute_extra_query1(self):
                start_date = self.start_date_var_e1.get()
                end_date = self.end_date_var_e1.get()
                
                try:
                    results = self.db.most_used_cards(start_date, end_date)
                    output = "Cartas mais usadas:\n"
                    for res in results:
                        output += f"\nCarta: {res['_id']}\n"
                        output += f"Usos: {res.get('usage_count', 0)}\n"
                    
                    self.display_result(output)
                    
                    # Mostrar gráfico
                    self.show_chart(
                        [res['_id'] for res in results],
                        [res['usage_count'] for res in results],
                        "Cartas mais usadas",
                        "Cartas",
                        "Número de usos"
                    )
                except Exception as e:
                    messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
            
            def execute_extra_query2(self):
                min_battles = self.min_battles_var.get()
                
                try:
                    results = self.db.player_win_rates(min_battles)
                    output = f"Taxa de vitória por jogador (min. {min_battles} batalhas):\n"
                    for res in results:
                        output += f"\nJogador: {res['_id']}\n"
                        output += f"Taxa de vitória: {res.get('win_rate', 0)*100:.2f}%\n"
                        output += f"Total de batalhas: {res.get('total_battles', 0)}\n"
                    
                    self.display_result(output)
                except Exception as e:
                    messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
            
            def execute_extra_query3(self):
                arena = self.arena_var.get()
                start_date = self.start_date_var_e3.get()
                end_date = self.end_date_var_e3.get()
                
                try:
                    results = self.db.card_win_rates_by_arena(arena, start_date, end_date)
                    output = f"Taxa de vitória por carta na arena {arena}:\n"
                    for res in results:
                        output += f"\nCarta: {res['_id']}\n"
                        output += f"Taxa de vitória: {res.get('win_rate', 0)*100:.2f}%\n"
                        output += f"Total de usos: {res.get('total_uses', 0)}\n"
                    
                    self.display_result(output)
                except Exception as e:
                    messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
            
            def display_result(self, text):
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, text)
            
            def show_chart(self, labels, values, title, xlabel, ylabel):
                # Cria uma nova janela para o gráfico
                chart_window = tk.Toplevel(self.root)
                chart_window.title(title)
                
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.bar(labels, values)
                ax.set_title(title)
                ax.set_xlabel(xlabel)
                ax.set_ylabel(ylabel)
                plt.xticks(rotation=45)
                
                canvas = FigureCanvasTkAgg(fig, master=chart_window)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
            # Substitua pela sua URI do MongoDB
                MONGO_URI = "mongodb+srv://admin:admin@cluster0.sargdmz.mongodb.net/"
                root = tk.Tk()
                db = ClashRoyaleAnalytics(MONGO_URI)
                app = AnalyticsGUI(root, db)
                root.mainloop()