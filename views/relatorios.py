import io, sys, os
import flet as ft
from models.database import Funcionario, Uniforme, Comodato, Compra, ItemCompra, Fornecedor, Reparo, db
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime, date

# Função que gera PDF e inicia download
def salvar_ou_download_pdf(page, pdf_bytes, file_name):
    # 🌐 Se estiver rodando no navegador
    if hasattr(page, "web") and page.web:
        page.download(file_name, pdf_bytes, "application/pdf")
        page.snack_bar = ft.SnackBar(ft.Text(f"📄 Download do PDF '{file_name}' iniciado!"))
        page.snack_bar.open = True
        page.update()
        return

    # 🖥️ Caso contrário, salva localmente
    try:
        # Detecta se está empacotado ou rodando no Python puro
        if getattr(sys, '_MEIPASS', False):
            base_dir = os.path.expanduser("~/Downloads")
        else:
            base_dir = os.path.join(os.getcwd(), "exports")

        os.makedirs(base_dir, exist_ok=True)
        file_path = os.path.join(base_dir, file_name)

        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        page.snack_bar = ft.SnackBar(ft.Text(f"📄 PDF salvo em: {file_path}"))
        page.snack_bar.open = True
        page.update()
        print(f"✅ PDF gerado em: {file_path}")

    except Exception as e:
        page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao salvar PDF: {e}"))
        page.snack_bar.open = True
        page.update()
        print("Erro ao exportar PDF:", e)

def exportar_para_pdf_flet(page, titulo, colunas, tabela=None, dados=None, coluna_total=None):
    """
    Exporta um relatório em PDF compatível com Flet Web e app compilado (PyInstaller).
    Pode receber um ft.DataTable ou uma lista de listas em 'dados'.
    Se 'coluna_total' for informado, adiciona uma linha com o total acumulado dessa coluna.
    """
    import io
    from datetime import datetime
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buffer = io.BytesIO()

    # --- Extrai dados da tabela se houver ---
    if tabela is not None:
        dados = [[cell.content.value for cell in row.cells] for row in tabela.rows]

    if not dados:
        page.snack_bar = ft.SnackBar(ft.Text("⚠️ Nenhum dado disponível para exportar!"))
        page.snack_bar.open = True
        page.update()
        return

    # --- Cria documento PDF ---
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20, rightMargin=20, topMargin=30, bottomMargin=20)
    elementos = []

    styles = getSampleStyleSheet()
    style_header = ParagraphStyle("header", parent=styles["Normal"], alignment=1, fontName="Helvetica-Bold", fontSize=9, textColor=colors.whitesmoke)
    style_cell = ParagraphStyle("cell", parent=styles["Normal"], alignment=1, fontSize=8, leading=10)
    style_total_label = ParagraphStyle("total_label", parent=styles["Normal"], alignment=2, fontName="Helvetica-Bold", fontSize=9)
    style_total_valor = ParagraphStyle("total_valor", parent=styles["Normal"], alignment=1, fontName="Helvetica-Bold", fontSize=9)

    titulo_formatado = Paragraph(f"<b>{titulo}</b>", styles["Title"])
    elementos.append(titulo_formatado)
    elementos.append(Spacer(1, 12))

    # --- Calcula total, se aplicável ---
    total_geral = None
    if coluna_total and coluna_total in colunas:
        idx = colunas.index(coluna_total)
        total_geral = 0.0
        for linha in dados:
            try:
                valor_str = str(linha[idx]).replace("R$", "").replace(",", ".").strip()
                total_geral += float(valor_str)
            except:
                pass

    # --- Converte dados em Paragraphs ---
    header_paragraphs = [Paragraph(col, style_header) for col in colunas]
    dados_formatados = [[Paragraph(str(valor), style_cell) for valor in linha] for linha in dados]

    # --- Adiciona linha de total (agora com Paragraphs corretos) ---
    if total_geral is not None:
        linha_total = [Paragraph("", style_cell)] * len(colunas)
        linha_total[0] = Paragraph("<b>Total Geral:</b>", style_total_label)
        linha_total[-1] = Paragraph(f"<b>R$ {total_geral:,.2f}</b>", style_total_valor)
        dados_formatados.append(linha_total)

    tabela_dados = [header_paragraphs] + dados_formatados

    # --- Define largura das colunas ---
    available_width = doc.width
    n_cols = len(colunas)
    colWidths = [available_width / n_cols] * n_cols

    t = Table(tabela_dados, colWidths=colWidths, repeatRows=1, hAlign="CENTER")

    estilo_base = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -2 if total_geral else -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]

    if total_geral is not None:
        estilo_base += [
            ("SPAN", (0, -1), (-2, -1)),
            ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("ALIGN", (-1, -1), (-1, -1), "RIGHT"),
        ]

    t.setStyle(TableStyle(estilo_base))
    elementos.append(t)

    doc.build(elementos)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # --- Salva PDF ---
    data_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{titulo.replace(' ', '_').lower()}_{data_str}.pdf"
    salvar_ou_download_pdf(page, pdf_bytes, file_name)

