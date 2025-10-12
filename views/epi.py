import flet as ft
from functools import partial
from models.database import Uniforme, Fornecedor, db

lista_tamanho = ["P", "M", "G", "GG", "XG", "XGG", "XXG", "G1", "G2", "EGG", "Único"]
lista_deposito = ["Escritório", "Opala"]
lista_estado = ["Novo", "Semi novo", "Usado", "Obra"]

def view(page: ft.Page):
    page.scroll = "auto"
    descricao = ft.TextField(label="Descrição",width=500)
    tamanho = ft.Dropdown(
        label="Tamanho",
        options=[ft.dropdown.Option(v) for v in lista_tamanho],
        width=150
    )
    quantidade_estoque = ft.TextField(label="Estoque", width=100)
    deposito = ft.Dropdown(
        label="Depósito",
        options=[ft.dropdown.Option(v) for v in lista_deposito],
        width=150
    )
    estado = ft.Dropdown(
        label="Estado",
        options=[ft.dropdown.Option(v) for v in lista_estado],
        width=150
    )
    fornecedor_dropdown = ft.Dropdown(label="Fornecedor",width=200, options=[])
    msg_cadastro = ft.Text(color="red")
    msg_pesquisa = ft.Text(color="red")

    # ---- Carrega fornecedores no dropdown ----
    def carregar_fornecedores():
        db.connect(reuse_if_open=True)
        fornecedores = Fornecedor.select()
        fornecedor_dropdown.options = [
            ft.dropdown.Option(str(f.id), f.nome)  # value = ID, texto = nome
            for f in fornecedores
        ]
        db.close()

    carregar_fornecedores()  # chamado após a função existir

    # ---- Salva uniforme ----
    def salvar_epi(e):
        try:
            db.connect(reuse_if_open=True)
            Uniforme.create(
                descricao=descricao.value,
                tamanho=tamanho.value,
                quantidade_estoque=int(quantidade_estoque.value),
                deposito=deposito.value,
                estado=estado.value,
                fornecedor=int(fornecedor_dropdown.value)  # Passa o ID do fornecedor
            )
            msg_cadastro.value = f"Uniforme {descricao.value} salvo com sucesso!"
            msg_cadastro.color = "green"

            # Limpa campos
            descricao.value = ""
            tamanho.value = None
            tamanho.selected_index = -1
            quantidade_estoque.value = ""
            deposito.value = None
            deposito.selected_index = -1
            estado.value = None
            estado.selected_index = -1
            fornecedor_dropdown.value = None
            fornecedor_dropdown.selected_index = -1
            page.update()

        except Exception as ex:
            msg_cadastro.value = f"Erro ao salvar/atualizar: {ex}"
            msg_cadastro.color = "red"
        finally:
            db.close()
            atualizar_tabela()
            page.update()

        # ------------------ ABA DE PESQUISA ------------------

    campo_busca = ft.TextField(label="Buscar por descrição", expand=True)
    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text("Descrição")),
            ft.DataColumn(label=ft.Text("Tamanho")),
            ft.DataColumn(label=ft.Text("quantidade_estoque")),
            ft.DataColumn(label=ft.Text("Deposito")),
            ft.DataColumn(label=ft.Text("Estado")),
            ft.DataColumn(label=ft.Text("Fornecedor")),
            ft.DataColumn(label=ft.Text("Ações")),
        ],
        rows=[]
    )

    def excluir_epi(uniforme_id):
        try:
            db.connect(reuse_if_open=True)
            # tenta get_by_id (peewee)
            try:
                epi = Uniforme.get_by_id(uniforme_id)
            except Exception:
                epi = Uniforme.get(Uniforme.id == uniforme_id)

            desc = getattr(epi, "descricao", str(uniforme_id))
            epi.delete_instance()
            msg_pesquisa.value = f"EPI '{desc}' excluído com sucesso!"
            msg_pesquisa.color = "green"
        except Exception as ex:
            msg_pesquisa.value = f"Erro ao excluir: {ex}"
            msg_pesquisa.color = "red"
        finally:
            db.close()
            atualizar_tabela()
            page.update()

    # Função para editar um uniforme (abre dialog)
    def editar_epi(uniforme_id,e):
        # busca dados atuais
        try:
            db.connect(reuse_if_open=True)
            uniforme = Uniforme.get_by_id(uniforme_id)
        finally:
            db.close()

        # campos do formulário
        descricao_field = ft.TextField(label="Descrição", value=uniforme.descricao or "")
        tamanho_field = ft.TextField(label="Tamanho", value=uniforme.tamanho or "")
        quantidade_field = ft.TextField(label="Quantidade", value=str(uniforme.quantidade_estoque or 0))
        deposito_field = ft.TextField(label="Depósito", value=uniforme.deposito or "")
        estado_field = ft.TextField(label="Estado", value=uniforme.estado or "")

        # dropdown de fornecedores (se quiser permitir trocar)
        fornecedores = Fornecedor.select()
        options = [ft.dropdown.Option(str(f.id), f.nome) for f in fornecedores]
        fornecedor_value = str(uniforme.fornecedor.id) if getattr(uniforme, "fornecedor", None) else None
        fornecedor_dropdown = ft.Dropdown(label="Fornecedor", options=options, value=fornecedor_value, width=300)

        def fechar_dialog():
            if page.dialog:
                page.dialog.open = False
                page.update()
                page.dialog = None

        def salvar_click(e):
            try:
                db.connect(reuse_if_open=True)
                u = Uniforme.get_by_id(uniforme_id)
                u.descricao = descricao_field.value
                u.tamanho = tamanho_field.value
                # tenta converter quantidade para int
                try:
                    u.quantidade_estoque = int(quantidade_field.value)
                except:
                    u.quantidade_estoque = 0
                u.deposito = deposito_field.value
                u.estado = estado_field.value
                if fornecedor_dropdown.value:
                    u.fornecedor = Fornecedor.get_by_id(int(fornecedor_dropdown.value))
                u.save()

                msg_pesquisa.value = "EPI atualizado com sucesso!"
                msg_pesquisa.color = "green"
            except Exception as ex:
                msg_pesquisa.value = f"Erro ao salvar: {ex}"
                msg_pesquisa.color = "red"
            finally:
                db.close()
                fechar_dialog()
                atualizar_tabela()
                page.update()

        btn_salvar = ft.ElevatedButton("Salvar", on_click=salvar_click)
        btn_cancel = ft.TextButton("Cancelar", on_click=lambda e: fechar_dialog())

        page.dialog = None
        dialog = ft.AlertDialog(
            title=ft.Text("Editar Uniforme"),
            content=ft.Column([
                descricao_field,
                tamanho_field,
                quantidade_field,
                deposito_field,
                estado_field,
                fornecedor_dropdown
            ], tight=True),
            actions=[btn_salvar, btn_cancel],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = dialog
        page.dialog.open = True
        page.update()

    # Atualiza a tabela — agora com botões de Editar e Excluir usando o id
    def atualizar_tabela():
        db.connect(reuse_if_open=True)
        filtro = campo_busca.value.strip()
        if filtro:
            query = Uniforme.select().where(
                (Uniforme.descricao.contains(filtro)) | (Uniforme.descricao.contains(filtro))
            )
        else:
            query = Uniforme.select()

        tabela.rows = []
        for c in query:
            fornecedor_nome = getattr(c.fornecedor, "nome", "") if getattr(c, "fornecedor", None) else ""
            tabela.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(c.descricao)),
                        ft.DataCell(ft.Text(c.tamanho)),
                        ft.DataCell(ft.Text(str(c.quantidade_estoque))),
                        ft.DataCell(ft.Text(str(c.deposito))),
                        ft.DataCell(ft.Text(str(c.estado))),
                        ft.DataCell(ft.Text(fornecedor_nome)),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Editar",
                                    on_click=partial(editar_epi, c.id)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Excluir",
                                    icon_color="red",
                                    on_click=lambda e, uid=c.id: excluir_epi(uid)
                                ),
                            ], tight=True)
                        )
                    ]
                )
            )
        db.close()
        page.update()

    def buscar(e):
        atualizar_tabela()
        page.update()

    botao_pesquisar = ft.ElevatedButton(text="Pesquisar", icon=ft.Icons.SEARCH, on_click=buscar)

    aba_pesquisa = ft.Column([
        ft.Text("Pesquisar EPI", size=20, weight="bold"),
        ft.Row([campo_busca, botao_pesquisar]),
        msg_pesquisa,
        tabela
    ], expand=True, scroll="auto")


    aba_cadastro = ft.Column([
        ft.Text("Cadastro de EPI", size=20, weight="bold"),
        descricao, tamanho, quantidade_estoque, deposito, estado, fornecedor_dropdown,
        ft.ElevatedButton(text="Salvar", on_click=salvar_epi),
        msg_cadastro
    ], expand=True, scroll="auto")

    atualizar_tabela()  # Preenche a tabela na inicialização

    return ft.Tabs(
        selected_index=0,
        expand=True,
        tabs=[
            ft.Tab(text="Cadastro", content=aba_cadastro),
            ft.Tab(text="Pesquisa", content=aba_pesquisa),
        ]
    )