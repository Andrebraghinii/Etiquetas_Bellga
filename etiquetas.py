import os, io, sys, json
import random
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox
from fpdf import FPDF
import xmltodict
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image

COR_FUNDO = "#2B2B2B" 
COR_DEST_DOURADO = "#CF9728"
COR_BOTAO_MARROM = "#8B651B"
DB_FILE = "memoria_codigos.json"

class SistemaEstoqueBellga(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Estoque Bellga Calçados - Elgin L42")
        
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        self.geometry(f"{min(1200, largura_tela-50)}x{min(900, altura_tela-100)}")
        self.configure(fg_color=COR_FUNDO)
        
        self.memoria = self.carregar_memoria()
        self.itens_nfe = []
        self.num_nf = ""
        self.nome_fornecedor = ""
        
        self.main_container = ctk.CTkFrame(self, fg_color=COR_FUNDO)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.topo_container = ctk.CTkFrame(self.main_container, fg_color=COR_FUNDO)
        self.topo_container.pack(fill="x", pady=(5, 10))

        self.inserir_logo_e_titulo()
        
        self.botoes_container = ctk.CTkFrame(self.main_container, fg_color=COR_FUNDO)
        self.botoes_container.pack(fill="x", pady=(5, 10))
        
        self.btn_carregar = ctk.CTkButton(self.botoes_container, text="1. IMPORTAR NOTA FISCAL (XML)", 
                                           command=self.processar_xml, fg_color=COR_BOTAO_MARROM,
                                           font=("Segoe UI", 16, "bold"), height=45)
        self.btn_carregar.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.btn_adicionar = ctk.CTkButton(self.botoes_container, text="+ ADICIONAR MATERIAL", 
                                            command=self.adicionar_linha_manual, fg_color="#34495e",
                                            font=("Segoe UI", 14, "bold"), height=45, state="normal")
        self.btn_adicionar.pack(side="right", expand=True, fill="x", padx=(5, 0))

        self.header = ctk.CTkFrame(self.main_container, fg_color=COR_FUNDO)
        self.header.pack(fill="x", padx=15)
        
        self.header.grid_columnconfigure(0, weight=0, minsize=40)
        self.header.grid_columnconfigure(1, weight=1)             
        self.header.grid_columnconfigure(2, weight=0, minsize=65)  
        self.header.grid_columnconfigure(3, weight=0, minsize=65)  
        self.header.grid_columnconfigure(4, weight=0, minsize=95) 
        self.header.grid_columnconfigure(5, weight=0, minsize=55)  
        self.header.grid_columnconfigure(6, weight=0, minsize=80)  
        self.header.grid_columnconfigure(7, weight=0, minsize=90) 

        ctk.CTkLabel(self.header, text="Pr?", text_color=COR_DEST_DOURADO).grid(row=0, column=0)
        ctk.CTkLabel(self.header, text="Material", text_color=COR_DEST_DOURADO, anchor="w").grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(self.header, text="Qtd NF", text_color=COR_DEST_DOURADO).grid(row=0, column=2)
        ctk.CTkLabel(self.header, text="Conv.", text_color=COR_DEST_DOURADO).grid(row=0, column=3)
        ctk.CTkLabel(self.header, text="Cód. Int.", text_color=COR_DEST_DOURADO).grid(row=0, column=4)
        ctk.CTkLabel(self.header, text="Vols.", text_color=COR_DEST_DOURADO).grid(row=0, column=5)
        ctk.CTkLabel(self.header, text="Qtd Padrão", text_color=COR_DEST_DOURADO).grid(row=0, column=6)
        ctk.CTkLabel(self.header, text="SÓ O Nº:", text_color="#5dade2").grid(row=0, column=7)

        self.frame_itens = ctk.CTkScrollableFrame(self.main_container, fg_color="#3D3D3D", border_color=COR_DEST_DOURADO, border_width=1)
        self.frame_itens.pack(pady=5, padx=5, fill="both", expand=True)
        
        self.footer = ctk.CTkFrame(self.main_container, fg_color=COR_FUNDO)
        self.footer.pack(fill="x", side="bottom", pady=5)
        
        ctk.CTkLabel(self.footer, text="© 2026 desenvolvido por André Nascimento - Todos os direitos reservados", 
                     font=("Segoe UI", 12, "italic"), text_color="#AAAAAA").pack(side="bottom")
        
        self.btn_gerar_footer = ctk.CTkButton(self.footer, text="2. GERAR ETIQUETAS AVULSAS", command=self.gerar_pdf, 
                                              fg_color=COR_BOTAO_MARROM, height=50, font=("Segoe UI", 16, "bold"))
        self.btn_gerar_footer.pack(pady=(5, 2), fill="x", padx=100)

    def carregar_memoria(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f: return json.load(f)
            except: return {}
        return {}

    def salvar_na_memoria(self, nome, codigo):
        if codigo.strip():
            self.memoria[nome] = codigo.strip()
            try:
                with open(DB_FILE, "w") as f: json.dump(self.memoria, f)
            except: pass

    def inserir_logo_e_titulo(self):
        inner_topo = ctk.CTkFrame(self.topo_container, fg_color=COR_FUNDO)
        inner_topo.pack(expand=True, fill="both")

        try:
            if hasattr(sys, '_MEIPASS'):
                path = os.path.join(sys._MEIPASS, "logo_bellga.png")
            else:
                path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_bellga.png")
            
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                w, h = img.size
                nova_h = 45
                nova_w = int(w * (nova_h / h))
                img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(nova_w, nova_h))
                self.logo_label = ctk.CTkLabel(inner_topo, image=img_ctk, text="")
                self.logo_label.place(x=10, y=0)
        except:
            pass 

        ctk.CTkLabel(inner_topo, text="BELLGA CALÇADOS", font=("Segoe UI", 28, "bold"), 
                     text_color=COR_DEST_DOURADO).pack(pady=5)

    def vincular_navegacao_enter(self, campos_ordenados):
        for i in range(len(campos_ordenados) - 1):
            atual = campos_ordenados[i]
            proximo = campos_ordenados[i+1]
            atual.bind("<Return>", lambda event, prox=proximo: self.pular_foco(event, prox), add="+")

    def pular_foco(self, event, proximo_widget):
        proximo_widget.focus_set()
        return "break"

    def processar_xml(self):
        caminho = filedialog.askopenfilename(filetypes=[("XML", "*.xml")])
        if not caminho: return
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = xmltodict.parse(f.read())
            inf = dados.get('nfeProc', {}).get('NFe', {}).get('infNFe', {}) or dados.get('NFe', {}).get('infNFe', {})
            self.num_nf = inf['ide']['nNF']
            self.nome_fornecedor = inf['emit']['xNome']
            det = inf['det']
            if not isinstance(det, list): det = [det]

            for w in self.frame_itens.winfo_children(): w.destroy()
            self.itens_nfe = []

            for i, p in enumerate(det):
                nome_prod = p['prod']['xProd']
                qtd_total = float(p['prod']['qCom'])
                
                row = ctk.CTkFrame(self.frame_itens, fg_color="#454545", height=40)
                row.pack(fill="x", pady=2, padx=5)
                
                row.grid_columnconfigure(0, weight=0, minsize=40)
                row.grid_columnconfigure(1, weight=1)
                row.grid_columnconfigure(2, weight=0, minsize=65)
                row.grid_columnconfigure(3, weight=0, minsize=65)
                row.grid_columnconfigure(4, weight=0, minsize=95)
                row.grid_columnconfigure(5, weight=0, minsize=55)
                row.grid_columnconfigure(6, weight=0, minsize=80)
                row.grid_columnconfigure(7, weight=0, minsize=90)
                
                v_chk = ctk.BooleanVar(value=True) 
                ctk.CTkCheckBox(row, text="", variable=v_chk, width=40, fg_color=COR_DEST_DOURADO).grid(row=0, column=0, padx=5)
                
                e_nome = ctk.CTkEntry(row, font=("Segoe UI", 11), height=28)
                e_nome.insert(0, nome_prod)
                e_nome.grid(row=0, column=1, sticky="ew", padx=2)
                
                e_qtd_xml = ctk.CTkEntry(row, font=("Segoe UI", 11), width=55, height=28, justify="center", fg_color="#333333")
                e_qtd_xml.insert(0, str(qtd_total))
                e_qtd_xml.grid(row=0, column=2, padx=2)

                e_conv = ctk.CTkEntry(row, justify="center", width=55, height=28); e_conv.insert(0, "1"); e_conv.grid(row=0, column=3, padx=2)
                
                e_c = ctk.CTkEntry(row, justify="center", width=85, height=28)
                e_c.insert(0, self.memoria.get(nome_prod, ""))
                e_c.grid(row=0, column=4, padx=2)
                
                e_v = ctk.CTkEntry(row, justify="center", width=45, height=28); e_v.insert(0, "1"); e_v.grid(row=0, column=5, padx=2)
                e_qp = ctk.CTkEntry(row, justify="center", width=70, height=28); e_qp.insert(0, str(qtd_total)); e_qp.grid(row=0, column=6, padx=2)
                
                e_so_num = ctk.CTkEntry(row, justify="center", width=65, height=28, fg_color="#2c3e50", border_color="#5dade2")
                e_so_num.insert(0, "")
                e_so_num.grid(row=0, column=7, padx=12)
                
                e_c.bind("<FocusOut>", lambda event, n=e_nome, c=e_c: self.buscar_por_codigo_callback(event, n, c))
                e_c.bind("<Return>", lambda event, n=e_nome, c=e_c: self.buscar_por_codigo_callback(event, n, c), add="+")
                
                self.vincular_navegacao_enter([e_nome, e_c, e_v, e_qp, e_so_num])
                
                self.itens_nfe.append({'chk':v_chk, 'e_nome':e_nome, 'e_qtd_xml':e_qtd_xml, 'e_conv':e_conv, 'e_cod':e_c, 'e_vol':e_v, 'e_pad':e_qp, 'e_so_num':e_so_num, 'manual':False})
            
            self.btn_gerar_footer.configure(text=f"2. GERAR ETIQUETAS (NF {self.num_nf})")
            
        except Exception as e: messagebox.showerror("Erro", f"Erro no XML: {e}")

    def adicionar_linha_manual(self):
        row = ctk.CTkFrame(self.frame_itens, fg_color="#555555", height=40)
        row.pack(fill="x", pady=2, padx=5)
        
        row.grid_columnconfigure(0, weight=0, minsize=40)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(2, weight=0, minsize=65)
        row.grid_columnconfigure(3, weight=0, minsize=65)
        row.grid_columnconfigure(4, weight=0, minsize=95)
        row.grid_columnconfigure(5, weight=0, minsize=55)
        row.grid_columnconfigure(6, weight=0, minsize=80)
        row.grid_columnconfigure(7, weight=0, minsize=90)
        
        v_chk = ctk.BooleanVar(value=True) 
        ctk.CTkCheckBox(row, text="", variable=v_chk, width=40, fg_color=COR_DEST_DOURADO).grid(row=0, column=0, padx=5)
        
        e_nome = ctk.CTkEntry(row, font=("Segoe UI", 11), height=28, placeholder_text="Nome do material manual...")
        e_nome.grid(row=0, column=1, sticky="ew", padx=2)
        
        e_qtd_xml = ctk.CTkEntry(row, font=("Segoe UI", 11), width=55, height=28, justify="center", fg_color="#333333")
        e_qtd_xml.insert(0, "0")
        e_qtd_xml.grid(row=0, column=2, padx=2)

        e_conv = ctk.CTkEntry(row, justify="center", width=55, height=28); e_conv.insert(0, "1"); e_conv.grid(row=0, column=3, padx=2)
        e_c = ctk.CTkEntry(row, justify="center", width=85, height=28); e_c.insert(0, "")
        e_c.grid(row=0, column=4, padx=2)
        e_v = ctk.CTkEntry(row, justify="center", width=45, height=28); e_v.insert(0, "1"); e_v.grid(row=0, column=5, padx=2)
        e_qp = ctk.CTkEntry(row, justify="center", width=70, height=28); e_qp.insert(0, "0"); e_qp.grid(row=0, column=6, padx=2)
        
        e_so_num = ctk.CTkEntry(row, justify="center", width=65, height=28, fg_color="#2c3e50", border_color="#5dade2")
        e_so_num.insert(0, "")
        e_so_num.grid(row=0, column=7, padx=12)
        
        e_c.bind("<FocusOut>", lambda event, n=e_nome, c=e_c: self.buscar_por_codigo_callback(event, n, c))
        e_c.bind("<Return>", lambda event, n=e_nome, c=e_c: self.buscar_por_codigo_callback(event, n, c), add="+")
        
        self.vincular_navegacao_enter([e_nome, e_c, e_v, e_qp, e_so_num])
        
        self.itens_nfe.append({'chk':v_chk, 'e_nome':e_nome, 'e_qtd_xml':e_qtd_xml, 'e_conv':e_conv, 'e_cod':e_c, 'e_vol':e_v, 'e_pad':e_qp, 'e_so_num':e_so_num, 'manual':True})
        
        e_nome.focus_set()

    def buscar_por_codigo_callback(self, event, widget_nome, widget_cod):
        codigo_atual = widget_cod.get().strip()
        if not codigo_atual: return
        
        for nome_salvo, cod_salvo in self.memoria.items():
            if cod_salvo == codigo_atual:
                widget_nome.delete(0, "end")
                widget_nome.insert(0, nome_salvo)
                break

    def abrir_janela_input(self, titulo, mensagem):
        janela_dialogo = ctk.CTkToplevel(self)
        janela_dialogo.title(titulo)
        janela_dialogo.geometry("400x200")
        janela_dialogo.configure(fg_color=COR_FUNDO)
        janela_dialogo.resizable(False, False)
        janela_dialogo.transient(self)
        janela_dialogo.grab_set()
        
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 200
        y = self.winfo_y() + (self.winfo_height() // 2) - 100
        janela_dialogo.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(janela_dialogo, text=mensagem, font=("Segoe UI", 14, "bold"), text_color=COR_DEST_DOURADO).pack(pady=(25, 10), padx=20)
        
        entrada = ctk.CTkEntry(janela_dialogo, width=320, height=35, font=("Segoe UI", 12), fg_color="#333333", border_color=COR_DEST_DOURADO)
        entrada.pack(pady=10)
        entrada.focus_set()
        
        resultado = {"valor": ""}
        
        def confirmar():
            resultado["valor"] = entrada.get()
            janela_dialogo.destroy()
            
        entrada.bind("<Return>", lambda e: confirmar())
        
        ctk.CTkButton(janela_dialogo, text="CONFIRMAR", font=("Segoe UI", 12, "bold"), fg_color=COR_BOTAO_MARROM, width=150, height=35, command=confirmar).pack(pady=(5, 15))
        
        self.wait_window(janela_dialogo)
        return resultado["valor"]

    def gerar_pdf(self):
        selecionados = [i for i in self.itens_nfe if i['chk'].get()]
        if not selecionados: return
        
        possui_manual_selecionado = any(item.get('manual', False) for item in selecionados)
        
        if possui_manual_selecionado and not self.num_nf:
            forn_input = self.abrir_janela_input("Dados do Fornecedor", "DIGITE O NOME DO FORNECEDOR:")
            if forn_input:
                self.nome_fornecedor = forn_input.strip().upper()
                
            nf_input = self.abrir_janela_input("Número da NF", "DIGITE O NÚMERO DA NOTA FISCAL:")
            if nf_input:
                self.num_nf = nf_input.strip().upper()

        data_i = datetime.now().strftime("%d/%m/%Y")
        
        try:
            diretorio_base = os.path.dirname(os.path.abspath(sys.argv[0]))
            pasta_pdfs = os.path.join(diretorio_base, "PDFS")
            if not os.path.exists(pasta_pdfs):
                os.makedirs(pasta_pdfs)

            pdf = FPDF(orientation='L', unit='mm', format=(50, 100))
            for item in selecionados:
                nome_prod = item['e_nome'].get().strip()
                qtd_base_xml = float(item['e_qtd_xml'].get().replace(',', '.') or 0)
                c_int = item['e_cod'].get().strip()
                conv = float(item['e_conv'].get().replace(',', '.') or 1)
                vols = int(item['e_vol'].get() or 1)
                padrao = float(item['e_pad'].get().replace(',', '.') or qtd_base_xml)
                
                so_num_val = item['e_so_num'].get().strip()
                avulsa_qtd_etiquetas = int(so_num_val) if so_num_val.isdigit() else 0
                apenas_uma = avulsa_qtd_etiquetas > 0
                
                self.salvar_na_memoria(nome_prod, c_int)
                total_limite_m2 = qtd_base_xml * conv
                acumulado = 0
                
                vols_loop = avulsa_qtd_etiquetas if apenas_uma else vols
                
                for idx in range(vols_loop):
                    n_vol = idx + 1
                    qtd_v = padrao if idx < vols - 1 else total_limite_m2 - acumulado
                    if apenas_uma:
                        qtd_v = padrao
                    if qtd_v <= 0 and not apenas_uma: continue
                    acumulado += qtd_v
                    
                    pdf.add_page()
                    pdf.set_font("Helvetica", 'B', 11)
                    
                    forn_texto = f"FORN: {self.nome_fornecedor[:35]}" if self.nome_fornecedor else "FORN:"
                    pdf.text(5, 10, forn_texto)
                    pdf.text(5, 18, f"MAT: {nome_prod[:40]}")
                    pdf.set_font("Helvetica", '', 11)
                    
                    nf_texto = f"NF: {self.num_nf} | COD: {c_int}" if self.num_nf else f"NF: | COD: {c_int}"
                    pdf.text(5, 26, nf_texto)
                    
                    qtd_final_str = f"{qtd_v:.2f}".rstrip('0').rstrip('.')
                    vol_str = f"1/1" if apenas_uma else f"{n_vol}/{vols}"
                    pdf.text(5, 34, f"DATA: {data_i} | VOL: {vol_str} | QTD: {qtd_final_str}")
                    
                    num_aleatorio = random.randint(1000, 9999)
                    conteudo_barcode = f"{c_int}#{qtd_final_str}${"0000" if apenas_uma else num_aleatorio}"
                    buf = io.BytesIO()
                    Code128(conteudo_barcode, writer=ImageWriter()).write(buf, options={"write_text":False, "module_height":5.0})
                    buf.seek(0)
                    pdf.image(buf, x=15, y=36, w=70, h=12)

            nome_arquivo = f"Etiquetas_NF_{self.num_nf}.pdf" if self.num_nf else f"Etiquetas_Avulsas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            caminho_final = os.path.join(pasta_pdfs, nome_arquivo)
            pdf.output(caminho_final)
            os.startfile(caminho_final)
        except Exception as e: messagebox.showerror("Erro", f"Erro no cálculo: {e}")

if __name__ == "__main__":
    SistemaEstoqueBellga().mainloop()