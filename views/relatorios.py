import flet as ft
from models.database import Funcionario, Uniforme, Comodato, Compra, ItemCompra, Fornecedor, Reparo
from reportlab.pdfgen import canvas
from tkinter import filedialog, Tk
from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Função que gera PDF
def exportar_para_pdf_flet(page, titulo, colunas, tabela: ft.DataTable):
    def salvar_pdf(file_picker_result):
        if file_picker_result.path:
            caminho = file_picker_result.path
            dados = [[cell.content.value for cell in row.cells] for row in tabela.rows]

            # Cria documento
            doc = SimpleDocTemplate(caminho, pagesize=A4)
            elementos = []

            # Estilo do título
            styles = getSampleStyleSheet()
            titulo_formatado = Paragraph(f"<b>{titulo}</b>", styles['Title'])
            elementos.append(titulo_formatado)
            elementos.append(Spacer(1, 12))

            # Junta colunas + dados
            tabela_dados = [colunas] + dados

            # Cria tabela
            t = Table(tabela_dados, repeatRows=1)

            # Estilo da tabela
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke

                 ),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))

            elementos.append(t)
            doc.build(elementos)

    # Picker
    fp = ft.FilePicker(on_result=salvar_pdf)
    page.overlay.append(fp)
    page.update()
    fp.save_file(file_type="application/pdf")
