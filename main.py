# ---------------------------------------------------------------------------- #
#                                  Importações                                 #
# ---------------------------------------------------------------------------- #

from vpython import *
from vpython.no_notebook import stop_server
from random import randint, randrange
from numpy import savetxt


# ---------------------------------------------------------------------------- #
#                                    Classes                                   #
# ---------------------------------------------------------------------------- #

class Individuo(simple_sphere):
    '''
    Classe utilizada para representar indivíduo no modelo.
    '''
    def __init__(self, pos:vector, vel:vector, raio:float, massa:float,
                especie:str, saudavel:bool, cor:vector):
        super().__init__(pos=pos, radius=raio, color=cor)
        self.vel = vel
        self.massa = massa
        self.especie = especie
        self.saudavel = saudavel
        self.vizinhos = []


# ---------------------------------------------------------------------------- #
#                                    Funções                                   #
# ---------------------------------------------------------------------------- #

# --------------------------------- Dinâmica --------------------------------- #

def dist(r1:vector, r2:vector):
    '''
    Calcula a distância euclidiana bidimensional entre os vetores posição r1 e
    r2.

    Args:
        r1 (vpython vector): vetor posição (x1, y1, 0) da partícula 1
        r2 (vpython vector): vetor posição (x2, y2, 0) da partícula 2

    Returns:
        (float): distância euclidiana entre os vetores r1 e r2
    '''
    return mag(r1-r2)


def neutro(i1:Individuo, i2:Individuo):
    '''
    Calcula e atualiza os vetores velocidade resultantes de cada indivíduo após
    sua interação, considerando uma interação neutra.

    Args:
        i1 (Individuo): representa um dos indivíduos na interação
        i2 (Individuo): representa o outro indivíduo
'''
    v1, m1, x1 = i1.vel, i1.massa, i1.pos
    v2, m2, x2 = i2.vel, i2.massa, i2.pos
    v1_ = v1 - ((2*m2)/(m1+m2))*(dot(v1-v2, x1-x2)/(mag2(x1-x2)))*(x1-x2)
    v2_ = v2 - ((2*m1)/(m1+m2))*(dot(v2-v1, x2-x1)/(mag2(x2-x1)))*(x2-x1)
    i1.vel, i2.vel = v1_, v2_


def infeccao(infect:Individuo, sus:Individuo):
    '''
    Infecção de um indivíduo suscetível por um infectado.

    Args:
        inf (Individuo): representa uma indivíduo infectado
        sus (Individuo): representa um indivíduo suscetível
    '''
    global propriedades
    
    neutro(infect, sus)
    print(f'\n---------- O {sus.especie} foi infectado pelo {infect.especie}!\
 :( ----------') 
    sus.saudavel = False
    sus.color = propriedades[sus.especie]['corInf']
    propriedades[sus.especie]['numInfectados'] += 1
    

def predacao(pred:Individuo, pres:Individuo):
    '''
    Calcula e atualiza os vetores velocidade resultantes dos indivíduos após a
    interação, considerando a predação da presa.

    Args:
        pred (Individuo): representa o predador
        pres (Individuo): representa a presa
    '''
    global indMortos
    
    v1, m1, x1 = pred.vel, pred.massa, pred.pos
    v2, m2, x2 = pres.vel, pres.massa, pres.pos
    m_ = (m1+m2)/2
    v_ = (m1*v1+m2*v2)/m_
    x_ = (x1+x2)/2
    print(f'\n---------- O {pres.especie} foi comido pelo {pred.especie}! :(\
 ----------')
    pred.vel, pred.pos = v_, x_
    if (pres not in indMortos):indMortos.append(pres)


def interacao(i1:Individuo, i2:Individuo):
    '''
    Define o tipo de interação a ocorrer entre os dois indivíduos.
    
    Args:
        i1 (Individuo): representa um dos indivíduos na interação
        i2 (Individuo): representa o outro indivíduo
    '''
    global probReacao
    
    esp1, esp2 = i1.especie, i2.especie
    esps = [esp1, esp2]
    sauds = [i1.saudavel, i2.saudavel]
    # Condições - infeccção:
    condEspInf = (esp1 == esp2)
    condSus =  all(state in sauds for state in (True, False))
    condInf = randint(0, 100) < propriedades[esp1]['taxaInf']
    # Condições - predação:
    combos = [('Gato', 'Rato'), ('Gato', 'Coelho'), ('Leao', 'Gato')]
    condEspPred = any(all(bicho in esps for bicho in combo)for combo in combos)
    if condEspPred:
        for pred_, pres_ in combos:
            if ((esp1==pred_) and (esp2==pres_)): pred, pres = i1, i2
            elif ((esp2==pred_) and (esp1==pres_)): pred, pres = i2, i1
        condPred = randint(0,100) < propriedades[pres.especie]['taxaPred']
    print(f'\n           Interação entre {esp1} e {esp2}!           ')
    # Defininindo tipo de interação:
    if (condEspInf and condSus and condInf): infeccao(i1, i2)
    elif (condEspPred and condPred): predacao(pred, pres)
    else: neutro(i1, i2)
    
    
