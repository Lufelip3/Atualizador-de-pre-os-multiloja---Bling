"""
script.py — Motor de atualizacao de precos
==========================================
Le o catalogo exportado do Bling (produtos.csv) e os arquivos de vinculo
exportados do modulo Multiloja. Para cada produto encontrado nas duas fontes,
sobrescreve o preco da loja com o preco vigente do Bling.

Regras de negocio principais:
- Produtos sem ID de loja valido sao removidos do arquivo de saida.
- O preco promocional so e atualizado se ja existia um valor maior que zero;
  caso contrario, permanece em branco (evita criar promocoes involuntarias).
- Os arquivos de saida sao gravados na subpasta "saidas/" sem sobrescrever
  os originais.
"""

import os
import sys
import glob
import unicodedata

import pandas as pd

# Garante que prints com acentos funcionem em qualquer terminal Windows
sys.stdout.reconfigure(encoding="utf-8")

# Define o diretorio de trabalho como a pasta onde o script esta salvo.
# Isso evita problemas quando o script e executado de outro diretorio (ex: pelo
# atalho da interface grafica).
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PASTA_SAIDA = "saidas"
os.makedirs(PASTA_SAIDA, exist_ok=True)

# Codigos de cor ANSI usados apenas no terminal — nao afetam os arquivos CSV.
COR_VERMELHO = "\033[91m"
COR_RESET = "\033[0m"


# ==============================================================================
# LOCALIZACAO DE ARQUIVOS
# ==============================================================================

def localizar_arquivo_bling() -> str:
    """
    Procura o arquivo de produtos exportado do Bling na pasta atual.

    Estrategia de busca (em ordem de prioridade):
    1. 'produtos.csv' (nome exato, mais previsivel)
    2. 'produtos_*.csv' (exportacoes com timestamp do Bling)

    Retorna o caminho do arquivo encontrado ou lanca FileNotFoundError.
    """
    candidato_fixo = "produtos.csv"
    if os.path.exists(candidato_fixo):
        print(f"Bling    : {candidato_fixo}")
        return candidato_fixo

    # Fallback: pega o mais recente quando ha mais de um arquivo com timestamp
    candidatos_com_data = sorted(glob.glob("produtos_*.csv"))
    if candidatos_com_data:
        arquivo = candidatos_com_data[-1]
        print(f"Bling    : {arquivo}  (encontrado automaticamente)")
        return arquivo

    csvs_presentes = glob.glob("*.csv")
    raise FileNotFoundError(
        "Arquivo de produtos do Bling nao encontrado.\n"
        f"Esperado: 'produtos.csv' ou 'produtos_*.csv'\n"
        f"CSVs na pasta: {csvs_presentes}"
    )


def localizar_arquivos_multiloja(arquivo_bling: str) -> list[str]:
    """
    Varre todos os CSVs da pasta e identifica os arquivos de multiloja pelo
    cabecalho, nao pelo nome — isso funciona independente de como o usuario
    nomeou o arquivo ao exportar do Bling.

    Um arquivo e considerado multiloja se contiver a coluna 'IdProduto' ou
    'Nome Loja (Multilojas)', que sao colunas-chave do modulo Multiloja do Bling.

    O arquivo do Bling e excluido da busca para evitar falso positivo.
    """
    arquivos_multiloja = []

    for csv in sorted(glob.glob("*.csv")):
        if csv == arquivo_bling:
            continue

        try:
            cabecalho = pd.read_csv(csv, sep=";", encoding="utf-8-sig", nrows=0)
            colunas = list(cabecalho.columns)
            eh_multiloja = "IdProduto" in colunas or "Nome Loja (Multilojas)" in colunas
            if eh_multiloja:
                arquivos_multiloja.append(csv)
        except Exception:
            # CSV malformado ou ilegivel — ignora silenciosamente
            pass

    if not arquivos_multiloja:
        raise FileNotFoundError(
            "Nenhum arquivo de multiloja encontrado na pasta.\n"
            f"CSVs presentes: {glob.glob('*.csv')}"
        )

    for arquivo in arquivos_multiloja:
        print(f"Multiloja: {arquivo}")

    return arquivos_multiloja


# ==============================================================================
# DETECCAO DE COLUNAS
# ==============================================================================

def remover_acentos(texto: str) -> str:
    """
    Normaliza uma string removendo acentos e convertendo para minusculo.
    Usado para comparar nomes de colunas de forma tolerante a variacoes de
    exportacao (ex: 'Preco' vs 'Preco' vs 'PRECO').
    """
    return "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", str(texto))
        if unicodedata.category(caractere) != "Mn"
    ).lower()


