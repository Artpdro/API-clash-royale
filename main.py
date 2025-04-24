import tkinter as tk
from tkinter import ttk, messagebox
from coletor import connect_db
from pymongo import MongoClient
from datetime import datetime

class ClashRoyaleAnalytics:
    def __init__(self, root):
        self.root = root
        self.root.title("Clash Royale Analytics")
        self.client, self.db = connect_db("mongodb+srv://admin:admin@cluster0.sargdmz.mongodb.net/")
        
        self.notebook = ttk.Notebook(self.root)
        self.tabs = [ttk.Frame(self.notebook) for _ in range(8)]
        self.create_widgets()
        
    def create_widgets(self):
        titles = [
            "1. Vitórias/Derrotas por Carta",
            "2. Decks de Alta Vitória",
            "3. Derrotas por Combo",
            "4. Vitórias Desbalanceadas",
            "5. Combos Vencedores",
            "6. Cartas de Alto Nível",
            "7. Troféus vs Vitórias",
            "8. Horários de Pico"
        ]
        
        for i in range(8):
            self.notebook.add(self.tabs[i], text=titles[i])
            getattr(self, f'create_query{i+1}_widgets')()
        
        self.notebook.pack(expand=1, fill="both")

    def get_card_id(self, card_name):
        card = self.db.cards.find_one({"name": {"$regex": f"^{card_name}$", "$options": "i"}})
        return card["id"] if card else None
    
    def _convert_date(self, date_str):
        """Converte 'YYYY-MM-DD' para o formato 'YYYYMMDD' usado no battleTime"""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d")
        except ValueError:
            raise ValueError("Formato de data inválido. Use YYYY-MM-DD")
        
    def _parse_date_filter(self, date_str, field_name):
        """Converte YYYY-MM-DD para o formato do campo no banco (date ou battleTime)"""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if field_name == "date":
                return dt.strftime("%Y/%m/%d")  # Formato do campo 'date'
            elif field_name == "battleTime":
                return dt.strftime("%Y%m%d") + "T000000.000Z"  # Formato inicial do battleTime
        except ValueError:
            raise ValueError(f"Data inválida: {date_str}")

    # Consulta 1 
    def create_query1_widgets(self):
        frame = self.tabs[0]
        
        tk.Label(frame, text="Nome da Carta:").grid(row=0, column=0, padx=5, pady=5)
        self.q1_card = tk.Entry(frame)
        self.q1_card.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Data Início (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5)
        self.q1_start = tk.Entry(frame)
        self.q1_start.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Data Fim (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5)
        self.q1_end = tk.Entry(frame)
        self.q1_end.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Button(frame, text="Calcular", command=self.run_query1).grid(row=3, column=0, columnspan=2, pady=10)
        
        self.q1_result = tk.Text(frame, height=8, width=60)
        self.q1_result.grid(row=4, column=0, columnspan=2, padx=10)

    def run_query1(self):
        card_name = self.q1_card.get().strip()
        card_id = self.get_card_id(card_name)
        if not card_id:
            messagebox.showerror("Erro", f"Carta '{card_name}' não encontrada!")
            return

        try:
            start_ts = int(datetime.strptime(self.q1_start.get(), "%Y-%m-%d").timestamp())
            end_ts = int(datetime.strptime(self.q1_end.get(), "%Y-%m-%d").timestamp())
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido!")
            return

        pipeline = [
            {"$match": {
                "team.cards.id": card_id,
                "timestampSeconds": {"$gte": start_ts, "$lte": end_ts}
            }},
            {"$facet": {
                "vitorias": [{"$match": {"$expr": {"$eq": ["$winner", "$playerTag"]}}}],
                "derrotas": [{"$match": {"$expr": {"$ne": ["$winner", "$playerTag"]}}}]
            }},
            {"$project": {
                "total_vitorias": {"$size": "$vitorias"},
                "total_derrotas": {"$size": "$derrotas"},
                "total": {"$add": [{"$size": "$vitorias"}, {"$size": "$derrotas"}]}
            }},
            {"$project": {
                "win_rate": {"$multiply": [{"$divide": ["$total_vitorias", "$total"]}, 100]},
                "loss_rate": {"$multiply": [{"$divide": ["$total_derrotas", "$total"]}, 100]}
            }}
        ]
        
        result = list(self.db.battles.aggregate(pipeline))[0]
        self.q1_result.delete(1.0, tk.END)
        self.q1_result.insert(tk.END, 
            f"Vitórias: {result['win_rate']:.2f}%\n"
            f"Derrotas: {result['loss_rate']:.2f}%\n"
            f"Total de Partidas: {result['win_rate'] + result['loss_rate']:.0f}")

    # Consulta 2
    def create_query2_widgets(self):
        frame = self.tabs[1]
        
        tk.Label(frame, text="% Mínima de Vitórias:").grid(row=0, column=0, padx=5, pady=5)
        self.q2_min_win = tk.Entry(frame)
        self.q2_min_win.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Data Início (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5)
        self.q2_start = tk.Entry(frame)
        self.q2_start.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Data Fim (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5)
        self.q2_end = tk.Entry(frame)
        self.q2_end.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Button(frame, text="Buscar Decks", command=self.run_query2).grid(row=3, column=0, columnspan=2, pady=10)
        
        self.q2_result = tk.Text(frame, height=15, width=70)
        self.q2_result.grid(row=4, column=0, columnspan=2, padx=10)

    def run_query2(self):
        try:
            min_win = float(self.q2_min_win.get())
            start_date = self._convert_date(self.q2_start.get())
            end_date = self._convert_date(self.q2_end.get())
        except Exception as e:
            messagebox.showerror("Erro", f"Dados inválidos: {str(e)}")
            return

        pipeline = [
            {"$match": {
                "battleTime": {
                    "$gte": f"{start_date}T000000.000Z",
                    "$lte": f"{end_date}T235959.999Z"
                }
            }},
            {"$unwind": "$team"},
            {"$unwind": "$team.cards"},
            {"$group": {
                "_id": "$team.cards.id",
                "total_partidas": {"$sum": 1},
                "vitorias": {"$sum": {"$cond": [{"$eq": ["$winner", "$playerTag"]}, 1, 0]}}
            }},
            {"$project": {
                "win_rate": {
                    "$cond": [
                        {"$eq": ["$total_partidas", 0]},
                        0,
                        {"$multiply": [{"$divide": ["$vitorias", "$total_partidas"]}, 100]}
                    ]
                },
                "card_id": "$_id",
                "_id": 0
            }},
            {"$match": {"win_rate": {"$gt": min_win}}},
            {"$lookup": {
                "from": "cards",
                "localField": "card_id",
                "foreignField": "id",
                "as": "card_info"
            }},
            {"$unwind": "$card_info"},
            {"$sort": {"win_rate": -1}}
        ]

        try:
            results = list(self.db.battles.aggregate(pipeline))
            self.q2_result.delete(1.0, tk.END)
            for res in results:
                self.q2_result.insert(tk.END, 
                    f"Carta: {res['card_info']['name']}\n"
                    f"Taxa de Vitória: {res['win_rate']:.2f}%\n"
                    "─"*50 + "\n")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # Consulta 3
    def create_query3_widgets(self):
        frame = self.tabs[2]
        
        tk.Label(frame, text="Combos (Nomes separados por vírgula):").grid(row=0, column=0, padx=5, pady=5)
        self.q3_combo = tk.Entry(frame)
        self.q3_combo.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Data Início (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5)
        self.q3_start = tk.Entry(frame)
        self.q3_start.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Data Fim (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5)
        self.q3_end = tk.Entry(frame)
        self.q3_end.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Button(frame, text="Calcular Derrotas", command=self.run_query3).grid(row=3, column=0, columnspan=2, pady=10)
        
        self.q3_result = tk.Text(frame, height=8, width=60)
        self.q3_result.grid(row=4, column=0, columnspan=2, padx=10)

    def run_query3(self):
        try:
            card_names = [x.strip() for x in self.q3_combo.get().split(",")]
            card_ids = []
            for name in card_names:
                card_id = self.get_card_id(name)
                if not card_id:
                    messagebox.showerror("Erro", f"Carta '{name}' não encontrada!")
                    return
                card_ids.append(card_id)
                
            start_ts = int(datetime.strptime(self.q3_start.get(), "%Y-%m-%d").timestamp())
            end_ts = int(datetime.strptime(self.q3_end.get(), "%Y-%m-%d").timestamp())
        except ValueError:
            messagebox.showerror("Erro", "Dados inválidos!")
            return

        pipeline = [
            {"$match": {
                "timestampSeconds": {"$gte": start_ts, "$lte": end_ts},
                "team.cards.id": {"$all": card_ids}
            }},
            {"$count": "total_derrotas"}
        ]
        
        result = list(self.db.battles.aggregate(pipeline))
        total = result[0]["total_derrotas"] if result else 0
        self.q3_result.delete(1.0, tk.END)
        self.q3_result.insert(tk.END, f"Total de Derrotas com o Combo: {total}")

    # Consulta 4
    def create_query4_widgets(self):
        frame = self.tabs[3]
        
        tk.Label(frame, text="Nome da Carta:").grid(row=0, column=0, padx=5, pady=5)
        self.q4_card = tk.Entry(frame)
        self.q4_card.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="% Troféus Inferiores:").grid(row=1, column=0, padx=5, pady=5)
        self.q4_trophy_percent = tk.Entry(frame)
        self.q4_trophy_percent.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Button(frame, text="Buscar", command=self.run_query4).grid(row=2, column=0, columnspan=2, pady=10)
        
        self.q4_result = tk.Text(frame, height=8, width=60)
        self.q4_result.grid(row=3, column=0, columnspan=2, padx=10)

    def run_query4(self):
        try:
            card_name = self.q4_card.get().strip()
            card_id = self.get_card_id(card_name)
            if not card_id:
                messagebox.showerror("Erro", f"Carta '{card_name}' não encontrada!")
                return
            
            z_percent = float(self.q4_trophy_percent.get()) / 100
        except Exception as e:
            messagebox.showerror("Erro", f"Dados inválidos: {str(e)}")
            return

        pipeline = [
            {"$match": {
                "team.cards.id": card_id,
                "winner": {"$exists": True},
                "$expr": {
                    "$and": [
                        {"$eq": ["$winner", "$playerTag"]},
                        {"$lte": [
                            {"$multiply": [
                                {"$toInt": {"$arrayElemAt": ["$opponent.0.startingTrophies", 0]}},
                                z_percent
                            ]},
                            {"$toInt": {"$arrayElemAt": ["$team.0.startingTrophies", 0]}}
                        ]}
                    ]
                }
            }},
            {"$count": "total_vitorias"}
        ]

        try:
            result = list(self.db.battles.aggregate(pipeline))
            total = result[0]["total_vitorias"] if result else 0
            self.q4_result.delete(1.0, tk.END)
            self.q4_result.insert(tk.END, f"Vitórias em condições especiais: {total}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # Consulta 5
    def create_query5_widgets(self):
        frame = self.tabs[4]
        
        tk.Label(frame, text="Tamanho do Combo:").grid(row=0, column=0, padx=5, pady=5)
        self.q5_n = tk.Entry(frame)
        self.q5_n.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="% Mínima de Vitórias:").grid(row=1, column=0, padx=5, pady=5)
        self.q5_min_win = tk.Entry(frame)
        self.q5_min_win.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Data Início (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5)
        self.q5_start = tk.Entry(frame)
        self.q5_start.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Data Fim (YYYY-MM-DD):").grid(row=3, column=0, padx=5, pady=5)
        self.q5_end = tk.Entry(frame)
        self.q5_end.grid(row=3, column=1, padx=5, pady=5)
        
        tk.Button(frame, text="Buscar Combos", command=self.run_query5).grid(row=4, column=0, columnspan=2, pady=10)
        
        self.q5_result = tk.Text(frame, height=15, width=70)
        self.q5_result.grid(row=5, column=0, columnspan=2, padx=10)

    def run_query5(self):
        try:
            n = int(self.q5_n.get())
            min_win = float(self.q5_min_win.get())
            start_date = self._parse_date_filter(self.q5_start.get(), "date")
            end_date = self._parse_date_filter(self.q5_end.get(), "date")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return

        pipeline = [
            {"$match": {
                "date": {"$gte": start_date, "$lte": end_date},
                "team.cards.id": {"$exists": True},
                "$expr": {"$eq": [{"$size": "$team.cards.id"}, 8]}
            }},
            {"$addFields": {"combo": "$team.cards.id"}},
            {"$unwind": "$combo"},
            {"$group": {
                "_id": {"battle_id": "$_id", "combo": "$combo"},
                "vitorias": {"$first": {"$cond": [{"$eq": ["$winner", "$playerTag"]}, 1, 0]}}
            }},
            {"$group": {
                "_id": "$_id.combo",
                "total": {"$sum": 1},
                "vitorias": {"$sum": "$vitorias"}
            }},
            {"$project": {
                "win_rate": {
                    "$cond": [
                        {"$eq": ["$total", 0]},
                        0,
                        {"$multiply": [{"$divide": ["$vitorias", "$total"]}, 100]}
                    ]
                },
                "combo_size": {"$size": "$_id"}
            }},
            {"$match": {"win_rate": {"$gt": min_win}, "combo_size": n}},
            {"$lookup": {
                "from": "cards",
                "localField": "_id",
                "foreignField": "id",
                "as": "nomes_cartas"
            }},
            {"$unwind": "$nomes_cartas"},
            {"$group": {
                "_id": "$_id",
                "win_rate": {"$first": "$win_rate"},
                "nomes": {"$push": "$nomes_cartas.name"}
            }},
            {"$sort": {"win_rate": -1}}
        ]

        try:
            results = list(self.db.battles.aggregate(pipeline))
            self.q5_result.delete(1.0, tk.END)
            
            if not results:
                self.q5_result.insert(tk.END, "Nenhum combo encontrado.")
                return

            for res in results:
                combo_nomes = ", ".join(res["nomes"])
                self.q5_result.insert(tk.END, 
                    f"Combo ({n} cartas): {combo_nomes}\n"
                    f"Taxa de Vitória: {res['win_rate']:.2f}%\n"
                    "─"*50 + "\n")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # Consulta 6
    def create_query6_widgets(self):
        frame = self.tabs[5]
        
        tk.Label(frame, text="Troféus Mínimos:").grid(row=0, column=0, padx=5, pady=5)
        self.q6_min_trophies = tk.Entry(frame)
        self.q6_min_trophies.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(frame, text="Buscar", command=self.run_query6).grid(row=1, column=0, columnspan=2, pady=10)
        
        self.q6_result = tk.Text(frame, height=10, width=60)
        self.q6_result.grid(row=2, column=0, columnspan=2, padx=10)

    def run_query6(self):
        try:
            min_trophies = int(self.q6_min_trophies.get())
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido!")
            return

        pipeline = [
            {"$match": {
                "team.startingTrophies": {"$gte": min_trophies}
            }},
            {"$unwind": "$team"},
            {"$unwind": "$team.cards"},
            {"$group": {
                "_id": "$team.cards.id", 
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10},
            {"$lookup": {
                "from": "cards",
                "localField": "_id",
                "foreignField": "id",
                "as": "card_info"
            }},
            {"$unwind": "$card_info"}
        ]

        try:
            results = list(self.db.battles.aggregate(pipeline))
            self.q6_result.delete(1.0, tk.END)
            for res in results:
                self.q6_result.insert(tk.END, 
                    f"Carta: {res['card_info']['name']}\n"
                    f"Usos: {res['count']}\n"
                    "─"*40 + "\n")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # Consulta 7
    def create_query7_widgets(self):
        frame = self.tabs[6]
        
        tk.Label(frame, text="Diferença Mínima de Troféus:").grid(row=0, column=0, padx=5, pady=5)
        self.q7_min_diff = tk.Entry(frame)
        self.q7_min_diff.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(frame, text="Analisar", command=self.run_query7).grid(row=1, column=0, columnspan=2, pady=10)
        
        self.q7_result = tk.Text(frame, height=10, width=60)
        self.q7_result.grid(row=2, column=0, columnspan=2, padx=10)

    def run_query7(self):
        try:
            min_diff = int(self.q7_min_diff.get())
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido!")
            return

        pipeline = [
            {"$match": {"trophyDifference": {"$gte": min_diff}}},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "vitorias": {"$sum": {"$cond": [{"$eq": ["$winner", "$playerTag"]}, 1, 0]}}
            }},
            {"$project": {
                "win_rate": {"$multiply": [{"$divide": ["$vitorias", "$total"]}, 100]}
            }}
        ]
        
        result = list(self.db.battles.aggregate(pipeline))
        self.q7_result.delete(1.0, tk.END)
        if result:
            self.q7_result.insert(tk.END, f"Taxa de Vitórias: {result[0]['win_rate']:.2f}%")
        else:
            self.q7_result.insert(tk.END, "Nenhum dado encontrado")

    # Consulta 8
    def create_query8_widgets(self):
        frame = self.tabs[7]
        
        tk.Button(frame, text="Analisar", command=self.run_query8).grid(row=0, column=0, columnspan=2, pady=10)
        
        self.q8_result = tk.Text(frame, height=10, width=60)
        self.q8_result.grid(row=1, column=0, columnspan=2, padx=10)

    def run_query8(self):
        pipeline = [
            {"$project": {
                "hour": {"$hour": {"$toDate": {"$multiply": ["$timestampSeconds", 1000]}}}
            }},
            {"$group": {
                "_id": "$hour",
                "total_batalhas": {"$sum": 1}
            }},
            {"$sort": {"total_batalhas": -1}},
            {"$limit": 5}
        ]
        
        results = list(self.db.battles.aggregate(pipeline))
        self.q8_result.delete(1.0, tk.END)
        for res in results:
            self.q8_result.insert(tk.END, f"Hora {res['_id']}h: {res['total_batalhas']} batalhas\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = ClashRoyaleAnalytics(root)
    root.mainloop()