# View principal
def view(page: ft.Page):
    page.scroll = "auto"
    # ---------- Comodatos Ativos ----------
    def gerar_comodatos_ativos():
        msg_consulta = ft.Text()
        msg_pdf = ft.Text()
        conteudo_resultado = ft.Column(spacing=10, scroll="auto")

        # --- Dropdown com funcionários que têm comodatos ativos ---
        db.connect(reuse_if_open=True)
        funcionarios_ativos = (
            Funcionario.select()
            .join(Comodato)
            .where(Comodato.ativo == True)
            .distinct()
            .order_by(Funcionario.nome)
        )
        db.close()

        funcionarios_opcoes = [ft.dropdown.Option("0", "Todos os funcionários")] + [
            ft.dropdown.Option(f.nome) for f in funcionarios_ativos
        ]

        dd_funcionarios = ft.Dropdown(
            label="Filtrar por funcionário",
            options=funcionarios_opcoes,
            value="0",
            width=300,
        )

        # --- Função de pesquisa ---
        def carregar_comodatos(filtro_nome="0"):
            msg_consulta.value = "🔄 Pesquisando..."
            msg_consulta.color = "blue"
            conteudo_resultado.controls.clear()
            page.update()

            try:
                db.connect(reuse_if_open=True)

                query = (
                    Comodato
                    .select()
                    .where(Comodato.ativo == True)
                    .join(Funcionario)
                    .switch(Comodato)
                    .join(Uniforme)
                    .order_by(Funcionario.nome)
                )

                if filtro_nome != "0":
                    query = query.where(Funcionario.nome == filtro_nome)

                if not query.exists():
                    msg_consulta.value = "⚠️ Nenhum comodato ativo encontrado."
                    msg_consulta.color = "orange"
                    conteudo_resultado.controls.clear()
                    page.update()
                    return

                atual_funcionario = None
                grupo = ft.Column(spacing=3)

                for c in query:
                    if atual_funcionario != c.funcionario.nome:
                        # Fecha grupo anterior
                        if atual_funcionario is not None:
                            conteudo_resultado.controls.append(grupo)
                            conteudo_resultado.controls.append(
                                ft.Container(ft.Divider(color="gray", thickness=1), padding=5)
                            )
                            grupo = ft.Column(spacing=2)

                        atual_funcionario = c.funcionario.nome

                        # Novo bloco do funcionário
                        grupo = ft.Column(
                            [
                                ft.Text(
                                    f"👤 {atual_funcionario}",
                                    size=18,
                                    weight="bold",
                                    color="blue",
                                )
                            ],
                            spacing=3,
                        )

                    # Itens do funcionário (com recuo visual)
                    grupo.controls.append(
                        ft.Container(
                            ft.Row(
                                controls=[
                                    ft.Text(f"{c.uniforme.descricao}", width=300),
                                    ft.Text(f"Qtd: {c.quantidade}", width=100),
                                    ft.Text(f"Data: {c.data_entrega.strftime('%d/%m/%Y')}"),
                                ],
                                spacing=20,
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            padding=ft.padding.only(left=20),  # <-- Recuo visual
                        )
                    )

                # Adiciona último grupo
                if grupo.controls:
                    conteudo_resultado.controls.append(grupo)

                # Adiciona último grupo
                if grupo.controls:
                    conteudo_resultado.controls.append(ft.Container(ft.Divider(color="gray", thickness=1)))
                    conteudo_resultado.controls.append(grupo)

                msg_consulta.value = "✅ Consulta concluída."
                msg_consulta.color = "green"

                conteudo_resultado.controls.append(
                    ft.Container(
                        ft.ElevatedButton(
                            "📄 Exportar PDF",
                            icon=ft.Icons.PICTURE_AS_PDF,
                            on_click=lambda e: (
                                exportar_para_pdf_flet(
                                    page,
                                    "Comodatos Ativos",
                                    ["Funcionário", "Uniforme", "Quantidade", "Data Entrega"],
                                    dados=[
                                        [c.funcionario.nome, c.uniforme.descricao, c.quantidade,
                                         c.data_entrega.strftime("%d/%m/%Y")]
                                        for c in query
                                    ],
                                ),
                                setattr(msg_pdf, "value",
                                        "✅ PDF gerado em: F:\\Projetos\\CEPI\\exports\\comodatos_ativos.pdf"),
                                setattr(msg_pdf, "color", "green"),
                                page.update()
                            ),
                        ),
                        alignment=ft.alignment.center,
                        padding=10,
                    )
                )

            except Exception as ex:
                msg_consulta.value = f"❌ Erro ao consultar: {ex}"
                msg_consulta.color = "red"
            finally:
                db.close()
                page.update()

        # --- Botão de pesquisa ---
        btn_pesquisar = ft.ElevatedButton(
            "Pesquisar",
            on_click=lambda e: carregar_comodatos(dd_funcionarios.value),
        )

        return ft.Column(
            [
                ft.Text("📋 Relatório de Comodatos Ativos", size=20, weight="bold"),
                ft.Row([dd_funcionarios, btn_pesquisar], spacing=10),
                msg_consulta,
                ft.Container(conteudo_resultado, expand=True),
                ft.Row([msg_pdf]
                       , alignment=ft.MainAxisAlignment.CENTER
                       ),
            ],
            expand=True,
            scroll="auto",
        )

    # ---------- Estoque Atual ----------
    def gerar_estoque_atual():
        msg_consulta = ft.Text()
        msg_pdf = ft.Text()
        conteudo = ft.Column(spacing=10, scroll="auto")

        # --- Dropdown de descrições distintas ---
        db.connect(reuse_if_open=True)
        descricoes = (
            Uniforme.select(Uniforme.descricao)
            .distinct()
            .order_by(Uniforme.descricao)
        )
        db.close()

        opcoes = [ft.dropdown.Option("0", "Todos os uniformes")] + [
            ft.dropdown.Option(d.descricao) for d in descricoes
        ]

        dd_uniformes = ft.Dropdown(
            label="Filtrar por descrição",
            options=opcoes,
            value="0",
            width=300,
        )

        # --- Função para consultar estoque ---
        def carregar_estoque(filtro="0", tipo_relatorio="detalhado"):
            msg_consulta.value = "🔄 Pesquisando..."
            msg_consulta.color = "blue"
            conteudo.controls.clear()
            page.update()

            # Função auxiliar para ordenar tamanhos
            def chave_tamanho(tamanho):
                ordem = ["PP", "P", "M", "G", "GG", "XG", "EG", "XGG", "XXG", "UNICO"]
                return ordem.index(tamanho.upper()) if tamanho and tamanho.upper() in ordem else len(ordem)

            try:
                db.connect(reuse_if_open=True)
                query = (
                    Uniforme
                    .select()
                    .order_by(
                        Uniforme.descricao,
                        Uniforme.deposito,
                        Uniforme.estado,
                        Uniforme.tamanho,
                    )
                )

                if filtro != "0":
                    query = query.where(Uniforme.descricao == filtro)

                if not query.exists():
                    msg_consulta.value = "⚠️ Nenhum item encontrado."
                    msg_consulta.color = "orange"
                    page.update()
                    return

                # --- Agrupar por descrição ---
                grupos_descricao = {}
                for u in query:
                    grupos_descricao.setdefault(u.descricao, []).append(u)

                # --- Montagem visual ---
                for descricao, itens in grupos_descricao.items():
                    conteudo.controls.append(
                        ft.Row(
                            [
                                ft.Icon(name=ft.Icons.INVENTORY_2, color=ft.Colors.BLUE_400),
                                ft.Text(descricao, size=18, weight="bold", color=ft.Colors.BLUE_700),
                            ],
                            spacing=8,
                        )
                    )

                    # --- RELATÓRIO RESUMIDO ---
                    if tipo_relatorio == "resumido":
                        resumo = {}
                        for u in itens:
                            resumo[u.tamanho] = resumo.get(u.tamanho, 0) + u.quantidade_estoque

                        tamanhos_ordenados = sorted(resumo.keys(), key=chave_tamanho)

                        tabela = ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("Tamanho")),
                                ft.DataColumn(ft.Text("Quantidade Total")),
                            ],
                            rows=[
                                ft.DataRow(
                                    cells=[
                                        ft.DataCell(ft.Text(t)),
                                        ft.DataCell(ft.Text(str(resumo[t]))),
                                    ]
                                )
                                for t in tamanhos_ordenados
                            ],
                            column_spacing=60,
                            data_row_min_height=30,
                            data_row_max_height=35,
                        )

                        conteudo.controls.append(
                            ft.Container(tabela, padding=ft.padding.only(left=45, bottom=5))
                        )

                    # --- RELATÓRIO DETALHADO ---
                    else:
                        # Agrupar por depósito
                        depositos = {}
                        for u in itens:
                            depositos.setdefault(u.deposito, []).append(u)

                        for deposito, lista in depositos.items():
                            conteudo.controls.append(
                                ft.Container(
                                    ft.Text(
                                        f"Depósito: {deposito}",
                                        size=16,
                                        weight="bold",
                                        color=ft.Colors.GREY_700,
                                    ),
                                    padding=ft.padding.only(left=25, top=5, bottom=5),
                                )
                            )

                            lista_ordenada = sorted(lista, key=lambda x: chave_tamanho(x.tamanho))

                            tabela = ft.DataTable(
                                columns=[
                                    ft.DataColumn(ft.Text("Estado")),
                                    ft.DataColumn(ft.Text("Tamanho")),
                                    ft.DataColumn(ft.Text("Quantidade")),
                                ],
                                rows=[
                                    ft.DataRow(
                                        cells=[
                                            ft.DataCell(ft.Text(u.estado)),
                                            ft.DataCell(ft.Text(u.tamanho)),
                                            ft.DataCell(ft.Text(str(u.quantidade_estoque))),
                                        ]
                                    )
                                    for u in lista_ordenada
                                ],
                                column_spacing=30,
                                data_row_min_height=30,
                                data_row_max_height=35,
                            )

                            conteudo.controls.append(
                                ft.Container(tabela, padding=ft.padding.only(left=45, bottom=5))
                            )

                    conteudo.controls.append(ft.Divider(thickness=1, color=ft.Colors.GREY_400))

                # --- Botão Exportar PDF ---
                conteudo.controls.append(
                    ft.Container(
                        ft.ElevatedButton(
                            "📄 Exportar PDF",
                            icon=ft.Icons.PICTURE_AS_PDF,
                            on_click=lambda e: (
                                exportar_para_pdf_flet(
                                    page,
                                    "Estoque Atual",
                                    ["Depósito", "Descrição", "Estado", "Tamanho", "Quantidade"],
                                    dados=[
                                        [c.deposito, c.descricao, c.estado, c.tamanho, c.quantidade_estoque]
                                        for c in query
                                    ],
                                ),
                                setattr(msg_pdf, "value",
                                        "✅ PDF gerado em: F:\\Projetos\\CEPI\\exports\\comodatos_ativos.pdf"),
                                setattr(msg_pdf, "color", "green"),
                                page.update()
                            ),
                        ),
                        alignment=ft.alignment.center,
                        padding=10,
                    )
                )

                msg_consulta.value = "✅ Consulta concluída."
                msg_consulta.color = "green"

            except Exception as ex:
                msg_consulta.value = f"❌ Erro ao consultar: {ex}"
                msg_consulta.color = "red"
            finally:
                db.close()
                page.update()
        dd_tipo_relatorio = ft.Dropdown(
            label="Tipo de relatório",
            options=[
                ft.dropdown.Option("detalhado", "Detalhado"),
                ft.dropdown.Option("resumido", "Resumido"),
            ],
            value="detalhado",
            width=200,
        )

        # --- Botão de pesquisa ---
        btn_pesquisar = ft.ElevatedButton(
            "Pesquisar",
            on_click=lambda e: carregar_estoque(dd_uniformes.value, dd_tipo_relatorio.value),
        )

        return ft.Column(
            [
                ft.Text("📦 Relatório de Estoque Atual", size=20, weight="bold"),
                ft.Row([dd_uniformes, dd_tipo_relatorio, btn_pesquisar], spacing=10),
                msg_consulta,
                conteudo,
                ft.Row([msg_pdf]
                       , alignment=ft.MainAxisAlignment.CENTER
                       ),
            ],
            expand=True,
            scroll="auto",
        )

    # ---------- Compras Realizadas ----------
    def gerar_compras_realizadas():
        data_inicio = ft.TextField(
            label="Data Inicial (dd/mm/yyyy)",
            width=200,
            value=date.today().replace(day=1).strftime("%d/%m/%Y"),
        )
        data_fim = ft.TextField(
            label="Data Final (dd/mm/yyyy)",
            width=200,
            value=date.today().strftime("%d/%m/%Y"),
        )
        fornecedores = Fornecedor.select()
        filtro_fornecedor = ft.Dropdown(
            label="Fornecedor",
            options=[ft.dropdown.Option(str(f.id), f.nome) for f in fornecedores],
            width=200,
        )
        msg_pdf = ft.Text()
        msg_consulta = ft.Text(value="", size=14)
        total_texto = ft.Text(value="", weight="bold", size=16, color=ft.Colors.BLACK)

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
            rows=[],
        )

        btn_exportar = ft.ElevatedButton(
            "Exportar PDF",
            icon=ft.Icons.PICTURE_AS_PDF,
            visible=False,
            on_click=lambda e: (exportar_para_pdf_flet(
                page,
                "Compras Realizadas",
                [
                    "Data Compra",
                    "Fornecedor",
                    "Uniforme",
                    "Tamanho",
                    "Quantidade",
                    "Valor Unitário",
                    "Subtotal",
                ],
                tabela_compras,
                coluna_total="Subtotal"
            ),
            setattr(msg_pdf, "value",
                    "✅ PDF gerado em: F:\\Projetos\\CEPI\\exports\\comodatos_ativos.pdf"),
            setattr(msg_pdf, "color", "green"),
            page.update()
            )
        )

        def carregar_tabela(e=None):
            msg_consulta.value = "🔄 Pesquisando..."
            msg_consulta.color = ft.Colors.BLUE
            total_texto.value = ""
            tabela_compras.rows = []
            btn_exportar.visible = False
            page.update()

            try:
                # --- Converter datas ---
                dt_inicio = datetime.strptime(data_inicio.value, "%d/%m/%Y").date()
                dt_fim = datetime.strptime(data_fim.value, "%d/%m/%Y").date()

                # --- Consultar ---
                query = (
                    ItemCompra.select()
                    .join(Compra)
                    .join(Fornecedor)
                    .switch(ItemCompra)
                    .join(Uniforme)
                    .where((Compra.data_compra >= dt_inicio) & (Compra.data_compra <= dt_fim))
                    .order_by(Compra.data_compra)
                )

                if filtro_fornecedor.value:
                    query = query.where(Compra.fornecedor == int(filtro_fornecedor.value))

                if not query.exists():
                    msg_consulta.value = "⚠️ Nenhuma compra encontrada para o período selecionado."
                    msg_consulta.color = ft.Colors.ORANGE
                    page.update()
                    return

                # --- Montagem das linhas ---
                total_geral = 0
                rows = []
                for item in query:
                    subtotal = item.subtotal
                    total_geral += subtotal
                    rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(item.compra.data_compra.strftime("%d/%m/%Y"))),
                                ft.DataCell(ft.Text(item.compra.fornecedor.nome)),
                                ft.DataCell(ft.Text(item.uniforme.descricao)),
                                ft.DataCell(ft.Text(item.tamanho)),
                                ft.DataCell(ft.Text(str(item.quantidade))),
                                ft.DataCell(ft.Text(f"R$ {item.preco_unitario:.2f}")),
                                ft.DataCell(ft.Text(f"R$ {subtotal:.2f}")),
                            ]
                        )
                    )

                tabela_compras.rows = rows
                btn_exportar.visible = True
                total_texto.value = f"Total: R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X",
                                                                                                                ".")
                msg_consulta.value = "✅ Consulta concluída."
                msg_consulta.color = ft.Colors.GREEN

            except Exception as ex:
                msg_consulta.value = f"❌ Erro: {ex}"
                msg_consulta.color = ft.Colors.RED

            page.update()

        btn_filtrar = ft.ElevatedButton("Filtrar", on_click=carregar_tabela)

        return ft.Column(
            [
                ft.Row(
                    [data_inicio, data_fim, filtro_fornecedor, btn_filtrar, btn_exportar],
                    spacing=10,
                    scroll="auto",
                ),
                msg_consulta,
                ft.Row([msg_pdf]
                       , alignment=ft.MainAxisAlignment.CENTER
                       ),
                tabela_compras,
                ft.Container(total_texto, padding=10),
            ],
            scroll="auto",
        )

    # ---------- Reparos Realizados ----------
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
        msg_pdf = ft.Text()
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
                query = query.where((Reparo.data_reparo >= dt_inicio) & (Reparo.data_reparo <= dt_fim))

            if filtro_fornecedor.value:
                query = query.where(Reparo.fornecedor == int(filtro_fornecedor.value))

            for r in query:
                total += r.subtotal

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(r.data_reparo.strftime("%d/%m/%Y"))),
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
            on_click=lambda e: (exportar_para_pdf_flet(
                page,
                "Reparos Realizados",
                ["Data Reparo", "Fornecedor", "Reparo", "Quantidade", "Valor Unitário", "Subtotal"],
                tabela_reparos,
                coluna_total="Subtotal"
            ),

            setattr(msg_pdf, "value",
                    "✅ PDF gerado em: F:\\Projetos\\CEPI\\exports\\comodatos_ativos.pdf"),
            setattr(msg_pdf, "color", "green"),
            page.update())
        )

        return ft.Column([
            ft.Row([data_inicio, data_fim, filtro_fornecedor, btn_filtrar, btn_exportar], spacing=10),
            ft.Row([msg_pdf]
                   , alignment=ft.MainAxisAlignment.CENTER
                   ),
            tabela_reparos,
            total_text,
        ], scroll = "auto")

    # Tabs finais
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