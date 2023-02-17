# import pixie
# imports the pygame library module
import random
import matplotlib.pyplot as plt

import pygame
from pygame import QUIT, KEYUP

TOPOLOGY = []
ALL_NODES = []
ALL_DATASOURCES = []
ALL_AGENTS = []
ALL_RATES = []

TIME = 0
SAMPLE_RATE = 1

DEBUG1 = False
DEBUG2 = False

SEND = 0
RX = 1
IMAGE = 2
USERX = 3
RL = 4

TASKOK = "Tasks"
CPUIDLE = "Idle"
CPUTX = "Tx"

Param = {'e': 0.2,
         'et': 0.04,
         'er': 0.04,
         'P0': 2.5,
         'P1': 5.5}


class Agent:
    def __init__(self, N=2, id = 0):
        # Crea una matrice NxN
        self.M = [1.0 / N] * N
        self.id = id
        # self.M[id] = 0
        self.sample = 0  # QUANTO MANCA PER IL PROSSIMO SAMPLE
        self.theta = [0.0]*N   #parametri della policy
        self.features = [0.0]*N

        print('INIT AGENT', self.M, self.id)
        return

    def makeAction(self):
        global TOPOLOGY, TIME, DURATA_ROUND
        # DECIDE UN'AZIONE DA COMPIERE, OSSIA DOVE SCHEDULARE IL TASK
        # sia nodeID il nodo che ha ricevuto il task
        # return id
        prob = 0  # totale probabilità di mandare al vicino
        dado = random.random()
        for i in range(len(self.M)):
            if TOPOLOGY[self.id][i] == 1:
                prob += self.M[i]
                if dado < prob:
                    if self.sample == 0:
                        self.learn(action=i)
                    #print(self.id, i, TIME)
                    return i
            prob += self.M[i]
        print('EVVAi')
        return len(self.M)

    def learn(self,action=-1):
        print('LEARNING...', self.id)
        #SAMPLE DEL VALORE DEL GRADIENTE
        if action==self.id:
            #PROCESSO LOCALMENTE

            return
        else:
            return
        return


class DataSource:
    def __init__(self, node, parameters: {} = {}):
        self.par = parameters
        self.every = parameters['every']
        self.taskTxLength = 1 + int(
            1000 * Param['er'] / (Param['P1'] - Param['P0']))  # time mini-slots needed to send pending data...
        self.edgeNode = node

    def tick(self):
        if TIME % self.every == 0:
            self.send()
            self.edgeNode.id
        return

    def send(self):  # INVIA NEW TASK AL NODO
        self.edgeNode.process[USERX] += self.taskTxLength
        return


