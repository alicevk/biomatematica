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


def colInelastica(i1:Individuo, i2:Individuo):
    '''
    Calcula e atualiza um vetor velocidade resultante em uma colisão inelástica.

    Args:
        i1 (Individuo): representa um dos indivíduos na colisão
        i2 (Individuo): representa o outro indivíduo
    '''
    v1, m1, x1 = i1.vel, i1.massa, i1.pos
    v2, m2, x2 = i2.vel, i2.massa, i2.pos
    m_ = (m1+m2)/2
    v_ = (m1*v1+m2*v2)/m_
    x_ = (x1+x2)/2
    
    return x_, v_


def colElastica(i1:Individuo, i2:Individuo):
    '''
    Calcula e atualiza os vetores velocidade resultantes de cada indivíduo em
    uma colisão elástica.

    Args:
        i1 (Individuo): representa um dos indivíduos na colisão
        i2 (Individuo): representa o outro indivíduo
    '''
    v1, m1, x1 = i1.vel, i1.massa, i1.pos
    v2, m2, x2 = i2.vel, i2.massa, i2.pos
    v1_ = v1 - ((2*m2)/(m1+m2))*(dot(v1-v2, x1-x2)/(mag2(x1-x2)))*(x1-x2)
    v2_ = v2 - ((2*m1)/(m1+m2))*(dot(v2-v1, x2-x1)/(mag2(x2-x1)))*(x2-x1)
    i1.vel, i2.vel = v1_, v2_


def infeccao(infect:Individuo, sus:Individuo):
    '''
    Calcula e atualiza os vetores velocidade resultantes de cada indivíduo após
    sua interação, considerando uma infecção.
    
    Args:
        inf (Individuo): representa uma indivíduo infectado
        sus (Individuo): representa um indivíduo suscetível
    '''
    global propriedades
    
    colElastica(infect, sus)
    print(f'\n--------- O {sus.especie} foi infectado pelo {infect.especie}! \
:(')
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
    
    print(f'\n--------- O {pres.especie} foi comido pelo {pred.especie}! :(')
    pred.pos, pred.vel = colInelastica(pred, pres)
    if (pres not in indMortos):indMortos.append(pres)
    # Infecção depois da predação:
    condSus, condInf = checkInf(pred, pres, completa=False)
    if (condSus and condInf): infeccao(pres, pred)


def reproducao(i1:Individuo,i2:Individuo):
    '''
    Calcula e atualiza os vetores velocidade resultantes dos indivíduos após a
    interação, considerando a reprodução dos indivíduos.

    Args:
        i1 (Individuo): representa um dos indivíduos na interação
        i2 (Individuo): representa o outro indivíduo
    '''
    
    colElastica(i1, i2)
    esp1, esp2 = i1.especie, i2.especie
    print(f'\n--------- O {esp1} se reproduziu com o {esp2}! :)')
    pos, vel = colInelastica(i1, i2)
    criaIndividuo(pos, vel, esp1)


def checkInf(i1:Individuo, i2:Individuo, completa=True):
    '''
    Checa as condições para interação de infecção.

    Args:
        i1 (Individuo): representa um dos indivíduos a serem checados
        i2 (Individuo): representa o outro indivíduo
        completa (bool, optional): verdadeiro para retornar a função completa,
    falso para retornar apenas a componente estatística. Verdadeiro por padrão
    '''
    global propriedades

    # Completa
    esp1, esp2 = i1.especie, i2.especie
    saud1, saud2 = i1.saudavel, i2.saudavel
    infect, sus = None, None
    condEspInf = (esp1 == esp2)
    condSus =  all(state in [saud1, saud2] for state in (True, False))
    condInf = randint(0, 100) < propriedades[esp1]['taxaInf']
    if ((not saud1) and (saud2)): infect, sus = i1, i2
    elif ((saud1) and (not saud2)): infect, sus = i2, i1
    # Incompleta:
    condSus2 = ((saud1==True) and (saud2==False))
    
    if completa: return condEspInf, condSus, condInf, infect, sus
    else: return condInf, condSus2


def checkPred(i1:Individuo, i2:Individuo):
    '''
    Checa as condições para interação de predação.

    Args:
        i1 (Individuo): representa um dos indivíduos a serem checados
        i2 (Individuo): representa o outro indivíduo
    '''
    global propriedades
    
    condPred, pred, pres = None, None, None
    esp1, esp2 = i1.especie, i2.especie
    esps = [esp1, esp2]
    combos = [('Raposa', 'Rato'), ('Raposa', 'Coelho'), ('Gaucho', 'Raposa')]
    condEspPred = any(all(bicho in esps for bicho in combo)for combo in combos)
    for pred_, pres_ in combos:
        if ((esp1 == pred_) and (esp2 == pres_)): pred, pres = i1, i2
        elif ((esp2 == pred_) and (esp1 == pres_)): pred, pres = i2, i1
    if pred: condPred = randint(0,100) < propriedades[pres.especie]['taxaPred']
    
    return condEspPred, condPred, pred, pres


