"""
interface.pyw — Interface grafica do Atualizador de Precos
==========================================================
Janela Tkinter que detecta os arquivos CSV na pasta do projeto, exibe
o status de cada um e executa o script.py em segundo plano ao clicar
em "Executar atualizacao".

O arquivo usa a extensao .pyw para abrir sem janela de terminal no Windows.
"""

import os
import re
import sys
import glob
import threading
import subprocess
from tkinter import ttk, scrolledtext, messagebox
import tkinter as tk

import pandas as pd

# Pasta onde este arquivo esta salvo — serve de raiz para todas as operacoes.
# Usar __file__ em vez de os.getcwd() garante que o caminho esteja correto
# mesmo quando o usuario executa o arquivo por atalho ou de outro diretorio.
PASTA_BASE = os.path.dirname(os.path.abspath(__file__))

# Mapa de codigos ANSI para cores do log (o script.py emite esses codigos
# para colorir o terminal; aqui nos convertemos para cores Tkinter)
CORES_ANSI = {
    "91": "#ff6b6b",  # vermelho — produtos removidos / erros
    "92": "#4ec94e",  # verde    — (reservado para uso futuro)
    "93": "#f0c040",  # amarelo  — (reservado para uso futuro)
    "0":  "#d4d4d4",  # reset    — cor padrao do log
}


# ==============================================================================
# DETECCAO DE ARQUIVOS CSV NA PASTA
# ==============================================================================

def detectar_csvs_na_pasta() -> tuple[str | None, list[str]]:
    """
    Varre a pasta base em busca dos arquivos de entrada esperados.

    Retorna uma tupla (arquivo_bling, lista_de_multilojas).
    Usa a mesma logica do script.py para garantir consistencia — se o script
    encontrar o arquivo, a interface tambem vai encontrar (e vice-versa).
    """
    arquivo_bling = None
    arquivos_multiloja = []

    for csv in sorted(glob.glob(os.path.join(PASTA_BASE, "*.csv"))):
        nome = os.path.basename(csv)

        if nome.startswith("produtos"):
            arquivo_bling = csv
            continue

        try:
            cabecalho = pd.read_csv(csv, sep=";", encoding="utf-8-sig", nrows=0)
            colunas = list(cabecalho.columns)
            eh_multiloja = "IdProduto" in colunas or "Nome Loja (Multilojas)" in colunas
            if eh_multiloja:
                arquivos_multiloja.append(csv)
        except Exception:
            pass

    return arquivo_bling, arquivos_multiloja


# ==============================================================================
# CONSTRUCAO DA JANELA
# ==============================================================================

janela = tk.Tk()
janela.title("Atualizador de Precos — Bling → Multiloja")
janela.geometry("620x560")
janela.resizable(False, True)
janela.minsize(620, 520)
janela.configure(bg="#f0f2f5")

# --- Cabecalho ---
# Faixa azul no topo com o nome do sistema
frame_cabecalho = tk.Frame(janela, bg="#2d6cdf", pady=14)
frame_cabecalho.pack(fill="x")

tk.Label(
    frame_cabecalho,
    text="Atualizador de Precos",
    font=("Segoe UI", 15, "bold"),
    bg="#2d6cdf",
    fg="white",
).pack()

tk.Label(
    frame_cabecalho,
    text="Bling  →  Multiloja",
    font=("Segoe UI", 10),
    bg="#2d6cdf",
    fg="#c8d9f7",
).pack()

# --- Painel de status dos arquivos ---
# Exibe quais CSVs foram detectados na pasta; atualizado antes de cada execucao
frame_status = tk.Frame(janela, bg="#f0f2f5", pady=10)
frame_status.pack(fill="x", padx=24)


def atualizar_painel_de_status():
    """
    Redesenha o painel de status dos arquivos com as informacoes mais recentes.

    E chamada tanto na inicializacao quanto no inicio de cada execucao, para
    refletir arquivos que o usuario possa ter adicionado desde que abriu a janela.
    """
    # Remove os widgets anteriores antes de redesenhar
    for widget in frame_status.winfo_children():
        widget.destroy()

    tk.Label(
        frame_status,
        text="Arquivos detectados na pasta:",
        font=("Segoe UI", 9, "bold"),
        bg="#f0f2f5",
        fg="#444",
    ).pack(anchor="w")

    arquivo_bling, arquivos_multiloja = detectar_csvs_na_pasta()

    if arquivo_bling:
        tk.Label(
            frame_status,
            text=f"  OK   Bling: {os.path.basename(arquivo_bling)}",
            font=("Segoe UI", 9),
            bg="#f0f2f5",
            fg="#1a7a3c",
        ).pack(anchor="w")
    else:
        tk.Label(
            frame_status,
            text="  FALTA   Bling: nenhum arquivo produtos_*.csv encontrado",
            font=("Segoe UI", 9),
            bg="#f0f2f5",
            fg="#c0392b",
        ).pack(anchor="w")

    if arquivos_multiloja:
        for caminho in arquivos_multiloja:
            tk.Label(
                frame_status,
                text=f"  OK   Loja: {os.path.basename(caminho)}",
                font=("Segoe UI", 9),
                bg="#f0f2f5",
                fg="#1a7a3c",
            ).pack(anchor="w")
    else:
        tk.Label(
            frame_status,
            text="  FALTA   Lojas: nenhum arquivo de multiloja encontrado",
            font=("Segoe UI", 9),
            bg="#f0f2f5",
            fg="#c0392b",
        ).pack(anchor="w")


