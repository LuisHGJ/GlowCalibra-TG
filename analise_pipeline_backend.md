# Análise Detalhada do Backend — GlowCalibra

## Sumário

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Arquitetura do Backend](#2-arquitetura-do-backend)
3. [Pipeline de Processamento — Passo a Passo](#3-pipeline-de-processamento--passo-a-passo)
   - 3.1 [Carregamento da Imagem](#31-carregamento-da-imagem)
   - 3.2 [Tratamento de Cor (Isolamento do Canal Vermelho)](#32-tratamento-de-cor-isolamento-do-canal-vermelho)
   - 3.3 [Conversão para Escala de Cinza](#33-conversão-para-escala-de-cinza)
   - 3.4 [Primeiro Desfoque Gaussiano (Blur)](#34-primeiro-desfoque-gaussiano-blur)
   - 3.5 [Limiarização Binária (Threshold Binary)](#35-limiarização-binária-threshold-binary)
   - 3.6 [Segundo Desfoque Gaussiano](#36-segundo-desfoque-gaussiano)
   - 3.7 [Inversão Bitwise NOT](#37-inversão-bitwise-not)
   - 3.8 [Segmentação de Componentes Conexos](#38-segmentação-de-componentes-conexos)
   - 3.9 [Detecção do Centro e Raio (Raycasting)](#39-detecção-do-centro-e-raio-raycasting)
   - 3.10 [Cálculo da Proporção Pixel → Centímetro](#310-cálculo-da-proporção-pixel--centímetro)
   - 3.11 [Aplicação da ROI Circular](#311-aplicação-da-roi-circular)
   - 3.12 [Conversão para Espaço de Cor HSV](#312-conversão-para-espaço-de-cor-hsv)
   - 3.13 [Criação da Máscara HSV (Isolamento das Gotas Fluorescentes)](#313-criação-da-máscara-hsv-isolamento-das-gotas-fluorescentes)
   - 3.14 [Aplicação da Máscara HSV](#314-aplicação-da-máscara-hsv)
   - 3.15 [Segunda Conversão para Escala de Cinza](#315-segunda-conversão-para-escala-de-cinza)
   - 3.16 [Limiarização de Otsu](#316-limiarização-de-otsu)
   - 3.17 [Fechamento Morfológico (Closing)](#317-fechamento-morfológico-closing)
   - 3.18 [Contagem de Gotas](#318-contagem-de-gotas)
   - 3.19 [Cálculo de Métricas Finais (Densidade e Cobertura)](#319-cálculo-de-métricas-finais-densidade-e-cobertura)
4. [Servidor e API REST](#4-servidor-e-api-rest)
5. [Arquivos de Saída Gerados](#5-arquivos-de-saída-gerados)
6. [Glossário Completo de Termos Técnicos](#6-glossário-completo-de-termos-técnicos)
7. [Diagrama Resumido do Fluxo](#7-diagrama-resumido-do-fluxo)

---

## 1. Visão Geral do Projeto

O **GlowCalibra** é um sistema de análise de imagens de **papéis hidrossensíveis** (ou alvos similares com gotas fluorescentes). O objetivo principal é:

- **Detectar** gotas fluorescentes depositadas sobre um alvo circular.
- **Contar** o número total de gotas.
- **Medir** a área e o diâmetro de cada gota individual.
- **Calcular métricas** como **densidade de gotas** (gotas/cm²) e **cobertura percentual** (%).

O sistema possui uma arquitetura **cliente-servidor**: o **frontend** (Next.js) envia uma imagem via upload, o **backend** (Flask + OpenCV) processa a imagem através de uma pipeline de visão computacional e retorna os resultados (imagens processadas, CSVs com dados das gotas e um resumo com as métricas).

A constante fundamental do sistema é o **diâmetro real do alvo circular**, definido como:

$$D_{alvo} = 4{,}6 \text{ cm}$$

Esse valor é essencial para converter medidas de pixels para centímetros.

---

## 2. Arquitetura do Backend

### 2.1 Estrutura de Pastas

```
backend/
├── core/
│   ├── server.py              ← Servidor Flask (API REST)
│   ├── teste.py               ← Script avulso de teste
│   ├── input/                 ← Pasta onde imagens enviadas são salvas
│   ├── output/                ← Pasta onde resultados são gerados
│   ├── src/                   ← Módulos de processamento
│   │   ├── IO/
│   │   │   └── file_management.py  ← Leitura/escrita de imagens e CSV
│   │   ├── processing/
│   │   │   ├── filters.py          ← Filtros (blur, laplaciano)
│   │   │   ├── logical_ops.py      ← Operações lógicas (NOT)
│   │   │   ├── morphology.py       ← Operações morfológicas (closing)
│   │   │   └── segmentation.py     ← Segmentação, limiarização, HSV, ROI
│   │   └── post_processing/
│   │       ├── count_drops.py      ← Contagem de gotas e extração de dados
│   │       └── find_proportion.py  ← Cálculo de proporção px→cm
│   └── testes/
│       └── pipeline.py        ← Pipeline principal (orquestra tudo)
└── requirements.txt           ← Dependências Python
```

### 2.2 Tecnologias Principais

| Tecnologia | Versão | Função |
|---|---|---|
| **Python** | 3.x | Linguagem principal |
| **Flask** | 3.1.0 | Framework web para a API REST |
| **Flask-CORS** | 5.0.1 | Permite requisições cross-origin (frontend ↔ backend) |
| **OpenCV** (opencv-python) | 4.11.0.86 | Processamento de imagens (visão computacional) |
| **NumPy** | 2.3.0 | Manipulação de arrays multidimensionais (imagens são arrays) |
| **Pandas** | 2.3.0 | Leitura de CSV para retorno ao frontend |

### 2.3 Fluxo Geral

```
[Frontend]                          [Backend]
    │                                   │
    │  POST /process (imagem)           │
    │──────────────────────────────────>│
    │                                   ├── Salva imagem em input/
    │                                   ├── Cria pasta timestamped em output/
    │                                   ├── Executa pipeline(image_path, output_dir)
    │                                   │     ├── 18+ etapas de processamento
    │                                   │     ├── Salva imagens intermediárias
    │                                   │     ├── Gera resultados.csv
    │                                   │     └── Gera resumo.csv
    │                                   ├── Lê resumo.csv
    │  JSON { status, results, resumo } │
    │<──────────────────────────────────│
```

---

## 3. Pipeline de Processamento — Passo a Passo

A pipeline está implementada na função `pipeline()` do arquivo `backend/core/testes/pipeline.py`. Ela recebe dois parâmetros:

- `image_path` — caminho absoluto da imagem de entrada.
- `output_dir` — caminho da pasta onde os resultados serão salvos.

A seguir, cada etapa é descrita em detalhe.

---

### 3.1 Carregamento da Imagem

**Arquivo:** `src/IO/file_management.py` → função `load_image()`

**O que faz:** Lê a imagem do disco para a memória usando `cv2.imread()`.

**Detalhes técnicos:**

Uma imagem digital colorida é armazenada como um **array tridimensional NumPy** com shape `(altura, largura, 3)`, onde as 3 camadas representam os canais de cor **B** (Blue), **G** (Green) e **R** (Red) — nesta ordem, que é o padrão do OpenCV (diferente do padrão RGB mais comum).

Cada pixel é representado por 3 valores inteiros de 0 a 255 (tipo `uint8`), onde:
- `0` = ausência total daquela cor
- `255` = intensidade máxima daquela cor

**Exemplo:** Uma imagem 4000×3000 pixels colorida gera um array de shape `(3000, 4000, 3)` com 36 milhões de valores.

```
image.shape = (3000, 4000, 3)
image.dtype = uint8
```

A função `load_image` aceita tanto um nome de arquivo (buscando na pasta `input/`) quanto um caminho absoluto.

---

### 3.2 Tratamento de Cor (Isolamento do Canal Vermelho)

**Arquivo:** `src/processing/segmentation.py` → função `color_treatment()`

**O que faz:** Remove os canais Azul (B) e Verde (G) da imagem, mantendo apenas o canal **Vermelho (R)**.

**Por que isso é feito:**

O alvo circular (papel hidrossensível) possui uma cor de fundo que se destaca no canal vermelho. Ao eliminar os canais azul e verde, o fundo do alvo fica mais visível e separável do restante da imagem, facilitando a detecção da forma circular do alvo.

**Matematicamente:**

Para cada pixel na posição $(x, y)$:

$$\text{pixel}(x,y) = \begin{bmatrix} B \\ G \\ R \end{bmatrix} \longrightarrow \begin{bmatrix} 0 \\ 0 \\ R \end{bmatrix}$$

O canal B é zerado ($B := 0$) e o canal G é zerado ($G := 0$). Apenas o valor original de R é preservado.

**Implementação:**
```python
b, g, r = cv2.split(image)   # Separa os 3 canais
b[:] = 0                      # Zera todo o canal Azul
g[:] = 0                      # Zera todo o canal Verde
noBlue = cv2.merge([b, g, r]) # Remonta a imagem com 3 canais
```

**Saída salva como:** `color_treatment.jpg`

---

### 3.3 Conversão para Escala de Cinza

**Arquivo:** `src/processing/segmentation.py` → função `grayScale()`

**O que faz:** Converte a imagem de 3 canais (BGR) para 1 único canal (escala de cinza).

**Fórmula:**

O OpenCV usa a fórmula de **luminância ponderada** (padrão ITU-R BT.601) para converter BGR em grayscale:

$$Y = 0{,}114 \cdot B + 0{,}587 \cdot G + 0{,}299 \cdot R$$

Como os canais B e G já foram zerados na etapa anterior, a fórmula efetivamente se reduz a:

$$Y = 0{,}299 \cdot R$$

Ou seja, a imagem grayscale resultante é essencialmente **29,9% do canal vermelho original**, produzindo uma imagem onde as regiões ricas em vermelho (o alvo) aparecem como áreas mais claras e o restante como áreas mais escuras.

**Shape resultante:**
```
Antes: (H, W, 3)  → Depois: (H, W)
```

A imagem passa de 3 dimensões para 2 dimensões (um único canal).

---

### 3.4 Primeiro Desfoque Gaussiano (Blur)

**Arquivo:** `src/processing/filters.py` → função `blur()`

**O que faz:** Aplica um **filtro Gaussiano** com kernel de tamanho **11×11** e sigma = 2, suavizando a imagem.

**Por que isso é feito:**

O desfoque remove **ruído de alta frequência** (variações bruscas de intensidade entre pixels vizinhos) e pequenas imperfeições que poderiam gerar falsos positivos na limiarização seguinte. É uma etapa de **pré-processamento** clássica em visão computacional.

**O que é um Kernel (Núcleo):**

Um kernel é uma pequena matriz (neste caso 11×11 = 121 elementos) que é "deslizada" sobre cada pixel da imagem. Para cada posição, o novo valor do pixel central é calculado como uma **média ponderada** dos pixels cobertos pelo kernel.

**Função Gaussiana 2D:**

O peso de cada posição $(x, y)$ no kernel é dado pela **distribuição Gaussiana bidimensional**:

$$G(x, y) = \frac{1}{2\pi\sigma^2} \cdot e^{-\frac{x^2 + y^2}{2\sigma^2}}$$

Onde:
- $(x, y)$ é a posição relativa ao centro do kernel
- $\sigma$ (sigma) é o **desvio padrão**, que controla o "espalhamento" do desfoque. Neste caso, $\sigma = 2$.
- $e$ é a base do logaritmo natural (≈ 2,71828)

**Intuição:** Os pixels mais próximos do centro têm peso maior (contribuem mais) e os mais distantes têm peso menor. Isso produz um desfoque "suave" e natural, diferente de uma média simples que trataria todos os vizinhos igualmente.

**Operação de convolução:**

Para cada pixel $I(x,y)$ da imagem, o resultado $I'(x,y)$ é:

$$I'(x, y) = \sum_{i=-k}^{k} \sum_{j=-k}^{k} G(i, j) \cdot I(x+i, y+j)$$

Onde $k = 5$ (metade do kernel 11×11, excluindo o centro).

---

### 3.5 Limiarização Binária (Threshold Binary)

**Arquivo:** `src/processing/segmentation.py` → função `thresholdBinary()`

**O que faz:** Transforma a imagem grayscale em uma **imagem binária** (preto e branco puro), usando um limiar (threshold) fixo de **1**.

**Fórmula:**

Para cada pixel $I(x,y)$:

$$I'(x, y) = \begin{cases} 255 & \text{se } I(x,y) > 1 \\ 0 & \text{se } I(x,y) \leq 1 \end{cases}$$

**Resultado:** Qualquer pixel com intensidade maior que 1 (ou seja, praticamente qualquer pixel que não seja completamente preto) se torna **branco** (255). Pixels completamente pretos (valor 0 ou 1) permanecem **pretos** (0).

**Por que o limiar é tão baixo (1)?**

Porque nesta etapa o objetivo é apenas separar o **alvo** (região que tinha conteúdo no canal vermelho, agora com alguma intensidade > 0) do **fundo preto** (regiões sem conteúdo vermelho). O limiar baixo garante que toda a área do alvo seja capturada como uma "mancha branca".

**Saída salva como:** `threshold_binary.jpg`

---

### 3.6 Segundo Desfoque Gaussiano

**O que faz:** Aplica novamente o filtro Gaussiano, desta vez com kernel **9×9**.

**Por que:**

Após a binarização, as bordas do alvo podem estar irregulares (dentadas). Este segundo blur suaviza essas bordas, criando uma transição mais gradual que será aproveitada na próxima etapa de inversão e segmentação.

A fórmula é a mesma do item 3.4, apenas com kernel menor (9×9 em vez de 11×11), resultando em um desfoque menos agressivo.

---

### 3.7 Inversão Bitwise NOT

**Arquivo:** `src/processing/logical_ops.py` → função `bitwise_not()`

**O que faz:** Inverte todos os bits de cada pixel da imagem.

**Fórmula:**

Para cada pixel com valor $v$ (8 bits, ou seja, 0–255):

$$v' = 255 - v$$

Ou equivalentemente, em operação bit a bit:

$$v' = \sim v = \text{NOT}(v)$$

**Exemplo:**
- Pixel branco (255 = `11111111` em binário) → preto (0 = `00000000`)
- Pixel preto (0 = `00000000`) → branco (255 = `11111111`)
- Pixel cinza (128 = `10000000`) → 127 = `01111111`

**Por que:**

Após a binarização, o alvo estava em **branco** e o fundo em **preto**. A inversão faz com que o **fundo fique branco** e o **alvo fique preto**. Isso é necessário porque a próxima etapa (`segment_components`) procura por componentes brancos — e queremos encontrar as regiões **externas** ao alvo para poder isolá-lo.

Na prática, após a inversão, tudo que **não** é o alvo fica branco (componentes grandes), e o alvo circular fica como um "buraco" preto. A segmentação vai filtrar os componentes grandes (o fundo externo), permitindo calcular onde está a borda do alvo.

**Saída salva como:** `bitwise_not.jpg`

---

### 3.8 Segmentação de Componentes Conexos

**Arquivo:** `src/processing/segmentation.py` → função `segment_components()`

**O que faz:** Identifica **componentes conexos** (regiões contíguas de pixels brancos) na imagem binária e mantém apenas aqueles com **área ≥ 20.000 pixels**.

**O que são "Componentes Conexos" (Connected Components):**

Em uma imagem binária, um componente conexo é um grupo de pixels brancos (255) em que cada pixel está **conectado** a pelo menos um outro pixel do mesmo grupo, diretamente adjacente (usando conectividade-8, que inclui vizinhos diagonais).

**Conectividade-8** significa que cada pixel pode se conectar a até 8 vizinhos:

```
[NW] [N] [NE]
[W]  [X] [E]
[SW] [S] [SE]
```

**Algoritmo usado:** `cv2.connectedComponentsWithStats()` — Um algoritmo de **rotulação** (labeling) que:
1. Percorre toda a imagem.
2. Atribui um **rótulo numérico** (1, 2, 3, ...) a cada grupo conexo distinto.
3. O rótulo 0 é reservado para o **fundo** (background).
4. Para cada rótulo, calcula **estatísticas**: posição (x, y), largura, altura e **área**.

**Filtragem por área:**

```python
for lbl in range(1, nLabels):
    area = stats[lbl, cv2.CC_STAT_AREA]
    if area >= min_area:      # min_area = 20000
        filtered[labels == lbl] = 255
```

Componentes com área < 20.000 pixels são **descartados** (considerados ruído). Apenas componentes grandes são preservados — estes correspondem ao fundo externo ao alvo (a região invertida).

**Resultado:** Uma imagem binária "limpa" onde apenas as grandes regiões brancas (fundo externo ao alvo) permanecem. Isso permite, na próxima etapa, encontrar com precisão onde está a **borda** do alvo circular.

---

### 3.9 Detecção do Centro e Raio (Raycasting)

**Arquivo:** `src/processing/segmentation.py` → função `find_center()`

**O que faz:** Determina o **centro** $(c_x, c_y)$ e o **raio** $r$ do alvo circular na imagem, usando uma técnica de **raycasting** (lançamento de raios).

**O que é Raycasting:**

Raycasting é uma técnica em que "raios" (linhas imaginárias) são disparados de pontos de partida em direção a um alvo. Quando o raio "atinge" algo (neste caso, um pixel branco), a posição do impacto é registrada.

**Algoritmo passo a passo:**

1. **Define 8 pontos de partida** nas bordas e cantos da imagem:
   - Centro superior: $(W/2, 0)$
   - Centro inferior: $(W/2, H-1)$
   - Centro esquerdo: $(0, H/2)$
   - Centro direito: $(W-1, H/2)$
   - Canto superior esquerdo: $(0, 0)$
   - Canto superior direito: $(W-1, 0)$
   - Canto inferior esquerdo: $(0, H-1)$
   - Canto inferior direito: $(W-1, H-1)$

2. **Para cada ponto de partida**, calcula o **vetor direção** apontando para o centro geométrico da imagem:

$$\vec{d} = \frac{\vec{p}_{centro\_img} - \vec{p}_{start}}{||\vec{p}_{centro\_img} - \vec{p}_{start}||}$$

Onde $||\cdot||$ é a norma euclidiana (distância):

$$||\vec{v}|| = \sqrt{v_x^2 + v_y^2}$$

3. **Caminha pixel a pixel** ao longo do raio (incrementando $t$ de 1 em 1):

$$\vec{p}(t) = \vec{p}_{start} + t \cdot \vec{d}$$

4. **Para em dois casos:**
   - O pixel na posição $\vec{p}(t)$ é **branco** (255) → registra como "ponto de impacto" (hitPoint).
   - O raio chegou ao centro da imagem sem encontrar nada.

5. **Calcula o centro** como a **média aritmética** de todos os pontos de impacto:

$$c_x = \frac{1}{n}\sum_{i=1}^{n} x_i, \quad c_y = \frac{1}{n}\sum_{i=1}^{n} y_i$$

6. **Calcula o raio** como a **distância média** de cada ponto de impacto ao centro calculado:

$$r_i = \sqrt{(x_i - c_x)^2 + (y_i - c_y)^2}$$

$$\bar{r} = \frac{1}{n}\sum_{i=1}^{n} r_i$$

7. **Filtra outliers:** Remove raios $r_i$ que diferem da média por mais de `margin` (20 pixels):

$$r_{final} = \text{média}\{r_i : |r_i - \bar{r}| \leq 20\}$$

**Resultado:** O centro $(c_x, c_y)$ e o raio $r_{final}$ do alvo, ambos em pixels.

**Por que usar raycasting e não detecção de círculos (Hough)?**

A técnica de raycasting é mais robusta para este caso específico porque:
- O alvo pode não ser perfeitamente circular na imagem (distorções de câmera).
- A borda pode não estar completamente definida.
- É computacionalmente mais simples e previsível.

---

### 3.10 Cálculo da Proporção Pixel → Centímetro

**Arquivo:** `src/post_processing/find_proportion.py` → função `find_proportion()`

**O que faz:** Calcula o **fator de conversão** de pixels para centímetros.

**Fórmula:**

$$\text{proporção} = \frac{r_{cm}}{r_{px}}$$

Onde:
- $r_{cm} = \frac{D_{alvo}}{2} = \frac{4{,}6}{2} = 2{,}3$ cm (raio real do alvo)
- $r_{px}$ = raio do alvo detectado em pixels (obtido na etapa 3.9)

**Unidade:** A proporção tem unidade de $\text{cm/px}$ (centímetros por pixel).

**Exemplo numérico:** Se o raio detectado for de 1415 pixels:

$$\text{proporção} = \frac{2{,}3}{1415} \approx 0{,}001626 \text{ cm/px}$$

Isso significa que cada pixel da imagem corresponde a aproximadamente 0,001626 cm (≈ 16,26 µm) no mundo real.

---

### 3.11 Aplicação da ROI Circular

**Arquivo:** `src/processing/segmentation.py` → função `apply_circular_roi()`

**O que faz:** Aplica uma **Região de Interesse (ROI — Region of Interest)** circular sobre a **imagem original** (colorida), "recortando" apenas a área dentro do alvo detectado.

**Como funciona:**

1. Cria uma **máscara** preta (toda zeros) do mesmo tamanho da imagem.
2. Desenha um **círculo branco preenchido** na máscara, centrado em $(c_x, c_y)$ com raio $r_{final}$.
3. Aplica a máscara usando **AND bit a bit** (bitwise AND):

$$I'(x, y) = I(x, y) \text{ AND } M(x, y)$$

Onde $M(x,y)$ é a máscara:

$$M(x, y) = \begin{cases} 255 & \text{se } \sqrt{(x - c_x)^2 + (y - c_y)^2} \leq r \\ 0 & \text{caso contrário} \end{cases}$$

**Resultado:** A imagem original com tudo **fora** do alvo circular convertido em preto (0). Apenas os pixels dentro do alvo preservam seus valores originais.

**Importância:** A partir daqui, todo processamento ocorre **apenas dentro do alvo**, eliminando qualquer interferência do fundo.

**Saída salva como:** `final_mask.jpg`

---

### 3.12 Conversão para Espaço de Cor HSV

**Arquivo:** `src/processing/segmentation.py` → função `convertToHSV()`

**O que faz:** Converte a imagem do espaço de cor **BGR** para **HSV**.

**O que é o espaço de cor HSV:**

HSV é um modelo de representação de cores com 3 componentes:

| Componente | Significado | Faixa no OpenCV | Descrição |
|---|---|---|---|
| **H** (Hue / Matiz) | A "cor pura" | 0–179 | Representa o tipo da cor em um círculo cromático (0=vermelho, 60=amarelo, 120=verde, 90–160 faixa azul-roxa) |
| **S** (Saturation / Saturação) | Pureza da cor | 0–255 | 0=cinza/branco, 255=cor totalmente pura/vívida |
| **V** (Value / Valor) | Brilho | 0–255 | 0=preto, 255=brilho máximo |

**Por que usar HSV em vez de BGR/RGB?**

No espaço BGR, a "cor" de um pixel é uma combinação dos 3 canais, tornando difícil isolar uma cor específica. No espaço HSV, a **matiz (H)** codifica diretamente o tipo de cor, independente do brilho ou saturação. Isso torna muito mais fácil criar uma máscara que selecione "todos os pixels azuis/roxos" — que é exatamente a cor das gotas fluorescentes.

**Fórmulas de conversão BGR→HSV (simplificadas):**

Dado $R, G, B \in [0, 255]$, normalizados para $[0, 1]$ como $r, g, b$:

$$V = \max(r, g, b)$$

$$S = \begin{cases} \frac{V - \min(r,g,b)}{V} & \text{se } V \neq 0 \\ 0 & \text{se } V = 0 \end{cases}$$

$$H = \begin{cases} 60 \cdot \frac{g - b}{V - \min(r,g,b)} & \text{se } V = r \\ 60 \cdot \left(2 + \frac{b - r}{V - \min(r,g,b)}\right) & \text{se } V = g \\ 60 \cdot \left(4 + \frac{r - g}{V - \min(r,g,b)}\right) & \text{se } V = b \end{cases}$$

(No OpenCV, H é dividido por 2 para caber em uint8, logo $H \in [0, 179]$.)

---

### 3.13 Criação da Máscara HSV (Isolamento das Gotas Fluorescentes)

**Arquivo:** `src/processing/segmentation.py` → função `createHSVMask()`

**O que faz:** Cria uma **máscara binária** que seleciona apenas os pixels cuja cor está na faixa **azul-roxa** — correspondente às gotas fluorescentes.

**Faixas definidas:**

| Canal | Limite Inferior | Limite Superior |
|---|---|---|
| H (Matiz) | 90 | 160 |
| S (Saturação) | 50 | 255 |
| V (Valor) | 50 | 255 |

**Fórmula:**

$$M(x,y) = \begin{cases} 255 & \text{se } H_{low} \leq H(x,y) \leq H_{high} \text{ AND } S_{low} \leq S(x,y) \leq S_{high} \text{ AND } V_{low} \leq V(x,y) \leq V_{high} \\ 0 & \text{caso contrário} \end{cases}$$

Onde:
- $H_{low} = 90$, $H_{high} = 160$ → captura matizes de azul (≈120) até roxo/magenta (≈160)
- $S_{low} = 50$ → exclui pixels "quase cinza" (saturação muito baixa)
- $V_{low} = 50$ → exclui pixels muito escuros (quase pretos)

**Intuição:** No círculo cromático HSV, o intervalo [90, 160] cobre desde um azul-ciano até um roxo/violeta, que é exatamente a faixa de cores emitidas pelas gotas fluorescentes sob iluminação UV.

---

### 3.14 Aplicação da Máscara HSV

**Arquivo:** `src/processing/segmentation.py` → função `applyMask()`

**O que faz:** Aplica a máscara HSV sobre a imagem HSV usando **AND bit a bit**, mantendo apenas os pixels que passaram no filtro de cor.

$$I'(x,y) = I(x,y) \text{ AND } M_{HSV}(x,y)$$

**Resultado:** Uma imagem onde apenas as gotas fluorescentes (azuis/roxas) são visíveis, com todo o restante (fundo do alvo, bordas, etc.) zerado (preto).

---

### 3.15 Segunda Conversão para Escala de Cinza

**O que faz:** Converte o resultado da etapa anterior (imagem HSV mascarada) para **escala de cinza**, preparando para a limiarização final.

Usa a mesma fórmula de luminância descrita na seção 3.3.

---

### 3.16 Limiarização de Otsu

**Arquivo:** `src/processing/segmentation.py` → função `thresholdOtsu()`

**O que faz:** Aplica o **método de Otsu** para encontrar automaticamente o **melhor limiar** de binarização.

**O que é o Método de Otsu:**

O método de Otsu (proposto por Nobuyuki Otsu em 1979) é um algoritmo que encontra automaticamente o valor de limiar $T^*$ que melhor separa os pixels em duas classes (foreground e background), maximizando a **variância entre classes** (ou equivalentemente, minimizando a **variância intra-classes**).

**Fundamento matemático:**

Dado um histograma de intensidades $h(i)$, $i \in [0, 255]$, com $N$ pixels totais:

1. **Probabilidade** de cada intensidade: $p(i) = \frac{h(i)}{N}$

2. Para um limiar $T$, define-se duas classes:
   - **Classe 0** (background): pixels com intensidade $\leq T$
   - **Classe 1** (foreground): pixels com intensidade $> T$

3. **Peso** de cada classe:

$$\omega_0(T) = \sum_{i=0}^{T} p(i), \quad \omega_1(T) = \sum_{i=T+1}^{255} p(i) = 1 - \omega_0(T)$$

4. **Média** de cada classe:

$$\mu_0(T) = \frac{\sum_{i=0}^{T} i \cdot p(i)}{\omega_0(T)}, \quad \mu_1(T) = \frac{\sum_{i=T+1}^{255} i \cdot p(i)}{\omega_1(T)}$$

5. **Variância entre classes (inter-class variance):**

$$\sigma_B^2(T) = \omega_0(T) \cdot \omega_1(T) \cdot (\mu_0(T) - \mu_1(T))^2$$

6. **Limiar ótimo de Otsu:**

$$T^* = \arg\max_{0 \leq T \leq 255} \sigma_B^2(T)$$

O algoritmo testa todos os 256 possíveis valores de $T$ e escolhe aquele que maximiza $\sigma_B^2$.

**Resultado da binarização:**

$$I'(x,y) = \begin{cases} 255 & \text{se } I(x,y) > T^* \\ 0 & \text{se } I(x,y) \leq T^* \end{cases}$$

**Vantagem:** Não é necessário definir manualmente o limiar — o algoritmo encontra o valor ótimo automaticamente com base na distribuição de intensidades da imagem.

**Nota:** No código, o valor `1` passado como segundo argumento para `cv2.threshold()` é ignorado quando se usa `THRESH_OTSU`, pois o Otsu calcula o limiar automaticamente.

**Saída salva como:** `final_threshold.jpg`

---

### 3.17 Fechamento Morfológico (Closing)

**Arquivo:** `src/processing/morphology.py` → função `closing()`

**O que faz:** Aplica uma operação de **fechamento morfológico** para preencher pequenos buracos e conectar regiões próximas nas gotas binarizadas.

**O que são Operações Morfológicas:**

São transformações aplicadas a imagens binárias baseadas na **geometria** dos objetos. As duas operações fundamentais são:

1. **Dilatação (Dilation):** Expande as regiões brancas. Cada pixel branco "cresce" para seus vizinhos.
2. **Erosão (Erosion):** Encolhe as regiões brancas. Pixels brancos nas bordas são removidos.

**Fechamento (Closing) = Dilatação seguida de Erosão:**

$$\text{Closing}(I) = \text{Erosion}(\text{Dilation}(I))$$

**Implementação no código:**

```python
image = cv2.dilate(image, None, iterations=2)   # 2 iterações de dilatação
image = cv2.erode(image, None, iterations=2)     # 2 iterações de erosão
```

O parâmetro `None` para o kernel significa que o OpenCV usa um kernel padrão 3×3 em forma de cruz (+).

**Efeito de cada etapa:**

1. **Dilatação (2×):** 
   - Cada pixel branco "cresce" em 2 pixels em todas as direções.
   - Pequenos buracos dentro das gotas são **preenchidos**.
   - Gotas próximas podem se **conectar**.
   - As gotas ficam ligeiramente **maiores**.

2. **Erosão (2×):**
   - Cada região branca "encolhe" em 2 pixels.
   - As gotas voltam aproximadamente ao **tamanho original**.
   - Os buracos preenchidos **permanecem** preenchidos.
   - Pequenos pontos de ruído que surgiram na dilatação são **removidos**.

**Formalmente (com elemento estruturante $B$):**

$$\text{Dilation: } (I \oplus B)(x,y) = \max_{(i,j) \in B} I(x+i, y+j)$$

$$\text{Erosion: } (I \ominus B)(x,y) = \min_{(i,j) \in B} I(x+i, y+j)$$

$$\text{Closing: } I \bullet B = (I \oplus B) \ominus B$$

**Saída salva como:** `final_image.jpg`

---

### 3.18 Contagem de Gotas

**Arquivo:** `src/post_processing/count_drops.py` → função `count_drops()`

**O que faz:** Encontra e conta todas as gotas individuais na imagem binária final, extraindo suas propriedades geométricas (posição, área, diâmetro).

**Algoritmo detalhado:**

#### Passo 1 — Encontrar Contornos

```python
contornos, _ = cv2.findContours(imagem_binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```

**O que são Contornos:**

Um contorno é uma **curva fechada** que delimita a borda de um objeto branco em uma imagem binária. O algoritmo `findContours` (baseado no algoritmo de Suzuki & Abe, 1985) percorre a imagem e identifica todas essas curvas.

Parâmetros:
- `cv2.RETR_EXTERNAL` → retorna apenas os contornos **externos** (ignora buracos dentro de objetos).
- `cv2.CHAIN_APPROX_SIMPLE` → comprime segmentos retilíneos (em vez de armazenar todos os pixels da borda, armazena apenas os pontos de inflexão).

#### Passo 2 — Para cada contorno, calcular propriedades

**a) Área do contorno:**

$$A = \text{cv2.contourArea(contorno)}$$

Utiliza a **fórmula de Shoelace** (fórmula da área de Gauss) para calcular a área encerrada pelo polígono do contorno:

$$A = \frac{1}{2} \left| \sum_{i=0}^{n-1} (x_i \cdot y_{i+1} - x_{i+1} \cdot y_i) \right|$$

Gotas com área < 1 pixel são descartadas (ruído).

**b) Momentos de imagem:**

$$M = \text{cv2.moments(contorno)}$$

**Momentos** são medidas estatísticas da distribuição espacial dos pixels de um contorno. Os momentos mais básicos são:

$$m_{pq} = \sum_{(x,y) \in \text{contorno}} x^p \cdot y^q$$

Onde:
- $m_{00}$ = área (soma de todos os pixels, cada um com peso 1)
- $m_{10}$ = soma das coordenadas x ponderadas
- $m_{01}$ = soma das coordenadas y ponderadas

**c) Centróide (centro de massa):**

O centróide $(c_x, c_y)$ de cada gota é calculado a partir dos momentos:

$$c_x = \frac{m_{10}}{m_{00}}, \quad c_y = \frac{m_{01}}{m_{00}}$$

**Intuição:** É a "posição média" de todos os pixels da gota — o ponto que seria o centro de equilíbrio se a gota fosse um objeto físico plano.

**d) Conversão para centímetros:**

$$A_{cm} = A_{px} \cdot (\text{proporção})^2$$

$$x_{cm} = c_x \cdot \text{proporção}, \quad y_{cm} = c_y \cdot \text{proporção}$$

A área é multiplicada pelo **quadrado** da proporção porque área é uma grandeza bidimensional ($cm^2 = px^2 \cdot (cm/px)^2$).

**e) Diâmetro equivalente:**

Calcula o diâmetro de um **círculo com a mesma área** que a gota:

$$d = 2 \cdot \sqrt{\frac{A_{cm}}{\pi}}$$

Derivação: Se $A = \pi r^2$, então $r = \sqrt{\frac{A}{\pi}}$ e $d = 2r$.

#### Passo 3 — Gerar visualização

Para cada gota, o algoritmo:
- Desenha o contorno em branco sobre fundo preto.
- Escreve o número (índice) da gota em verde na posição do centróide.

#### Passo 4 — Gerar máscara de rótulos

Cria uma imagem onde cada pixel pertencente a uma gota recebe o **valor do índice** daquela gota (1, 2, 3, ...). Pixels que não pertencem a nenhuma gota têm valor 0.

**Saídas:**
- `vis.jpg` — imagem de visualização com contornos e números.
- `resultados.csv` — CSV com colunas: Index, X, Y, Area, Diameter.

---

### 3.19 Cálculo de Métricas Finais (Densidade e Cobertura)

**Localização:** Diretamente na função `pipeline()`.

**O que faz:** Calcula as duas métricas principais de qualidade da pulverização.

#### a) Área total do alvo

$$A_{total} = \pi \cdot r_{cm}^2$$

Onde $r_{cm} = r_{px} \cdot \text{proporção}$. Idealmente, $r_{cm} \approx 2{,}3$ cm, então $A_{total} \approx \pi \cdot 2{,}3^2 \approx 16{,}62$ cm².

#### b) Número total de gotas

$$N = |\text{data}|$$

É simplesmente o comprimento da lista de dados das gotas.

#### c) Área total das gotas

$$A_{gotas} = \sum_{i=1}^{N} A_i$$

Soma das áreas individuais de cada gota (em cm²).

#### d) Densidade

$$\rho = \frac{N}{A_{total}} \quad \text{[gotas/cm²]}$$

Quantas gotas existem por centímetro quadrado de área do alvo.

#### e) Cobertura

$$C = \frac{A_{gotas}}{A_{total}} \times 100 \quad \text{[%]}$$

Qual porcentagem da área total do alvo está coberta por gotas.

**Saída:** Estas métricas são salvas em `resumo.csv` com as colunas: "Total gotas", "Densidade (gotas/cm²)", "Cobertura (%)".

---

## 4. Servidor e API REST

### 4.1 Visão Geral

O servidor é implementado em `backend/core/server.py` usando **Flask**, um microframework web para Python. Ele escuta na porta **5000** e expõe 3 endpoints.

### 4.2 Endpoints

#### `POST /process`

**Função:** Recebe uma imagem, processa-a e retorna os resultados.

**Corpo da requisição:** `multipart/form-data` com um campo `file` contendo a imagem.

**Fluxo interno:**
1. Salva a imagem em `core/input/<nome_original>`.
2. Cria uma subpasta em `core/output/` com formato `<nome>_<timestamp>` (ex: `foto_20260305_143022`).
3. Chama `pipeline(image_path, output_subdir)`.
4. Lê o `resumo.csv` gerado.
5. Retorna JSON:

```json
{
  "status": "ok",
  "results": [
    "http://localhost:5000/files/<subdir>/final_image.jpg",
    "http://localhost:5000/files/<subdir>/vis.jpg",
    "http://localhost:5000/files/<subdir>/resultados.csv",
    "http://localhost:5000/files/<subdir>/resumo.csv"
  ],
  "resumo": [
    {
      "Total gotas": 245,
      "Densidade (gotas/cm²)": 14.75,
      "Cobertura (%)": 3.21
    }
  ]
}
```

#### `GET /files/<subdir>/<filename>`

**Função:** Serve arquivos estáticos gerados pelo processamento (imagens e CSVs).

O frontend usa as URLs retornadas no campo `results` para exibir as imagens processadas e baixar os CSVs.

#### `GET /download_csvs/<subdir>`

**Função:** Gera e retorna um arquivo **ZIP** contendo `resumo.csv` e `resultados.csv`.

Permite ao usuário baixar todos os dados em um único arquivo compactado.

### 4.3 CORS

```python
CORS(app, resources={r"/*": {"origins": "*"}})
```

**CORS (Cross-Origin Resource Sharing)** é um mecanismo de segurança dos navegadores que, por padrão, impede que um site (ex: `localhost:3000` do frontend Next.js) faça requisições para outro domínio/porta (ex: `localhost:5000` do backend Flask). A configuração `origins: "*"` permite requisições de **qualquer origem**, necessário durante o desenvolvimento.

---

## 5. Arquivos de Saída Gerados

A pipeline gera os seguintes arquivos na pasta de output:

| # | Arquivo | Tipo | Etapa | Descrição |
|---|---|---|---|---|
| 1 | `color_treatment.jpg` | Imagem | 3.2–3.3 | Imagem após remoção dos canais B/G e conversão para grayscale |
| 2 | `threshold_binary.jpg` | Imagem | 3.5 | Imagem binarizada (alvo branco, fundo preto) |
| 3 | `bitwise_not.jpg` | Imagem | 3.7 | Imagem invertida (alvo preto, fundo branco) |
| 4 | `final_mask.jpg` | Imagem | 3.11 | Imagem original com ROI circular aplicada |
| 5 | `final_threshold.jpg` | Imagem | 3.16 | Gotas binarizadas após Otsu (branco sobre preto) |
| 6 | `final_image.jpg` | Imagem | 3.17 | Gotas após fechamento morfológico (resultado final da segmentação) |
| 7 | `vis.jpg` | Imagem | 3.18 | Visualização com contornos desenhados e gotas numeradas |
| 8 | `resultados.csv` | CSV | 3.18 | Dados individuais de cada gota (Index, X, Y, Area, Diameter) |
| 9 | `resumo.csv` | CSV | 3.19 | Métricas globais (total gotas, densidade, cobertura) |

---

## 6. Glossário Completo de Termos Técnicos

### Array / ndarray
Estrutura de dados multidimensional do NumPy. Uma imagem grayscale é um array 2D (matriz), uma imagem colorida é um array 3D (tensor de ordem 3). Cada elemento armazena um valor numérico (geralmente `uint8`, inteiro de 0 a 255).

### BGR (Blue, Green, Red)
Ordem dos canais de cor usada pelo OpenCV. Diferente do RGB (Red, Green, Blue) usado pela maioria dos outros sistemas. A imagem `img[y, x]` retorna `[B, G, R]`.

### Binarização / Imagem Binária
Processo de converter uma imagem grayscale em uma imagem com apenas dois valores: 0 (preto) e 255 (branco). Cada pixel é classificado como "fundo" ou "objeto".

### Bitwise NOT (Negação bit a bit)
Operação que inverte todos os bits de cada byte. Para uint8: `NOT(v) = 255 - v`. Troca preto por branco e vice-versa.

### Bitwise AND (E bit a bit)
Operação entre dois valores que retorna 1 apenas quando ambos os bits correspondentes são 1. Usado para "mascarar" regiões: `pixel AND 0 = 0` (apaga), `pixel AND 255 = pixel` (preserva).

### Blur (Desfoque)
Suavização da imagem que reduz variações bruscas de intensidade. Cada pixel é substituído por uma média ponderada de seus vizinhos. Reduz ruído mas também borram detalhes finos.

### Centróide
Centro de massa de uma região/forma. Calculado como a média das coordenadas x e y de todos os pixels da região, ponderada por seus valores.

### Closing (Fechamento Morfológico)
Operação: dilatação seguida de erosão. Preenche pequenos buracos e conecta objetos próximos, sem alterar significativamente o tamanho dos objetos.

### Componentes Conexos (Connected Components)
Regiões de pixels brancos em uma imagem binária onde todos os pixels estão conectados entre si (direta ou indiretamente). Cada grupo isolado de pixels brancos é um componente distinto.

### Conectividade-4 vs Conectividade-8
- **4-conectividade:** Cada pixel tem 4 vizinhos (cima, baixo, esquerda, direita).
- **8-conectividade:** Cada pixel tem 8 vizinhos (inclui as 4 diagonais). O código usa 8-conectividade.

### Contorno
Curva que delimita a borda de um objeto em uma imagem binária. É uma sequência de pontos $(x, y)$ que formam um polígono fechado.

### Convolução
Operação matemática onde um kernel (filtro) é "deslizado" sobre a imagem, e para cada posição, calcula-se a soma ponderada dos pixels cobertos. É a base de muitas operações de processamento de imagem (blur, detecção de bordas, etc.).

### CORS (Cross-Origin Resource Sharing)
Mecanismo de segurança dos navegadores web que controla quais sites podem fazer requisições para outros domínios. Sem CORS habilitado, o frontend não conseguiria se comunicar com o backend.

### CSV (Comma-Separated Values)
Formato de arquivo de texto simples onde dados tabulares são separados por vírgulas. Cada linha é um registro, cada valor separado por vírgula é uma coluna.

### Dilatação (Dilation)
Operação morfológica que expande regiões brancas. Para cada pixel, se **qualquer** vizinho dentro do kernel for branco, o pixel se torna branco. Efeito: objetos crescem, buracos diminuem.

### Elemento Estruturante (Structuring Element)
Kernel usado em operações morfológicas. Define a "vizinhança" considerada. Pode ter diferentes formas (cruz, quadrado, elipse). No código, é o kernel padrão 3×3.

### Erosão (Erosion)
Operação morfológica que encolhe regiões brancas. Para cada pixel, **todos** os vizinhos dentro do kernel devem ser brancos para que o pixel permaneça branco. Efeito: objetos encolhem, pequenos pontos desaparecem.

### Escala de Cinza (Grayscale)
Imagem com um único canal onde cada pixel tem um valor de 0 (preto) a 255 (branco), representando intensidade luminosa. Não possui informação de cor.

### Flask
Microframework web em Python para criação de APIs e aplicações web. "Micro" porque fornece apenas o essencial (roteamento, templates), sem impor estrutura rígida.

### Fórmula de Shoelace (Fórmula do Cadarço)
Fórmula geométrica para calcular a área de um polígono a partir das coordenadas de seus vértices. Nome vem do padrão "cruzado" da multiplicação, similar a amarrar um cadarço.

### Função Gaussiana
Função em forma de "sino" usada como kernel de desfoque. Pixels mais próximos do centro contribuem mais, criando um efeito de suavização natural e isotrópica (igual em todas as direções).

### Histograma
Gráfico que mostra a distribuição de frequência das intensidades dos pixels em uma imagem. O eixo X vai de 0 a 255, o eixo Y mostra quantos pixels têm cada valor.

### HSV (Hue, Saturation, Value)
Espaço de cor que separa a informação de **cor** (H), **pureza** (S) e **brilho** (V). Mais intuitivo que RGB para segmentação por cor.

### Kernel (Núcleo)
Pequena matriz usada em operações de convolução e morfologia. Define os pesos (para convolução) ou a forma (para morfologia) da operação.

### Limiarização (Thresholding)
Técnica de segmentação que classifica cada pixel como "objeto" ou "fundo" com base em um valor de corte (limiar). Pixels acima do limiar se tornam brancos, abaixo se tornam pretos.

### Máscara (Mask)
Imagem binária usada para selecionar/ocultar regiões. Pixels brancos na máscara = região de interesse preservada. Pixels pretos = região descartada (zerada).

### Momentos de Imagem
Medidas estatísticas que descrevem a distribuição espacial dos pixels de uma região. Permitem calcular propriedades como área ($m_{00}$), centróide ($m_{10}/m_{00}$, $m_{01}/m_{00}$), orientação e forma.

### Método de Otsu
Algoritmo que encontra automaticamente o melhor limiar de binarização, maximizando a separação entre as duas classes de pixels (fundo e objeto). Não requer ajuste manual.

### OpenCV (Open Source Computer Vision Library)
Biblioteca open-source de visão computacional com milhares de funções para processamento de imagens, detecção de objetos, reconhecimento facial, etc. Originalmente escrita em C++, com bindings para Python.

### Pixel (Picture Element)
Menor unidade de uma imagem digital. Cada pixel contém um valor numérico que representa sua cor/intensidade. Uma imagem de 4000×3000 tem 12 milhões de pixels.

### Raycasting
Técnica de lançamento de "raios" (linhas retas imaginárias) a partir de pontos de origem em direções específicas, verificando onde eles intersectam objetos. Usado aqui para encontrar a borda do alvo circular.

### REST (Representational State Transfer)
Estilo arquitetural para APIs web. Usa verbos HTTP (GET, POST, etc.) e URLs para operações. No projeto: POST /process para enviar imagem, GET /files/... para obter resultados.

### ROI (Region of Interest)
Região de Interesse — subárea da imagem onde o processamento deve ser focado. No projeto, é a área circular correspondente ao alvo, excluindo o fundo.

### Ruído (Noise)
Variações aleatórias indesejadas nos valores dos pixels, causadas por sensor da câmera, iluminação, compressão, etc. O desfoque é uma técnica clássica de redução de ruído.

### Segmentação
Processo de dividir uma imagem em regiões significativas (objetos vs. fundo, gotas vs. alvo, etc.). É uma das tarefas fundamentais em visão computacional.

### Sigma (σ)
Desvio padrão da distribuição Gaussiana. Controla o "espalhamento" do kernel: σ maior = desfoque mais forte; σ menor = desfoque mais sutil.

### uint8
Tipo de dado "unsigned integer 8-bit" — inteiro sem sinal de 8 bits. Armazena valores de 0 a 255 ($2^8 - 1$). É o tipo padrão para pixels de imagem.

### Variância Entre Classes (Inter-class Variance)
No método de Otsu, é a medida de quão separadas estão as intensidades médias das duas classes (fundo e objeto). O limiar ótimo é aquele que maximiza essa separação.

---

## 7. Diagrama Resumido do Fluxo

```
IMAGEM ORIGINAL (BGR, colorida)
        │
        ▼
┌─────────────────────────┐
│  FASE 1: DETECÇÃO DO    │
│  ALVO CIRCULAR          │
├─────────────────────────┤
│ 1. color_treatment()    │──→ Remove canais B, G (isola R)
│ 2. grayScale()          │──→ Converte para escala de cinza
│ 3. blur(11×11)          │──→ Suaviza ruído
│ 4. thresholdBinary()    │──→ Binariza (limiar = 1)
│ 5. blur(9×9)            │──→ Suaviza bordas
│ 6. bitwise_not()        │──→ Inverte (fundo branco, alvo preto)
│ 7. segment_components() │──→ Filtra componentes ≥ 20000 px
│ 8. find_center()        │──→ Raycasting → (centro, raio)
│ 9. find_proportion()    │──→ cm/px = 2.3 / raio_px
│10. apply_circular_roi() │──→ Recorta ROI circular na imagem original
└─────────────────────────┘
        │
        ▼ (imagem original recortada no alvo)
┌─────────────────────────┐
│  FASE 2: SEGMENTAÇÃO    │
│  DAS GOTAS              │
├─────────────────────────┤
│11. convertToHSV()       │──→ BGR → HSV
│12. createHSVMask()      │──→ Máscara [H:90-160, S:50-255, V:50-255]
│13. applyMask()          │──→ Isola gotas fluorescentes
│14. grayScale()          │──→ Converte para escala de cinza
│15. thresholdOtsu()      │──→ Binariza com limiar automático
│16. closing()            │──→ Dilata 2× + Erode 2× (fecha buracos)
└─────────────────────────┘
        │
        ▼ (imagem binária: gotas brancas, fundo preto)
┌─────────────────────────┐
│  FASE 3: CONTAGEM E     │
│  MÉTRICAS               │
├─────────────────────────┤
│17. count_drops()        │──→ Contornos → centróide, área, diâmetro
│18. Cálculos finais      │──→ Densidade (gotas/cm²), Cobertura (%)
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│  SAÍDAS                 │
├─────────────────────────┤
│ • 7 imagens (.jpg)      │
│ • resultados.csv        │
│ • resumo.csv            │
└─────────────────────────┘
```

---

*Documento gerado automaticamente em 05/03/2026 como parte da análise do backend do projeto GlowCalibra.*