# View principal
def view(page: ft.Page):

    # ---------- Comodatos Ativos ----------
    def gerar_comodatos_ativos():
        rows = []
        query = (
            Comodato
            .select()
            .where(Comodato.ativo == True)
            .join(Funcionario)
            .switch(Comodato)
            .join(Uniforme)
        )
        for c in query:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(c.funcionario.nome)),
                        ft.DataCell(ft.Text(c.uniforme.descricao)),
                        ft.DataCell(ft.Text(str(c.quantidade))),
                        ft.DataCell(ft.Text(str(c.data_entrega))),
                    ]
                )
            )

        tabela = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Funcionário")),
                ft.DataColumn(ft.Text("Uniforme")),
                ft.DataColumn(ft.Text("Quantidade")),
                ft.DataColumn(ft.Text("Data Entrega")),
            ],
            rows=rows
        )

        btn_exportar = ft.ElevatedButton(
            "Exportar PDF",
            on_click=lambda e: exportar_para_pdf_flet(
                page,
                "Comodatos Ativos",
                ["Funcionário", "Uniforme", "Quantidade", "Data Entrega"],
                tabela
            )
        )

        return ft.Column([btn_exportar, tabela])

    # ---------- Estoque Atual ----------
    def gerar_estoque_atual():
        rows = []
        query = Uniforme.select()
        for u in query:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(u.descricao)),
                        ft.DataCell(ft.Text(u.tamanho)),
                        ft.DataCell(ft.Text(u.deposito)),
                        ft.DataCell(ft.Text(u.estado)),
                        ft.DataCell(ft.Text(u.fornecedor)),
                        ft.DataCell(ft.Text(str(u.quantidade_estoque))),
                    ]
                )
            )

        tabela = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Descrição")),
                ft.DataColumn(ft.Text("Tamanho")),
                ft.DataColumn(ft.Text("Depósito")),
                ft.DataColumn(ft.Text("Estado")),
                ft.DataColumn(ft.Text("Fornecedor")),
                ft.DataColumn(ft.Text("Quantidade")),
            ],
            rows=rows
        )

        btn_exportar = ft.ElevatedButton(
            "Exportar PDF",
            on_click=lambda e: exportar_para_pdf_flet(
                page,
                "Estoque Atual",
                ["Descrição", "Tamanho", "Depósito", "Estado", "Fornecedor", "Quantidade"],
                tabela
            )
        )
        return ft.Column([btn_exportar, tabela])

    # ---------- Compras Realizadas ----------
    def gerar_compras_realizadas():
        data_inicio = ft.TextField(
            label="Data Inicial (dd/mm/yyyy)",
            width=200,
            value=date.today().replace(day=1).strftime("%d/%m/%Y")
        )
        data_fim = ft.TextField(
            label="Data Final (dd/mm/yyyy)",
            width=200,
            value=date.today().strftime("%d/%m/%Y")
        )
        fornecedores = Fornecedor.select()
        filtro_fornecedor = ft.Dropdown(
            label="Fornecedor",
            options=[ft.dropdown.Option(str(f.id), f.nome) for f in fornecedores],
            width=200
        )

        tabela_compras = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Data Compra")),
                ft.DataColumn(ft.Text("Fornecedor")),
                ft.DataColumn(ft.Text("Uniforme")),
                ft.DataColumn(ft.Text("Tamanho")),
                ft.DataColumn(ft.Text("Quantidade")),
                ft.DataColumn(ft.Text("Valor Unitário")),
                ft.DataColumn(ft.Text("Subtotal")),
            ],
            rows=[]
        )

        def carregar_tabela(e=None):
            rows = []
            try:
                dt_inicio = datetime.strptime(data_inicio.value, "%d/%m/%Y").date()
                dt_fim = datetime.strptime(data_fim.value, "%d/%m/%Y").date()
            except:
                dt_inicio = None
                dt_fim = None

            query = (
                ItemCompra
                .select()
                .join(Compra)
                .join(Fornecedor)
                .switch(ItemCompra)
                .join(Uniforme)
            )

            if dt_inicio and dt_fim:
                query = query.where((Compra.data_compra >= dt_inicio) & (Compra.data_compra <= dt_fim))

            if filtro_fornecedor.value:
                query = query.where(Compra.fornecedor == int(filtro_fornecedor.value))

            for item in query:
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(item.compra.data_compra.strftime("%d/%m/%Y"))),
                            ft.DataCell(ft.Text(item.compra.fornecedor.nome)),
                            ft.DataCell(ft.Text(item.uniforme.descricao)),
                            ft.DataCell(ft.Text(item.tamanho)),
                            ft.DataCell(ft.Text(str(item.quantidade))),
                            ft.DataCell(ft.Text(f"R$ {item.preco_unitario:.2f}")),
                            ft.DataCell(ft.Text(f"R$ {item.subtotal:.2f}")),
                        ]
                    )
                )

            tabela_compras.rows = rows
            tabela_compras.update()

        btn_filtrar = ft.ElevatedButton("Filtrar", on_click=carregar_tabela)
        btn_exportar = ft.ElevatedButton(
            "Exportar PDF",
            on_click=lambda e: exportar_para_pdf_flet(
                page,
                "Compras Realizadas",
                ["Data Compra", "Fornecedor", "Uniforme", "Tamanho", "Quantidade", "Valor Unitário", "Subtotal"],
                tabela_compras
            )
        )
        return ft.Column([
            ft.Row([data_inicio, data_fim, filtro_fornecedor, btn_filtrar, btn_exportar], spacing=10),
            tabela_compras
        ])

    def gerar_reparos_realizados(page: ft.Page):
        data_inicio = ft.TextField(
            label="Data Inicial (dd/mm/yyyy)",
            width=200,
            value=date.today().replace(day=1).strftime("%d/%m/%Y")
        )
        data_fim = ft.TextField(
            label="Data Final (dd/mm/yyyy)",
            width=200,
            value=date.today().strftime("%d/%m/%Y")
        )

        fornecedores = Fornecedor.select()
        filtro_fornecedor = ft.Dropdown(
            label="Fornecedor",
            options=[ft.dropdown.Option(str(f.id), f.nome) for f in fornecedores],
            width=200
        )

        tabela_reparos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Data Reparo")),
                ft.DataColumn(ft.Text("Fornecedor")),
                ft.DataColumn(ft.Text("Reparo")),
                ft.DataColumn(ft.Text("Quantidade")),
                ft.DataColumn(ft.Text("Valor Unitário")),
                ft.DataColumn(ft.Text("Subtotal")),
            ],
            rows=[]
        )

        # Totalizador
        total_text = ft.Text(value="Total: R$ 0,00", size=16, weight="bold")

        def carregar_tabela(e=None):
            rows = []
            total = 0.0

            try:
                dt_inicio = datetime.strptime(data_inicio.value, "%d/%m/%Y").date()
                dt_fim = datetime.strptime(data_fim.value, "%d/%m/%Y").date()
            except:
                dt_inicio = None
                dt_fim = None

            query = Reparo.select().join(Fornecedor)

            if dt_inicio and dt_fim:
                query = query.where((Reparo.data_repado >= dt_inicio) & (Reparo.data_repado <= dt_fim))

            if filtro_fornecedor.value:
                query = query.where(Reparo.fornecedor == int(filtro_fornecedor.value))

            for r in query:
                total += r.subtotal  # acumula subtotal

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(r.data_repado.strftime("%d/%m/%Y"))),
                            ft.DataCell(ft.Text(r.fornecedor.nome)),
                            ft.DataCell(ft.Text(r.reparo)),
                            ft.DataCell(ft.Text(str(r.quantidade))),
                            ft.DataCell(ft.Text(f"R$ {r.preco_unitario:.2f}")),
                            ft.DataCell(ft.Text(f"R$ {r.subtotal:.2f}")),
                        ]
                    )
                )

            tabela_reparos.rows = rows
            total_text.value = f"Total: R$ {total:,.2f}"
            tabela_reparos.update()
            total_text.update()

        btn_filtrar = ft.ElevatedButton("Filtrar", on_click=carregar_tabela)

        btn_exportar = ft.ElevatedButton(
            "Exportar PDF",
            on_click=lambda e: exportar_para_pdf_flet(
                page,
                "Reparos Realizados",
                ["Data Reparo", "Fornecedor", "Reparo", "Quantidade", "Valor Unitário", "Subtotal"],
                tabela_reparos
            )
        )

        return ft.Column([
            ft.Row([data_inicio, data_fim, filtro_fornecedor, btn_filtrar, btn_exportar], spacing=10),
            tabela_reparos,
            total_text  # exibindo o total abaixo da tabela
        ])
    # ---------- Tabs finais ----------
    return ft.Tabs(
        selected_index=0,
        animation_duration=300,
        expand=1,
        tabs=[
            ft.Tab(text="Comodatos Ativos", content=ft.Container(content=gerar_comodatos_ativos(), padding=20)),
            ft.Tab(text="Estoque Atual", content=ft.Container(content=gerar_estoque_atual(), padding=20)),
            ft.Tab(text="Compras Realizadas", content=ft.Container(content=gerar_compras_realizadas(), padding=20)),
            ft.Tab(text="Reparos Solicitados", content=ft.Container(content=gerar_reparos_realizados(page), padding=20)),
        ]
    )