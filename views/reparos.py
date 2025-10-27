import flet as ft
from datetime import date, datetime
from models.database import db, Fornecedor, Reparo

def view(page: ft.Page):
    page.scroll = "auto"

    fornecedor_dropdown = ft.Dropdown(label="Fornecedor", options=[], width=300)

    def carregar_fornecedores():
        try:
            db.connect(reuse_if_open=True)
            fornecedores = Fornecedor.select().order_by(Fornecedor.nome)
            fornecedor_dropdown.options = [
                ft.dropdown.Option(str(f.id), f.nome)
                for f in fornecedores
            ]
        except Exception as ex:
            msg_compra.value = f"Erro ao carregar fornecedores: {ex}"
            msg_compra.color = "red"
        finally:
            try:
                db.close()
            except:
                pass

    carregar_fornecedores()

    # Campos de entrada
    data_entrega = ft.TextField(
        label="Data da Entrega (dd/mm/yyyy)",
        value=date.today().strftime("%d/%m/%Y"),
        width=200
    )
    quantidade = ft.TextField(label="Quantidade", value="1", width=100)
    descricao_reparo = ft.TextField(label="Descrição do Reparo", width=250)
    preco_unitario = ft.TextField(label="Preço Unitário", value="0.00", width=120)

    # Variáveis de controle
    itens_reparo = []
    tabela_itens = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("Data")),
        ft.DataColumn(ft.Text("Fornecedor")),
        ft.DataColumn(ft.Text("Reparo")),
        ft.DataColumn(ft.Text("Quantidade")),
        ft.DataColumn(ft.Text("Preço Unit")),
        ft.DataColumn(ft.Text("Subtotal")),
        ft.DataColumn(ft.Text("Ação")),
    ], rows=[])

    subtotal_text = ft.Text(value="Subtotal: R$ 0,00", size=16, weight="bold")
    msg_compra = ft.Text()

    def carregar_fornecedores():
        if not fornecedor_dropdown.options:
            db.connect(reuse_if_open=True)
            fornecedor_dropdown.options.clear()
            for f in Fornecedor.select():
                fornecedor_dropdown.options.append(ft.dropdown.Option(key=str(f.id), text=f.nome))
            db.close()
            page.update()

    def atualizar_subtotal():
        total = sum(item["quantidade"] * item["preco"] for item in itens_reparo)
        subtotal_text.value = f"Subtotal: R$ {total:,.2f}"
        page.update()

    def atualizar_tabela():
        tabela_itens.rows.clear()

        for idx, item in enumerate(itens_reparo):
            subtotal = item["quantidade"] * item["preco"]

            def remover_item_closure(i=idx):
                def remover_item(e):
                    itens_reparo.pop(i)
                    atualizar_tabela()
                    atualizar_subtotal()
                return remover_item

            tabela_itens.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(item["data"])),
                ft.DataCell(ft.Text(item["fornecedor_nome"])),
                ft.DataCell(ft.Text(item["descricao"])),
                ft.DataCell(ft.Text(str(item["quantidade"]))),
                ft.DataCell(ft.Text(f"R$ {item['preco']:.2f}")),
                ft.DataCell(ft.Text(f"R$ {subtotal:.2f}")),
                ft.DataCell(ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=remover_item_closure())),
            ]))

        page.update()
        atualizar_subtotal()

    def adicionar_item(e):
        try:
            # Validação
            if not fornecedor_dropdown.value:
                msg_compra.value = "Selecione um fornecedor."
                msg_compra.color = "red"
                page.update()
                return

            if not descricao_reparo.value.strip():
                msg_compra.value = "Descrição do reparo não pode estar vazia."
                msg_compra.color = "red"
                page.update()
                return

            qtd = int(quantidade.value)
            preco = float(preco_unitario.value)

            if qtd <= 0 or preco <= 0:
                msg_compra.value = "Quantidade e preço devem ser maiores que zero."
                msg_compra.color = "red"
                page.update()
                return

            data_formatada = datetime.strptime(data_entrega.value, "%d/%m/%Y").date()
            fornecedor = Fornecedor.get_by_id(int(fornecedor_dropdown.value))

            # Adiciona item à lista
            itens_reparo.append({
                "data": data_formatada.strftime("%d/%m/%Y"),
                "fornecedor_id": fornecedor.id,
                "fornecedor_nome": fornecedor.nome,
                "descricao": descricao_reparo.value,
                "quantidade": qtd,
                "preco": preco,
            })

            msg_compra.value = ""
            atualizar_tabela()

        except Exception as ex:
            msg_compra.value = f"Erro ao adicionar item: {ex}"
            msg_compra.color = "red"
        finally:
            page.update()

    def salvar_compra(e):
        if not itens_reparo:
            msg_compra.value = "Nenhum item adicionado."
            msg_compra.color = "red"
            page.update()
            return

        try:
            db.connect(reuse_if_open=True)

            for item in itens_reparo:
                subtotal = item["quantidade"] * item["preco"]
                data_formatada = datetime.strptime(item["data"], "%d/%m/%Y").date()
                fornecedor = Fornecedor.get_by_id(int(item["fornecedor_id"]))

                Reparo.create(
                    data_reparo=data_formatada,
                    fornecedor=fornecedor,
                    reparo=item["descricao"],
                    quantidade=item["quantidade"],
                    preco_unitario=item["preco"],
                    subtotal=subtotal,
                )

            msg_compra.value = "Reparo(s) salvo(s) com sucesso!"
            msg_compra.color = "green"
            itens_reparo.clear()
            atualizar_tabela()
            subtotal_text.value = "Subtotal: R$ 0,00"

        except Exception as ex:
            msg_compra.value = f"Erro ao salvar: {ex}"
            msg_compra.color = "red"
        finally:
            db.close()
            page.update()

    #### consulta ####

    def aba_consulta_reparos(page: ft.Page):
        tabela_reparos = ft.DataTable(columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Fornecedor")),
            ft.DataColumn(ft.Text("Data")),
            ft.DataColumn(ft.Text("Reparo")),
            ft.DataColumn(ft.Text("Quantidade")),
            ft.DataColumn(ft.Text("Valor Unitário")),
            ft.DataColumn(ft.Text("Subtotal")),
            ft.DataColumn(ft.Text("Ação")),
        ], rows=[])

        msg_consulta = ft.Text()

        # --- Campos de filtro ---
        filtro_nome = ft.TextField(label="Buscar por fornecedor", width=250)
        filtro_data_inicio = ft.TextField(label="Data início (dd/mm/aaaa)", width=180)
        filtro_data_fim = ft.TextField(label="Data fim (dd/mm/aaaa)", width=180)

        def carregar_reparos(filtro="", data_inicio="", data_fim=""):
            msg_consulta.value = "🔄 Pesquisando..."
            msg_consulta.color = "blue"
            page.update()

            from datetime import datetime
            try:
                tabela_reparos.rows.clear()
                db.connect(reuse_if_open=True)

                query = Reparo.select().join(Fornecedor)

                # --- Filtros dinâmicos ---
                if filtro:
                    query = query.where(Fornecedor.nome.contains(filtro))

                # --- Filtro por datas ---
                if data_inicio:
                    try:
                        data_i = datetime.strptime(data_inicio, "%d/%m/%Y").date()
                        query = query.where(Reparo.data_reparo >= data_i)
                    except ValueError:
                        msg_consulta.value = "⚠️ Data inicial inválida. Use o formato dd/mm/aaaa."
                        msg_consulta.color = "orange"
                        page.update()
                        return

                if data_fim:
                    try:
                        data_f = datetime.strptime(data_fim, "%d/%m/%Y").date()
                        query = query.where(Reparo.data_reparo <= data_f)
                    except ValueError:
                        msg_consulta.value = "⚠️ Data final inválida. Use o formato dd/mm/aaaa."
                        msg_consulta.color = "orange"
                        page.update()
                        return

                # --- Executa a consulta ---
                for reparo in query.order_by(Reparo.data_reparo.desc()):
                    def excluir_reparo_closure(r=reparo):
                        def excluir_reparo(e):
                            try:
                                r.delete_instance()
                                msg_consulta.value = f"Reparo {r.id} excluído com sucesso."
                                msg_consulta.color = "green"
                                carregar_reparos(filtro_nome.value, filtro_data_inicio.value, filtro_data_fim.value)
                            except Exception as ex:
                                msg_consulta.value = f"Erro ao excluir: {ex}"
                                msg_consulta.color = "red"
                            finally:
                                page.update()

                        return excluir_reparo

                    tabela_reparos.rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(reparo.id))),
                        ft.DataCell(ft.Text(reparo.fornecedor.nome)),
                        ft.DataCell(ft.Text(reparo.data_reparo.strftime("%d/%m/%Y"))),
                        ft.DataCell(ft.Text(reparo.reparo)),
                        ft.DataCell(ft.Text(str(reparo.quantidade))),
                        ft.DataCell(ft.Text(f"R$ {reparo.preco_unitario:.2f}")),
                        ft.DataCell(ft.Text(f"R$ {reparo.subtotal:.2f}")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=excluir_reparo_closure())
                            ])
                        )
                    ]))

                msg_consulta.value = "✅ Consulta concluída."
                msg_consulta.color = "green"

            except Exception as ex:
                msg_consulta.value = f"Erro ao consultar: {ex}"
                msg_consulta.color = "red"

            finally:
                db.close()
                page.update()

        btn_consultar = ft.ElevatedButton(
            "Consultar",
            on_click=lambda e: carregar_reparos(
                filtro_nome.value,
                filtro_data_inicio.value,
                filtro_data_fim.value
            )
        )

        # --- Layout da aba ---
        aba_consulta = ft.Column([
            ft.Text("Consulta de Reparos", size=20, weight="bold"),
            ft.ResponsiveRow([
                ft.Container(filtro_nome, col={"xs": 12, "md": 4}),
                ft.Container(filtro_data_inicio, col={"xs": 6, "md": 3}),
                ft.Container(filtro_data_fim, col={"xs": 6, "md": 3}),
                ft.Container(btn_consultar, col={"xs": 12, "md": 2}, alignment=ft.alignment.center),
            ], spacing=10),
            msg_consulta,
            tabela_reparos,
        ], expand=True, scroll="auto")

        return aba_consulta

    aba_cadastro = ft.Column([
        ft.Text("Novo Reparo", size=20, weight="bold"),
        data_entrega,
        fornecedor_dropdown,
        ft.Row([
            descricao_reparo,
            quantidade,
            preco_unitario,
            ft.ElevatedButton("Adicionar", on_click=adicionar_item)
        ]),
        tabela_itens,
        subtotal_text,
        ft.ElevatedButton("Salvar Reparo", on_click=salvar_compra),
        msg_compra,
    ], expand=True, scroll="auto")

    abas = ft.Tabs(expand=True, selected_index=0, tabs=[
        ft.Tab(text="Cadastro de Reparo", content=aba_cadastro),
        ft.Tab(text="Consulta de Reparo", content=aba_consulta_reparos(page)),
    ])

    return abas