def checkRepr(i1:Individuo, i2:Individuo):
    '''
    Cehca as condições para interação de reprodução.

    Args:
        i1 (Individuo): representa um dos indivíduos a serem checados
        i2 (Individuo): representa o outro indivíduo
    '''
    global propriedades
    
    esp1, esp2 = i1.especie, i2.especie
    condEspRepr = (esp1 == esp2)
    condRepr = randint(0,100) < propriedades[esp1]['taxaNat']
    
    return condEspRepr, condRepr


def interacao(i1:Individuo, i2:Individuo):
    '''
    Define o tipo de interação a ocorrer entre os dois indivíduos.
    
    Args:
        i1 (Individuo): representa um dos indivíduos na interação
        i2 (Individuo): representa o outro indivíduo
    '''
    global propriedades

    print(f'\n          Interação entre {i1.especie} e {i2.especie}!')
    
    # Checando tipo de interação:
    condEspInf, condSus, condInf, infect, sus = checkInf(i1, i2)
    condEspPred, condPred, pred, pres = checkPred(i1, i2)
    condEspRepr, condRepr = checkRepr(i1, i2)

    # Defininindo tipo de interação:
    if (condEspInf and condSus and condInf): infeccao(infect, sus)
    if (condEspPred and condPred): predacao(pred, pres)
    if (condEspRepr and condRepr): reproducao(i1, i2)
    else: colElastica(i1, i2)
    
    
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


def criaIndividuo(pos:vector, vel:vector, especie:str, saudavel:bool=True):
    '''
    Cria instância da classe Individuo de uma determinada espécie na lista de
    indivíduos vivos.

    Args:
        pos (vector): posição inicial do indivíduo
        vel (vector): velocidade inicial do indivíduo
        especie (str): espécie do indivíduo a ser criado
        saudavel (bool): condição de infecção para o indivíduo;
    Verdadeiro = saudável, Falso = infectado. Verdadeiro por padrão
    '''
    global propriedades
    
    raio, massa, cor = propriedades[especie]['raio'], \
    propriedades[especie]['massa'], propriedades[especie]['cor']
    p = Individuo(pos, vel, raio, massa, especie, saudavel, cor)
    if (not saudavel): propriedades[especie]['numInfectados'] += 1
    indVivos.append(p)
    propriedades[especie]['numIndividuos'] +=1


def criaPopulacao(especie:str):
    '''
    Cria população de instâncias da classe Individuo de uma determinada espécie
    na lista de indivíduos vivos.

    Args:
        especie (str): espécie da população a ser criada
    '''
    global propriedades, ladoCaixa, velLimite, indVivos
    
    numIndividuosInicial = propriedades[especie]['numIndividuosInicial']
    for _ in range(numIndividuosInicial):
        pos = [randrange(-ladoCaixa/2+1, ladoCaixa/2-1) for _ in range (2)]
        pos = vector(pos[0], pos[1], 0)
        vel = [randint(0, velLimite) for _ in range(2)]
        vel = vector(vel[0], vel[1], 0)
        saudavel = randint(1, 100) > propriedades[especie]['taxaInf']
        criaIndividuo(pos, vel, especie, saudavel)
        
        
def criaGraficos():
    '''
    Cria gráficos que acompanham a simulação.
    '''
    global grafComp, grafAlt, listaConc, listaInf
    
    # Gráfico de concentração:
    valMaximo = 120
    grafico1 = graph(title='Concentração', width=grafComp,
                    height=grafAlt, align='left', ymax=valMaximo,
                    xtitle='Tempo', ytitle='Número de indivíduos')
    concRato = gcurve(data=list(zip(listaConc[0], listaConc[1])),
                    color=vector(.5,.5,.5), label='Ratos')
    concCoelho = gcurve(data=list(zip(listaConc[0], listaConc[2])),
                    color=vector(0,0,0), label='Coelhos')
    concRaposa = gcurve(data=list(zip(listaConc[0], listaConc[3])),
                    color=vector(1,.5,0), label='Raposas')
    concGaucho = gcurve(data=list(zip(listaConc[0], listaConc[4])),
                    color=vector(1,1,0), label='Gaucho')
    graficosConc.extend([concRato, concCoelho, concRaposa, concGaucho])
    
    # Gráfico de infecção:
    valMaximo = 120
    grafico2 = graph(title='Infecção', width=grafComp,
                    height=grafAlt, align='left', ymax=valMaximo,
                    xtitle='Tempo', ytitle='Número de indivíduos infectados')
    infRato = gcurve(data=list(zip(listaConc[0], listaConc[1])),
                    color=vector(.5,.5,.5), label='Ratos')
    infRaposa = gcurve(data=list(zip(listaConc[0], listaConc[2])),
                    color=vector(1,.5,0), label='Raposas')
    infGaucho = gcurve(data=list(zip(listaConc[0], listaConc[3])),
                    color=vector(1,1,0), label='Gaucho')
    graficosInf.extend([infRato, infRaposa, infGaucho])