def atualizaVizinhos(i:Individuo):
    '''
    Atualiza a lista de indivíduos próximos a um determinado indivíduo.

    Args:
        i (Individuo): Indivíduo a ter seus vizinhos recalculados
    '''
    global indVivos
    
    i.vizinhos.clear()
    x, r = i.pos, i.radius
    for i2 in indVivos:
        x2 = i2.pos
        if (dist(x, x2) <= r+2.5) and (i != i2): i.vizinhos.append(i2)
    
    
def atualizaPos(i:Individuo):
    '''
    Atualiza a posição de um indivíduo.
    '''
    global dt

    i.pos += i.vel*dt
    
    
def colCheckIndInd(i1:Individuo, i2:Individuo):
    '''
    Checa colisão entre dois indivíduos.

    Args:
        i1 (Individuo): representa um dos indivíduos na interação
        i2 (Individuo): representa o outro indivíduo
    '''
    global dt
    
    x1, v1, r1 = i1.pos, i1.vel, i1.radius
    x2, v2, r2 = i2.pos, i2.vel, i2.radius
    distMinima = r1+r2
    distancia = dist(x1, x2)
    distancia_ = dist(x1+(v1*dt), x2+(v2*dt))
    if (distancia <= distMinima) and (distancia > distancia_):
        interacao(i1, i2)


def colCheckIndParede(i:Individuo):
    '''
    Checa colisão entre um indivíduo e as paredes da caixa.

    Args:
        i (Individuo): indivíduo a ser examinada
    '''
    global dt, ladoCaixa
    
    r = i.radius
    pos = i.pos
    pos_  = pos+(i.vel*dt)
    if (abs(pos.x) >= (ladoCaixa/2-r)) and (abs(pos.x) < abs(pos_.x)):
        i.vel.x = -i.vel.x
    if (abs(pos.y) >= (ladoCaixa/2-r)) and (abs(pos.y) < abs(pos_.y)):
        i.vel.y = -i.vel.y
    
    
# ---------------------------------- Visual ---------------------------------- #

def criaCaixa():
    '''
    Cria representação das arestas da caixa imaginária para conter a simulação.
    '''
    global ladoCaixa
    
    d = ladoCaixa/2 + 1e-2
    caixa = curve(color=vector(1,1,1), radius=1e-2)
    caixa.append([vector(-d,-d,0), vector(-d,d,0), vector(d,d,0),
                  vector(d,-d,0), vector(-d,-d,0)])


def criaIndividuos(especie:str):
    '''
    Cria instâncias da classe Individuo de uma determinada espécie na lista de
    indivíduos vivos.

    Args:
        especie (str): espécie da população a ser criada
    '''
    global propriedades, ladoCaixa, velLimite, indVivos
    
    numIndividuos = propriedades[especie]['numIndividuos']
    raio, massa, cor = propriedades[especie]['raio'], \
    propriedades[especie]['massa'], propriedades[especie]['cor']
    for _ in range(numIndividuos):
        pos = [randrange(-ladoCaixa/2+1, ladoCaixa/2-1) for _ in range (2)]
        pos = vector(pos[0], pos[1], 0)
        vel = [randint(0, velLimite) for _ in range(2)]
        vel = vector(vel[0], vel[1], 0)
        saudavel = randint(0, 100) > propriedades[especie]['taxaInf']
        if (not saudavel): propriedades[especie]['numInfectados'] += 1
        p = Individuo(pos, vel, raio, massa, especie, saudavel, cor)
        indVivos.append(p)
        
        
def criaGraficos():
    '''
    Cria gráficos que acompanham a simulação.
    '''
    global grafComp, grafAlt, listaConc, listaInf
    
    # Gráfico de concentração:
    valMaximo = 65
    grafico1 = graph(title='Concentração', width=grafComp,
                    height=grafAlt, align='left', ymax=valMaximo,
                    xtitle='Tempo', ytitle='Número de indivíduos')
    concRato = gcurve(data=list(zip(listaConc[0], listaConc[1])),
                    color=vector(.5,.5,.5), label='Ratos')
    concCoelho = gcurve(data=list(zip(listaConc[0], listaConc[2])),
                    color=vector(0,0,0), label='Coelhos')
    concGato = gcurve(data=list(zip(listaConc[0], listaConc[3])),
                    color=vector(1,.5,0), label='Gatos')
    concLeao = gcurve(data=list(zip(listaConc[0], listaConc[4])),
                    color=vector(1,1,0), label='Leao')
    graficosConc.extend([concRato, concCoelho, concGato, concLeao])
    
    # Gráfico de infecção:
    valMaximo = 65
    grafico2 = graph(title='Infecção', width=grafComp,
                    height=grafAlt, align='left', ymax=valMaximo,
                    xtitle='Tempo', ytitle='Número de indivíduos infectados')
    infRato = gcurve(data=list(zip(listaConc[0], listaConc[1])),
                    color=vector(.5,.5,.5), label='Ratos')
    infGato = gcurve(data=list(zip(listaConc[0], listaConc[2])),
                    color=vector(1,.5,0), label='Gatos')
    infLeao = gcurve(data=list(zip(listaConc[0], listaConc[3])),
                    color=vector(1,1,0), label='Leao')
    graficosInf.extend([infRato, infGato, infLeao])