class EdgeNode:
    def __init__(self, parameters: {} = {}):
        self.par = parameters
        self.turn = 0  # idle
        self.state = 0  # IDLE
        self.process = [0] * 5
        self.vicini = []
        self.M = []
        self.id = parameters['id']
        self.taskMiniSlotRxLength = 1 + int(
            1000 * Param['er'] / (Param['P1'] - Param['P0']))  # time mini-slots needed to send pending data...

        self.taskMiniSlotProcessLength = int(
            1000 * Param['e'] / (Param['P1'] - Param['P0']))  # time mini-slots needed to process pending data...

        self.taskMiniSlotReceived = 0
        self.taskMiniSlotUserReceived = 0
        self.taskMiniSlotProcessed = 0
        if parameters.keys().__contains__('battery'):
            self.Battery = parameters['battery']
        else:
            self.Battery = 100

        self.statistics = {TASKOK: 0,
                           CPUIDLE: 0,
                           CPUTX: 0,
                           'CPUrx': 0,
                           'CPUuserrx': 0,
                           'CPUtask': 0,
                           'CPUticks': 0,
                           'battery': self.Battery}

    def tick(self):
        self.statistics['CPUticks'] = self.statistics['CPUticks'] + 1
        if sum(self.process) == 0:  # NON CI SONO PROCESSI DA ESEGUIRE
            self.statistics[CPUIDLE] = self.statistics[CPUIDLE] + 1
            self.statistics['battery'] -= Param['P0']  # assumo 1 ms
            return
        self.statistics['battery'] -= Param['P1']  # assumo 1 ms
        # SERVI PROSSIMO PROCESSO
        turn = self.turn % 5

        # SALTA IL TURNO SE IL PROCESSO NON DEVE FARE PROGRESS
        if self.process[turn] == 0:
            turn = (turn + 1) % 5
        if self.process[turn] == 0:
            turn = (turn + 1) % 5
        if self.process[turn] == 0:
            turn = (turn + 1) % 5
        if self.process[turn] == 0:
            turn = (turn + 1) % 5

        # AGGIORNA CHI RICEVERA' IL TURNO
        self.turn = turn + 1

        DEBUG2 and print(turn, self.process)

        if self.process[turn] == 0:
            DEBUG1 and print(TIME, self.par['id'], 'CPU IDLE')
            self.statistics[CPUIDLE] = self.statistics[CPUIDLE] + 1
            return

        # TURNO DEL PROCESSO CHE SPEDISCE AD ALTRI NODI
        if turn == RL:
            self.process[RL] -= 1
            return

        if turn == SEND:
            # CONSUMO MINISLOT PER SPEDIRE
            self.statistics[CPUTX] = self.statistics[CPUTX] + 1
            DEBUG1 and print(TIME, self.par['id'], 'CPU SENDING')
            self.process[SEND] -= 1
            return

        if turn == USERX:
            # CONSUMO MINISLOT PER RICEVERE DA UTENTE...
            self.statistics['CPUuserrx'] += 1
            DEBUG1 and print(TIME, self.par['id'], 'CPU RECEIVING')
            self.process[USERX] -= 1  # diminusco il lavoro di un minislot
            self.taskMiniSlotUserReceived += 1  # aumento di uno i minislot che formeranno il nuovo task

            if self.taskMiniSlotUserReceived == self.taskMiniSlotRxLength:  # quando che ho collezionato abbastanza
                self.taskMiniSlotUserReceived = 0  # azzero i ricevuti perche' sono relativi al prossimo task

                i = ALL_AGENTS[self.id].makeAction()
                if i == self.id:
                    self.process[
                        IMAGE] += self.taskMiniSlotProcessLength  # aggiungo tutti i minislot per preocessare il taask
                else:
                    ALL_NODES[i].process[RX] += self.taskMiniSlotRxLength
                    # self.vicini[i].process[RX] += self.taskMiniSlotRxLength
                    self.process[SEND] += self.taskMiniSlotRxLength
                return

                prob = 0  # totale probabilità di mandare al vicino
                dado = random.random()
                # print(dado,self.M)
                for i in range(len(self.M)):
                    prob += self.M[i]
                    if dado < prob:
                        #        # INVIA AD UN VICINO
                        return
                    prob += self.M[i]

        if turn == RX:
            # CONSUMO MINISLOT PER RICEVERE
            self.statistics['CPUrx'] = self.statistics['CPUrx'] + 1

            DEBUG1 and print(TIME, self.par['id'], 'CPU RECEIVING')

            self.process[RX] -= 1  # diminusco il lavoro di un minislot
            self.taskMiniSlotReceived += 1  # aumento di uno i minislot che formeranno il nuovo task
            if self.taskMiniSlotReceived == self.taskMiniSlotRxLength:  # quando che ho collezionato abbastanza
                self.process[
                    IMAGE] += self.taskMiniSlotProcessLength  # aggiungo tutti i minislot per preocessare il taask
                self.taskMiniSlotReceived = 0  # azzero i ricevuti perche' sono relativi al prossimo task

        if turn == IMAGE:  # PROCESSO UN TASK DI CV
            self.statistics['CPUtask'] = self.statistics['CPUtask'] + 1
            DEBUG1 and print(TIME, self.par['id'], 'CPU PROCESSING')

            self.process[IMAGE] -= 1
            self.taskMiniSlotProcessed += 1

            if self.taskMiniSlotProcessed == self.taskMiniSlotProcessLength:
                self.taskMiniSlotProcessed = 0
                self.statistics[TASKOK] += 1


class FullyConnectedSystem:

    def __init__(self, N):
        global ALL_NODES, ALL_DATASOURCES, ALL_AGENTS, TOPOLOGY, ALL_RATES

        self.N = N

        for i in range(N):
            TOPOLOGY.append([1] * N)

        for i in range(N):
            ALL_NODES.append(EdgeNode(parameters={'id': i, 'battery': 10.6 * 1000, 'rate': 0}))
            ALL_DATASOURCES.append(DataSource(ALL_NODES[i], parameters={'rate': 2 + i, 'every': 100 + 10 * i}))
            ALL_AGENTS.append(Agent(N, id=i))

        print(TOPOLOGY, ALL_NODES)

    def tick(self):
        for i in range(self.N):
            ALL_DATASOURCES[i].tick()
        for i in range(self.N):
            ALL_NODES[i].tick()
        return

        if TIME % 150 == 0:
            # self.ds0.send()
            ALL_DATASOURCES[0].send()
            print('SENDING DS0---')

        if TIME % 95 == 0:
            # self.ds1.send()
            ALL_DATASOURCES[1].send()
            print('SENDING DS1---')


# Press the green button in the gutter to run the script.

