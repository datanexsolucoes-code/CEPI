import flet as ft
from models.database import Uniforme, db

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

    msg_cadastro = ft.Text(color="red")
    msg_pesquisa = ft.Text(color="red")

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
                )
                msg_cadastro.value = f"EPI '{descricao.value}' salvo com sucesso!"
                msg_cadastro.color = "green"

            # Limpa campos e reseta modo edição
            descricao.value = ""
            tamanho.value = None
            quantidade_estoque.value = ""
            deposito.value = None
            estado.value = None
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
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(c.descricao)),
                            ft.DataCell(ft.Text(c.tamanho)),
                            ft.DataCell(ft.Text(str(c.quantidade_estoque))),
                            ft.DataCell(ft.Text(str(c.deposito))),
                            ft.DataCell(ft.Text(str(c.estado))),
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

    # ---------- ABA: TRANSFERÊNCIA ----------
    # ---------- ABA: TRANSFERÊNCIA ----------

    dd_descricao = ft.Dropdown(
        label="Uniforme",
        width=400
    )

    dd_tamanho = ft.Dropdown(
        label="Tamanho",
        width=150
    )

    dd_estado = ft.Dropdown(
        label="Estado",
        width=150
    )

    deposito_origem = ft.Dropdown(
        label="Depósito Origem",
        options=[ft.dropdown.Option(v) for v in lista_deposito],
        width=200
    )

    deposito_destino = ft.Dropdown(
        label="Depósito Destino",
        options=[ft.dropdown.Option(v) for v in lista_deposito],
        width=200
    )

    qtd_transferir = ft.TextField(
        label="Quantidade",
        width=120,
        keyboard_type=ft.KeyboardType.NUMBER
    )

    msg_transferencia = ft.Text()

    def carregar_descricoes():
        db.connect(reuse_if_open=True)
        descricoes = (
            Uniforme
            .select(Uniforme.descricao)
            .distinct()
            .order_by(Uniforme.descricao)
        )
        dd_descricao.options = [
            ft.dropdown.Option(d.descricao) for d in descricoes
        ]
        dd_descricao.value = None
        dd_tamanho.options = []
        dd_estado.options = []
        db.close()

    def carregar_tamanhos(e=None):
        if not dd_descricao.value:
            return

        db.connect(reuse_if_open=True)
        tamanhos = (
            Uniforme
            .select(Uniforme.tamanho)
            .where(Uniforme.descricao == dd_descricao.value)
            .distinct()
            .order_by(Uniforme.tamanho)
        )

        dd_tamanho.options = [
            ft.dropdown.Option(t.tamanho) for t in tamanhos
        ]
        dd_tamanho.value = None
        dd_estado.options = []
        db.close()
        page.update()

    def carregar_estados(e=None):
        if not dd_descricao.value or not dd_tamanho.value:
            return

        db.connect(reuse_if_open=True)
        estados = (
            Uniforme
            .select(Uniforme.estado)
            .where(
                (Uniforme.descricao == dd_descricao.value) &
                (Uniforme.tamanho == dd_tamanho.value)
            )
            .distinct()
            .order_by(Uniforme.estado)
        )

        dd_estado.options = [
            ft.dropdown.Option(s.estado) for s in estados
        ]
        dd_estado.value = None
        db.close()
        page.update()

    def transferir_uniforme(e):
        try:
            db.connect(reuse_if_open=True)

            if not all([
                dd_descricao.value,
                dd_tamanho.value,
                dd_estado.value,
                deposito_origem.value,
                deposito_destino.value,
                qtd_transferir.value
            ]):
                raise Exception("Preencha todos os campos.")

            if deposito_origem.value == deposito_destino.value:
                raise Exception("Depósito origem e destino não podem ser iguais.")

            qtd = int(qtd_transferir.value)

            epi_origem = Uniforme.get(
                Uniforme.descricao == dd_descricao.value,
                Uniforme.tamanho == dd_tamanho.value,
                Uniforme.estado == dd_estado.value,
                Uniforme.deposito == deposito_origem.value
            )

            if epi_origem.quantidade_estoque < qtd:
                raise Exception("Quantidade maior que o estoque disponível.")

            # ↓ diminui origem
            epi_origem.quantidade_estoque -= qtd
            epi_origem.save()

            # ↑ soma destino
            epi_destino, created = Uniforme.get_or_create(
                descricao=epi_origem.descricao,
                tamanho=epi_origem.tamanho,
                estado=epi_origem.estado,
                deposito=deposito_destino.value,
                defaults={"quantidade_estoque": 0}
            )

            epi_destino.quantidade_estoque += qtd
            epi_destino.save()

            msg_transferencia.value = "✅ Transferência realizada com sucesso!"
            msg_transferencia.color = "green"

            buscar(None)  # atualiza aba pesquisa

        except Exception as ex:
            msg_transferencia.value = f"❌ {ex}"
            msg_transferencia.color = "red"

        finally:
            db.close()
            page.update()

    dd_descricao.on_change = carregar_tamanhos
    dd_tamanho.on_change = carregar_estados

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
        ft.Row([ft.ElevatedButton(text="Salvar", on_click=salvar_epi), msg_cadastro]),
    ], expand=True, scroll="auto")

    aba_transferencia = ft.Column(
        [
            ft.Text("Transferência de Uniforme", size=20, weight="bold"),
            dd_descricao,
            ft.Row([dd_tamanho, dd_estado], spacing=12),
            ft.Row([deposito_origem, deposito_destino], spacing=12),
            qtd_transferir,
            ft.ElevatedButton(
                "Transferir",
                icon=ft.Icons.SWAP_HORIZ,
                on_click=transferir_uniforme
            ),
            msg_transferencia
        ],
        expand=True,
        scroll="auto"
    )

    # Tabs principal
    tabs = ft.Tabs(
        selected_index=0,
        expand=True,
        tabs=[
            ft.Tab(text="Cadastro", content=aba_cadastro),
            ft.Tab(text="Pesquisa", content=aba_pesquisa),
            ft.Tab(text="Transferência", content=aba_transferencia),
        ]
    )

    carregar_descricoes()

    return tabs