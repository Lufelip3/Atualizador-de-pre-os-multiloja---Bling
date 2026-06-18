# Atualizador de Preços Multiloja — Bling  💰

> **v2.0** — Interface Dark, suporte a ZIPs, organização estruturada de pastas e validação inteligente de catálogo.

Ferramenta profissional para automatizar a atualização de preços de produtos em lojas virtuais (Shopee, Magalu, Nuvemshop, entre outras) com base nos valores cadastrados no Bling ERP. 

O objetivo é tornar o processo diário de precificação rápido, seguro e escalável, eliminando totalmente a edição manual de planilhas e evitando discrepâncias de preços entre canais de venda.

---

## 🚀 O que há de novo na Versão 2.0

- **Visual Premium (Tema Verde Dark):** Interface gráfica totalmente renovada com padrão dark financeiro, construída em arquitetura orientada a objetos (`interface.pyw`). Possui barra de progresso customizada, scrollbars integradas e suporte a redimensionamento (`resizable`).
- **Pasta centralizada `inputs/`:** Todos os arquivos de entrada agora ficam organizados dentro da pasta `inputs/`, mantendo a raiz do projeto limpa.
- **Suporte Nativo a arquivos `.zip`:** Descompactação e leitura direta de arquivos ZIP. Útil para exportações diretas do Bling. O programa adiciona o nome do ZIP como prefixo nos arquivos extraídos (ex: `shopee.zip` extrai produtos em `_extraidos/shopee_produtos.csv`), evitando conflitos de nomes.
- **Limpeza Automática:** Sempre que a atualização é executada, as pastas `saidas/` e `_extraidos/` são limpas automaticamente, garantindo que não existam arquivos residuais de atualizações antigas.
- **Validação de Catálogo Inteligente (Terminal Colorido):** Relatório detalhado diretamente no log da interface usando cores ANSI para destacar possíveis erros de sincronização:
  - 🔴 **Vermelho (FALTANTE):** Produto ativo no Bling que não foi encontrado em nenhuma das multilojas.
  - 🟠 **Laranja (PARCIAL):** Produto que está cadastrado em algumas lojas, mas falta em outras (inconsistência de catálogo).
  - 🟣 **Magenta (FANTASMA):** Produto ativo na multiloja que não existe no Bling exportado (cadastros diretos ou desatualizados).

---

## 📁 Estrutura do Projeto

```text
Atualizador de preços multiloja - Bling/
├── interface.pyw                 # Interface gráfica principal (Orientada a Objetos)
├── script.py                      # Motor de processamento (Executado em segundo plano)
├── COMO_USAR.txt                  # Manual simplificado de uso rápido
├── .gitignore                     # Configuração de arquivos ignorados no repositório
│
├── inputs/                        # Pasta de entrada (Coloque seus arquivos CSV ou ZIP aqui)
│   └── .gitkeep
│
├── _extraidos/                    # Pasta temporária (Criada e limpa automaticamente)
│   └── .gitkeep
│
└── saidas/                        # Pasta de saída dos arquivos processados
    ├── .gitkeep
    └── *_atualizado.csv           # Arquivos finais prontos para importação no Bling
```

---

## 🛠️ Como usar

### 1. Exportar arquivos do Bling

- **Planilha de Produtos:**
  Acesse no Bling: `Produtos` ➔ `Exportar` ➔ Selecione `CSV`.
  *(Você pode colocar o arquivo CSV diretamente na pasta inputs/ ou compactado em um .zip)*

- **Planilha de Vínculo Multiloja (Repetir para cada loja):**
  Acesse no Bling: `Integrações` ➔ `Multilojas` ➔ Selecione a loja correspondente ➔ Clique em `Exportar produtos`.
  *(Coloque o CSV na pasta inputs/ ou compactado em um ZIP nomeado com o nome da loja, ex: shopee.zip, magalu.zip)*

### 2. Executar o Processamento

1. Mova todas as exportações (CSVs ou ZIPs) para a pasta [inputs/](file:///c:/Users/JcEnxovais/Desktop/Documentos/Programa/Atualizador%20de%20pre%C3%A7os%20multiloja%20-%20Bling/inputs).
2. Execute o arquivo [interface.pyw](file:///c:/Users/JcEnxovais/Desktop/Documentos/Programa/Atualizador%20de%20pre%C3%A7os%20multiloja%20-%20Bling/interface.pyw) com duplo clique.
3. No painel de status, verifique se todos os arquivos e arquivos ZIP foram corretamente mapeados (ícone amarelo para ZIPs e verde para CSVs detectados).
4. Clique no botão **🚀 Executar Atualização**.
5. Aguarde o fim da barra de progresso. Acompanhe o log visual no terminal.
6. Avalie o relatório colorido de validação do catálogo no final do processamento para identificar faltas ou inconsistências.

### 3. Importar de volta no Bling

1. Clique no botão **📂 Abrir pasta saidas/** na interface.
2. No Bling, acesse: `Integrações` ➔ `Multilojas` ➔ Selecione a loja correspondente ➔ Clique em `Importar produtos`.
3. Selecione o respectivo arquivo `*_atualizado.csv` gerado na pasta [saidas/](file:///c:/Users/JcEnxovais/Desktop/Documentos/Programa/Atualizador%20de%20pre%C3%A7os%20multiloja%20-%20Bling/saidas).

---

## ⚙️ Regras de Negócio e Sincronização

- **Atualização de Preço:** O preço de venda normal na multiloja é atualizado de forma exata de acordo com o preço do catálogo do Bling.
- **Preço Promocional:** O preço promocional só é atualizado se o produto já tinha anteriormente um preço promocional cadastrado na loja (maior que zero). Isso previne a criação de promoções acidentais. Além disso, o preço promocional nunca ficará maior que o preço normal atualizado.
- **Filtro de ID de Loja:** Produtos que não possuem código de identificação da plataforma (ID de Loja) são automaticamente removidos da planilha de atualização para evitar falhas ou erros de importação na API do Bling.
- **Segurança de Dados:** Os arquivos originais em `inputs/` permanecem intocados. Todo o resultado é gravado em novos arquivos na pasta `saidas/`.

---

## 🔍 Regras de Detecção de Arquivos

O programa não depende de nomes fixos ou rígidos para as planilhas, operando de forma inteligente:
1. **Arquivo do Bling:** Identificado se o nome do arquivo contém `produtos` e não possui colunas de multiloja. Caso existam múltiplos arquivos que correspondam a esse critério, o programa utilizará o mais recente.
2. **Planilhas Multiloja:** O programa lê a primeira linha de cabeçalho de todos os arquivos restantes (inclusive de dentro dos ZIPs). Se encontrar colunas com o nome `IdProduto` ou `Nome Loja (Multilojas)`, classifica o arquivo automaticamente como uma planilha de vínculo multiloja.

---

## 📦 Requisitos e Configuração

### Requisitos do Sistema
- **Python 3.8** ou superior instalado.
- Biblioteca **pandas** para manipulação dos arquivos de dados.

### Instalação de Dependências
Caso precise configurar o ambiente, execute o comando abaixo no terminal da pasta do projeto:

```bash
pip install pandas
```

---

## 🎯 Resumo da Sincronização

Com a versão 2.0, você garante um fluxo 100% livre de planilhas temporárias manuais, com feedback visual imediato sobre a saúde do seu catálogo de vendas online.