def go2Nodes():
    system = FullyConnectedSystem(2)
    time = 0
    X = []
    B0 = []
    B1 = []
    IDLE = []
    while 1:
        time += 1
        X.append(time)
        system.tick(time)
        # b0 = min(sum(system.n0.process), 1)
        # b1 = min(sum(system.n1.process), 1)
        B0.append(system.n0.statistics['battery'])
        B1.append(system.n1.statistics['battery'])
        IDLE.append(sum(system.n1.process))
        # B0.append(b0)
        # B1.append(b1)

        if system.n1.statistics['battery'] <= 0 or system.n0.statistics['battery'] <= 0:
            break

    print('END...')
    fig, ax = plt.subplots()
    ax.set_xlabel("Time ")
    ax.set_ylabel("Battery ")
    ax.set_title("")
    ax.plot(X, IDLE)
    plt.show()
    return


def play2Nodes():
    global TIME
    system = FullyConnectedSystem(2)
    pygame.init()
    screen = pygame.display.set_mode((1200, 1200))
    pygame.display.set_caption("Two nodes")
    time = 0
    n0 = ALL_NODES[0]
    n1 = ALL_NODES[1]

    red = (255, 0, 0)
    c1 = (0, 255, 0)
    c2 = (0, 0, 255)
    c3 = (255, 30, 30)
    c4 = (255, 255, 0)
    c5 = (255, 0, 255)
    backgroud = (255, 200, 200)
    colors = [c1, c2, c3, c4, c5]

    H = 200;
    W = 200  # Dimensioni superficie
    step = W / 10
    dimSurface = (W, H)

    surface0 = pygame.surface.Surface(dimSurface)
    surface0.fill(backgroud)
    surface1 = pygame.surface.Surface(dimSurface)
    surface1.fill(backgroud)

    my_font = pygame.font.SysFont('Times new roman', 13)
    metric = my_font.render("TX RX TA US RL                    Battery", True, (0, 0, 0))

    while 1:
        for event in pygame.event.get():
            if event.type == QUIT or event.type == KEYUP:
                return  # pygame.quit()
        time += 1
        TIME += 1
        system.tick()
        screen.fill((255, 255, 255))
        if n0.statistics['battery'] <= 0 or n1.statistics['battery'] <= 0:
            return
        pygame.time.wait(0)

        stat = n0.statistics
        my_font = pygame.font.SysFont('Comic Sans MS', 15)
        text_surface = my_font.render(str(stat) + str(n0.process) + str(ALL_AGENTS[0].M), False, (0, 0, 0))
        screen.blit(text_surface, pygame.Rect(0, 0, 0, 0))

        stat = n1.statistics
        my_font = pygame.font.SysFont('Comic Sans MS', 15)
        text_surface = my_font.render(str(stat) + str(n1.process) + str(ALL_AGENTS[1].M), False, (0, 0, 0))
        screen.blit(text_surface, pygame.Rect(0, 20, 0, 0))

        # DISPLAY METERS
        screen.blit(metric, (100, 400, 0, 0))
        screen.blit(metric, (100 + 250, 400, 300, 300))

        surface0.fill(backgroud)
        for i in range(5):
            pygame.draw.rect(surface0, colors[i], (i * step, max(0, H - n0.process[i]), W / 10, H), 100)
        pygame.draw.rect(surface0, c1, (9 * step, max(0, H - 0.008 * n0.statistics['battery']), W / 5, H), 100)

        surface1.fill(backgroud)
        for i in range(5):
            pygame.draw.rect(surface1, colors[i], (i * step, max(0, H - n1.process[i]), W / 10, H), 100)
        pygame.draw.rect(surface1, c1, (9 * step, max(0, H - 0.008 * n1.statistics['battery']), W / 5, H),
                         100)

        screen.blit(surface0, (100, 200, 0, 0))
        screen.blit(surface1, (100 + 250, 200, 300, 300))

        pygame.display.flip()


def run():
    global TIME
    n1 = EdgeNode({'id': 1})
    d1 = DataSource(n1)

    n2 = EdgeNode({'id': 2})
    d2 = DataSource(n2)

    n3 = EdgeNode({'id': 3})
    d3 = DataSource(n3)

    d1.send();
    d1.send();
    d1.send()
    d2.send();
    d2.send();
    d2.send()
    d3.send();
    d3.send();
    d3.send()
    for i in range(300):
        n1.tick();
        n2.tick();
        n3.tick()
        TIME = TIME + 1

    s = n1.statistics
    I = s[CPUIDLE] + s[CPUTX] + s['CPUrx'] + s['CPUtask']
    I = (I - s[CPUIDLE]) / I
    print(n1.statistics, n2.statistics, n3.statistics)


if __name__ == '__main__':
    # run()
    # go2Nodes()
    play2Nodes()

    # exit()
