import flet as ft
import bcrypt
from models.database import Users, db

# Login padrão embutido
LOGIN_PADRAO = {
    "user": "lbservicos",
    "psw": "lb2025"
}

def login_view(page: ft.Page, on_login_success):
    """Tela de login"""

    user_tf = ft.TextField(label="Usuário", width=250)
    psw_tf = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=250)

    def tentar_login(e):
        db.connect(reuse_if_open=True)

        try:
            usuarios_cadastrados = Users.select().count()

            if usuarios_cadastrados == 0:
                # Não há usuários no banco, permite login padrão embutido
                if user_tf.value == LOGIN_PADRAO["user"] and psw_tf.value == LOGIN_PADRAO["psw"]:
                    page.session.set("perfil", "Administrador")
                    page.session.set("usuario", "Login Padrão")
                    on_login_success()
                    return
                else:
                    mostrar_erro("Usuário ou senha incorretos (modo padrão)")
                    return

            # Verifica login pelo banco de dados
            try:
                user = Users.get(Users.user == user_tf.value)
                if bcrypt.checkpw(psw_tf.value.encode(), user.psw.encode()):
                    page.session.set("perfil", user.perfil)  # Salva o perfil
                    page.session.set("usuario", user.nome)  # Opcional: nome do usuário logado
                    on_login_success()
                else:
                    mostrar_erro("Senha incorreta")
            except Users.DoesNotExist:
                mostrar_erro("Usuário não encontrado")

        except Exception as ex:
            mostrar_erro(f"Erro ao validar login: {ex}")

        finally:
            db.close()

    def mostrar_erro(msg):
        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="red")
        page.snack_bar.open = True
        page.update()

    # Layout da tela
    page.views.clear()
    page.views.append(
        ft.View(
            "/login",
            controls=[
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        [
                            ft.Text("Login", size=24, weight="bold"),
                            user_tf,
                            psw_tf,
                            ft.ElevatedButton("Entrar", on_click=tentar_login)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
            ],
        ),
    )
    page.update()