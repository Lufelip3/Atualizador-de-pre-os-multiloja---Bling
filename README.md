# Atualizador de Preços — Bling para Multiloja

Ferramenta para atualizar automaticamente os preços dos produtos
nas lojas virtuais (Shopee, Magalu, Nuvemshop, entre outras)
com base nos valores cadastrados no Bling.

O objetivo é tornar o processo mais rápido, seguro e escalável,
eliminando a necessidade de edição manual de planilhas.

---

## O que o programa faz

- Lê o arquivo de produtos exportado do Bling
- Lê os arquivos de cada loja virtual (Multiloja)
- Cruza os dados pelo campo Código (SKU)
- Atualiza preços automaticamente
- Ajusta preço promocional quando necessário
- Remove produtos sem vínculo com a loja
- Gera arquivos prontos para importação
- Cria um relatório com todas as alterações

---

## Estrutura da pasta


Atualiza preços/
├── interface.pyw
├── script.py
├── COMO_USAR.txt
│
├── produtos_.csv
├── vinculo_produtos_multiloja_.csv
│
└── saidas/
├── *_atualizado.csv
└── *_relatorio.csv


---

## Como usar

1. Exporte os dados do Bling

Produtos:
> Produtos → Exportar → CSV

Multiloja:
> Integrações → Multilojas → selecionar loja → Exportar produtos

2. Coloque os arquivos na pasta do programa

Não é necessário renomear os arquivos.

3. Execute o programa

Abra o arquivo `interface.pyw`.

4. Execute a atualização

- Confira os arquivos detectados
- Clique em "Executar atualização"
- Aguarde o processamento

5. Importe os arquivos no Bling

> Integrações → Multilojas → selecionar loja → Importar produtos

Selecione o arquivo gerado com o sufixo `_atualizado.csv`.

---

## Arquivos gerados

| Arquivo | Descrição |
|--------|----------|
| *_atualizado.csv | Arquivo pronto para importar no Bling |
| *_relatorio.csv  | Lista de produtos com alteração de preço |

---

## Regras de funcionamento

- Preço diferente do Bling é atualizado
- Preço promocional nunca fica maior que o preço normal
- Produtos sem ID de loja são removidos
- Produtos não encontrados no Bling são mantidos

---

## Detecção automática de arquivos

O programa identifica os arquivos pelo conteúdo:

- Arquivo do Bling: começa com "produtos"
- Arquivos de loja: contêm informações de Multiloja

Se houver mais de um arquivo, o mais recente é utilizado.

---

## Requisitos

- Python 3.8 ou superior
- Biblioteca pandas

Instalação:

```bash
pip install pandas
Problemas comuns

Erro ao abrir a interface:
→ Abra com Python manualmente

Erro de biblioteca:
→ Instale com pip install pandas

Arquivo não detectado:
→ Verifique se está na mesma pasta do programa

Problemas com acentuação:
→ Prefira exportar os arquivos em UTF-8


---

## 💬 Resultado

Agora você tem:

- 📄 TXT mais direto e fácil pra usuário final  
- 📘 README mais profissional pra GitHub  
- Linguagem natural (sem parecer gerado)  
- Estrutura clara e organizada  

---

Se quiser, posso dar um próximo passo e:
- deixar o README com **cara de projeto open source (nível GitHub top)**  
- ou adicionar imagens / prints da interface 👍