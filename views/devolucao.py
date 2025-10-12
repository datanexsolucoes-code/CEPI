import flet as ft
from datetime import datetime, date
from models.database import Funcionario, Uniforme, Comodato, db

def view(page: ft.Page):
    page.scroll = "auto"
    db.connect(reuse_if_open=True)
    funcionarios = list(Funcionario.select())

    # --- Controles ---
    funcionario_dd = ft.Dropdown(
        label="Funcionário",
        options=[ft.dropdown.Option(str(f.id), f.nome) for f in funcionarios],
        width=300
    )

    resultado_container = ft.Column()

    # --- Função para exibir mensagens ---
    def show_message(msg, color="blue"):
        try:
            page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
            page.snack_bar.open = True
            page.update()
        except Exception as err:
            print("SnackBar error:", err)
            page.dialog = ft.AlertDialog(title=ft.Text(msg))
            page.dialog.open = True
            page.update()

    # --- Função para pesquisar comodatos ativos ---
    def pesquisar_comodatos(e):
        resultado_container.controls.clear()
        if not funcionario_dd.value:
            show_message("Selecione um funcionário!", "red")
            return

        comodatos = Comodato.select().where(
            (Comodato.funcionario == int(funcionario_dd.value)) &
            (Comodato.ativo == True)
        )

        if not comodatos:
            resultado_container.controls.append(ft.Text("Nenhum uniforme ativo para este funcionário."))
        else:
            for com in comodatos:
                uni = com.uniforme
                data_entrega_str = com.data_entrega.strftime("%d/%m/%Y")
                resultado_container.controls.append(
                    ft.Card(
                        content=ft.Column([
                            ft.Text(f"{uni.descricao} - Qtd: {com.quantidade} - Entregue: {data_entrega_str}", weight="bold"),
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.REPLAY,
                                    icon_color="green",
                                    tooltip="Registrar devolução",
                                    on_click=lambda e, c=com: registrar_devolucao(c)
                                )
                            ])
                        ])
                    )
                )
        page.update()

    # --- Função para registrar devolução ---
    def registrar_devolucao(comodato):
        try:
            with db.atomic():
                # Atualiza comodato
                comodato.data_devolucao = date.today()
                comodato.ativo = False
                comodato.save()

                # # Atualiza estoque
                # uni = comodato.uniforme
                # uni.quantidade_estoque = (uni.quantidade_estoque or 0) + comodato.quantidade
                # uni.save()

            show_message(f"Devolução registrada para {comodato.uniforme.descricao}.", "green")
            pesquisar_comodatos(None)
        except Exception as ex:
            print("Erro ao registrar devolução:", ex)
            show_message(f"Erro ao registrar devolução: {ex}", "red")

    # --- Layout ---
    pesquisa_layout = ft.Column([
        ft.Text("Devolução de Uniformes", size=20, weight="bold"),
        funcionario_dd,
        ft.ElevatedButton(text="Pesquisar", icon=ft.Icons.SEARCH, on_click=pesquisar_comodatos),
        resultado_container
    ], scroll="auto")

    return pesquisa_layout
