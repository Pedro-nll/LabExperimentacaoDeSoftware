Tema: Qualidade de código

Universo: Java - top 1000 repo

### RQS

RQ1: Qualidade x popularidade?

RQ2: qualidade x maturidade

RQ3: qualidade x atividade

RQ4: qualidade x tamanho

### Métricas

Popularidade = Numero de estrelas

Tamanho = LOC + comentários

Atividade = Número de releases

Maturidade = idade

##### Qualidade (ferramenta CK):

CBO = acoplamento

DIT = Tamanho da herança

LCOM = falta de coesão entre métodos

### Coleta de dados:

CK gera arquivos csv das analises

Arquivos são sumarizados (mediana, média e desvio padrão)

### Hipoteses:

A popularidade do repositório não está diretamente atrelada a sua qualidade interna

Quanto mais velho o repositório mais dívida técnica foi acumulada e portanto pior a qualidade

Quanto mais ativo o repositório mais dificil se torna a comunicação e garantia da qualidade constante, portanto a qualidade tende a descer

Quanto maior o tamanho do repositório mais dificil se torna manter ele coeso (bonus: Relação entre quantidade de comentários e qualidade? Ou gera mais docs ou documenta mais dívidas)