atualizar_painel_de_status()

ttk.Separator(janela, orient="horizontal").pack(fill="x", padx=24, pady=4)

# --- Area de log ---
# Exibe a saida do script.py em tempo real apos a execucao
frame_log = tk.Frame(janela, bg="#f0f2f5")
frame_log.pack(fill="both", expand=True, padx=24)

tk.Label(
    frame_log,
    text="Log de execucao:",
    font=("Segoe UI", 9, "bold"),
    bg="#f0f2f5",
    fg="#444",
).pack(anchor="w")

area_log = scrolledtext.ScrolledText(
    frame_log,
    height=12,
    font=("Consolas", 9),
    bg="#1e1e1e",
    fg="#d4d4d4",
    insertbackground="white",
    relief="flat",
    bd=0,
    state="disabled",
)
area_log.pack(fill="both", expand=True, pady=(4, 0))

# --- Barra de progresso ---
barra_progresso = ttk.Progressbar(janela, mode="indeterminate")
barra_progresso.pack(fill="x", padx=24, pady=(8, 0))

# --- Botoes ---
frame_botoes = tk.Frame(janela, bg="#f0f2f5", pady=12)
frame_botoes.pack()


# ==============================================================================
# ESCRITA NO LOG COM SUPORTE A CORES ANSI
# ==============================================================================

def escrever_no_log(texto: str, cor_padrao: str = "#d4d4d4"):
    """
    Insere uma linha no log da interface, interpretando codigos de cor ANSI
    emitidos pelo script.py.

    O log e mantido em modo 'disabled' enquanto nao esta sendo escrito para
    evitar que o usuario edite o conteudo acidentalmente.
    """
    area_log.configure(state="normal")

    # Divide o texto em segmentos: sequencias ANSI e texto normal intercalados
    segmentos = re.split(r"(\033\[[0-9;]+m)", texto)
    cor_atual = cor_padrao
    contador_tags = 0

    for segmento in segmentos:
        match_ansi = re.match(r"\033\[([0-9;]+)m", segmento)
        if match_ansi:
            codigo = match_ansi.group(1)
            cor_atual = CORES_ANSI.get(codigo, cor_padrao)
        elif segmento:
            # Cada trecho recebe uma tag unica para poder ter cor diferente
            nome_tag = f"cor_{id(segmento)}_{contador_tags}"
            contador_tags += 1
            area_log.tag_configure(nome_tag, foreground=cor_atual)
            area_log.insert("end", segmento, nome_tag)

    area_log.insert("end", "\n")
    area_log.configure(state="disabled")
    area_log.see("end")  # Rola automaticamente para a ultima linha


# ==============================================================================
# ACOES DOS BOTOES
# ==============================================================================

def abrir_pasta_saidas():
    """
    Abre a pasta 'saidas/' no Explorer do Windows.
    Se a pasta ainda nao existe, avisa o usuario em vez de abrir um caminho invalido.
    """
    pasta_saidas = os.path.join(PASTA_BASE, "saidas")
    if os.path.exists(pasta_saidas):
        os.startfile(pasta_saidas)
    else:
        messagebox.showinfo(
            "Aviso",
            "A pasta 'saidas' ainda nao foi criada.\nExecute o processo primeiro."
        )


