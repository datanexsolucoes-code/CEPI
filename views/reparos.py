import flet as ft
from functools import partial
from models.database import Uniforme, Fornecedor, db

lista_tamanho = ["P", "M", "G", "GG", "XG", "XGG", "XXG", "G1", "G2", "EGG", "Único"]
lista_deposito = ["Escritório", "Opala"]
lista_estado = ["Novo", "Semi novo", "Usado", "Obra"]


def view(page: ft.Page):
    page.scroll = "auto"
    descricao = ft.TextField(label="Descrição", width=500)
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
    fornecedor_dropdown = ft.Dropdown(label="Fornecedor", width=200, options=[])
    msg_cadastro = ft.Text(color="red")
    msg_pesquisa = ft.Text(color="red")

    # ---- Carrega fornecedores no dropdown ----
    def carregar_fornecedores():
        db.connect(reuse_if_open=True)
        fornecedores = Fornecedor.select()
        fornecedor_dropdown.options = [
            ft.dropdown.Option(str(f.id), f.nome)
            for f in fornecedores
        ]
        db.close()

    carregar_fornecedores()

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
                fornecedor=int(fornecedor_dropdown.value)
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
            page.update()

    # ------------------ ABA DE PESQUISA ------------------
    campo_busca = ft.TextField(label="Buscar por descrição", expand=True)
    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text("Descrição")),
            ft.DataColumn(label=ft.Text("Tamanho")),
            ft.DataColumn(label=ft.Text("Estoque")),
            ft.DataColumn(label=ft.Text("Depósito")),
            ft.DataColumn(label=ft.Text("Estado")),
            ft.DataColumn(label=ft.Text("Fornecedor")),
            ft.DataColumn(label=ft.Text("Ações")),
        ],
        rows=[]
    )

    def excluir_epi(uniforme_id):
        try:
            db.connect(reuse_if_open=True)
            epi = Uniforme.get_by_id(uniforme_id)
            desc = getattr(epi, "descricao", str(uniforme_id))
            epi.delete_instance()
            msg_pesquisa.value = f"EPI '{desc}' excluído com sucesso!"
            msg_pesquisa.color = "green"
        except Exception as ex:
            msg_pesquisa.value = f"Erro ao excluir: {ex}"
            msg_pesquisa.color = "red"
        finally:
            db.close()
            page.update()

    # Editar uniforme
    def editar_epi(uniforme_id, e):
        try:
            db.connect(reuse_if_open=True)
            uniforme = Uniforme.get_by_id(uniforme_id)
        finally:
            db.close()

        descricao_field = ft.TextField(label="Descrição", value=uniforme.descricao or "")
        tamanho_field = ft.TextField(label="Tamanho", value=uniforme.tamanho or "")
        quantidade_field = ft.TextField(label="Quantidade", value=str(uniforme.quantidade_estoque or 0))
        deposito_field = ft.TextField(label="Depósito", value=uniforme.deposito or "")
        estado_field = ft.TextField(label="Estado", value=uniforme.estado or "")

        fornecedores = Fornecedor.select()
        options = [ft.dropdown.Option(str(f.id), f.nome) for f in fornecedores]
        fornecedor_value = str(uniforme.fornecedor.id) if getattr(uniforme, "fornecedor", None) else None
        fornecedor_dropdown_edit = ft.Dropdown(label="Fornecedor", options=options, value=fornecedor_value, width=300)

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
                u.quantidade_estoque = int(quantidade_field.value or 0)
                u.deposito = deposito_field.value
                u.estado = estado_field.value
                if fornecedor_dropdown_edit.value:
                    u.fornecedor = Fornecedor.get_by_id(int(fornecedor_dropdown_edit.value))
                u.save()
                msg_pesquisa.value = "EPI atualizado com sucesso!"
                msg_pesquisa.color = "green"
            except Exception as ex:
                msg_pesquisa.value = f"Erro ao salvar: {ex}"
                msg_pesquisa.color = "red"
            finally:
                db.close()
                fechar_dialog()
                page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Editar Uniforme"),
            content=ft.Column([
                descricao_field,
                tamanho_field,
                quantidade_field,
                deposito_field,
                estado_field,
                fornecedor_dropdown_edit
            ], tight=True),
            actions=[
                ft.ElevatedButton("Salvar", on_click=salvar_click),
                ft.TextButton("Cancelar", on_click=lambda e: fechar_dialog())
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = dialog
        page.dialog.open = True
        page.update()

    # ---- Buscar uniformes (consulta apenas sob demanda) ----
    def buscar(e):
        msg_pesquisa.value = "🔄 Pesquisando..."
        msg_pesquisa.color = "blue"
        page.update()

        try:
            db.connect(reuse_if_open=True)
            filtro = campo_busca.value.strip()
            query = Uniforme.select()
            if filtro:
                query = query.where(Uniforme.descricao.contains(filtro))

            tabela.rows.clear()
            for c in query:
                fornecedor_nome = getattr(c.fornecedor, "nome", "") if getattr(c, "fornecedor", None) else ""
                tabela.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(c.descricao)),
                            ft.DataCell(ft.Text(c.tamanho)),
                            ft.DataCell(ft.Text(str(c.quantidade_estoque))),
                            ft.DataCell(ft.Text(c.deposito)),
                            ft.DataCell(ft.Text(c.estado)),
                            ft.DataCell(ft.Text(fornecedor_nome)),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar",
                                                  on_click=partial(editar_epi, c.id)),
                                    ft.IconButton(icon=ft.Icons.DELETE, tooltip="Excluir", icon_color="red",
                                                  on_click=lambda e, uid=c.id: excluir_epi(uid))
                                ], tight=True)
                            )
                        ]
                    )
                )

            msg_pesquisa.value = "✅ Pesquisa concluída!"
            msg_pesquisa.color = "green"

        except Exception as ex:
            msg_pesquisa.value = f"Erro ao buscar: {ex}"
            msg_pesquisa.color = "red"

        finally:
            try:
                db.close()
            except:
                pass
            page.update()

    # --- Layout das abas ---
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

    return ft.Tabs(
        selected_index=0,
        expand=True,
        tabs=[
            ft.Tab(text="Cadastro", content=aba_cadastro),
            ft.Tab(text="Pesquisa", content=aba_pesquisa),
        ]
    )