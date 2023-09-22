# autor: František Horázný
# email: fhorazny@seznam.cz
# rok: 2021


import tkinter as tk
import numpy as np
from collections import defaultdict
from random import choices

colToNum = {"red":0,"blue":1, "green":2, "yellow":3, "violet":4, "brown":5, "cyan":6}
numToCol = ["red", "blue", "green", "yellow", "violet", "brown", "cyan"]

P_R = 8  #POINT_RADIUS (velikost nakreslených bodů -> bude se hodit při případném využití ve výuce pro lepší viditelnost koláčových grafů)


class Data():

    # přidá do databáze počáteční stav bodu (souřadnice a jeho zadaná barva)
    def appendPoint(self,x,y,col):
        self.pointsCoor = np.append(self.pointsCoor,[[x,y]],axis = 0)
        self.pointsColor = np.append(self.pointsColor,[col],axis = 0)
    
    # vypíše údaje v databázi
    def printDB(self):
        print("cluster count: ",self.clusterCount)
        print("mids: ",self.middles)
        print("weights: ", self.pointXmidsWeighs)
        print("points colors: ", self.pointsColor)
        print("points coords: ", self.pointsCoor)
        print("value q = ", self.q)
        
    # uvede databázi do počátečního stavu 
    def clearAll(self):
        self.pointsCoor = np.empty((0,2))
        self.pointsColor = np.array([])
        self.middles = {}
        self.pointXmidsWeighs = defaultdict(list)
        self.phase = 0
        self.q = 2.0
    
    # odstraní středy (předchozí výpočet) a k bodům přiřadí náhodnou barvu. počet různých barev bude podle zvoleného počtu v "vysouvacím menu"
    def randomize(self):
        self.reset()
        self.pointsColor = choices(numToCol[:self.clusterCount], k=len(self.pointsColor))
        gui.clearPoints() #smazat všechny body
        gui.drawPoints(self.pointsCoor,self.pointsColor) #překrestlit body
    
    # vrátí výpočet do stavu před prvním stiskem tlačítka step. 
    def reset(self):
        self.phase = 0
        self.middles = {}
        self.pointXmidsWeighs = defaultdict(list)
        
        gui.clearCanvas(clearData=False)
        gui.drawPoints(self.pointsCoor,self.pointsColor)
        
    # změna počtu tříd, se kterými má funkce randomize počítat
    def changeClusterCount(self, newVal):
        self.clusterCount = newVal
        
    def step10(self):
        for i in range(20):
            self.step()
    
    # krok algoritmu fuzzk-means
    # při prvním kroku vypočte "těžiště" bodů stejné barvy (phase == 0)
    # při druhém kroku přepočte náležitost bodů ke každému středu (phase == 1). v této fázi se také přebarvují body do barvi jejich největší náležitosti.
    # při třetím kroku se přepočtou středy s váhovanými body a určí se jako další krok phase = 1
    def step(self):
        if self.phase == 0: #fáze výpočtu středů
            count = defaultdict(int)
            coords = {}
            for i,pointClass in enumerate(self.pointsColor):
                count[pointClass] += 1          # počet bodů určité třídy
                if pointClass not in coords:    # pokud se třída pointClass ještě nedetekovala, přidá se do coords a přičte se vektor bodu
                    coords[pointClass] = np.copy(self.pointsCoor[i])
                else:                           # přičti vektor bodu k určité třídě
                    coords[pointClass] += self.pointsCoor[i]

            for key in count:
                print(key + " -> " + str(count[key]))
                self.middles[key] = coords[key]/count[key]      # vyděl vektor počtem bodů v určité třídě
            
            gui.drawMids(self.middles)      # nakresli vypočtené středy
            self.phase = 1
        elif self.phase == 1:   #fáze přepočtu náležitosti bodů
            bestColors = []     # pole pro uchování ke každému bodu jeho nejlepší příslušnosti (barva, kterou bude mít vizualizovanou
            self.pointXmidsWeighs = defaultdict(list)
            
            for point_i in self.pointsCoor:
                bestC = "red"
                best = 0.0
                for mid_j in self.middles:      # výpočet pro každý bod a každý střed
                    result = 0.0
                    for mid in self.middles:    # suma přes všechny středy
                    
                        # vzorec https://www.fit.vutbr.cz/study/courses/SFC/private/20sfc_9.pdf slide 26
                        tmp = np.linalg.norm(point_i-self.middles[mid_j]+0.0000000001)/ np.linalg.norm(point_i-self.middles[mid]+0.0000000001)
                        tmp = tmp**(2.0/(self.q-1))
                        result += tmp
                    result = 1.0/result
                    if result > best:       # uchování nejlepší hodnoty a barvy
                        best = result
                        bestC = mid_j
                    
                    self.pointXmidsWeighs[mid_j] = np.append(self.pointXmidsWeighs[mid_j],result)       # vytváření matice vah, kam který bod patří (realizovaný slovníkem)
                    
                bestColors.append(bestC)     # list nových barev, které budou vizualizované
                
            
            gui.clearPoints() #smazat všechny body
            if self.isPie:
                gui.drawPieChartPoints(self.pointsCoor,self.pointXmidsWeighs)   #nakreslit body jako koláčový graf
            else:
                gui.drawPoints(self.pointsCoor,bestColors) #nakrestlit body s jejich dominantní třídou
            
            self.phase = 2
        elif self.phase == 2: #přepočty středů
            for mid in self.middles:    #pro každý střed přepočti 
                # vzorec z wikipedie
                sumWeigh = self.pointXmidsWeighs[mid]**self.q
                sumWeigh = sumWeigh.sum()
                self.middles[mid] = (((self.pointXmidsWeighs[mid][:, None]**self.q) * self.pointsCoor)/sumWeigh).sum(axis=0)
            
                # vzorec https://www.fit.vutbr.cz/study/courses/SFC/private/20sfc_9.pdf slide 26
                # sumWeigh = self.pointXmidsWeighs[mid].sum()
                # self.middles[mid] = ((self.pointXmidsWeighs[mid][:, None] * self.pointsCoor)/sumWeigh).sum(axis=0)
            
            gui.clearMids()             #smazat středy
            gui.drawMids(self.middles)  #nakreslit nové přepočtené středy
            
            self.phase = 1 #přepočti náležitosti bodů
            
    # přepne do režimu koláčových grafů (a překreslí aktuální body)
    def piePoints(self):
        self.isPie = not self.isPie
        
        if  self.isPie and set(self.pointXmidsWeighs):
            gui.clearPoints()
            gui.drawPieChartPoints(self.pointsCoor,self.pointXmidsWeighs)
            
        elif not self.isPie and set(self.pointXmidsWeighs):
            bestColors = []    
            for i in range(len(self.pointsCoor)):
                bestC = "red"
                best = 0.0
                for mid in self.pointXmidsWeighs:
                    if self.pointXmidsWeighs[mid][i] > best:       # uchování nejlepší hodnoty a barvy
                        best = self.pointXmidsWeighs[mid][i]
                        bestC = mid                    
                bestColors.append(bestC)

            gui.clearPoints()
            gui.drawPoints(self.pointsCoor,bestColors) #nakrestlit body v barvě jejich dominantní třídy
    
    def __init__(self):
        self.isPie = False
        self.q = 2.0
        self.phase = 0
        self.clusterCount = 2
        self.pointsCoor = np.empty((0,2))
        self.pointsColor = np.array([])
        self.middles = {}
        self.pointXmidsWeighs = defaultdict(list)
        

