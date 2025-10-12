import flet as ft
from models.database import Funcionario, db

pessoa_editavel = {"cpf": None}

def view(page: ft.Page):
    page.scroll = "auto"
    # FORMULÁRIO DE CADASTRO
    cpf = ft.TextField(label="CPF")
    nome = ft.TextField(label="Nome")
    telefone = ft.TextField(label="Telefone")
    endereco = ft.TextField(label="Endereço")
    tamanho = ft.TextField(label="Tamanho")
    prazo = ft.TextField(label="Prazo de troca")
    msg_cadastro = ft.Text(color="red")
    msg_pesquisa = ft.Text(color="red")

    def salva_funcionario(e):
        try:
            db.connect(reuse_if_open=True)
            if pessoa_editavel["cpf"]:  # Modo edição
                funcionario = Funcionario.get(Funcionario.cpf == pessoa_editavel["cpf"])
                funcionario.nome = nome.value
                funcionario.telefone = int(telefone.value)
                funcionario.endereco = endereco.value
                funcionario.tamanho = tamanho.value
                funcionario.prazo = prazo.value
                funcionario.save()
                msg_cadastro.value = f"Funcionario {funcionario.nome} atualizado com sucesso!"
            else:
                Funcionario.create(
                    cpf=cpf.value,
                    nome=nome.value,
                    telefone=int(telefone.value),
                    endereco=endereco.value,
                    tamanho=tamanho.value,
                    prazo_troca_meses=prazo.value
                )
                msg_cadastro.value = f"Funcionario {nome.value} salvo com sucesso!"
            msg_cadastro.color = "green"
            cpf.value = nome.value = telefone.value = endereco.value = tamanho.value = prazo.value = ""
            pessoa_editavel["cpf"] = None
        except Exception as ex:
            msg_cadastro.value = f"Erro ao salvar/atualizar: {ex}"
            msg_cadastro.color = "red"
        finally:
            db.close()
            atualizar_tabela()
            page.update()

    # ------------------ ABA DE PESQUISA ------------------
    campo_busca = ft.TextField(label="Buscar por nome ou CPF", expand=True)
    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text("CPF")),
            ft.DataColumn(label=ft.Text("Nome")),
            ft.DataColumn(label=ft.Text("Telefone")),
            ft.DataColumn(label=ft.Text("Endereço")),
            ft.DataColumn(label=ft.Text("Tamanho")),
            ft.DataColumn(label=ft.Text("Ações")),
        ],
        rows=[]
    )

    def excluir_funcionario(cpf_funcionario):
        try:
            db.connect(reuse_if_open=True)
            funcionario = Funcionario.get(Funcionario.cpf == cpf_funcionario)
            funcionario.delete_instance()
            msg_pesquisa.value = f"Funcionário {funcionario.nome} excluído com sucesso!"
            msg_pesquisa.color = "green"
        except Exception as ex:
            msg_pesquisa.value = f"Erro ao excluir: {ex}"
            msg_pesquisa.color = "red"
        finally:
            db.close()
            atualizar_tabela()
            page.update()

    def editar_funcionario(cpf_cliente):
        try:
            db.connect(reuse_if_open=True)
            funcionario = Funcionario.get(Funcionario.cpf == cpf_cliente)
            cpf.value = funcionario.cpf
            nome.value = funcionario.nome
            telefone.value = str(funcionario.telefone)
            endereco.value = funcionario.endereco
            tamanho.value = funcionario.tamanho
            prazo.value = funcionario.prazo
            pessoa_editavel["cpf"] = funcionario.cpf
            msg_cadastro.value = f"Editando funcionario {funcionario.nome}"
            msg_cadastro.color = "blue"
            page.update()
        except Exception as ex:
            msg_pesquisa.value = f"Erro ao carregar cliente: {ex}"
            msg_pesquisa.color = "red"
            page.update()
        finally:
            db.close()

    def atualizar_tabela():
        db.connect(reuse_if_open=True)
        filtro = campo_busca.value.strip()
        if filtro:
            query = Funcionario.select().where(
                (Funcionario.nome.contains(filtro)) | (Funcionario.cpf.contains(filtro))
            )
        else:
            query = Funcionario.select()
        tabela.rows = []
        for c in query:
            tabela.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(c.cpf)),
                        ft.DataCell(ft.Text(c.nome)),
                        ft.DataCell(ft.Text(str(c.telefone))),
                        ft.DataCell(ft.Text(str(c.endereco))),
                        ft.DataCell(ft.Text(str(c.tamanho))),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Editar",
                                    icon_color="blue",
                                    on_click=lambda e, cpf=c.cpf: editar_funcionario(cpf)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Excluir",
                                    icon_color="red",
                                    on_click=lambda e, cpf=c.cpf: excluir_funcionario(cpf)),
                            ])
                        )
                    ]
                )
            )
        db.close()

    def buscar(e):
        atualizar_tabela()
        page.update()

    botao_pesquisar = ft.ElevatedButton(text="Pesquisar", icon=ft.Icons.SEARCH, on_click=buscar)

    aba_pesquisa = ft.Column([
        ft.Text("Pesquisar Funcionário", size=20, weight="bold"),
        ft.Row([campo_busca, botao_pesquisar]),
        msg_pesquisa,
        tabela
    ], expand=True, scroll="auto")

    # ------------------------------------------------------

    aba_cadastro = ft.Column([
        ft.Text("Cadastro de Funcionário", size=20, weight="bold"),
        cpf, nome, telefone, endereco, tamanho,
        ft.ElevatedButton(text="Salvar", on_click=salva_funcionario),
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