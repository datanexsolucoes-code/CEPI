import flet as ft
import bcrypt
from models.database import Users, db

pessoa_editavel = {"cpf": None}
lista_perfil = ["Administrador", "Usuário"]

def view(page: ft.Page):
    # ---------- CAMPOS DE CADASTRO ----------
    cpf = ft.TextField(label="CPF")
    nome = ft.TextField(label="Nome")
    usuario = ft.TextField(label="Usuário")
    senha = ft.TextField(label="Senha", password=True, can_reveal_password=True)
    perfil = ft.Dropdown(
        label="Perfil",
        options=[ft.dropdown.Option(v) for v in lista_perfil],
        width=150
    )
    msg_cadastro = ft.Text(color="red")
    msg_pesquisa = ft.Text(color="red")

    # ---------- TABELA (DEFINIDA FORA DAS FUNÇÕES) ----------
    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text("CPF")),
            ft.DataColumn(label=ft.Text("Nome")),
            ft.DataColumn(label=ft.Text("Usuário")),
            ft.DataColumn(label=ft.Text("Perfil")),
            ft.DataColumn(label=ft.Text("Ações")),
        ],
        rows=[]
    )

    # ---------- FUNÇÕES ----------
    def salva_usuario(e):
        try:
            db.connect(reuse_if_open=True)
            if pessoa_editavel["cpf"]:  # Modo edição
                user = Users.get(Users.cpf == pessoa_editavel["cpf"])
                user.nome = nome.value
                user.user = usuario.value
                user.psw = bcrypt.hashpw(senha.value.encode(), bcrypt.gensalt()).decode()
                user.perfil = perfil.value
                user.save()
                msg_cadastro.value = f"Usuário {user.nome} atualizado com sucesso!"
            else:
                Users.create(
                    cpf=cpf.value,
                    nome=nome.value,
                    user=usuario.value,
                    psw=bcrypt.hashpw(senha.value.encode(), bcrypt.gensalt()).decode(),
                    perfil=perfil.value,
                )
                msg_cadastro.value = f"Usuário {nome.value} salvo com sucesso!"
            msg_cadastro.color = "green"
            cpf.value = nome.value = usuario.value = senha.value = perfil.value = ""
            pessoa_editavel["cpf"] = None
        except Exception as ex:
            msg_cadastro.value = f"Erro ao salvar/atualizar: {ex}"
            msg_cadastro.color = "red"
        finally:
            db.close()
            atualizar_tabela()
            page.update()

    def excluir_funcionario(cpf_usuario):
        try:
            db.connect(reuse_if_open=True)
            user = Users.get(Users.cpf == cpf_usuario)
            user.delete_instance()
            msg_pesquisa.value = f"Usuário {user.nome} excluído com sucesso!"
            msg_pesquisa.color = "green"
        except Exception as ex:
            msg_pesquisa.value = f"Erro ao excluir: {ex}"
            msg_pesquisa.color = "red"
        finally:
            db.close()
            atualizar_tabela()
            page.update()

    def editar_funcionario(cpf_usuario):
        try:
            db.connect(reuse_if_open=True)
            user = Users.get(Users.cpf == cpf_usuario)
            cpf.value = user.cpf
            nome.value = user.nome
            usuario.value = user.user
            senha.value = ""  # Nunca exibir senha
            perfil.value = user.perfil
            pessoa_editavel["cpf"] = user.cpf
            msg_cadastro.value = f"Editando usuário {user.nome}"
            msg_cadastro.color = "blue"
            page.update()
        except Exception as ex:
            msg_pesquisa.value = f"Erro ao carregar usuário: {ex}"
            msg_pesquisa.color = "red"
            page.update()
        finally:
            db.close()

    def atualizar_tabela():
        try:
            db.connect(reuse_if_open=True)
            query = Users.select()
            tabela.rows = []
            for c in query:
                tabela.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(c.cpf)),
                            ft.DataCell(ft.Text(c.nome)),
                            ft.DataCell(ft.Text(str(c.user))),
                            ft.DataCell(ft.Text(str(c.perfil))),
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
                                        on_click=lambda e, cpf=c.cpf: excluir_funcionario(cpf)
                                    ),
                                ])
                            )
                        ]
                    )
                )
        finally:
            db.close()
            page.update()

    # ---------- ABAS ----------
    aba_cadastro = ft.Column([
        ft.Text("Cadastro de Usuário", size=20, weight="bold"),
        cpf, nome, usuario, senha, perfil,
        ft.ElevatedButton(text="Salvar", on_click=salva_usuario),
        msg_cadastro
    ], expand=True, scroll="auto")

    aba_pesquisa = ft.Column([
        ft.Text("Usuários Cadastrados", size=20, weight="bold"),
        msg_pesquisa,
        tabela
    ], expand=True, scroll="auto")

    atualizar_tabela()  # Carrega a tabela ao iniciar

    return ft.Tabs(
        selected_index=0,
        expand=True,
        tabs=[
            ft.Tab(text="Cadastro", content=aba_cadastro),
            ft.Tab(text="Usuários", content=aba_pesquisa),
        ]
    )