def detectar_coluna_codigo(colunas: list[str]) -> str | None:
    """
    Encontra a coluna que representa o codigo/SKU do produto.
    Prioriza colunas com 'cod' ou 'sku' no nome; como ultimo recurso, aceita
    uma coluna chamada exatamente 'id'.
    """
    for coluna in colunas:
        nome = remover_acentos(coluna)
        if "cod" in nome or "sku" in nome:
            return coluna

    # 'id' sozinho e muito generico, mas serve de fallback quando nao ha outra opcao
    for coluna in colunas:
        if remover_acentos(coluna) == "id":
            return coluna

    return None


def detectar_coluna_preco(colunas: list[str]) -> str | None:
    """
    Encontra a coluna de preco de venda principal.

    Regra de negocio: exclui explicitamente 'custo', 'promocional' e 'compra'
    para nao confundir com preco de custo ou preco promocional, que sao
    tratados separadamente.
    """
    for coluna in colunas:
        nome = remover_acentos(coluna)
        e_preco = nome.startswith("pre") or nome == "valor"
        nao_e_excecao = "custo" not in nome and "promocional" not in nome and "compra" not in nome
        if e_preco and nao_e_excecao:
            return coluna
    return None


def detectar_coluna_preco_promocional(colunas: list[str]) -> str | None:
    """Encontra a coluna de preco promocional, se existir."""
    for coluna in colunas:
        if "promocional" in remover_acentos(coluna):
            return coluna
    return None


def detectar_coluna_id_loja(colunas: list[str]) -> str | None:
    """
    Encontra a coluna que armazena o ID do produto na loja (Nuvemshop,
    Shopee, Magalu, etc.). Produtos sem esse ID nao estao publicados e
    devem ser removidos do arquivo de saida.
    """
    for coluna in colunas:
        nome = remover_acentos(coluna)
        if "id" in nome and "loja" in nome:
            return coluna
    return None


# ==============================================================================
# VALIDACAO E CONVERSAO DE VALORES
# ==============================================================================

def produto_tem_id_de_loja_valido(valor) -> bool:
    """
    Verifica se o produto ja foi publicado na loja, ou seja, se possui um
    ID de plataforma valido.

    Casos invalidos conhecidos:
    - Celula vazia, NaN ou '0'
    - Campo preenchido apenas com tab (\\t), que e como a Shopee exporta
      produtos nao publicados

    Produtos sem ID valido existem no Bling mas nao na loja — inclui-los no
    arquivo de atualizacao causaria erros de importacao.
    """
    valor_str = str(valor).strip()
    sem_valor = valor_str in ("", "nan", "0")
    apenas_tab = valor_str == "\\t" or valor_str.replace("\\t", "").strip() == ""
    return not sem_valor and not apenas_tab