def atualizaGraficos():
    '''
    Atualiza os gráficos que acompanham a simulação.
    '''
    global graficosConc, listaConc
    
    # Gráfico de concentração:
    concRato, concCoelho, concRaposa, concGaucho = graficosConc[0], \
    graficosConc[1], graficosConc[2], graficosConc[3]
    concRato.data = list(zip(listaConc[0], listaConc[1]))
    concCoelho.data = list(zip(listaConc[0], listaConc[2]))
    concRaposa.data = list(zip(listaConc[0], listaConc[3]))
    concGaucho.data = list(zip(listaConc[0], listaConc[4]))
    
    # Gráfico de infecção:
    infRato, infRaposa, infGaucho = graficosInf[0], graficosInf[1], graficosInf[2]
    infRato.data = list(zip(listaInf[0], listaInf[1]))
    infRaposa.data = list(zip(listaInf[0], listaInf[2]))
    infGaucho.data = list(zip(listaInf[0], listaInf[3]))
    
    
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
    listaConc[3].append(nRaposa)
    listaConc[4].append(nGaucho)
    
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
    global indMortos, indVivos, nRato, nCoelho, nRaposa, nGaucho, nRInf, nGInf, nLInf
    
    # * Deleta todos os indivíduos mortos:
    [delIndividuo(i) for i in indMortos]
    # * Reseta a lista de indivíduos mortos:
    indMortos.clear()
    # * Atualiza número de indivíduos de cada população:
    nRato = propriedades['Rato']['numIndividuos']
    nCoelho = propriedades['Coelho']['numIndividuos']
    nRaposa = propriedades['Raposa']['numIndividuos']
    nGaucho = propriedades['Gaucho']['numIndividuos']
    # * Atualiza número de indivíduos infectados de cada população:
    nRInf = propriedades['Rato']['numInfectados']
    nGInf = propriedades['Raposa']['numInfectados']
    nLInf = propriedades['Gaucho']['numInfectados']
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
    global rate, parar, listaConc, nRato, nCoelho, nRaposa, nGaucho
    
    rate = 300
    t = 0
    criaCaixa()
    criaPopulacao('Rato')
    criaPopulacao('Coelho')
    criaPopulacao('Raposa')
    criaPopulacao('Gaucho')
    criaGraficos()
    while (not parar):
        step()
        t += 1
        atualizaListas(t)
    print('\n\n--------- Fim da simulação!\n')
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
        'taxaNat':15,
        'taxaInf':15,
        'taxaPred':60,
        'numIndividuosInicial':100,
        'numIndividuos':0,
        'numInfectados':0
    },

    'Coelho' : {
        'raio':.2,
        'massa':2,
        'especie':'Coelho',
        'cor':vector(1,1,1),
        'taxaNat':20,
        'taxaInf':0,
        'taxaPred':55,
        'numIndividuosInicial':70,
        'numIndividuos':0,
        'numInfectados':0
    },

    'Raposa' : {
        'raio':.25,
        'massa':3,
        'especie':'Raposa',
        'cor':vector(1,.5,0),
        'corInf':vector(.2,1,.2),
        'taxaNat':10,
        'taxaInf':10,
        'taxaPred':30,
        'numIndividuosInicial':75,
        'numIndividuos':0,
        'numInfectados':0
    },

    'Gaucho' : {
        'raio':.3,
        'massa':4,
        'especie':'Gaucho',
        'cor':vector(1,1,0),
        'corInf':vector(.4,1,.4),
        'taxaNat':1,
        'taxaInf':5,
        'taxaPred':0,
        'numIndividuosInicial':20,
        'numIndividuos':0,
        'numInfectados':0
    }
}

dt = 1e-3 # Variação no tempo em cada frame
velLimite = 20 # Limite de velocidade inicial para as partículas

nRato = propriedades['Rato']['numIndividuosInicial'] # Número de ratos
nCoelho = propriedades['Coelho']['numIndividuosInicial'] # Número de coelhos
nRaposa = propriedades['Raposa']['numIndividuosInicial'] # Número de gatos
nGaucho = propriedades['Gaucho']['numIndividuosInicial'] # Número de leões

nRInf = propriedades['Rato']['numInfectados'] # Número de ratos infectados
nGInf = propriedades['Raposa']['numInfectados'] # Número de gatos infectados
nLInf = propriedades['Gaucho']['numInfectados'] # Número de leões infectados

indVivos = [] # Lista de indivíduos vivos
indMortos = [] # Lista de indivíduos mortos

ladoCaixa = 20 # Lado da caixa imaginária contendo a simulação

# Gráfico de concentração:
graficosConc = []
listaTempo = [0]
listaRato = [nRato]
listaCoelho = [nCoelho]
listaRaposa = [nRaposa]
listaGaucho = [nGaucho]
listaConc = [listaTempo, listaRato, listaCoelho, listaRaposa, listaGaucho]

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
# Implementar morte por infecção --> Proporcional ao tempo função crescente sigmoide
# Parâmetros!
# Implementar mortalidade!!!!! Por interação