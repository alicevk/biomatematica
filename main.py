# ---------------------------------------------------------------------------- #
#                                  Importações                                 #
# ---------------------------------------------------------------------------- #

from vpython import *
from random import randint, randrange
from numpy import array, unique, savetxt


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
    print(f'\nInteração entre {i1.especie} e {i2.especie}!')
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
    print(f'O {sus.especie} foi infectado pelo {infect.especie}! :(')    
    sus.saudavel = False
    sus.color = propriedades[sus.especie]['corInf']
    

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
    print(f'\nInteração entre {pred.especie} e {pres.especie}!')
    print(f'O {pres.especie} foi comido pelo {pred.especie}! :(')
    pred.vel, pred.pos = v_, x_
    indMortos.append(pres)


def interacao(i1:Individuo, i2:Individuo):
    '''
    Define o tipo de interação a ocorrer entre os dois indivíduos.
    
    Args:
        i1 (Individuo): representa um dos indivíduos na interação
        i2 (Individuo): representa o outro indivíduo
    '''
    global probReacao
    
    esp1, esp2 = i1.especie, i2.especie
    # Condições - infeccção:
    condEspecie = (esp1 == esp2)
    condSus = (False and True) in [i.saudavel for i in (i1, i2)]
    condInf = randint(0, 100) < propriedades[esp1]['taxaInf']
    # Condições - predação:
    c1, c2, c3 = ('Gato' and 'Rato'), ('Gato' and 'Coelho'), ('Leao' and 'Gato')
    condEspecies = (c1 or c2 or c3) in [esp1, esp2]
    pres = (i1 if ((esp1=='Gato' and esp2=='Leao') and (esp1!='Leao')) else i2)
    pred = (i1 if (pres==i2) else i2)
    condPred = randint(0,100) < propriedades[pres.especie]['taxaPred']
    # Defininindo tipo de interação:
    if (condEspecie and condSus and condInf): infeccao(i1, i2)
    elif (condEspecies and condPred): predacao(pred, pres)
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
    
    numInicial = propriedades[especie]['numInicial']
    raio, massa, cor = propriedades[especie]['raio'], \
    propriedades[especie]['massa'], propriedades[especie]['cor']
    for _ in range(numInicial):
        pos = [randrange(-ladoCaixa/2+1, ladoCaixa/2-1) for _ in range (2)]
        pos = vector(pos[0], pos[1], 0)
        vel = [randint(0, velLimite) for _ in range(2)]
        vel = vector(vel[0], vel[1], 0)
        saudavel = randint(0, 100) < propriedades[especie]['taxaInf']
        p = Individuo( pos, vel, raio, massa, especie, saudavel, cor)
        indVivos.append(p)
        
        
def criaGraficos():
    '''
    Cria gráficos que acompanham a simulação.
    '''
    global grafComp, grafAlt, listaConc
    
    # Gráfico de concentração:
    valMaximo = 65
    grafico2 = graph(title='Concentração', width=grafComp,
                    height=grafAlt, align='left', ymax=valMaximo,
                    xtitle='Tempo', ytitle='Número de indivíduos')
    concRato = gcurve(data=list(zip(listaConc[0], listaConc[1])),
                    color=vector(.5,.5,.5), label='Ratos')
    concCoelho = gcurve(data=list(zip(listaConc[0], listaConc[2])),
                    color=vector(1,1,1), label='Coelhos')
    concGato = gcurve(data=list(zip(listaConc[0], listaConc[3])),
                    color=vector(1,.5,0), label='Gatos')
    concLeao = gcurve(data=list(zip(listaConc[0], listaConc[4])),
                    color=vector(1,1,0), label='Leao')
    graficos.extend([concRato, concCoelho, concGato, concLeao])


def atualizaGraficos():
    '''
    Atualiza os gráficos que acompanham a simulação.
    '''
    global graficos, listaConc
    
    # Gráfico de concentração:
    concRato, concCoelho, concGato, concLeao = graficos[0], graficos[1], \
    graficos[2], graficos[3]
    concRato.data = list(zip(listaConc[0], listaConc[1]))
    concCoelho.data = list(zip(listaConc[0], listaConc[2]))
    concGato.data = list(zip(listaConc[0], listaConc[3]))
    concLeao.data = list(zip(listaConc[0], listaConc[4]))
    
    
# --------------------------------- Simulação -------------------------------- #

def delIndividuo(i:Individuo):
    '''
    Deleta partícula da simulação.

    Args:
        i (Individuo): partícula a ser deletada
    '''
    global indVivos
    
    i.visible = False
    indVivos.remove(i)
    del i
    
    
def exportarDados():
    '''
    Exporta os dados do gráfico de concentração.
    '''
    global listaConc
    
    dados = [i for i in zip(listaConc[0], listaConc[1], listaConc[2],
                            listaConc[3], listaConc[4])]
    savetxt(f'dados/dadosSimulacao.csv', dados, delimiter=', ',
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
        * Atualiza gráficos;
        * Atualiza posições dos indivíduos;
        * Atualiza vizinhos;
        * Check de colisão entre dois indivíduos;
        * Check de colisão indivíduo-parede
    '''
    global indMortos, indVivos
    
    # * Deleta todos os indivíduos mortos:
    [delIndividuo(i) for i in indMortos]
    # * Reseta a lista de indivíduos mortos:
    indMortos.clear()
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
    global parar, listaConc, nRato, nCoelho, nGato, nLeao
    
    t = 0
    criaCaixa()
    criaIndividuos('Rato')
    criaIndividuos('Coelho')
    criaIndividuos('Gato')
    criaIndividuos('Leao')
    criaGraficos()
    while not parar:
        step()
        t += 1
        listaConc[0].append(t)
        listaConc[1].append(nRato)
        listaConc[2].append(nCoelho)
        listaConc[3].append(nGato)
        listaConc[4].append(nLeao)
    print('\n\nFim da simulação!')



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
        'numInicial':50
    },

    'Coelho' : {
        'raio':.2,
        'massa':2,
        'especie':'Coelho',
        'cor':vector(1,1,1),
        'taxaInf':0,
        'taxaPred':50,
        'numInicial':60
    },

    'Gato' : {
        'raio':.25,
        'massa':3,
        'especie':'Gato',
        'cor':vector(1,.5,0),
        'corInf':vector(0,.5,0),
        'taxaInf':10,
        'taxaPred':40,
        'numInicial':30
    },

    'Leao' : {
        'raio':.4,
        'massa':5,
        'especie':'Leao',
        'cor':vector(1,1,0),
        'corInf':vector(0,.2,0),
        'taxaInf':5,
        'taxaPred':0,
        'numInicial':20
    }
}

dt = 1e-3 # Variação no tempo em cada frame
velLimite = 40 # Limite de velocidade inicial para as partículas

nRato = propriedades['Rato']['numInicial'] # Número de indivíduos da espécie Rato
nCoelho = propriedades['Coelho']['numInicial'] # Número de indivíduos da espécie Coelho
nGato = propriedades['Gato']['numInicial'] # Número de indivíduos da espécie Gato
nLeao = propriedades['Leao']['numInicial'] # Número de indivíduos da espécie Leão

indVivos = [] # Lista de indivíduos vivos
indMortos = [] # Lista de indivíduos mortos

ladoCaixa = 20 # Lado da caixa imaginária contendo a simulação

# Gráfico de concentração:
graficos = []
listaTempo = [0]
listaRato = [nRato]
listaCoelho = [nCoelho]
listaGato = [nGato]
listaLeao = [nLeao]
listaConc = [listaTempo, listaRato, listaCoelho, listaGato, listaLeao]


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