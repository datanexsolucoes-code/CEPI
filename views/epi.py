import flet as ft
from models.database import Uniforme, db

lista_tamanho = ["P", "M", "G", "GG", "XG", "XGG", "XXG", "G1", "G2", "EGG", "Único"]
lista_deposito = ["Escritório", "Opala"]
lista_estado = ["Novo", "Semi novo", "Usado", "Obra"]

# Definição da ordem personalizada dos tamanhos
ORDEM_TAMANHOS = {
    "P": 1,
    "M": 2,
    "G": 3,
    "GG": 4,
    "XG": 5,
    "XGG": 6,
    "XXG": 7,
    "G1": 8,
    "G2": 9,
    "EGG": 10,
    "Único": 11
}

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
                # Encontra o próximo ID disponível (considerando possíveis gaps)
                proximo_id = 1
                ids_existentes = [u.id for u in Uniforme.select(Uniforme.id).order_by(Uniforme.id)]

                if ids_existentes:
                    # Procura o primeiro gap na sequência
                    for i in range(1, max(ids_existentes) + 2):
                        if i not in ids_existentes:
                            proximo_id = i
                            break

                # Cria o novo registro
                Uniforme.create(
                    id=proximo_id,
                    descricao=descricao.value.strip(),
                    tamanho=tamanho.value,
                    quantidade_estoque=int(quantidade_estoque.value or 0),
                    deposito=deposito.value,
                    estado=estado.value,
                )
                msg_cadastro.value = f"EPI '{descricao.value}' salvo com sucesso! (ID: {proximo_id})"
                msg_cadastro.color = "green"

            # Limpa campos e reseta modo edição
            descricao.value = ""
            tamanho.value = None
            quantidade_estoque.value = ""
            deposito.value = None
            estado.value = None
            epi_editavel["id"] = None

            # Atualiza os dropdowns de busca com os novos dados
            carregar_opcoes_busca()

        except Exception as ex:
            msg_cadastro.value = f"Erro ao salvar: {ex}"
            msg_cadastro.color = "red"
            print(f"Erro detalhado: {ex}")

        finally:
            db.close()
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

            # Atualiza os dropdowns de busca após exclusão
            carregar_opcoes_busca()

        except Exception as ex:
            msg_pesquisa.value = f"Erro ao excluir: {ex}"
            msg_pesquisa.color = "red"
        finally:
            db.close()
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

    # ---------- CAMPOS DE BUSCA COM DROPDOWNS ----------
    # Dropdown para descrição
    descricao_busca = ft.Dropdown(
        label="Descrição",
        hint_text="Selecione uma descrição",
        width=250,
        options=[ft.dropdown.Option("todos", "Todos")],
        value="todos"
    )

    # Dropdown para depósito
    deposito_busca = ft.Dropdown(
        label="Depósito",
        hint_text="Selecione um depósito",
        width=200,
        options=[ft.dropdown.Option("todos", "Todos")],
        value="todos"
    )

    # Dropdown para tamanho
    tamanho_busca = ft.Dropdown(
        label="Tamanho",
        hint_text="Selecione um tamanho",
        width=150,
        options=[ft.dropdown.Option("todos", "Todos")],
        value="todos"
    )

    # Botões de ação
    botao_pesquisar = ft.ElevatedButton(
        text="Pesquisar",
        icon=ft.Icons.SEARCH,
        on_click=lambda e: buscar(e)
    )

    botao_limpar = ft.OutlinedButton(
        text="Limpar Filtros",
        icon=ft.Icons.CLEAR,
        on_click=lambda e: limpar_filtros(e)
    )

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

    def carregar_opcoes_busca():
        """Carrega as opções únicas para os dropdowns de busca (sem fazer consulta na tabela)"""
        try:
            db.connect(reuse_if_open=True)

            # Carregar descrições únicas
            descricoes = Uniforme.select(Uniforme.descricao).distinct().order_by(Uniforme.descricao)
            descricao_busca.options = [ft.dropdown.Option("todos", "Todos")]
            for c in descricoes:
                descricao_busca.options.append(ft.dropdown.Option(c.descricao, c.descricao))
            descricao_busca.value = "todos"

            # Carregar depósitos únicos
            depositos = Uniforme.select(Uniforme.deposito).distinct().order_by(Uniforme.deposito)
            deposito_busca.options = [ft.dropdown.Option("todos", "Todos")]
            for d in depositos:
                if d.deposito:
                    deposito_busca.options.append(ft.dropdown.Option(d.deposito, d.deposito))
            deposito_busca.value = "todos"

            # Carregar tamanhos únicos com ordenação personalizada
            tamanhos = Uniforme.select(Uniforme.tamanho).distinct()

            # Ordenar os tamanhos de acordo com a ordem definida
            tamanhos_lista = []
            for t in tamanhos:
                if t.tamanho:
                    tamanhos_lista.append(t.tamanho)

            # Remover duplicatas e ordenar pela ordem definida
            tamanhos_unicos = list(dict.fromkeys(tamanhos_lista))
            tamanhos_ordenados = sorted(
                tamanhos_unicos,
                key=lambda x: ORDEM_TAMANHOS.get(x, 999)
            )

            tamanho_busca.options = [ft.dropdown.Option("todos", "Todos")]
            for t in tamanhos_ordenados:
                tamanho_busca.options.append(ft.dropdown.Option(t, t))
            tamanho_busca.value = "todos"

        except Exception as ex:
            print(f"Erro ao carregar opções de busca: {ex}")
        finally:
            db.close()

    def limpar_filtros(e):
        """Limpa todos os filtros e limpa a tabela"""
        descricao_busca.value = "todos"
        deposito_busca.value = "todos"
        tamanho_busca.value = "todos"

        # Limpa a tabela e a mensagem de status
        tabela.rows.clear()
        status_text.value = "✅ Filtros limpos. Selecione os filtros e clique em Pesquisar."
        status_text.color = "green"
        page.update()

    def buscar(e):
        """Função de busca com múltiplos filtros em dropdowns"""
        status_text.value = "🔄 Pesquisando..."
        status_text.color = "blue"
        tabela.rows.clear()
        page.update()

        try:
            db.connect(reuse_if_open=True)

            # Construir query base
            query = Uniforme.select().order_by(Uniforme.descricao)

            # Controle para verificar se algum filtro foi selecionado
            filtros_aplicados = False

            # Aplicar filtros
            if descricao_busca.value and descricao_busca.value != "todos":
                query = query.where(Uniforme.descricao == descricao_busca.value)
                filtros_aplicados = True

            if deposito_busca.value and deposito_busca.value != "todos":
                query = query.where(Uniforme.deposito == deposito_busca.value)
                filtros_aplicados = True

            if tamanho_busca.value and tamanho_busca.value != "todos":
                query = query.where(Uniforme.tamanho == tamanho_busca.value)
                filtros_aplicados = True

            # Se nenhum filtro foi selecionado, mostrar mensagem e não fazer consulta
            if not filtros_aplicados:
                status_text.value = "ℹ️ Selecione pelo menos um filtro para pesquisar."
                status_text.color = "orange"
                tabela.rows.clear()
                page.update()
                return

            # Executar query
            resultados = list(query.execute())

            # Ordenar os resultados pelo tamanho (ordem personalizada)
            resultados.sort(key=lambda x: ORDEM_TAMANHOS.get(x.tamanho, 999))

            # Construir as linhas da tabela
            rows = []
            for c in resultados:
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(c.descricao)),
                            ft.DataCell(ft.Text(c.tamanho or "-")),
                            ft.DataCell(ft.Text(str(c.quantidade_estoque))),
                            ft.DataCell(ft.Text(c.deposito or "-")),
                            ft.DataCell(ft.Text(c.estado or "-")),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        tooltip="Editar",
                                        icon_color="blue",
                                        on_click=lambda e, uid=c.id: editar_epi(uid)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        tooltip="Excluir",
                                        icon_color="red",
                                        on_click=lambda e, uid=c.id: excluir_epi(uid)
                                    )
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
            print(f"Erro detalhado: {ex}")
        finally:
            db.close()
            page.update()

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
        )

        # Ordenar tamanhos pela ordem personalizada
        tamanhos_lista = [t.tamanho for t in tamanhos if t.tamanho]
        tamanhos_ordenados = sorted(
            tamanhos_lista,
            key=lambda x: ORDEM_TAMANHOS.get(x, 999)
        )

        dd_tamanho.options = [
            ft.dropdown.Option(t) for t in tamanhos_ordenados
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

            # Atualiza os dropdowns de busca após transferência
            carregar_opcoes_busca()

        except Exception as ex:
            msg_transferencia.value = f"❌ {ex}"
            msg_transferencia.color = "red"

        finally:
            db.close()
            page.update()

    dd_descricao.on_change = carregar_tamanhos
    dd_tamanho.on_change = carregar_estados

    # ---------- LAYOUT ----------

    # Layout da aba de pesquisa com os novos filtros e tabela vazia inicialmente
    aba_pesquisa = ft.Column([
        ft.Text("Pesquisar EPI", size=20, weight="bold"),
        ft.Text("Selecione os filtros desejados e clique em Pesquisar", size=12, color="gray"),
        ft.Row([
            descricao_busca,
            deposito_busca,
            tamanho_busca,
            botao_pesquisar,
            botao_limpar
        ], wrap=True, spacing=10),
        ft.Container(content=status_text, padding=ft.padding.only(top=8, bottom=8)),
        msg_pesquisa,
        ft.Container(
            content=tabela,
            padding=ft.padding.only(top=10)
        )
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

    # Carregar apenas as opções dos dropdowns, mas NÃO fazer consulta inicial
    carregar_descricoes()
    carregar_opcoes_busca()

    # Deixar a tabela vazia com uma mensagem inicial
    status_text.value = "ℹ️ Selecione os filtros desejados e clique em Pesquisar"
    status_text.color = "blue"
    tabela.rows = []

    return tabs