def executar_atualizacao():
    """
    Ponto de entrada do botao 'Executar'. Valida a presenca dos arquivos
    necessarios antes de iniciar o processo, e exibe mensagens de erro claras
    caso algo esteja faltando.

    O script.py e executado em uma thread separada para nao travar a interface
    enquanto o processamento ocorre.
    """
    atualizar_painel_de_status()

    arquivo_bling, arquivos_multiloja = detectar_csvs_na_pasta()

    if not arquivo_bling:
        messagebox.showerror(
            "Arquivo nao encontrado",
            f"Nenhum arquivo de produtos encontrado!\n"
            f"Esperado: produtos.csv ou produtos_*.csv\n\n"
            f"Pasta: {PASTA_BASE}"
        )
        return

    if not arquivos_multiloja:
        messagebox.showerror(
            "Arquivo nao encontrado",
            f"Nenhum arquivo de loja encontrado!\n"
            f"Coloque os arquivos exportados do Bling na pasta:\n{PASTA_BASE}"
        )
        return

    # Desabilita os botoes durante o processamento para evitar execucoes paralelas
    botao_executar.config(state="disabled")
    botao_abrir.config(state="disabled")

    # Limpa o log antes de cada nova execucao
    area_log.configure(state="normal")
    area_log.delete("1.0", "end")
    area_log.configure(state="disabled")

    escrever_no_log(f"Pasta de trabalho: {PASTA_BASE}")
    barra_progresso.start(10)

    def rodar_em_segundo_plano():
        """
        Executa o script.py como subprocesso e captura toda a sua saida.

        Usamos subprocess em vez de importar o modulo diretamente para isolar
        o ambiente de execucao e garantir que erros no script nao derrubem a
        interface grafica.
        """
        try:
            caminho_script = os.path.join(PASTA_BASE, "script.py")
            resultado = subprocess.run(
                [sys.executable, caminho_script],
                capture_output=True,
                text=True,
                cwd=PASTA_BASE,  # Garante que o script encontre os CSVs na pasta correta
            )
            # Atualiza a interface na thread principal (obrigatorio no Tkinter)
            janela.after(0, lambda: finalizar_execucao(resultado))
        except Exception as erro:
            janela.after(0, lambda: finalizar_com_erro(str(erro)))

    threading.Thread(target=rodar_em_segundo_plano, daemon=True).start()


def finalizar_execucao(resultado):
    """
    Chamada pela thread principal apos o subprocesso terminar.
    Exibe o log completo e o resultado (sucesso ou erro).
    """
    barra_progresso.stop()
    botao_executar.config(state="normal")
    botao_abrir.config(state="normal")

    if resultado.stdout:
        for linha in resultado.stdout.strip().split("\n"):
            escrever_no_log(linha)

    if resultado.returncode == 0:
        escrever_no_log("\n" + "-" * 37, "#555")
        escrever_no_log("Arquivos salvos em:  saidas/", "#4ec94e")
        escrever_no_log("  - arquivos _atualizado.csv por loja", "#4ec94e")
        escrever_no_log("  - relatorio_alteracoes.csv", "#4ec94e")
        messagebox.showinfo("Concluido", "Processo finalizado!\n\nArquivos gerados na pasta saidas/")
    else:
        escrever_no_log("\nERRO:", "#ff6b6b")
        if resultado.stderr:
            for linha in resultado.stderr.strip().split("\n"):
                escrever_no_log("  " + linha, "#ff6b6b")
        messagebox.showerror("Erro", "Ocorreu um erro.\nVeja o log para detalhes.")


def finalizar_com_erro(mensagem_erro: str):
    """
    Chamada quando ocorre uma excecao inesperada ao tentar iniciar o subprocesso
    (ex: Python nao encontrado, permissao negada).
    """
    barra_progresso.stop()
    botao_executar.config(state="normal")
    botao_abrir.config(state="normal")
    escrever_no_log(f"Erro inesperado: {mensagem_erro}", "#ff6b6b")
    messagebox.showerror("Erro", f"Erro inesperado:\n{mensagem_erro}")


# ==============================================================================
# DECLARACAO DOS BOTOES
# (declarados apos as funcoes que referenciam para evitar NameError)
# ==============================================================================

botao_executar = tk.Button(
    frame_botoes,
    text="  Executar atualizacao",
    font=("Segoe UI", 10, "bold"),
    bg="#2d6cdf",
    fg="white",
    activebackground="#1a4fa3",
    relief="flat",
    padx=20,
    pady=8,
    cursor="hand2",
    command=executar_atualizacao,
)
botao_executar.pack(side="left", padx=6)

botao_abrir = tk.Button(
    frame_botoes,
    text="  Abrir pasta saidas/",
    font=("Segoe UI", 10),
    bg="#e8edf5",
    fg="#333",
    activebackground="#d0d8e8",
    relief="flat",
    padx=20,
    pady=8,
    cursor="hand2",
    command=abrir_pasta_saidas,
)
botao_abrir.pack(side="left", padx=6)


# ==============================================================================
# INICIO DA APLICACAO
# ==============================================================================

janela.mainloop()
