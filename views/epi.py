import flet as ft
from models.database import Uniforme, Fornecedor, db

lista_tamanho = ["P", "M", "G", "GG", "XG", "XGG", "XXG", "G1", "G2", "EGG", "Único"]
lista_deposito = ["Escritório", "Opala"]
lista_estado = ["Novo", "Semi novo", "Usado", "Obra"]

# Controla se está em modo de edição
epi_editavel = {"id": None}


def view(page: ft.Page):
    page.scroll = "auto"

    # ---------- CAMPOS DE CADASTRO ----------
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
    fornecedor_dropdown = ft.Dropdown(label="Fornecedor", width=300, options=[])

    msg_cadastro = ft.Text(color="red")
    msg_pesquisa = ft.Text(color="red")

    # ---------- FUNÇÃO: Carregar fornecedores ----------
    def carregar_fornecedores():
        try:
            db.connect(reuse_if_open=True)
            fornecedores = Fornecedor.select().order_by(Fornecedor.nome)
            fornecedor_dropdown.options = [
                ft.dropdown.Option(str(f.id), f.nome) for f in fornecedores
            ]
        except Exception as ex:
            msg_cadastro.value = f"Erro ao carregar fornecedores: {ex}"
            msg_cadastro.color = "red"
        finally:
            db.close()

    carregar_fornecedores()

    # ---------- FUNÇÃO: Salvar ou Atualizar ----------
    def salvar_epi(e):
        try:
            db.connect(reuse_if_open=True)
            if epi_editavel["id"]:  # modo edição
                epi = Uniforme.get_by_id(epi_editavel["id"])
                epi.descricao = descricao.value.strip()
                epi.tamanho = tamanho.value
                epi.quantidade_estoque = int(quantidade_estoque.value or 0)
                epi.deposito = deposito.value
                epi.estado = estado.value
                epi.fornecedor = (
                    Fornecedor.get_by_id(int(fornecedor_dropdown.value))
                    if fornecedor_dropdown.value
                    else None
                )
                epi.save()
                msg_cadastro.value = f"EPI '{descricao.value}' atualizado com sucesso!"
                msg_cadastro.color = "green"
            else:  # novo cadastro
                Uniforme.create(
                    descricao=descricao.value.strip(),
                    tamanho=tamanho.value,
                    quantidade_estoque=int(quantidade_estoque.value or 0),
                    deposito=deposito.value,
                    estado=estado.value,
                    fornecedor=int(fornecedor_dropdown.value)
                    if fornecedor_dropdown.value
                    else None,
                )
                msg_cadastro.value = f"EPI '{descricao.value}' salvo com sucesso!"
                msg_cadastro.color = "green"

            # Limpa campos e reseta modo edição
            descricao.value = ""
            tamanho.value = None
            quantidade_estoque.value = ""
            deposito.value = None
            estado.value = None
            fornecedor_dropdown.value = None
            epi_editavel["id"] = None

        except Exception as ex:
            msg_cadastro.value = f"Erro ao salvar: {ex}"
            msg_cadastro.color = "red"
        finally:
            db.close()
            buscar(None)
            page.update()

    # ---------- FUNÇÃO: Excluir ----------
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
            buscar(None)
            page.update()

    # ---------- FUNÇÃO: Editar ----------
    def editar_epi(uniforme_id):
        try:
            db.connect(reuse_if_open=True)
            epi = Uniforme.get_by_id(uniforme_id)
            descricao.value = epi.descricao
            tamanho.value = epi.tamanho
            quantidade_estoque.value = str(epi.quantidade_estoque or 0)
            deposito.value = epi.deposito
            estado.value = epi.estado
            fornecedor_dropdown.value = (
                str(epi.fornecedor.id)
                if getattr(epi, "fornecedor", None)
                else None
            )
            epi_editavel["id"] = epi.id
            msg_cadastro.value = f"Editando EPI '{epi.descricao}'"
            msg_cadastro.color = "blue"

            # Muda automaticamente para aba de cadastro
            tabs.selected_index = 0
            page.update()

        except Exception as ex:
            msg_pesquisa.value = f"Erro ao carregar EPI: {ex}"
            msg_pesquisa.color = "red"
            page.update()
        finally:
            db.close()

    # ---------- FUNÇÃO: Buscar ----------
    campo_busca = ft.TextField(label="Buscar por descrição", expand=True)
    status_text = ft.Text(value="", color="blue")
    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Descrição")),
            ft.DataColumn(ft.Text("Tamanho")),
            ft.DataColumn(ft.Text("Estoque")),
            ft.DataColumn(ft.Text("Depósito")),
            ft.DataColumn(ft.Text("Estado")),
            ft.DataColumn(ft.Text("Fornecedor")),
            ft.DataColumn(ft.Text("Ações")),
        ],
        rows=[],
    )

    def buscar(e):
        status_text.value = "🔄 Pesquisando..."
        status_text.color = "blue"
        tabela.rows.clear()
        page.update()

        try:
            db.connect(reuse_if_open=True)
            filtro = campo_busca.value.strip()
            query = Uniforme.select().order_by(Uniforme.descricao)
            if filtro:
                query = query.where(Uniforme.descricao.contains(filtro))

            rows = []
            for c in query:
                fornecedor_nome = getattr(c.fornecedor, "nome", "") if getattr(c, "fornecedor", None) else ""
                rows.append(
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
                                    ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar", icon_color="blue",
                                                  on_click=lambda e, uid=c.id: editar_epi(uid)),
                                    ft.IconButton(icon=ft.Icons.DELETE, tooltip="Excluir", icon_color="red",
                                                  on_click=lambda e, uid=c.id: excluir_epi(uid))
                                ], tight=True)
                            )
                        ]
                    )
                )

            tabela.rows = rows
            status_text.value = f"✅ {len(rows)} resultado(s) encontrado(s)." if rows else "⚠️ Nenhum resultado encontrado."
            status_text.color = "green" if rows else "orange"

        except Exception as ex:
            status_text.value = f"❌ Erro ao buscar: {ex}"
            status_text.color = "red"
        finally:
            db.close()
            page.update()

    # ---------- LAYOUT ----------
    botao_pesquisar = ft.ElevatedButton(text="Pesquisar", icon=ft.Icons.SEARCH, on_click=buscar)

    aba_pesquisa = ft.Column([
        ft.Text("Pesquisar EPI", size=20, weight="bold"),
        ft.Row([campo_busca, botao_pesquisar]),
        ft.Container(content=status_text, padding=ft.padding.only(top=8, bottom=8)),
        msg_pesquisa,
        tabela
    ], expand=True, scroll="auto")

    aba_cadastro = ft.Column([
        ft.Text("Cadastro de EPI", size=20, weight="bold"),
        descricao,
        ft.Row([tamanho, quantidade_estoque, deposito, estado], wrap=True, spacing=12),
        fornecedor_dropdown,
        ft.Row([ft.ElevatedButton(text="Salvar", on_click=salvar_epi), msg_cadastro]),
    ], expand=True, scroll="auto")

    # Tabs principal
    global tabs
    tabs = ft.Tabs(
        selected_index=0,
        expand=True,
        tabs=[
            ft.Tab(text="Cadastro", content=aba_cadastro),
            ft.Tab(text="Pesquisa", content=aba_pesquisa),
        ]
    )

    return tabs