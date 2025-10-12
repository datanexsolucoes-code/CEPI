import flet as ft
from models.database import Fornecedor, db

empresa_editavel = {"cpf_cnpj": None}

def view(page: ft.Page):
    page.scroll = "auto"
    nome = ft.TextField(label="Nome")
    cpf_cnpj = ft.TextField(label="CPF/CNPJ")
    telefone = ft.TextField(label="Telefone")
    endereco = ft.TextField(label="Endereço")
    email = ft.TextField(label="Email")
    chave_pg = ft.TextField(label="Chave de Pagamento")
    msg_cadastro = ft.Text(color="red")
    msg_pesquisa = ft.Text(color="red")

    def salvar_fornecedor(e):
        try:
            db.connect(reuse_if_open=True)
            if empresa_editavel["cpf_cnpj"]:  # Modo edição
                fornecedor = Fornecedor.get(Fornecedor.cpf_cnpj == empresa_editavel["cpf"])
                fornecedor.nome = nome.value
                fornecedor.cpf_cnpj = cpf_cnpj.value
                fornecedor.telefone = int(telefone.value)
                fornecedor.endereco = endereco.value
                fornecedor.email = email.value
                fornecedor.chave_pg = chave_pg.value
                fornecedor.save()
                msg_cadastro.value = f"Fornecedor {fornecedor.nome} atualizado com sucesso!"
            else:
                Fornecedor.create(
                    nome=nome.value,
                    cpf_cnpj=cpf_cnpj.value,
                    telefone=int(telefone.value),
                    endereco=endereco.value,
                    email=email.value,
                    chave_pg=chave_pg.value
                )
                msg_cadastro.value = f"Fornecedor {nome.value} salvo com sucesso!"
            msg_cadastro.color = "green"
            cpf_cnpj.value = nome.value = cpf_cnpj.value = telefone.value = endereco.value = email.value = chave_pg.value = ""
            empresa_editavel["cpf"] = None
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
            ft.DataColumn(label=ft.Text("Nome")),
            ft.DataColumn(label=ft.Text("CPF")),
            ft.DataColumn(label=ft.Text("Telefone")),
            ft.DataColumn(label=ft.Text("Endereço")),
            ft.DataColumn(label=ft.Text("Email")),
            ft.DataColumn(label=ft.Text("Chave de Pagamento")),
            ft.DataColumn(label=ft.Text("Ações")),
        ],
        rows=[]
    )

    def excluir_fornecedor(cpf_fornecedor):
        try:
            db.connect(reuse_if_open=True)
            fornecedor = Fornecedor.get(Fornecedor.cpf_cnpj == cpf_fornecedor)
            fornecedor.delete_instance()
            msg_pesquisa.value = f"Fornecedor {fornecedor.nome} excluído com sucesso!"
            msg_pesquisa.color = "green"
        except Exception as ex:
            msg_pesquisa.value = f"Erro ao excluir: {ex}"
            msg_pesquisa.color = "red"
        finally:
            db.close()
            atualizar_tabela()
            page.update()

    def editar_fornecedor(cpf_fornecedor):
        try:
            db.connect(reuse_if_open=True)
            fornecedor = Fornecedor.get(Fornecedor.cpf_cnpj == cpf_fornecedor)
            nome.value = fornecedor.nome
            cpf_cnpj.value = fornecedor.cpf_cnpj
            telefone.value = str(fornecedor.telefone)
            endereco.value = fornecedor.endereco
            email.value = fornecedor.email
            chave_pg.value = fornecedor.chave_pg
            empresa_editavel["cpf/cnpj"] = fornecedor.cpf_cnpj
            msg_cadastro.value = f"Editando fornecedor {fornecedor.nome}"
            msg_cadastro.color = "blue"
            page.update()
        except Exception as ex:
            msg_pesquisa.value = f"Erro ao carregar fornecedor: {ex}"
            msg_pesquisa.color = "red"
            page.update()
        finally:
            db.close()

    def atualizar_tabela():
        db.connect(reuse_if_open=True)
        filtro = campo_busca.value.strip()
        if filtro:
            query = Fornecedor.select().where(
                (Fornecedor.nome.contains(filtro)) | (Fornecedor.cpf_cnpj.contains(filtro))
            )
        else:
            query = Fornecedor.select()
        tabela.rows = []
        for c in query:
            tabela.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(c.nome)),
                        ft.DataCell(ft.Text(c.cpf_cnpj)),
                        ft.DataCell(ft.Text(str(c.telefone))),
                        ft.DataCell(ft.Text(str(c.endereco))),
                        ft.DataCell(ft.Text(str(c.email))),
                        ft.DataCell(ft.Text(str(c.chave_pg))),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Editar",
                                    icon_color="blue",
                                    on_click=lambda e, cpf_cnpj=c.cpf_cnpj: editar_fornecedor(cpf_cnpj)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Excluir",
                                    icon_color="red",
                                    on_click=lambda e, cpf_cnpj=c.cpf_cnpj: excluir_fornecedor(cpf_cnpj)),
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
        ft.Text("Pesquisar Fornecedor", size=20, weight="bold"),
        ft.Row([campo_busca, botao_pesquisar]),
        msg_pesquisa,
        tabela
    ], expand=True, scroll="auto")

    # ------------------------------------------------------

    aba_cadastro = ft.Column([
        ft.Text("Cadastro de Fornecedor", size=20, weight="bold"),
        cpf_cnpj, nome, telefone, endereco, email, chave_pg,
        ft.ElevatedButton(text="Salvar", on_click=salvar_fornecedor),
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