def atualizaGraficos():
    '''
    Atualiza os gráficos que acompanham a simulação.
    '''
    global graficosConc, listaConc
    
    # Gráfico de concentração:
    concRato, concCoelho, concGato, concLeao = graficosConc[0], graficosConc[1],\
    graficosConc[2], graficosConc[3]
    concRato.data = list(zip(listaConc[0], listaConc[1]))
    concCoelho.data = list(zip(listaConc[0], listaConc[2]))
    concGato.data = list(zip(listaConc[0], listaConc[3]))
    concLeao.data = list(zip(listaConc[0], listaConc[4]))
    
    # Gráfico de infecção:
    infRato, infGato, infLeao = graficosInf[0], graficosInf[1], graficosInf[2]
    infRato.data = list(zip(listaInf[0], listaInf[1]))
    infGato.data = list(zip(listaInf[0], listaInf[2]))
    infLeao.data = list(zip(listaInf[0], listaInf[3]))
    
    
def atualizaListas(t:int):
    '''
    Atualiza listas para a plotagem dos gráficos.

    Args:
        t (int): tempo (frame) atual da simulação
    '''
    global listaConc, listaInf
    
    # Gráfico de concentração:
    listaConc[0].append(t)
    listaConc[1].append(nRato)
    listaConc[2].append(nCoelho)
    listaConc[3].append(nGato)
    listaConc[4].append(nLeao)
    
    # Gráfico de infecção:
    listaInf[0].append(t)
    listaInf[1].append(nRInf)
    listaInf[2].append(nGInf)
    listaInf[3].append(nLInf)
    
    
# --------------------------------- Simulação -------------------------------- #

def delIndividuo(i:Individuo):
    '''
    Deleta partícula da simulação.

    Args:
        i (Individuo): partícula a ser deletada
    '''
    global indVivos, propriedades
    
    propriedades[i.especie]['numIndividuos'] -= 1
    i.visible = False
    indVivos.remove(i)
    del i
    
    
def exportarDados():
    '''
    Exporta os dados do gráfico de concentração e de infecção.
    '''
    global listaConc, listaInf
    
    # Gráfico de concentração:
    dadosConc = [valor for valor in zip(listaConc[0], listaConc[1], listaConc[2],
                                        listaConc[3], listaConc[4])]
    savetxt(f'dados/dadosConcentracao.csv', dadosConc, delimiter=', ',
            fmt='% s')
    
    # Gráfico de infecção:
    dadosConc = [valor for valor in zip(listaInf[0], listaInf[1], listaInf[2],
                                        listaInf[3])]
    savetxt(f'dados/dadosInfeccao.csv', dadosConc, delimiter=', ',
            fmt='% s')
    
    
def pararSimulacao():
    '''
    Para a simulação e exporta os dados de concentração
    '''
    global parar
    
    parar = True
    exportarDados()
    

def step():
    '''
    Passo da simulação:
        * Deleta todos os indivíduos mortos;
        * Reseta a lista de indivíduos mortos;
        * Atualiza número de indivíduos de cada população;
        * Atualiza número de indivíduos infectados de cada população;
        * Atualiza gráficos;
        * Atualiza posições dos indivíduos;
        * Atualiza vizinhos;
        * Check de colisão entre dois indivíduos;
        * Check de colisão indivíduo-parede
    '''
    global indMortos, indVivos, nRato, nCoelho, nGato, nLeao, nRInf, nGInf, nLInf
    
    # * Deleta todos os indivíduos mortos:
    [delIndividuo(i) for i in indMortos]
    # * Reseta a lista de indivíduos mortos:
    indMortos.clear()
    # * Atualiza número de indivíduos de cada população:
    nRato = propriedades['Rato']['numIndividuos']
    nCoelho = propriedades['Coelho']['numIndividuos']
    nGato = propriedades['Gato']['numIndividuos']
    nLeao = propriedades['Leao']['numIndividuos']
    # * Atualiza número de indivíduos infectados de cada população:
    nRInf = propriedades['Rato']['numInfectados']
    nGInf = propriedades['Gato']['numInfectados']
    nLInf = propriedades['Leao']['numInfectados']
    # * Atualiza gráficos:
    atualizaGraficos()
    # * Atualiza posições dos indivíduos;
    for i in indVivos:
        atualizaPos(i)
    # * Atualiza vizinhos:
        atualizaVizinhos(i)
    # * Check de colisão entre dois indivíduos;
        for i2 in i.vizinhos:
            colCheckIndInd(i, i2)
    # * Check de colisão indivíduo-parede:
        colCheckIndParede(i)


