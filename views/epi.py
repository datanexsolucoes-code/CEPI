import flet as ft
from functools import partial
from models.database import Uniforme, Fornecedor, db

lista_tamanho = ["P", "M", "G", "GG", "XG", "XGG", "XXG", "G1", "G2", "EGG", "Único"]
lista_deposito = ["Escritório", "Opala"]
lista_estado = ["Novo", "Semi novo", "Usado", "Obra"]


def view(page: ft.Page):
    page.scroll = "auto"

    # Campos de cadastro
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

    # ---- Carrega fornecedores no dropdown ----
    def carregar_fornecedores():
        try:
            db.connect(reuse_if_open=True)
            fornecedores = Fornecedor.select().order_by(Fornecedor.nome)
            fornecedor_dropdown.options = [
                ft.dropdown.Option(str(f.id), f.nome)
                for f in fornecedores
            ]
        except Exception as ex:
            msg_cadastro.value = f"Erro ao carregar fornecedores: {ex}"
            msg_cadastro.color = "red"
        finally:
            try:
                db.close()
            except:
                pass

    carregar_fornecedores()

    # ---- Salva uniforme ----
    def salvar_epi(e):
        try:
            db.connect(reuse_if_open=True)
            Uniforme.create(
                descricao=descricao.value.strip(),
                tamanho=tamanho.value,
                quantidade_estoque=int(quantidade_estoque.value or 0),
                deposito=deposito.value,
                estado=estado.value,
                fornecedor=int(fornecedor_dropdown.value) if fornecedor_dropdown.value else None
            )
            msg_cadastro.value = f"Uniforme '{descricao.value}' salvo com sucesso!"
            msg_cadastro.color = "green"

            # Limpa campos
            descricao.value = ""
            tamanho.value = None
            quantidade_estoque.value = ""
            deposito.value = None
            estado.value = None
            fornecedor_dropdown.value = None

        except Exception as ex:
            msg_cadastro.value = f"Erro ao salvar: {ex}"
            msg_cadastro.color = "red"
        finally:
            try:
                db.close()
            except:
                pass
            page.update()

    # ------------------ ABA DE PESQUISA ------------------
    campo_busca = ft.TextField(label="Buscar por descrição", expand=True)
    status_text = ft.Text(value="", color="blue")  # indica "Pesquisando..." e resultados
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

    # ---- Excluir EPI ----
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
            try:
                db.close()
            except:
                pass
            # atualiza a tabela após exclusão
            buscar(None)
            page.update()

    # ---- Editar EPI ----
    def editar_epi(uniforme_id, e):
        try:
            db.connect(reuse_if_open=True)
            uniforme = Uniforme.get_by_id(uniforme_id)
        finally:
            try:
                db.close()
            except:
                pass

        descricao_field = ft.TextField(label="Descrição", value=uniforme.descricao or "")
        tamanho_field = ft.TextField(label="Tamanho", value=uniforme.tamanho or "")
        quantidade_field = ft.TextField(label="Quantidade", value=str(uniforme.quantidade_estoque or 0))
        deposito_field = ft.TextField(label="Depósito", value=uniforme.deposito or "")
        estado_field = ft.TextField(label="Estado", value=uniforme.estado or "")

        # monta opções de fornecedores para o diálogo
        fornecedores = []
        try:
            db.connect(reuse_if_open=True)
            fornecedores = list(Fornecedor.select().order_by(Fornecedor.nome))
        finally:
            try:
                db.close()
            except:
                pass

        fornecedor_dropdown_edit = ft.Dropdown(
            label="Fornecedor",
            options=[ft.dropdown.Option(str(f.id), f.nome) for f in fornecedores],
            value=str(uniforme.fornecedor.id) if getattr(uniforme, "fornecedor", None) else None,
            width=300
        )

        def fechar_dialog(e=None):
            if page.dialog:
                page.dialog.open = False
                page.update()
                page.dialog = None

        def salvar_click(ev):
            try:
                db.connect(reuse_if_open=True)
                u = Uniforme.get_by_id(uniforme_id)
                u.descricao = descricao_field.value.strip()
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
                try:
                    db.close()
                except:
                    pass
                fechar_dialog()
                buscar(None)
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
                ft.TextButton("Cancelar", on_click=fechar_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = dialog
        page.dialog.open = True
        page.update()

    # ---- Buscar uniformes (consulta sob demanda) ----
    def buscar(e):
        # mostra status imediatamente
        status_text.value = "🔄 Pesquisando..."
        status_text.color = "blue"
        tabela.rows.clear()
        page.update()  # força render para exibir o status antes da query

        try:
            db.connect(reuse_if_open=True)
            filtro = campo_busca.value.strip()
            query = Uniforme.select().order_by(Uniforme.descricao)
            if filtro:
                query = query.where(Uniforme.descricao.contains(filtro))

            rows = []
            count = 0
            for c in query:
                count += 1
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
                                    ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar", on_click=partial(editar_epi, c.id)),
                                    ft.IconButton(icon=ft.Icons.DELETE, tooltip="Excluir", icon_color="red",
                                                  on_click=lambda e, uid=c.id: excluir_epi(uid))
                                ], tight=True)
                            )
                        ]
                    )
                )

            tabela.rows = rows
            if count == 0:
                status_text.value = "⚠️ Nenhum resultado encontrado."
                status_text.color = "orange"
            else:
                status_text.value = f"✅ {count} resultado(s) encontrado(s)."
                status_text.color = "green"

        except Exception as ex:
            status_text.value = f"❌ Erro ao buscar: {ex}"
            status_text.color = "red"
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
        ft.Container(content=status_text, padding=ft.padding.only(top=8, bottom=8)),
        tabela
    ], expand=True, scroll="auto")

    aba_cadastro = ft.Column([
        ft.Text("Cadastro de EPI", size=20, weight="bold"),
        descricao,
        ft.Row([tamanho, quantidade_estoque, deposito, estado], wrap=True, spacing=12),
        fornecedor_dropdown,
        ft.Row([ft.ElevatedButton(text="Salvar", on_click=salvar_epi), msg_cadastro]),
    ], expand=True, scroll="auto")

    # Começa com abas vazias (nenhuma consulta automática)
    tabela.rows = []
    page.update()

    return ft.Tabs(
        selected_index=0,
        expand=True,
        tabs=[
            ft.Tab(text="Cadastro", content=aba_cadastro),
            ft.Tab(text="Pesquisa", content=aba_pesquisa),
        ]
    )