def converter_preco_para_float(serie: pd.Series) -> pd.Series:
    """
    Converte uma coluna de preco do formato brasileiro (ex: '1.299,90') para
    float (1299.90).

    O Bling exporta valores com ponto como separador de milhar e virgula como
    decimal — o inverso do padrao Python/pandas, por isso a conversao manual.
    """
    return (
        serie.astype(str)
        .str.strip()
        .str.replace("R$", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(".", "", regex=False)   # remove separador de milhar
        .str.replace(",", ".", regex=False)  # converte decimal para padrao Python
        .replace("", float("nan"))
        .astype(float)
    )


def formatar_preco_para_csv(valor: float) -> str:
    """
    Converte um float de volta para o formato brasileiro esperado pelo Bling
    na importacao (ex: 1299.90 → '1299,90').

    Nota: o Bling nao usa ponto de milhar na importacao, apenas na exportacao.
    """
    return f"{valor:.2f}".replace(".", ",")


# ==============================================================================
# LEITURA DO CATALOGO BLING
# ==============================================================================

def carregar_catalogo_bling(caminho_arquivo: str) -> dict[str, float]:
    """
    Le o CSV do Bling e retorna um dicionario {codigo_produto: preco_de_venda}.

    Esse dicionario e a 'fonte da verdade' para os precos — qualquer preco
    diferente nos arquivos de multiloja sera sobrescrito com o valor daqui.
    """
    bling = pd.read_csv(caminho_arquivo, sep=";", encoding="utf-8-sig")

    # O Bling as vezes exporta nomes de colunas com aspas — limpamos aqui
    bling.columns = bling.columns.str.replace('"', "").str.strip()

    coluna_codigo = detectar_coluna_codigo(bling.columns)
    coluna_preco = detectar_coluna_preco(bling.columns)

    if not coluna_codigo or not coluna_preco:
        raise Exception(
            "Nao foi possivel identificar as colunas de Codigo/Preco no arquivo do Bling.\n"
            f"Colunas encontradas: {list(bling.columns)}"
        )

    print(f"\nCodigo Bling : {coluna_codigo}")
    print(f"Preco Bling  : {coluna_preco}")

    codigos = bling[coluna_codigo].astype(str).str.strip()
    precos = converter_preco_para_float(bling[coluna_preco])

    return dict(zip(codigos, precos))


# ==============================================================================
# PROCESSAMENTO DOS ARQUIVOS DE MULTILOJA
# ==============================================================================

def separar_produtos_sem_id_de_loja(
    dataframe: pd.DataFrame,
    coluna_id_loja: str | None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Divide o dataframe em dois grupos:
    - com_id: produtos publicados na loja (serao atualizados e exportados)
    - sem_id: produtos nao publicados (serao descartados com aviso no log)

    Se nao houver coluna de ID de loja, assume que todos os produtos sao validos.
    """
    if coluna_id_loja is None:
        return dataframe, pd.DataFrame()

    mascara_sem_id = ~dataframe[coluna_id_loja].apply(produto_tem_id_de_loja_valido)
    com_id = dataframe[~mascara_sem_id].reset_index(drop=True)
    sem_id = dataframe[mascara_sem_id]
    return com_id, sem_id


def calcular_alteracoes_de_preco(
    dataframe: pd.DataFrame,
    codigos: pd.Series,
    precos_atuais: pd.Series,
    catalogo_bling: dict[str, float],
    nome_arquivo: str,
) -> list[dict]:
    """
    Compara os precos do arquivo de multiloja com o catalogo do Bling e retorna
    uma lista com os produtos cujo preco mudou.

    Essa lista e usada para gerar o relatorio de alteracoes — util para auditoria
    e para o usuario entender o que foi modificado em cada execucao.
    """
    alteracoes = []

    for indice, codigo in enumerate(codigos):
        preco_bling = catalogo_bling.get(codigo)
        preco_multiloja = precos_atuais.iloc[indice]

        # Produto nao encontrado no Bling — nao ha o que atualizar
        if preco_bling is None:
            continue

        # Compara com arredondamento para evitar falsos positivos por
        # imprecisao de ponto flutuante (ex: 99.999999 != 100.0)
        preco_mudou = round(preco_bling, 2) != round(preco_multiloja, 2)
        if preco_mudou:
            nome_produto = dataframe["Nome"].iloc[indice] if "Nome" in dataframe.columns else ""
            alteracoes.append({
                "Arquivo": nome_arquivo,
                "Codigo": codigo,
                "Nome": nome_produto,
                "Preco_Antigo": preco_multiloja,
                "Preco_Novo": preco_bling,
                "Diferenca": round(preco_bling - preco_multiloja, 2),
            })

    return alteracoes


def aplicar_novos_precos(
    dataframe: pd.DataFrame,
    codigos: pd.Series,
    coluna_preco: str,
    coluna_promo: str | None,
    precos_atuais_num: pd.Series,
    precos_promo_num: pd.Series | None,
    catalogo_bling: dict[str, float],
) -> pd.DataFrame:
    """
    Atualiza as colunas de preco no dataframe com os valores do Bling.

    Regra do preco promocional:
    Se o produto tinha um preco promocional configurado (> 0), ele tambem e
    atualizado para o novo preco de venda. Isso garante que a promocao nao fique
    com um valor maior que o preco normal apos a atualizacao.

    Se o campo promocional estava vazio (0 ou em branco), ele nao e preenchido —
    isso evita criar promocoes involuntarias em produtos que nunca tiveram.
    """
    novos_precos = []
    novos_promos = []

    for indice, codigo in enumerate(codigos):
        preco_bling = catalogo_bling.get(codigo)

        if preco_bling is None:
            # Produto nao encontrado no Bling — mantém o valor original
            novos_precos.append(dataframe[coluna_preco].iloc[indice])
            if coluna_promo:
                novos_promos.append(dataframe[coluna_promo].iloc[indice])
        else:
            novos_precos.append(formatar_preco_para_csv(preco_bling))
            if coluna_promo:
                preco_promo_atual = precos_promo_num.iloc[indice] if precos_promo_num is not None else 0
                tinha_promocao = preco_promo_atual != 0
                if tinha_promocao:
                    novos_promos.append(formatar_preco_para_csv(preco_bling))
                else:
                    novos_promos.append(dataframe[coluna_promo].iloc[indice])

    dataframe[coluna_preco] = novos_precos
    if coluna_promo:
        dataframe[coluna_promo] = novos_promos

    return dataframe


def processar_arquivo_multiloja(
    caminho_arquivo: str,
    catalogo_bling: dict[str, float],
) -> tuple[int, int]:
    """
    Orquestra o processamento completo de um arquivo de multiloja:
    1. Leitura e deteccao de colunas
    2. Filtragem de produtos sem ID de loja
    3. Calculo das alteracoes de preco
    4. Atualizacao dos precos
    5. Gravacao dos arquivos de saida

    Retorna (qtd_alteracoes, qtd_removidos) para o totalizador final.
    """
    print(f"\n{'=' * 55}")
    print(f"Processando: {caminho_arquivo}")

    multiloja = pd.read_csv(caminho_arquivo, sep=";", encoding="utf-8-sig")
    multiloja.columns = multiloja.columns.str.replace('"', "").str.strip()

    # Detecta as colunas relevantes pelo conteudo do cabecalho
    coluna_codigo = detectar_coluna_codigo(multiloja.columns)
    coluna_preco = detectar_coluna_preco(multiloja.columns)
    coluna_promo = detectar_coluna_preco_promocional(multiloja.columns)
    coluna_id_loja = detectar_coluna_id_loja(multiloja.columns)

    if not coluna_codigo or not coluna_preco:
        print(f"  AVISO: colunas de Codigo/Preco nao encontradas em '{caminho_arquivo}', pulando.")
        return 0, 0

    print(f"Codigo       : {coluna_codigo}")
    print(f"Preco        : {coluna_preco}")
    print(f"Preco Promo  : {coluna_promo}")
    print(f"ID na Loja   : {coluna_id_loja}")

    # Limpa espacos extras no campo de ID (pode causar falso negativo na validacao)
    if coluna_id_loja:
        multiloja[coluna_id_loja] = multiloja[coluna_id_loja].astype(str).str.strip()

    # Separa produtos publicados dos nao publicados antes de processar
    multiloja, produtos_sem_id = separar_produtos_sem_id_de_loja(multiloja, coluna_id_loja)

    # Pre-converte os precos para float para facilitar a comparacao e os calculos
    precos_atuais_num = converter_preco_para_float(multiloja[coluna_preco])
    precos_promo_num = converter_preco_para_float(multiloja[coluna_promo]) if coluna_promo else None
    codigos = multiloja[coluna_codigo].astype(str).str.strip()

    # Gera o relatorio antes de modificar o dataframe
    alteracoes = calcular_alteracoes_de_preco(
        multiloja, codigos, precos_atuais_num, catalogo_bling, caminho_arquivo
    )

    # Aplica os novos precos diretamente no dataframe
    multiloja = aplicar_novos_precos(
        multiloja, codigos, coluna_preco, coluna_promo,
        precos_atuais_num, precos_promo_num, catalogo_bling
    )

    # Salva usando o nome original com sufixo para nao sobrescrever o original
    nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
    caminho_saida = os.path.join(PASTA_SAIDA, f"{nome_base}_atualizado.csv")
    caminho_relatorio = os.path.join(PASTA_SAIDA, f"{nome_base}_relatorio.csv")

    multiloja.to_csv(caminho_saida, sep=";", index=False, encoding="utf-8-sig")
    pd.DataFrame(alteracoes).to_csv(caminho_relatorio, sep=";", index=False, encoding="utf-8-sig")

    # Log de resumo por arquivo
    qtd_alteracoes = len(alteracoes)
    qtd_removidos = len(produtos_sem_id)

    print(f"\n{qtd_alteracoes} produto(s) com preco alterado.")
    print(f"{len(multiloja)} produto(s) incluidos no arquivo final.")

    if qtd_removidos > 0:
        print(f"\n--- {qtd_removidos} produto(s) removidos (sem ID de loja) ---")
        for _, linha in produtos_sem_id.iterrows():
            nome = linha.get("Nome", "sem nome")
            print(f"  - {COR_VERMELHO}{nome}{COR_RESET}")

    return qtd_alteracoes, qtd_removidos


# ==============================================================================
# PONTO DE ENTRADA
# ==============================================================================

def main():
    """
    Fluxo principal do script:
    1. Localiza os arquivos de entrada
    2. Carrega o catalogo de precos do Bling
    3. Processa cada arquivo de multiloja encontrado
    4. Exibe o resumo final
    """
    arquivo_bling = localizar_arquivo_bling()
    arquivos_multiloja = localizar_arquivos_multiloja(arquivo_bling)
    catalogo_bling = carregar_catalogo_bling(arquivo_bling)

    total_alteracoes = 0
    total_removidos = 0

    for arquivo in arquivos_multiloja:
        alteracoes, removidos = processar_arquivo_multiloja(arquivo, catalogo_bling)
        total_alteracoes += alteracoes
        total_removidos += removidos

    print(f"\n{'=' * 55}")
    print(f"CONCLUIDO: {total_alteracoes} alteracao(oes) | {total_removidos} removido(s) no total")


if __name__ == "__main__":
    main()
