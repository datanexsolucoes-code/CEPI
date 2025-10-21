import os
import flet as ft
from views.epi import view as view_epi
from views.fornecedor import view as view_fornecedor
from views.funcionario import view as view_funcionario
from views.entrega import view as view_entregas
from views.devolucao import view as view_devolucao
from views.compra import view as view_compra
from views.login import login_view
from views.users import view as view_user
from views.relatorios import view as view_relatorios
from views.reparos import view as view_reparos
from models.database import inicializar_banco  # seu arquivo de banco (com create_tables)

# VIEW PRINCIPAL (home)
def view_home(page: ft.Page):
    return ft.Column([
        ft.Text("Bem-vindo ao CEPI - Controle de EPI", size=20, weight="bold")
    ], expand=True, alignment=ft.MainAxisAlignment.CENTER)


# Função principal
def main(page: ft.Page):
    icon_path = os.path.abspath("Imagens/icone_D.ico")
    page.window.icon = icon_path
    page.title = "CEPI"
    page.bgcolor = ft.Colors.BLACK87
    page.window.width = 1000
    page.window.height = 700
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_maximized = True

    # Inicializa banco
    inicializar_banco()

    # Função para abrir o app principal após login
    def abrir_app_principal():
        # --- Drawer e navegação (igual ao seu código atual) ---
        def abrir_menu(e):
            page.drawer.open = True
            page.update()

        def appbar():
            return ft.AppBar(
                title=ft.Text("Menu"),
                leading=ft.IconButton(icon=ft.Icons.MENU, on_click=abrir_menu),
            )

        drawer = ft.NavigationDrawer(
            controls=[
                ft.Container(height=20),
                ft.NavigationDrawerDestination(icon=ft.Icons.HOME, label="Início"),
                ft.NavigationDrawerDestination(icon=ft.Icons.PEOPLE, label="Funcionário"),
                ft.NavigationDrawerDestination(icon=ft.Icons.WORK, label="Uniformes"),
                ft.NavigationDrawerDestination(icon=ft.Icons.INVENTORY_2, label="Entregas"),
                ft.NavigationDrawerDestination(icon=ft.Icons.INVENTORY_2, label="Devolução"),
                ft.NavigationDrawerDestination(icon=ft.Icons.HOME, label="Compra"),
                ft.NavigationDrawerDestination(icon=ft.Icons.CONTENT_CUT, label="Reparo"),
                ft.NavigationDrawerDestination(icon=ft.Icons.FACTORY, label="Fornecedor"),
                ft.NavigationDrawerDestination(icon=ft.Icons.INSIGHTS, label="Relatórios"),
                ft.NavigationDrawerDestination(icon=ft.Icons.PEOPLE, label="Usuários"),
            ],
            on_change=lambda e: page.go({
                0: "/",
                1: "/funcionario",
                2: "/uniformes",
                3: "/entregas",
                4: "/devolucao",
                5: "/compra",
                6: "/reparo",
                7: "/fornecedor",
                8: "/relatorios",
                9: "/usuario"
            }[e.control.selected_index])
        )
        page.drawer = drawer

        # --- Função route_change e página inicial ---
        def route_change(route):
            page.views.clear()
            match page.route:
                case "/":
                    page.views.append(
                        ft.View(
                            route="/",
                            controls=[
                                appbar(),
                                ft.Container(
                                    expand=True,
                                    alignment=ft.alignment.center,
                                    content=ft.Column([
                                        ft.Text("Bem-vindo ao CEPI - Controle de EPI's", size=22, weight="bold",
                                            color=ft.Colors.BLACK87
                                        ),
                                        ft.Text("Gerencie entregas, EPI's, funcionários e fornecimento de forma simples e eficaz.",
                                            size=16, color=ft.Colors.BLACK45
                                        ),
                                        ft.Container(
                                            content=ft.Image(
                                            src=os.path.abspath("Imagens/LB.PNG"),
                                            fit=ft.ImageFit.CONTAIN
                                            ),
                                        ),
                                    ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        expand=True
                                    ),
                                ),
                            ],
                            drawer=drawer,
                        ),
                    ),
                case "/funcionario":
                    page.views.append(ft.View(route="/funcionario", controls=[appbar(), view_funcionario(page)], drawer=drawer))
                case "/uniformes":
                    page.views.append(ft.View(route="/uniformes", controls=[appbar(), view_epi(page)], drawer=drawer))
                case "/entregas":
                    page.views.append(ft.View(route="/entregas", controls=[appbar(), view_entregas(page)], drawer=drawer))
                case "/devolucao":
                    page.views.append(ft.View(route="/devolucao", controls=[appbar(), view_devolucao(page)], drawer=drawer))
                case "/compra":
                    page.views.append(ft.View(route="/compra", controls=[appbar(), view_compra(page)], drawer=drawer))
                case "/reparo":
                    page.views.append(ft.View(route="/reparo", controls=[appbar(), view_reparos(page)], drawer=drawer))
                case "/fornecedor":
                    page.views.append(ft.View(route="/fornecedor", controls=[appbar(), view_fornecedor(page)], drawer=drawer))
                case "/relatorios":
                    page.views.append(ft.View(route="/relatorios", controls=[appbar(), view_relatorios(page)], drawer=drawer))
                case "/usuario":
                    perfil = page.session.get("perfil")
                    if perfil == "Administrador":
                        page.views.append(
                            ft.View(route="/usuario", controls=[appbar(), view_user(page)], drawer=drawer))
                    else:
                        page.views.append(
                            ft.View(
                                route="/usuario",
                                controls=[
                                    appbar(),
                                    ft.Container(
                                        content=ft.Text(
                                            "Acesso negado: visível apenas para perfil administrador",
                                            color="red", size=18),
                                        alignment=ft.alignment.center,
                                        expand=True
                                    )
                                ],
                                drawer=drawer
                            )
                        )
            page.update()

        page.on_route_change = route_change
        page.go("/")

    # --- Inicializa com tela de login ---
    login_view(page, abrir_app_principal)

# Executa app
if __name__ == "__main__":
    ft.app(target=main)
    #ft.app(target=main, view=ft.WEB_BROWSER, assets_dir="Imagens")