class Gui():
    # vymaže z canvasu vše namalované a pokud cleardata není False tak i data
    def clearCanvas(self, event=None, clearData = True):
        self.canvas.delete("all")
        if clearData:
            db.clearAll()
    
    # vymaže z canvasu všechny středy
    def clearMids(self, event=None):
        self.canvas.delete("mid")
    
    # vymaže z canvasu všechny body
    def clearPoints(self, event=None):
        self.canvas.delete("point")
    
    # nakreslí středy. mids je slovník, kde klíče jsou barvy a hodnoty jsou souřadnice
    def drawMids(self,mids):
        for key in mids:
            self.canvas.create_rectangle(mids[key][0]-5, mids[key][1]-5, mids[key][0]+5, mids[key][1]+5, fill=key,tags=("mid"))
    
    # změna počtu clusterů (využito pouze pro tlačítko randomize)
    def changeClusterCount(self, var, indx, mode):
        db.changeClusterCount(self.clusterCount.get())
    
    def drawPieChartPoints(self,points,colors):
        # print("start")
        for i,point in enumerate(points):
            lastEnd = 0.0
            for col in colors:
                strt = lastEnd
                lastEnd = 360.0*colors[col][i]
                if strt + lastEnd >= 360.0:
                    lastEnd = 360.0 - strt - 0.000000001
                if lastEnd < 3.5:       # vyhýbání se chybě v create_arc (úhel 0.1 až 3.5 neumí vykreslit (vykreslí celý kruh) - nevím proč... - závislý na poloměru
                    continue
                self.canvas.create_arc((point[0]-P_R,point[1]-P_R,point[0]+P_R,point[1]+P_R),fill=col,outline=col,start=strt,extent=lastEnd,tags=("point"))
                lastEnd = lastEnd + strt
    
    # nakreslí body v poli points příslušnou barvou v colors
    def drawPoints(self,points,colors):
        for i,point in enumerate(points):
            self.canvas.create_oval(point[0]+P_R,point[1]+P_R,point[0]-P_R,point[1]-P_R,fill=colors[i],tags=("point"))
    
    # nakreslí bod v místě kliknutí
    def drawPoint(self, event=None, db=True):
        if self.db.phase == 0:
            self.db.appendPoint(event.x,event.y,self.clusterVar.get())
            self.canvas.create_oval(event.x+P_R,event.y+P_R,event.x-P_R,event.y-P_R,fill=self.clusterVar.get(),tags=("point"))

    # kontroluje validnost zadané hodnoty a případně jí uloží do "databáze"
    def setQ(self):
        q = 2.0
        try:
            q = float(self.entryQ.get())
        except:
            q = 1.0
        
        if q <= 1.0:
            print("invalid value, enter q>1 (something like 1.00001 is enough == nonfuzzy k-means)")
            self.entryQ.delete(0,tk.END)
            self.entryQ.insert(0,"error")
        else:
            self.db.q = q
            self.entryQ.delete(0,tk.END)
            self.entryQ.insert(0,str(q)+" = q")
    
    def pie(self):
        self.db.piePoints()
        if self.buttonPie["text"] == "pie design":
            self.buttonPie.config(text="max design")
        else:
            self.buttonPie.config(text="pie design")
        

    def __init__(self, root, db):
        self.root = root
        self.root.title("Fuzzy k-means demonstration")
        self.db = db
        self.clusterVar=tk.StringVar()      # pomocná proměnná pro uložení kreslící barvy
        self.clusterVar.set("red")
        
        self.clusterCount=tk.IntVar()       # pomocná proměnná pro uložení počtu tříd pro náhodné určení tříd
        self.clusterCount.set(2)
        self.clusterCount.trace("w", self.changeClusterCount)


        root.rowconfigure(0,weight=1)
        root.columnconfigure(1,weight=1)
        self.canvas = tk.Canvas(root, width = 600, height = 400, background = 'white')
        self.canvas.grid(row = 0,column = 1,sticky="snew")

        frame = tk.Frame(self.root)             # podokno pro tlačítka
        frame.grid(row = 0,column = 0, sticky = "ne")

        optionCol = tk.OptionMenu(frame, self.clusterVar, "red", "blue", "green", "yellow", "violet", "brown", "cyan")      #jakou barevnou třídu použít při malování bodů
        optionClustCount = tk.OptionMenu(frame, self.clusterCount, 1, 2, 3, 4, 5, 6, 7) #určuje kolik clusterů se má použít při "míchání" barev bodů
        tk.Label(frame, text="Color").grid(row=0,column=0, sticky="nw")
        optionCol.grid(row=0,column=1,sticky="nwe")
        optionClustCount.grid(row=1,column=1, sticky="nwe")
        buttonRandomize = tk.Button(frame,text="Randomize",command=self.db.randomize).grid(row = 1,column = 0, sticky = "we")# změní všem bodům barvu na náhodnou - využívá bar s počtem clusterů
        buttonStep = tk.Button(frame,text="step",command=self.db.step).grid(row = 2,column = 0, sticky = "we")               # tlačítko na krokování
        button10Step = tk.Button(frame,text="10xstep",command=self.db.step10).grid(row = 2,column = 1, sticky = "we")          # tlačítko na 10 kroků
        buttonReset = tk.Button(frame,text="reset",command=self.db.reset).grid(row = 3,column = 1, sticky = "we")            # tlačítko na odstranění středů a obarvení bodů do jejich barvy při prvním stisku tlačítka step
        self.buttonPie = tk.Button(frame,text="max design",command=self.pie)        # tlačítko na překreslení bodů na koláčové grafy jejich náležitosti
        self.buttonPie.grid(row = 3,column = 0, sticky = "we")
        buttonClear = tk.Button(frame,text="clear",command=self.clearCanvas).grid(row = 4,column = 1, sticky = "we")    # tlačítko mazání bodů a středů
        self.entryQ = tk.Entry(frame,width=12)
        self.entryQ.grid(row = 5, column=0)
        buttonSetQ = tk.Button(frame,text="<- set q",command=self.setQ).grid(row = 5,column = 1, sticky = "we")         #update q
        buttonPrint = tk.Button(frame,text="debug",command=self.db.printDB).grid(row = 6,column = 1, sticky = "we")          # vypíše do konzole info o bodech a středech atd.
        

        self.canvas.bind('<Button-1>',self.drawPoint)       #zaznamenat bod do canvas
        
        tk.Label(frame, text="autor:").grid(row=7,column=0, sticky="sw")
        tk.Label(frame, text="František").grid(row=8,column=0, sticky="sw")
        tk.Label(frame, text="Horázný").grid(row=9,column=0, sticky="sw")
if __name__ == '__main__':
    root = tk.Tk()
    db = Data()
    gui = Gui(root, db)
    root.mainloop()