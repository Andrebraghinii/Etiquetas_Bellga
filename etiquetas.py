import os, io, sys, json
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
DB_FILE = "memoria_codigos.json"

class SistemaEstoqueBellga(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Estoque Bellga Calçados")
        
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        self.geometry(f"{min(1200, largura_tela-50)}x{min(900, altura_tela-100)}")
        self.configure(fg_color=COR_FUNDO)
        
        self.memoria = self.carregar_memoria()
        self.itens_nfe = []
        
        self.main_container = ctk.CTkFrame(self, fg_color=COR_FUNDO)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.inserir_logo_topo()
        
        self.btn_carregar = ctk.CTkButton(self.main_container, text="1. IMPORTAR NOTA FISCAL (XML)", 
                                           command=self.processar_xml, fg_color="#8B651B",
                                           font=("Segoe UI", 16, "bold"), height=45)
        self.btn_carregar.pack(pady=(5, 10))

        self.header = ctk.CTkFrame(self.main_container, fg_color=COR_FUNDO)
        self.header.pack(fill="x", padx=15)
        
        self.header.grid_columnconfigure(0, weight=0)
        self.header.grid_columnconfigure(1, weight=4)
        self.header.grid_columnconfigure(2, weight=1)
        self.header.grid_columnconfigure(3, weight=1)
        self.header.grid_columnconfigure(4, weight=1)
        self.header.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(self.header, text="Pr?", text_color=COR_DEST_DOURADO, width=40).grid(row=0, column=0, padx=5)
        ctk.CTkLabel(self.header, text="Material e Quantidade na NF", text_color=COR_DEST_DOURADO, anchor="w").grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkLabel(self.header, text="Cód. Int.", text_color=COR_DEST_DOURADO).grid(row=0, column=2, padx=5)
        ctk.CTkLabel(self.header, text="Vols.", text_color=COR_DEST_DOURADO).grid(row=0, column=3, padx=5)
        ctk.CTkLabel(self.header, text="Qtd Padrão", text_color=COR_DEST_DOURADO).grid(row=0, column=4, padx=5)
        ctk.CTkLabel(self.header, text="SÓ O Nº:", text_color="#5dade2").grid(row=0, column=5, padx=5)

        self.frame_itens = ctk.CTkScrollableFrame(self.main_container, fg_color="#3D3D3D", border_color=COR_DEST_DOURADO, border_width=1)
        self.frame_itens.pack(pady=5, padx=5, fill="both", expand=True)
        
        self.footer = ctk.CTkFrame(self.main_container, fg_color=COR_FUNDO)
        self.footer.pack(fill="x", side="bottom", pady=5)
        
        self.btn_gerar_final = None
        ctk.CTkLabel(self.footer, text="© 2026 André Nascimento - Todos os direitos reservados\nSistema de Gerenciamento de Etiquetas Bellga Calçados", font=("Segoe UI", 12, "italic"), text_color="#AAAAAA").pack(side="bottom")

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

    def inserir_logo_topo(self):
        try:
            base = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base, "logo_bellga.png")
            if os.path.exists(path):
                img = Image.open(path).convert("RGB")
                img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(150, int(img.size[1] * 150 / img.size[0])))
                ctk.CTkLabel(self.main_container, image=img_ctk, text="").pack(pady=(5,5))
            else: raise Exception
        except:
            ctk.CTkLabel(self.main_container, text="BELLGA CALÇADOS", font=("Segoe UI", 28, "bold"), text_color=COR_DEST_DOURADO).pack(pady=10)

    def focar_proximo(self, event, index):
        if index + 1 < len(self.itens_nfe):
            self.itens_nfe[index + 1]['e_cod'].focus()

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
                qtd_total = int(float(p['prod']['qCom']))
                
                row = ctk.CTkFrame(self.frame_itens, fg_color="#454545", height=50)
                row.pack(fill="x", pady=2, padx=5)
                
                row.grid_columnconfigure(0, weight=0); row.grid_columnconfigure(1, weight=4)
                row.grid_columnconfigure(2, weight=1); row.grid_columnconfigure(3, weight=1)
                row.grid_columnconfigure(4, weight=1); row.grid_columnconfigure(5, weight=1)
                
                v_chk = ctk.BooleanVar(value=True) 
                ctk.CTkCheckBox(row, text="", variable=v_chk, width=40, fg_color=COR_DEST_DOURADO).grid(row=0, column=0, padx=5)
                ctk.CTkLabel(row, text=f"({qtd_total}x) {nome_prod[:40]}", anchor="w", font=("Segoe UI", 11)).grid(row=0, column=1, padx=5, sticky="ew")
                
                cod_sugerido = self.memoria.get(nome_prod, "")
                e_c = ctk.CTkEntry(row, justify="center")
                e_c.insert(0, cod_sugerido)
                e_c.grid(row=0, column=2, padx=5, sticky="ew")
                e_c.bind("<Return>", lambda e, idx=i: self.focar_proximo(e, idx))
                
                e_v = ctk.CTkEntry(row, justify="center")
                e_v.insert(0, "1"); e_v.grid(row=0, column=3, padx=5, sticky="ew")
                
                e_qp = ctk.CTkEntry(row, justify="center")
                e_qp.insert(0, str(qtd_total)); e_qp.grid(row=0, column=4, padx=5, sticky="ew")

                e_sel = ctk.CTkEntry(row, justify="center", fg_color="#1A1A1A", border_color="#5dade2")
                e_sel.grid(row=0, column=5, padx=5, sticky="ew")
                
                self.itens_nfe.append({'chk':v_chk, 'nome':nome_prod, 'total':qtd_total, 'e_cod':e_c, 'e_vol':e_v, 'e_pad':e_qp, 'e_sel':e_sel})
            
            if self.btn_gerar_final: self.btn_gerar_final.destroy()
            self.btn_gerar_final = ctk.CTkButton(self.footer, text=f"2. GERAR ETIQUETAS (NF {self.num_nf})", 
                                                command=self.gerar_pdf, fg_color="#27ae60", height=50, font=("Segoe UI", 16, "bold"))
            self.btn_gerar_final.pack(pady=(5, 2), fill="x", padx=100)
            
        except Exception as e: messagebox.showerror("Erro", f"Erro no XML: {e}")

    def gerar_pdf(self):
        selecionados = [i for i in self.itens_nfe if i['chk'].get()]
        if not selecionados: return
        
        data_impressao = datetime.now().strftime("%d/%m/%Y")
        
        try:
            pdf = FPDF(orientation='L', unit='mm', format=(35, 100))
            for item in selecionados:
                c_int = item['e_cod'].get().strip()
                vols = int(item['e_vol'].get() or 1)
                padrao = int(item['e_pad'].get() or item['total'])
                
                if (vols * padrao) > (item['total'] * 1.5):
                    if not messagebox.askyesno("Aviso", f"Quantidade suspeita para '{item['nome'][:15]}'. Continuar?"):
                        return

                self.salvar_na_memoria(item['nome'], c_int)
                filtro = item['e_sel'].get().strip()
                vols_alvo = [int(x) for x in filtro.replace(',', ' ').split() if x.isdigit()]

                acumulado = 0
                for idx in range(vols):
                    n_vol = idx + 1
                    qtd_v = padrao if idx < vols - 1 else item['total'] - acumulado
                    acumulado += qtd_v
                    if vols_alvo and n_vol not in vols_alvo: continue
                    if qtd_v <= 0: continue
                    
                    pdf.add_page()
                    pdf.set_font("Helvetica", 'B', 9)
                    pdf.text(5, 6, f"FORN: {self.nome_fornecedor[:35]}")
                    pdf.text(5, 11, f"MAT: {item['nome'][:40]}")
                    pdf.set_font("Helvetica", '', 9)
                    pdf.text(5, 16, f"NF: {self.num_nf} | COD: {c_int} | DATA: {data_impressao}")
                    pdf.text(5, 21, f"VOL: {n_vol}/{vols} | QTD: {qtd_v}")
                    
                    buf = io.BytesIO()
                    Code128(f"{c_int}*{qtd_v}#{n_vol}", writer=ImageWriter()).write(buf, options={"write_text":False, "module_height":5.0})
                    buf.seek(0); pdf.image(buf, x=25, y=23, w=50, h=10)

            pasta_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(pasta_desktop): pasta_desktop = os.getcwd()
            caminho_final = os.path.join(pasta_desktop, f"Etiquetas_Bellga_{self.num_nf}.pdf")
            pdf.output(caminho_final)
            os.startfile(caminho_final)
        except Exception as e: messagebox.showerror("Erro", f"Erro ao salvar: {e}")

if __name__ == "__main__":
    SistemaEstoqueBellga().mainloop()