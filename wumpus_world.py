import os

class WumpusGameFull:
    def __init__(self):
        self.size = 4
        # 4x4 Izgara 
        self.grid = [['-' for _ in range(self.size)] for _ in range(self.size)]
        
        # --- HARİTA AYARLARI ---
        self.agent_pos = [3, 0] # Başlangıç (1,1)
        self.grid[1][0] = 'W'   # Wumpus (Konum: 3,1)
        self.grid[3][2] = 'P'   # Çukur
        self.grid[0][3] = 'P'   # Çukur
        self.grid[2][2] = 'P'   # Çukur
        self.grid[1][1] = 'G'   # Altın (Konum: 3,2)
        # -----------------------

        self.game_over = False
        self.has_arrow = True      # Tek ok hakkı
        self.wumpus_alive = True   # Wumpus canlı mı?
        self.has_gold = False      # Altını aldık mı?
        
        self.visited = set()
        self.safe_squares = set()
        self.suspected_pits = set()
        self.suspected_wumpus = set()
        
        self.visited.add(tuple(self.agent_pos))
        self.safe_squares.add(tuple(self.agent_pos))

    def get_percepts(self, r, c):
        percepts = []
        current_obj = self.grid[r][c]
        
        # Ölüm Kontrolü
        if current_obj == 'P':
            self.game_over = True
            return ["ÖLÜM (Çukura Düştün!)"]
        elif current_obj == 'W' and self.wumpus_alive:
            self.game_over = True
            return ["ÖLÜM (Wumpus seni yedi!)"]
        elif current_obj == 'G':
            percepts.append("Parıltı") # Altın varsa parlar

        # Komşulardan gelen algılar
        neighbors = self.get_neighbors(r, c)
        for nr, nc in neighbors:
            if self.grid[nr][nc] == 'P':
                if "Esinti" not in percepts: percepts.append("Esinti")
            # Wumpus sadece yaşıyorsa koku yayar
            if self.grid[nr][nc] == 'W' and self.wumpus_alive:
                if "Koku" not in percepts: percepts.append("Koku")
        
        return percepts if percepts else ["Hiçbir şey"]

    def get_neighbors(self, r, c):
        neighbors = []
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)] 
        for dr, dc in moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbors.append((nr, nc))
        return neighbors

    def shoot_arrow(self):
        if not self.has_arrow:
            print(">> HATA: Okun kalmadı! Daha önce kullandın.")
            return

        direction = input("Ok atmak için yön seçin (W/A/S/D): ").upper()
        self.has_arrow = False # Oku harca
        print(">> Ok fırlatıldı...")

        # Hedef koordinatı (Sadece bitişik kareye atıyoruz varsayalım)
        r, c = self.agent_pos
        tr, tc = r, c
        
        if direction == 'W': tr -= 1
        elif direction == 'S': tr += 1
        elif direction == 'A': tc -= 1
        elif direction == 'D': tc += 1
        
        # Wumpus'u vurduk mu?
        if 0 <= tr < self.size and 0 <= tc < self.size:
            if self.grid[tr][tc] == 'W':
                self.wumpus_alive = False
                self.grid[tr][tc] = '-' # Wumpus öldü
                print("\n*** ÇIĞLIK DUYULDU! (Wumpus'u öldürdün!) ***")
                # Bildiğimiz şüpheli wumpus yerlerini temizle
                self.suspected_wumpus.clear()
            else:
                print(">> Iska! Ok duvara veya boşluğa gitti.")
        else:
             print(">> Iska! Ok duvara çarptı.")

    def grab_gold(self):
        r, c = self.agent_pos
        if self.grid[r][c] == 'G':
            self.has_gold = True
            self.grid[r][c] = '-' # Altın artık yerde değil
            print("\n*** ALTINI ALDIN! (Çantana eklendi) ***") #
        
            print("*** OYUNU KAZANDIN! ***")
            self.game_over = True
        else:
            print(">> Burada alınacak altın yok!")

    def make_inference(self, r, c, percepts):
        logic_pos = (4-r, c+1)
        print(f"\n--- MANTIK MOTORU (Konum: {logic_pos}) ---")
        
        neighbors = self.get_neighbors(r, c)
        logic_neighbors = [(4-nr, nc+1) for nr, nc in neighbors]

        # Temiz alan analizi
        if "Esinti" not in percepts and "Koku" not in percepts and "ÖLÜM" not in percepts[0]:
            print(f"--> ÇIKARIM: Burası temiz. Komşular {logic_neighbors} GÜVENLİ.")
            for n in neighbors:
                self.safe_squares.add(n)
                if n in self.suspected_pits: self.suspected_pits.remove(n)
                if n in self.suspected_wumpus: self.suspected_wumpus.remove(n)

        # Çukur analizi
        if "Esinti" in percepts:
            print("--> ÇIKARIM: Esinti var -> Komşularda ÇUKUR olabilir.")
            possible_pits = [n for n in neighbors if n not in self.safe_squares]
            for p in possible_pits: self.suspected_pits.add(p)
            logic_pits = [(4-x, y+1) for x, y in possible_pits]
            print(f"    Şüpheli Çukurlar: {logic_pits}")

        # Wumpus analizi
        if "Koku" in percepts:
            print("--> ÇIKARIM: Koku var -> Komşularda WUMPUS olabilir.")
            possible_wumpus = [n for n in neighbors if n not in self.safe_squares]
            for w in possible_wumpus: self.suspected_wumpus.add(w)
            logic_wumpus = [(4-x, y+1) for x, y in possible_wumpus]
            print(f"    Şüpheli Wumpus: {logic_wumpus}")
            
            if self.has_arrow:
                print("!!! ÖNERİ: Wumpus yakınlarda. 'F' tuşu ile ok atabilirsin!")

    def display_map(self):
        print("\n--- OYUN ALANI ---")
        for r in range(self.size):
            row_str = ""
            for c in range(self.size):
                if r == self.agent_pos[0] and c == self.agent_pos[1]:
                    row_str += "[A] "
                elif (r, c) in self.visited:
                    char = self.grid[r][c]
                    if char == 'W' and not self.wumpus_alive: char = 'x' # Ölü Wumpus
                    row_str += f" {char}  "
                else:
                    row_str += " ?  "
            print(row_str)
        print(f"Durum: Ok={'VAR' if self.has_arrow else 'YOK'} | Altın={'VAR' if self.has_gold else 'YOK'}")
        print("------------------")

    def play(self):
        print("Wumpus World")
        print("Hareket: W, A, S, D")
        print("Aksiyon: F (Ok At), G (Altını Al)")
        
        while not self.game_over:
            r, c = self.agent_pos
            self.visited.add((r, c))
            self.safe_squares.add((r, c))
            
            self.display_map()
            
            percepts = self.get_percepts(r, c)
            print(f"Algı: {percepts}")
            
            if self.game_over:
                print("\n*** OYUN BİTTİ ***")
                break

            self.make_inference(r, c, percepts)
            
           
            cmd = input("\nKomut (Yürü: W/A/S/D | Ok At: F | Altın Al: G): ").upper()
            
            if cmd == 'F':
                self.shoot_arrow()
            elif cmd == 'G':
                self.grab_gold()
            elif cmd in ['W', 'A', 'S', 'D']:
                nr, nc = r, c
                if cmd == 'W': nr -= 1
                elif cmd == 'S': nr += 1
                elif cmd == 'A': nc -= 1
                elif cmd == 'D': nc += 1
                
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    self.agent_pos = [nr, nc]
                else:
                    print(">> Duvara çarptın!")
            else:
                print(">> Geçersiz komut.")

# Oyunu Başlat
game = WumpusGameFull()
game.play()