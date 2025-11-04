import flet as ft
from datetime import datetime, date
from collections import defaultdict
from models.database import Funcionario, Uniforme, Entrega, ItemEntrega, Comodato, db


def view(page: ft.Page):
    page.scroll = "auto"
    db.connect(reuse_if_open=True)

    # --- Carrega dados apenas no início ---
    funcionarios = list(Funcionario.select())
    uniformes = list(Uniforme.select())

    # Agrupa uniformes por descrição para gerar dropdown "distinct"
    descr_map = defaultdict(list)
    for u in uniformes:
        descr_map[u.descricao].append(u)

    # Opções únicas de descrição
    uniforme_descr_options = [ft.dropdown.Option(d, d) for d in descr_map.keys()]

    # --- Cadastro ---
    itens_container = ft.Column()
    data_entrega = ft.TextField(
        label="Data da Entrega (dd/mm/yyyy)",
        value=date.today().strftime("%d/%m/%Y"),
        width=200
    )
    funcionario_dd = ft.Dropdown(
        label="Funcionário",
        options=[ft.dropdown.Option(str(f.id), f.nome) for f in funcionarios],
        width=300
    )

    # Função de exibir mensagens
    def show_message(msg, color="blue"):
        try:
            page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
            page.snack_bar.open = True
            page.update()
        except Exception as err:
            print("SnackBar error:", err)
            page.dialog = ft.AlertDialog(title=ft.Text(msg))
            page.dialog.open = True
            page.update()

    # Atualiza os dropdowns dependentes com base na descrição do uniforme
    def atualizar_dropdowns(uniforme_dd, estado_dd, tamanho_dd, deposito_dd):
        desc = uniforme_dd.value
        if not desc:
            return

        unis = descr_map.get(desc, [])
        if not unis:
            return

        estados = sorted({u.estado for u in unis if u.estado})
        tamanhos = sorted({u.tamanho for u in unis if u.tamanho})
        depositos = sorted({u.deposito for u in unis if u.deposito})
        # fornecedores = sorted({u.fornecedor.nome for u in unis if u.fornecedor})

        estado_dd.options = [ft.dropdown.Option(e, e) for e in estados]
        tamanho_dd.options = [ft.dropdown.Option(t, t) for t in tamanhos]
        deposito_dd.options = [ft.dropdown.Option(d, d) for d in depositos]
        # fornecedor_dd.options = [ft.dropdown.Option(f, f) for f in fornecedores]

        if estados:
            estado_dd.value = estados[0]
        if tamanhos:
            tamanho_dd.value = tamanhos[0]
        if depositos:
            deposito_dd.value = depositos[0]
        # if fornecedores:
        #     fornecedor_dd.value = fornecedores[0]

        page.update()

    # Adicionar nova linha de item
    def adicionar_item(e=None):
        uniforme_dd = ft.Dropdown(
            label="Uniforme",
            options=uniforme_descr_options,
            width=200
        )
        estado_dd = ft.Dropdown(label="Estado", width=150)
        tamanho_dd = ft.Dropdown(label="Tamanho", width=150)
        deposito_dd = ft.Dropdown(label="Depósito", width=170)
        # fornecedor_dd = ft.Dropdown(label="Fornecedor", width=200)
        qtd_tf = ft.TextField(label="Quantidade", width=100)

        uniforme_dd.on_change = lambda e: atualizar_dropdowns(uniforme_dd, estado_dd, tamanho_dd, deposito_dd)

        linha = ft.Row(
            controls=[
                uniforme_dd,
                estado_dd,
                tamanho_dd,
                deposito_dd,
                # fornecedor_dd,
                qtd_tf,
                ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=lambda e: remover_item(linha))
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.START
        )
        itens_container.controls.append(linha)
        page.update()

    def remover_item(linha):
        if linha in itens_container.controls:
            itens_container.controls.remove(linha)
            page.update()

    # Resetar formulário
    def resetar_form():
        funcionario_dd.value = None
        data_entrega.value = date.today().strftime("%d/%m/%Y")
        itens_container.controls.clear()
        adicionar_item()
        page.update()

    # Salvar entrega
    def salvar_entrega(e):
        try:
            if not funcionario_dd.value:
                show_message("Selecione um funcionário!", "red")
                return

            try:
                data = datetime.strptime((data_entrega.value or "").strip(), "%d/%m/%Y").date()
            except Exception:
                show_message("Data inválida. Use o formato dd/mm/yyyy.", "red")
                return

            itens_validos = []
            for idx, row in enumerate(itens_container.controls):
                if not isinstance(row, ft.Row):
                    continue

                uniforme_dd = row.controls[0]
                estado_dd = row.controls[1]
                tamanho_dd = row.controls[2]
                deposito_dd = row.controls[3]
                qtd_tf = row.controls[4]  # ✅ Corrigido

                descricao = (uniforme_dd.value or "").strip()
                qtd_txt = (qtd_tf.value or "").strip()
                estado = (estado_dd.value or "").strip()
                tamanho = (tamanho_dd.value or "").strip()
                deposito = (deposito_dd.value or "").strip()

                if not (descricao and qtd_txt):
                    continue

                try:
                    qtd = int(qtd_txt)
                    if qtd <= 0:
                        show_message("Quantidade deve ser maior que zero.", "red")
                        return
                except ValueError:
                    show_message("Quantidade inválida!", "red")
                    return

                # Localiza fornecedor
                # try:
                #     fornecedor_obj = Fornecedor.get(Fornecedor.nome == fornecedor_nome)
                # except Fornecedor.DoesNotExist:
                #     show_message(f"Fornecedor '{fornecedor_nome}' não encontrado.", "red")
                #     return

                # Localiza o uniforme pela combinação completa
                try:
                    uni = Uniforme.get(
                        (Uniforme.descricao == descricao) &
                        (Uniforme.tamanho == tamanho) &
                        (Uniforme.deposito == deposito) &
                        (Uniforme.estado == estado)
                        # (Uniforme.fornecedor == fornecedor_obj)
                    )
                except Uniforme.DoesNotExist:
                    show_message(f"Uniforme '{descricao}' ({tamanho}, {estado}, {deposito}) não encontrado.", "red")
                    return

                if qtd > (uni.quantidade_estoque or 0):
                    show_message(f"Estoque insuficiente para {uni.descricao}.", "red")
                    return

                itens_validos.append({
                    "uni": uni,
                    "qtd": qtd,
                    "estado": estado,
                    "tamanho": tamanho,
                    "deposito": deposito
                })

            if not itens_validos:
                show_message("Inclua ao menos um item para a entrega.", "red")
                return

            with db.atomic():
                ent = Entrega.create(
                    funcionario=int(funcionario_dd.value),
                    data_entrega=data,
                    usuario=page.session.get("usuario")
                )

                for it in itens_validos:
                    ItemEntrega.create(
                        entrega=ent,
                        uniforme=it["uni"],
                        quantidade=it["qtd"],
                        estado=it["estado"],
                        tamanho=it["tamanho"]
                    )

                    Comodato.create(
                        entrega=ent,
                        funcionario=int(funcionario_dd.value),
                        uniforme=it["uni"],
                        quantidade=it["qtd"],
                        data_entrega=data,
                        ativo=True
                    )

                    # Atualiza o estoque
                    it["uni"].quantidade_estoque = (it["uni"].quantidade_estoque or 0) - it["qtd"]
                    it["uni"].save(force_insert=False)

            show_message("Entrega cadastrada e comodato atualizado!", "green")
            resetar_form()

        except Exception as ex:
            print("Erro salvar_entrega:", ex)
            show_message(f"Erro ao salvar entrega: {ex}", "red")

    # Botões
    btn_add = ft.IconButton(icon=ft.Icons.ADD, icon_color="green", on_click=adicionar_item)

    cadastro_layout = ft.Column([
        ft.Text("Cadastro de Entrega", size=20, weight="bold"),
        data_entrega,
        funcionario_dd,
        ft.Row([ft.Text("Itens da entrega", size=16), btn_add]),
        itens_container,
        ft.ElevatedButton(text="Salvar Entrega", on_click=salvar_entrega),
    ], scroll="auto")

    ###### Pesquisa #####
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

    funcionario_filtro_dd = ft.Dropdown(
        label="Funcionário",
        options=[ft.dropdown.Option("0", "Todos")] + [ft.dropdown.Option(str(f.id), f.nome) for f in funcionarios],
        value="0",
        width=300
    )

    resultado_lista = ft.ListView(
        expand=True,
        spacing=5,
        padding=10,
        on_scroll_interval=True
    )

    def excluir_entrega(entrega_id):
        try:
            with db.atomic():
                entrega = Entrega.get_by_id(entrega_id)
                itens = list(ItemEntrega.select().where(ItemEntrega.entrega == entrega.id))

                for item in itens:
                    uni = item.uniforme
                    uni.quantidade_estoque = (uni.quantidade_estoque or 0) + item.quantidade
                    uni.save(force_insert=False)

                for item in itens:
                    Comodato.update(ativo=False).where(
                        (Comodato.funcionario == entrega.funcionario) &
                        (Comodato.uniforme == item.uniforme) &
                        (Comodato.ativo == True)
                    ).execute()

                ItemEntrega.delete().where(ItemEntrega.entrega == entrega.id).execute()
                entrega.delete_instance()

            show_message("Entrega excluída, estoque atualizado e comodato desativado!", "green")
            pesquisar_entregas(None)
        except Exception as ex:
            print(">> ERRO ao excluir entrega:", ex)
            show_message(f"Erro ao excluir entrega: {ex}", "red")

    msg_consulta = ft.Text()

    def pesquisar_entregas(e):
        resultado_lista.controls.clear()
        msg_consulta.value = "🔄 Pesquisando..."
        msg_consulta.color = "blue"
        page.update()

        try:
            inicio = datetime.strptime(data_inicio.value, "%d/%m/%Y").date()
            fim = datetime.strptime(data_fim.value, "%d/%m/%Y").date()
        except ValueError:
            show_message("Datas inválidas!", "red")
            return

        query = Entrega.select().where(
            (Entrega.data_entrega >= inicio) & (Entrega.data_entrega <= fim)
        )
        if funcionario_filtro_dd.value != "0":
            query = query.where(Entrega.funcionario == int(funcionario_filtro_dd.value))

        entregas = list(query)

        if not entregas:
            resultado_lista.controls.append(ft.Text("Nenhuma entrega encontrada."))
        else:
            for ent in entregas:
                func = ent.funcionario.nome
                data_str = ent.data_entrega.strftime("%d/%m/%Y")
                user = ent.usuario
                itens = ItemEntrega.select().where(ItemEntrega.entrega == ent.id)

                itens_column = ft.Column([
                    ft.Text(f"- {i.uniforme.descricao} (Qtd: {i.quantidade}, Estado: {i.estado}, Tamanho: {i.tamanho})")
                    for i in itens
                ], spacing=2)

                resultado_lista.controls.append(
                    ft.Card(
                        content=ft.Column([
                            ft.Text(f"Data: {data_str} - Funcionário: {func} - Entregue por: {user}", weight="bold"),
                            itens_column,
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color="red",
                                    tooltip="Excluir entrega",
                                    on_click=lambda e, ent_id=ent.id: excluir_entrega(ent_id)
                                )
                            ], alignment=ft.MainAxisAlignment.END)
                        ], spacing=5),
                        elevation=2
                    )
                )
        msg_consulta.value = "✅ Consulta concluída."
        msg_consulta.color = "green"
        db.close()
        page.update()

    pesquisa_layout = ft.Column(
        [
            ft.Text("Pesquisar Entregas", size=20, weight="bold"),
            ft.Row([data_inicio, data_fim], spacing=10),
            funcionario_filtro_dd,
            msg_consulta,
            ft.ElevatedButton(text="Pesquisar", icon=ft.Icons.SEARCH, on_click=pesquisar_entregas),
            ft.Container(content=resultado_lista, expand=True, padding=0)
        ],
        expand=True, scroll="auto"
    )

    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Cadastro", content=cadastro_layout),
            ft.Tab(text="Pesquisa", content=pesquisa_layout),
        ]
    )

    adicionar_item()
    return tabs