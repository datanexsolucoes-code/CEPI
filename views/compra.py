import flet as ft
from models.database import Compra, ItemCompra, Uniforme, Fornecedor, db
from datetime import date

lista_tamanho = ["P", "M", "G", "GG", "XG", "XGG", "XXG", "G1", "G2", "EGG", "Único"]
lista_deposito = ["Escritório", "Opala"]


def view(page: ft.Page):
    page.scroll = "auto"

    # --- Dropdowns e controles ---
    fornecedor_dropdown = ft.Dropdown(label="Fornecedor", options=[], width=300)
    uniforme_dropdown = ft.Dropdown(label="Uniforme", options=[], width=300)
    tamanho_dropdown = ft.Dropdown(
        label="Tamanho",
        options=[ft.dropdown.Option(v) for v in lista_tamanho],
        width=150
    )
    quantidade = ft.TextField(label="Quantidade", value="1", width=100)
    preco_unitario = ft.TextField(label="Preço Unitário", value="0.00", width=120)

    itens_compra = []
    tabela_itens = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("Uniforme")),
        ft.DataColumn(ft.Text("Tamanho")),
        ft.DataColumn(ft.Text("Qtd")),
        ft.DataColumn(ft.Text("Preço Unit")),
        ft.DataColumn(ft.Text("Subtotal")),
        ft.DataColumn(ft.Text("Ação")),
    ], rows=[])

    subtotal_text = ft.Text(value="Subtotal: R$ 0,00", size=16, weight="bold")
    msg_compra = ft.Text()

    # --- Funções de carregamento ---
    def carregar_fornecedores():
        db.connect(reuse_if_open=True)
        fornecedor_dropdown.options.clear()
        for f in Fornecedor.select():
            fornecedor_dropdown.options.append(ft.dropdown.Option(key=str(f.id), text=f.nome))
        db.close()

    def carregar_uniformes():
        db.connect(reuse_if_open=True)
        uniforme_dropdown.options.clear()
        query = Uniforme.select(Uniforme.descricao).distinct()
        for u in query:
            uniforme_dropdown.options.append(ft.dropdown.Option(key=u.descricao, text=u.descricao))
        db.close()

    # --- Funções de atualização ---
    def atualizar_subtotal():
        total = sum(item["quantidade"] * item["preco"] for item in itens_compra)
        subtotal_text.value = f"Subtotal: R$ {total:,.2f}"
        page.update()

    def atualizar_tabela():
        tabela_itens.rows.clear()
        for idx, item in enumerate(itens_compra):
            subtotal = item["quantidade"] * item["preco"]

            def remover_item_closure(i=idx):
                def remover_item(e):
                    itens_compra.pop(i)
                    atualizar_tabela()
                    atualizar_subtotal()
                return remover_item

            tabela_itens.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(item["produto"].descricao)),
                ft.DataCell(ft.Text(item["tamanho"])),
                ft.DataCell(ft.Text(str(item["quantidade"]))),
                ft.DataCell(ft.Text(f"R$ {item['preco']:.2f}")),
                ft.DataCell(ft.Text(f"R$ {subtotal:.2f}")),
                ft.DataCell(ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=remover_item_closure())),
            ]))
        page.update()
        atualizar_subtotal()

    # --- Adicionar item ---
    def adicionar_item(e):
        try:
            db.connect(reuse_if_open=True)
            u = Uniforme.select().where(Uniforme.descricao == uniforme_dropdown.value).first()
            qtd = int(quantidade.value)
            preco = float(preco_unitario.value)

            if qtd <= 0 or preco <= 0:
                msg_compra.value = "Quantidade e preço devem ser maiores que zero."
                msg_compra.color = "red"
                page.update()
                return

            itens_compra.append({
                "produto": u,
                "tamanho": tamanho_dropdown.value,
                "quantidade": qtd,
                "preco": preco
            })

            atualizar_tabela()
            msg_compra.value = ""
        except Exception as ex:
            msg_compra.value = f"Erro: {ex}"
            msg_compra.color = "red"
        finally:
            db.close()
            page.update()

    # --- Salvar compra ---
    def salvar_compra(e):
        if not itens_compra:
            msg_compra.value = "Nenhum item adicionado."
            msg_compra.color = "red"
            page.update()
            return

        try:
            db.connect(reuse_if_open=True)
            fornecedor = Fornecedor.get_by_id(int(fornecedor_dropdown.value))
            total = sum(item["quantidade"] * item["preco"] for item in itens_compra)

            compra = Compra.create(
                fornecedor=fornecedor,
                data_compra=date.today(),
                valor=total
            )

            for item in itens_compra:
                subtotal = item["quantidade"] * item["preco"]
                ItemCompra.create(
                    compra=compra,
                    uniforme=item["produto"],
                    tamanho=item["tamanho"],
                    quantidade=item["quantidade"],
                    preco_unitario=item["preco"],
                    subtotal=subtotal,
                    estado="Novo"
                )
                u = item["produto"]
                u.quantidade_estoque += item["quantidade"]
                u.estado = "Novo"
                u.deposito = "Escritório"
                u.save()

            msg_compra.value = f"Compra salva com sucesso! ID: {compra.id}"
            msg_compra.color = "green"
            itens_compra.clear()
            atualizar_tabela()
            subtotal_text.value = "Subtotal: R$ 0,00"
        except Exception as ex:
            msg_compra.value = f"Erro ao salvar: {ex}"
            msg_compra.color = "red"
        finally:
            db.close()
            page.update()

    carregar_fornecedores()
    carregar_uniformes()

    aba_cadastro = ft.Column([
        ft.Text("Nova Compra", size=20, weight="bold"),
        fornecedor_dropdown,
        ft.Row([
            uniforme_dropdown, tamanho_dropdown, quantidade, preco_unitario,
            ft.ElevatedButton("Adicionar", on_click=adicionar_item)
        ]),
        tabela_itens,
        subtotal_text,
        ft.ElevatedButton("Salvar Compra", on_click=salvar_compra),
        msg_compra,
    ], expand=True, scroll="auto")

    # --- Aba Consulta ---
    tabela_compras = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("ID")),
        ft.DataColumn(ft.Text("Fornecedor")),
        ft.DataColumn(ft.Text("Data")),
        ft.DataColumn(ft.Text("Valor Total")),
        ft.DataColumn(ft.Text("Ação")),
    ], rows=[])

    tabela_itens_compra = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("Uniforme")),
        ft.DataColumn(ft.Text("Tamanho")),
        ft.DataColumn(ft.Text("Quantidade")),
        ft.DataColumn(ft.Text("Preço Unitário")),
        ft.DataColumn(ft.Text("Subtotal")),
    ], rows=[])

    msg_consulta = ft.Text()
    filtro_nome = ft.TextField(label="Buscar por fornecedor", width=300)
    btn_consultar = ft.ElevatedButton("Consultar", on_click=lambda e: carregar_compras(filtro_nome.value))

    # --- Função carregar compras (com mensagens de status) ---
    def carregar_compras(filtro=""):
        msg_consulta.value = "🔄 Pesquisando..."
        msg_consulta.color = "blue"
        page.update()

        try:
            tabela_compras.rows.clear()
            tabela_itens_compra.rows.clear()
            db.connect(reuse_if_open=True)

            query = Compra.select().join(Fornecedor)
            if filtro:
                query = query.where(Fornecedor.nome.contains(filtro))

            for compra in query.order_by(Compra.data_compra.desc()):

                def excluir_compra_closure(c=compra):
                    def excluir_compra(e):
                        try:
                            for item in ItemCompra.select().where(ItemCompra.compra == c):
                                u = item.uniforme
                                u.quantidade_estoque -= item.quantidade
                                u.save()
                            ItemCompra.delete().where(ItemCompra.compra == c).execute()
                            c.delete_instance()
                            msg_consulta.value = f"Compra {c.id} excluída com sucesso."
                            msg_consulta.color = "green"
                            carregar_compras(filtro_nome.value)
                            tabela_itens_compra.rows.clear()
                            page.update()
                        except Exception as ex:
                            msg_consulta.value = f"Erro ao excluir: {ex}"
                            msg_consulta.color = "red"
                            page.update()
                    return excluir_compra

                def mostrar_detalhes_closure(c=compra):
                    def mostrar_detalhes(e):
                        tabela_itens_compra.rows.clear()
                        for item in ItemCompra.select().where(ItemCompra.compra == c):
                            try:
                                descricao_uniforme = item.uniforme.descricao
                            except Uniforme.DoesNotExist:
                                descricao_uniforme = "Uniforme removido"
                            tabela_itens_compra.rows.append(ft.DataRow(cells=[
                                ft.DataCell(ft.Text(descricao_uniforme)),
                                ft.DataCell(ft.Text(item.tamanho)),
                                ft.DataCell(ft.Text(str(item.quantidade))),
                                ft.DataCell(ft.Text(f"R$ {item.preco_unitario:.2f}")),
                                ft.DataCell(ft.Text(f"R$ {item.subtotal:.2f}")),
                            ]))
                        page.update()
                    return mostrar_detalhes

                tabela_compras.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(compra.id))),
                    ft.DataCell(ft.Text(compra.fornecedor.nome)),
                    ft.DataCell(ft.Text(compra.data_compra.strftime("%d/%m/%Y"))),
                    ft.DataCell(ft.Text(f"R$ {compra.valor:,.2f}")),
                    ft.DataCell(ft.Row([
                        ft.IconButton(icon=ft.Icons.VISIBILITY, tooltip="Detalhes", on_click=mostrar_detalhes_closure()),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=excluir_compra_closure()),
                    ]))
                ]))

            msg_consulta.value = "✅ Consulta concluída."
            msg_consulta.color = "green"

        except Exception as ex:
            msg_consulta.value = f"Erro ao consultar: {ex}"
            msg_consulta.color = "red"

        finally:
            db.close()
            page.update()

    aba_consulta = ft.Column([
        ft.Text("Consulta de Compras", size=20, weight="bold"),
        ft.Row([filtro_nome, btn_consultar], spacing=10),
        msg_consulta,
        tabela_compras,
        ft.Text("Itens da Compra Selecionada:", size=16, weight="bold"),
        tabela_itens_compra,
    ], expand=True, scroll="auto")

    abas = ft.Tabs(expand=True, selected_index=0, tabs=[
        ft.Tab(text="Cadastro de Compras", content=aba_cadastro),
        ft.Tab(text="Consulta de Compras", content=aba_consulta),
    ])

    return abas