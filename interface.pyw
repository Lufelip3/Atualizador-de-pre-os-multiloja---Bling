import os
import re
import sys
import glob
import zipfile
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

import pandas as pd

# Pastas globais
PASTA_BASE = os.path.dirname(os.path.abspath(__file__))
PASTA_INPUTS = os.path.join(PASTA_BASE, "inputs")
PASTA_EXTRAIDOS = os.path.join(PASTA_BASE, "_extraidos")
PASTA_SAIDAS = os.path.join(PASTA_BASE, "saidas")


class AtualizadorMultilojaApp:
    # ── PALETA DE CORES (Tema Verde Dark) ───────────
    COR_BG_RAIZ     = "#1a241c"
    COR_BG_HEADER   = "#111812"
    COR_BG_PAINEL   = "#1a241c"
    COR_BG_LOG      = "#0b0f0b"
    COR_TITULO      = "#86efac"
    COR_BTN_ACAO    = "#15803d"
    COR_BTN_ACAO_H  = "#166534"
    
    COR_SUBTITULO   = "#888899"
    COR_LABEL       = "#ddddee"
    COR_LOG_TEXT    = "#ccccdd"
    COR_BTN_ABRIR   = "#3a3a5c"
    COR_BTN_ABRIR_H = "#4a4a75"

    CORES_ANSI = {
        "91": "#ff6b6b",  # vermelho — produtos removidos / erros
        "92": "#4ec94e",  # verde    — sucesso
        "93": "#f0c040",  # amarelo  
        "95": "#ff33cc",  # magenta  — produtos fantasmas (chamativo)
        "33": "#ff8c00",  # laranja  — produtos faltantes
        "0":  "#ccccdd",  # reset    — cor padrao do log
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Atualizador de Precos — Bling → Multiloja")
        self.root.geometry("660x620")
        self.root.resizable(True, True)
        self.root.minsize(660, 560)
        self.root.configure(bg=self.COR_BG_RAIZ)

        # Configurar estilo para a barra de progresso não ter borda branca
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Dark.Horizontal.TProgressbar", 
                        background=self.COR_BTN_ACAO, 
                        troughcolor=self.COR_BG_LOG, 
                        bordercolor=self.COR_BG_RAIZ, 
                        lightcolor=self.COR_BTN_ACAO, 
                        darkcolor=self.COR_BTN_ACAO)

        self._criar_widgets()
        self.atualizar_painel_de_status()

    def _criar_widgets(self):
        # ── HEADER ───────────
        header = tk.Frame(self.root, bg=self.COR_BG_HEADER, pady=12)
        header.pack(fill=tk.X)
        
        tk.Label(
            header,
            text="Atualizador de Precos  💰",
            font=("Helvetica", 17, "bold"),
            bg=self.COR_BG_HEADER,
            fg=self.COR_TITULO,
        ).pack()
        
        tk.Label(
            header,
            text="Bling  →  Multiloja",
            font=("Helvetica", 9),
            bg=self.COR_BG_HEADER,
            fg=self.COR_SUBTITULO,
        ).pack()

        # ── PAINEL DE STATUS DOS ARQUIVOS ───────────
        self.frame_status = tk.Frame(self.root, bg=self.COR_BG_PAINEL, pady=10)
        self.frame_status.pack(fill=tk.X, padx=24)

        ttk.Separator(self.root, orient="horizontal").pack(fill=tk.X, padx=24, pady=4)

        # ── BOTÃO PRINCIPAL ───────────
        frame_btn = tk.Frame(self.root, bg=self.COR_BG_RAIZ, pady=12)
        frame_btn.pack(fill=tk.X, padx=24)

        self.btn_executar = tk.Button(
            frame_btn,
            text="🚀  Executar Atualizacao",
            bg=self.COR_BTN_ACAO,
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            padx=14, pady=8,
            activebackground=self.COR_BTN_ACAO_H,
            command=self.executar_atualizacao
        )
        self.btn_executar.pack(fill=tk.X, pady=(0, 8))

        self.btn_abrir = tk.Button(
            frame_btn,
            text="📂  Abrir pasta saidas/",
            bg=self.COR_BTN_ABRIR,
            fg="white",
            font=("Arial", 10),
            relief="flat",
            cursor="hand2",
            padx=14, pady=5,
            activebackground=self.COR_BTN_ABRIR_H,
            command=self.abrir_pasta_saidas
        )
        self.btn_abrir.pack(fill=tk.X)

        # ── BARRA DE PROGRESSO ───────────
        self.barra_progresso = ttk.Progressbar(self.root, mode="indeterminate", style="Dark.Horizontal.TProgressbar")
        self.barra_progresso.pack(fill=tk.X, padx=24, pady=(0, 8))

        # ── ÁREA DE LOG ───────────
        frame_log = tk.Frame(self.root, bg=self.COR_BG_RAIZ)
        frame_log.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 16))

        tk.Label(
            frame_log,
            text="Log de execucao:",
            font=("Segoe UI", 9, "bold"),
            bg=self.COR_BG_RAIZ,
            fg=self.COR_SUBTITULO,
        ).pack(anchor="w")

        container = tk.Frame(frame_log, bg=self.COR_BG_LOG)
        container.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        
        self.area_log = tk.Text(
            container,
            font=("Consolas", 10),
            bg=self.COR_BG_LOG,
            fg=self.COR_LOG_TEXT,
            insertbackground="white",
            relief="flat",
            bd=0,
            state="disabled",
            padx=8, pady=6
        )
        sb = ttk.Scrollbar(container, command=self.area_log.yview)
        self.area_log.configure(yscrollcommand=sb.set)
        
        self.area_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    # ── MÉTODOS DE LÓGICA E ARQUIVOS ───────────
    def extrair_csvs_de_zips(self):
        """
        Extrai arquivos CSV de dentro de qualquer ZIP na pasta inputs/
        e os salva na pasta temporaria _extraidos/, adicionando o prefixo
        do nome do arquivo ZIP para evitar colisoes de nomes.
        """
        zips = sorted(glob.glob(os.path.join(PASTA_INPUTS, "*.zip")))
        if not zips:
            return []

        if os.path.exists(PASTA_EXTRAIDOS):
            import shutil
            for item in os.listdir(PASTA_EXTRAIDOS):
                if item == ".gitkeep": continue
                caminho = os.path.join(PASTA_EXTRAIDOS, item)
                try:
                    if os.path.isfile(caminho): os.remove(caminho)
                    elif os.path.isdir(caminho): shutil.rmtree(caminho)
                except Exception:
                    pass
        os.makedirs(PASTA_EXTRAIDOS, exist_ok=True)

        zips_processados = []
        for zip_path in zips:
            nome_zip = os.path.splitext(os.path.basename(zip_path))[0]
            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    csvs_no_zip = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                    if not csvs_no_zip:
                        continue
                    for csv_interno in csvs_no_zip:
                        nome_csv = os.path.basename(csv_interno)
                        nome_destino = f"{nome_zip}_{nome_csv}"
                        caminho_destino = os.path.join(PASTA_EXTRAIDOS, nome_destino)
                        with zf.open(csv_interno) as fonte, open(caminho_destino, "wb") as destino:
                            destino.write(fonte.read())
                    zips_processados.append(zip_path)
            except (zipfile.BadZipFile, Exception):
                pass
        return zips_processados

    def detectar_csvs_na_pasta(self):
        """
        Varre as pastas inputs/ e _extraidos/ para identificar os arquivos.
        - Arquivo Bling: 'produtos.csv' ou 'produtos_*.csv' em inputs/, ou '*produtos*.csv' em _extraidos/.
        - Arquivos de Loja: CSVs que contenham colunas de vinculo multiloja (IdProduto ou Nome Loja).
        """
        zips_processados = self.extrair_csvs_de_zips()

        arquivo_bling = None
        arquivos_multiloja = []

        candidato_fixo = os.path.join(PASTA_INPUTS, "produtos.csv")
        if os.path.exists(candidato_fixo):
            arquivo_bling = candidato_fixo
        else:
            candidatos = sorted(glob.glob(os.path.join(PASTA_INPUTS, "produtos_*.csv")))
            if candidatos:
                arquivo_bling = candidatos[-1]

        todos_csvs = sorted(glob.glob(os.path.join(PASTA_INPUTS, "*.csv")))
        if os.path.isdir(PASTA_EXTRAIDOS):
            todos_csvs += sorted(glob.glob(os.path.join(PASTA_EXTRAIDOS, "*.csv")))

        for csv in todos_csvs:
            if arquivo_bling and os.path.abspath(csv) == os.path.abspath(arquivo_bling):
                continue
            try:
                cabecalho = pd.read_csv(csv, sep=";", encoding="utf-8-sig", nrows=0)
                colunas = list(cabecalho.columns)
                
                eh_multiloja = "IdProduto" in colunas or "Nome Loja (Multilojas)" in colunas
                if eh_multiloja:
                    arquivos_multiloja.append(csv)
                elif arquivo_bling is None and "produtos" in os.path.basename(csv).lower():
                    arquivo_bling = csv
            except Exception:
                pass

        return arquivo_bling, arquivos_multiloja, zips_processados

    def atualizar_painel_de_status(self):
        for widget in self.frame_status.winfo_children():
            widget.destroy()

        tk.Label(
            self.frame_status,
            text="Arquivos detectados na pasta inputs/:",
            font=("Segoe UI", 10, "bold"),
            bg=self.COR_BG_PAINEL,
            fg=self.COR_LABEL,
        ).pack(anchor="w", pady=(0, 4))

        arquivo_bling, arquivos_multiloja, zips_processados = self.detectar_csvs_na_pasta()

        if zips_processados:
            for zip_path in zips_processados:
                tk.Label(
                    self.frame_status,
                    text=f"  ZIP   {os.path.basename(zip_path)}",
                    font=("Segoe UI", 10),
                    bg=self.COR_BG_PAINEL,
                    fg="#f0c040", # Amarelo
                ).pack(anchor="w")

        if arquivo_bling:
            via_zip = " (via ZIP)" if PASTA_EXTRAIDOS in arquivo_bling else ""
            tk.Label(
                self.frame_status,
                text=f"  OK   Bling: {os.path.basename(arquivo_bling)}{via_zip}",
                font=("Segoe UI", 10),
                bg=self.COR_BG_PAINEL,
                fg="#4ec94e", # Verde
            ).pack(anchor="w")
        else:
            tk.Label(
                self.frame_status,
                text="  FALTA   Bling: nenhum arquivo de produtos encontrado",
                font=("Segoe UI", 10),
                bg=self.COR_BG_PAINEL,
                fg="#ff6b6b", # Vermelho
            ).pack(anchor="w")

        if arquivos_multiloja:
            for caminho in arquivos_multiloja:
                via_zip = " (via ZIP)" if PASTA_EXTRAIDOS in caminho else ""
                tk.Label(
                    self.frame_status,
                    text=f"  OK   Loja: {os.path.basename(caminho)}{via_zip}",
                    font=("Segoe UI", 10),
                    bg=self.COR_BG_PAINEL,
                    fg="#4ec94e",
                ).pack(anchor="w")
        else:
            tk.Label(
                self.frame_status,
                text="  FALTA   Lojas: nenhum arquivo de multiloja encontrado",
                font=("Segoe UI", 10),
                bg=self.COR_BG_PAINEL,
                fg="#ff6b6b",
            ).pack(anchor="w")

    def limpar_pasta_saidas(self):
        if os.path.exists(PASTA_SAIDAS):
            import shutil
            for item in os.listdir(PASTA_SAIDAS):
                if item == ".gitkeep": continue
                caminho = os.path.join(PASTA_SAIDAS, item)
                try:
                    if os.path.isfile(caminho): os.remove(caminho)
                    elif os.path.isdir(caminho): shutil.rmtree(caminho)
                except Exception:
                    pass
        else:
            os.makedirs(PASTA_SAIDAS, exist_ok=True)

    def abrir_pasta_saidas(self):
        if os.path.exists(PASTA_SAIDAS):
            os.startfile(PASTA_SAIDAS)
        else:
            messagebox.showinfo("Aviso", "A pasta 'saidas' ainda nao foi criada.")

    def escrever_no_log(self, texto: str, cor_padrao: str = "#d4d4d4"):
        self.area_log.configure(state="normal")
        segmentos = re.split(r"(\033\[[0-9;]+m)", texto)
        cor_atual = cor_padrao
        contador_tags = 0

        for segmento in segmentos:
            match_ansi = re.match(r"\033\[([0-9;]+)m", segmento)
            if match_ansi:
                codigo = match_ansi.group(1)
                cor_atual = self.CORES_ANSI.get(codigo, cor_padrao)
            elif segmento:
                nome_tag = f"cor_{id(segmento)}_{contador_tags}"
                contador_tags += 1
                self.area_log.tag_configure(nome_tag, foreground=cor_atual)
                self.area_log.insert("end", segmento, nome_tag)

        self.area_log.insert("end", "\n")
        self.area_log.configure(state="disabled")
        self.area_log.see("end")

    def executar_atualizacao(self):
        self.atualizar_painel_de_status()
        arquivo_bling, arquivos_multiloja, _ = self.detectar_csvs_na_pasta()

        if not arquivo_bling:
            messagebox.showerror("Arquivo nao encontrado", f"Nenhum arquivo de produtos do Bling encontrado na pasta inputs/.")
            return

        if not arquivos_multiloja:
            messagebox.showerror("Arquivo nao encontrado", f"Nenhum arquivo de loja encontrado na pasta inputs/.")
            return

        self.btn_executar.config(state="disabled")
        self.btn_abrir.config(state="disabled")

        self.area_log.configure(state="normal")
        self.area_log.delete("1.0", "end")
        self.area_log.configure(state="disabled")
        
        self.limpar_pasta_saidas()
        self.escrever_no_log(f"Pasta de trabalho: {PASTA_INPUTS}")
        self.barra_progresso.start(10)

        def rodar_em_segundo_plano():
            try:
                caminho_script = os.path.join(PASTA_BASE, "script.py")
                resultado = subprocess.run(
                    [sys.executable, caminho_script],
                    capture_output=True,
                    text=True,
                    cwd=PASTA_BASE,
                )
                self.root.after(0, lambda: self.finalizar_execucao(resultado))
            except Exception as erro:
                self.root.after(0, lambda: self.finalizar_com_erro(str(erro)))

        threading.Thread(target=rodar_em_segundo_plano, daemon=True).start()

    def finalizar_execucao(self, resultado):
        self.barra_progresso.stop()
        self.btn_executar.config(state="normal")
        self.btn_abrir.config(state="normal")

        if resultado.stdout:
            for linha in resultado.stdout.strip().split("\n"):
                self.escrever_no_log(linha)

        if resultado.returncode == 0:
            self.escrever_no_log("\n" + "-" * 37, "#555")
            self.escrever_no_log("Arquivos salvos em:  saidas/", self.CORES_ANSI["92"])
            self.escrever_no_log("  - arquivos _atualizado.csv por loja", self.CORES_ANSI["92"])
            messagebox.showinfo("Concluido", "Processo finalizado!\n\nArquivos gerados na pasta saidas/")
        else:
            self.escrever_no_log("\nERRO:", self.CORES_ANSI["91"])
            if resultado.stderr:
                for linha in resultado.stderr.strip().split("\n"):
                    self.escrever_no_log("  " + linha, self.CORES_ANSI["91"])
            messagebox.showerror("Erro", "Ocorreu um erro.\nVeja o log para detalhes.")

    def finalizar_com_erro(self, mensagem_erro: str):
        self.barra_progresso.stop()
        self.btn_executar.config(state="normal")
        self.btn_abrir.config(state="normal")
        self.escrever_no_log(f"Erro inesperado: {mensagem_erro}", self.CORES_ANSI["91"])
        messagebox.showerror("Erro", f"Erro inesperado:\n{mensagem_erro}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AtualizadorMultilojaApp(root)
    root.mainloop()