def simulacao():
    '''
    Função responsável pela simulação completa.
    '''
    global rate, parar, listaConc, nRato, nCoelho, nGato, nLeao
    
    rate = 300
    t = 0
    criaCaixa()
    criaIndividuos('Rato')
    criaIndividuos('Coelho')
    criaIndividuos('Gato')
    criaIndividuos('Leao')
    criaGraficos()
    while (not parar):
        step()
        t += 1
        atualizaListas(t)
    print('\n\n---------- Fim da simulação! ----------\n')
    stop_server()



################################################################################



# ---------------------------------------------------------------------------- #
#                            Parâmetros da simulação                           #
# ---------------------------------------------------------------------------- #

# Propriedades dos indivíduos:
propriedades = {
    'Rato' : {
        'raio':.15,
        'massa':1,
        'especie':'Rato',
        'cor':vector(.5,.5,.5),
        'corInf':vector(0,1,0),
        'taxaInf':15,
        'taxaPred':60,
        'numIndividuos':50,
        'numInfectados':0
    },

    'Coelho' : {
        'raio':.2,
        'massa':2,
        'especie':'Coelho',
        'cor':vector(1,1,1),
        'taxaInf':0,
        'taxaPred':50,
        'numIndividuos':60
    },

    'Gato' : {
        'raio':.25,
        'massa':3,
        'especie':'Gato',
        'cor':vector(1,.5,0),
        'corInf':vector(.2,1,.2),
        'taxaInf':10,
        'taxaPred':40,
        'numIndividuos':30,
        'numInfectados':0
    },

    'Leao' : {
        'raio':.3,
        'massa':4,
        'especie':'Leao',
        'cor':vector(1,1,0),
        'corInf':vector(.4,1,.4),
        'taxaInf':5,
        'taxaPred':0,
        'numIndividuos':20,
        'numInfectados':0
    }
}

dt = 1e-3 # Variação no tempo em cada frame
velLimite = 40 # Limite de velocidade inicial para as partículas

nRato = propriedades['Rato']['numIndividuos'] # Número de ratos
nCoelho = propriedades['Coelho']['numIndividuos'] # Número de coelhos
nGato = propriedades['Gato']['numIndividuos'] # Número de gatos
nLeao = propriedades['Leao']['numIndividuos'] # Número de leões

nRInf = propriedades['Rato']['numInfectados'] # Número de ratos infectados
nGInf = propriedades['Gato']['numInfectados'] # Número de gatos infectados
nLInf = propriedades['Leao']['numInfectados'] # Número de leões infectados

indVivos = [] # Lista de indivíduos vivos
indMortos = [] # Lista de indivíduos mortos

ladoCaixa = 20 # Lado da caixa imaginária contendo a simulação

# Gráfico de concentração:
graficosConc = []
listaTempo = [0]
listaRato = [nRato]
listaCoelho = [nCoelho]
listaGato = [nGato]
listaLeao = [nLeao]
listaConc = [listaTempo, listaRato, listaCoelho, listaGato, listaLeao]

# Gráfico de infecção:
graficosInf = []
listaRInf = [nRInf]
listaGInf = [nGInf]
listaLInf = [nLInf]
listaInf = [listaTempo, listaRInf, listaGInf, listaLInf]


# ---------------------------------------------------------------------------- #
#                                 Setup VPython                                #
# ---------------------------------------------------------------------------- #

# Configurações da janela:
ladoJanela = 800
grafComp = ladoJanela/2
grafAlt = ladoJanela/3

# Criando a animação:
animacao = canvas(width=ladoJanela, height=ladoJanela, align='left')
animacao.range = ladoCaixa
animacao.camera.pos = vector(0,0,20)

parar = False

animacao.append_to_caption('\n\n\n                                            ')
botaoParar = button(pos=animacao.caption_anchor, text='Parar simulação',
                    bind=pararSimulacao, left=50)
animacao.append_to_caption('\n\n\n\n')


# ---------------------------------------------------------------------------- #
#                                   Simulação                                  #
# ---------------------------------------------------------------------------- #

simulacao()


# --------------------------------- A Fazer: --------------------------------- #
# Implementar infecção durante predação;
# Implementar morte por infecção;
# Implementar natalidade e mortalidade (?)