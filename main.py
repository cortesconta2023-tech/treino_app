import json
import os
from datetime import datetime, timedelta

from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import platform as kivy_platform

try:
    from plyer import vibrator
except ImportError:
    vibrator = None




class MeuApp(App):

    def build(self):
        # Define o caminho dos dados do app no diretório do usuário
        self.data_path = os.path.join(self.user_data_dir, "treino_data.json")
        self.load_data()

        # Cria o widget raiz do app para trocar telas facilmente
        # BoxLayout não tem a propriedade "background_color" -- por isso o fundo
        # precisa ser desenhado manualmente no canvas com Color + Rectangle.
        self.root = BoxLayout(orientation="vertical")
        with self.root.canvas.before:
            self.instrucao_cor_fundo = Color(*self.cor_fundo)
            self.retangulo_fundo = Rectangle(pos=self.root.pos, size=self.root.size)
        self.root.bind(pos=self._atualizar_fundo, size=self._atualizar_fundo)

        self.root.add_widget(self.criar_tela_preparar())
        return self.root

    def _atualizar_fundo(self, instance, value):
        # Mantém o retângulo de fundo do canvas sincronizado com o tamanho/posição do root
        self.retangulo_fundo.pos = instance.pos
        self.retangulo_fundo.size = instance.size

    def load_data(self):
        # Carrega configurações e histórico de treino de um arquivo JSON
        default = {
            "settings": {
                "series": "",
                "repeticoes": "",
                "descanso": "",
                "preparacao": "",
                "sound": True,
                "theme": "light",
                "vibration": False
            },
            "history": []
        }
        self.data = default

        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as file:
                    self.data = json.load(file)
            except Exception:
                self.data = default

        self.settings = self.data.get("settings", default["settings"])
        self.history = self.data.get("history", [])
        self.cores_app()

    def save_data(self):
        self.data["settings"] = self.settings
        self.data["history"] = self.history
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, "w", encoding="utf-8") as file:
                json.dump(self.data, file, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def cores_app(self):
        # Responsável por TODAS as cores do app: fundo, texto, campos de entrada e botões
        # (Paleta Energia e Foco), para tema claro e escuro
        tema = self.settings.get("theme", "light")
        if tema == "dark":
            # Fundo geral do app em tema escuro (tom de azul)
            self.cor_fundo = [0.05, 0.09, 0.18, 1]
            # Cor do texto em tema escuro
            self.cor_texto = [1, 1, 1, 1]
            # Cor de fundo dos campos de entrada em tema escuro (azul um pouco mais claro que o fundo)
            self.cor_fundo_input = [0.10, 0.16, 0.28, 1]
            # Cor de fundo dos botões secundários em tema escuro (azul, sem bege)
            self.cor_botao_secundario = [0.20, 0.34, 0.55, 1]
            # Cor do botão de destaque (ex: Iniciar Treino) quando ATIVO: azul mais claro que os outros botões
            self.cor_destaque_ativo = [0.35, 0.55, 0.85, 1]
            # Cor do botão de destaque quando DESATIVADO: azul escuro
            self.cor_destaque_inativo = [0.10, 0.16, 0.30, 1]
        else:
            # Fundo geral do app em tema claro (tom de cinza, não branco puro)
            self.cor_fundo = [0.88, 0.89, 0.91, 1]
            # Cor do texto em tema claro
            self.cor_texto = [0.15, 0.15, 0.2, 1]
            # Cor de fundo dos campos de entrada em tema claro
            self.cor_fundo_input = [0.97, 0.97, 0.98, 1]
            # Cor de fundo dos botões secundários em tema claro (cinza, sem bege)
            self.cor_botao_secundario = [0.68, 0.68, 0.71, 1]
            # Cor do botão de destaque quando ATIVO: cinza mais claro que os outros botões
            self.cor_destaque_ativo = [0.82, 0.82, 0.85, 1]
            # Cor do botão de destaque quando DESATIVADO: cinza mais escuro
            self.cor_destaque_inativo = [0.48, 0.48, 0.51, 1]

        # Cor do texto dos botões (mesma nos dois temas, pois os botões têm fundo colorido)
        self.cor_texto_botao = [1, 1, 1, 1]

        # Cores de estado do timer (independentes do tema)
        # Cor para a tela de preparação (contagem regressiva)
        self.cor_status_preparo = [1, 0.84, 0, 1]       # Amarelo dourado
        # Cor para indicar que o treino começou
        self.cor_status_em_acao = [0.2, 0.8, 0.2, 1]    # Verde
        # Cor para a tela de descanso entre séries
        self.cor_status_descanso = [0.2, 0.6, 1, 1]     # Azul elétrico
        # Cor para indicar pausa
        self.cor_status_pausado = [0.9, 0.2, 0.2, 1]    # Vermelho
        # Cor para indicar treino finalizado
        self.cor_status_finalizado = [0.2, 0.8, 0.2, 1] # Verde

        # Se o canvas de fundo já existe (troca de tema em runtime), atualiza a cor
        if hasattr(self, "instrucao_cor_fundo"):
            self.instrucao_cor_fundo.rgba = self.cor_fundo

    def criar_botao(self, texto, cor_fundo=None, cor_fundo_desativado=None, **kwargs):
        # Cria um botão já estilizado com a cor sólida do tema.
        # background_normal/background_down/background_disabled_normal ficam vazios
        # porque, por padrão, o Kivy desenha os botões com uma textura bege e apenas
        # tinge essa textura com background_color -- por isso os botões pareciam bege
        # mesmo com uma cor de fundo diferente definida. Com a textura removida, o
        # botão fica com a cor sólida escolhida.
        if cor_fundo is None:
            cor_fundo = self.cor_botao_secundario
        # Se não for informada uma cor específica para o estado desativado,
        # o botão mantém a mesma cor nos dois estados.
        if cor_fundo_desativado is None:
            cor_fundo_desativado = cor_fundo

        botao = Button(
            text=texto,
            color=self.cor_texto_botao,
            background_color=cor_fundo,
            background_normal="",
            background_down="",
            background_disabled_normal="",
            **kwargs
        )
        # Guarda as duas cores no próprio botão para poder trocar quando ele for
        # ativado/desativado (ex: "Iniciar Treino" só fica ativo com os campos preenchidos)
        botao.cor_quando_ativo = cor_fundo
        botao.cor_quando_desativado = cor_fundo_desativado
        botao.bind(disabled=self._atualizar_cor_botao)
        # Se o botão já nasce desativado, aplica a cor correta desde já
        if botao.disabled:
            botao.background_color = cor_fundo_desativado
        return botao

    def _atualizar_cor_botao(self, instance, esta_desativado):
        # Troca a cor de fundo do botão conforme ele fica ativo ou desativado
        instance.background_color = (
            instance.cor_quando_desativado if esta_desativado else instance.cor_quando_ativo
        )

    def criar_tela_preparar(self):
        # Barra de rolagem
        scroll = ScrollView(size_hint=(1, 1))
        # Cria o layout principal da tela de preparação
        layout = BoxLayout(
            orientation="vertical",
            padding=20,
            spacing=15,
            size_hint_y=None
        )
        layout.bind(minimum_height=layout.setter("height"))
        # Titulo principal "Treino Rápido"
        titulo = Label(
            text=" Treino Rápido",
            font_size=36,
            size_hint_y=None,
            height=70,
            color=self.cor_texto
        )
        # Adiciona o título ao layout principal
        layout.add_widget(titulo)
        # Adiciona o resumo do histórico de treinos ao layout principal
        self.label_recorde = Label(
            text=self.obter_resumo_historico(),# Chama função para obter o resumo do histórico de treinos
            font_size=16,
            size_hint_y=None,
            height=60,
            color=self.cor_texto
        )
        # Adiciona o resumo do histórico de treinos ao layout principal
        layout.add_widget(self.label_recorde)

        # Cria e adiciona no layout principal o texto "Séries" acima do primeiro input
        layout.add_widget(Label
            (text="Séries",
            font_size=20,
            size_hint_y=None,
            height=32,
            color=self.cor_texto))
        
        # Input para "Series" com validação de número inteiro e estilo baseado no tema
        self.input_series = TextInput(
            text="",
            hint_text="Digite as séries",
            multiline=False,
            input_filter="int",
            font_size=20,
            size_hint_y=None,
            height=50,
            foreground_color=self.cor_texto,
            # Usa a cor de cor_fundo_input definida em cores_app() para manter consistência
            background_color=self.cor_fundo_input
        )
        # Ao apertar enter vai para "Repetição"
        self.input_series.bind(on_text_validate=self.ir_para_repeticao)
        # Verifica se todos os campos estão preenchidos para habilitar o botão de iniciar
        self.input_series.bind(text=self.verificar_campos)
        # Adiciona o input de "Series" ao layout principal
        layout.add_widget(self.input_series)

        # Cria e adiciona no layout principal o texto "Repetições" acima do segundo input
        layout.add_widget(Label
            (text="Repetições",
            font_size=20,
            size_hint_y=None,
            height=32,
            color=self.cor_texto))
        
        # Input para "Repetições" com validação de número inteiro e estilo baseado no tema
        self.input_repeticao = TextInput(
            text="",
            hint_text="Digite as repetições",
            multiline=False,# Permite apenas uma linha de texto
            input_filter="int",
            font_size=20,
            size_hint_y=None,
            height=50,
            foreground_color=self.cor_texto,
            background_color=self.cor_fundo_input
        )
        # Ao apertar enter vai para "Descanso"
        self.input_repeticao.bind(on_text_validate=self.ir_para_descanso)
        # Verifica se todos os campos estão preenchidos para habilitar o botão de iniciar
        self.input_repeticao.bind(text=self.verificar_campos)
        # Adiciona o input de "Repetições" ao layout principal
        layout.add_widget(self.input_repeticao)

        # Cria e adiciona no layout principal o texto "Descanso (segundos)" acima do terceiro input
        layout.add_widget(Label
            (text="Descanso (segundos)",
            font_size=20, size_hint_y=None,
            height=32,
            color=self.cor_texto))
        
        # Input para "Descanso" com validação de número inteiro e estilo baseado no tema
        self.input_descanso = TextInput(
            text="",
            hint_text="Digite o tempo de descanso",
            multiline=False,
            input_filter="int",
            font_size=20,
            size_hint_y=None,
            height=50,
            foreground_color=self.cor_texto,
            background_color=self.cor_fundo_input
        )
        # Ao apertar enter vai para "Preparação"
        self.input_descanso.bind(on_text_validate=self.ir_para_preparacao)
        # Verifica se todos os campos estão preenchidos para habilitar o botão de iniciar
        self.input_descanso.bind(text=self.verificar_campos)
        # Adiciona o input de "Descanso" ao layout principal
        layout.add_widget(self.input_descanso)

        # Cria e adiciona no layout principal o texto "Preparação" acima dos botões
        layout.add_widget(Label(
            text="Preparação",
            font_size=20,
            size_hint_y=None,
            height=32,
            color=self.cor_texto
        ))

        self.preparacao_selecionada = 3
        valor_preparacao_salvo = self.settings.get("preparacao", "")
        if isinstance(valor_preparacao_salvo, str) and valor_preparacao_salvo.strip():
            try:
                self.preparacao_selecionada = int(valor_preparacao_salvo)
            except ValueError:
                self.preparacao_selecionada = 3
        elif valor_preparacao_salvo not in [None, ""]:
            try:
                self.preparacao_selecionada = int(valor_preparacao_salvo)
            except ValueError:
                self.preparacao_selecionada = 3

        linha_preparacao = BoxLayout(
            orientation="horizontal",
            spacing=10,
            size_hint_y=None,
            height=50
        )

        self.botao_preparacao_3 = self.criar_botao("3s", font_size=18)
        self.botao_preparacao_3.bind(on_press=lambda instance: self.selecionar_preparacao(3))
        linha_preparacao.add_widget(self.botao_preparacao_3)

        self.botao_preparacao_5 = self.criar_botao("5s", font_size=18)
        self.botao_preparacao_5.bind(on_press=lambda instance: self.selecionar_preparacao(5))
        linha_preparacao.add_widget(self.botao_preparacao_5)

        self.botao_preparacao_10 = self.criar_botao("10s", font_size=18)
        self.botao_preparacao_10.bind(on_press=lambda instance: self.selecionar_preparacao(10))
        linha_preparacao.add_widget(self.botao_preparacao_10)

        layout.add_widget(linha_preparacao)
        self.atualizar_botoes_preparacao()

        # Botao do som 
        # Cria um layout horizontal para os botões de opções
        opcoes = BoxLayout(
            orientation="horizontal",
            spacing=10,
            size_hint_y=None,
            height=50)
        # Cria o botão de som com o texto baseado na configuração atual
        self.botao_som = self.criar_botao(
            "Som: Ativado" if self.settings.get("sound") else "Som: Desativado",
            font_size=16)
        # Alterna o estado do som ao pressionar o botão
        self.botao_som.bind(on_press=self.alternar_som)
        # Adiciona o botão de som ao layout de opções
        opcoes.add_widget(self.botao_som)

        # Botao  de tema 
        # Cria o botão de tema com o texto baseado na configuração atual
        self.botao_tema = self.criar_botao(
            "Tema Escuro" if self.settings.get("theme") == "light" else "Tema Claro",
            font_size=16)
        # Alterna o tema ao pressionar o botão
        self.botao_tema.bind(on_press=self.alternar_tema)
        # Adiciona o botão de tema ao layout de opções
        opcoes.add_widget(self.botao_tema)
        # Adiciona o layout de "opções" ao layout principal
        layout.add_widget(opcoes)

        # Cria um segundo layout horizontal para os botões de "vibração" e "histórico"
        opcoes2 = BoxLayout(
            orientation="horizontal",
            spacing=10,
            size_hint_y=None,
            height=50)
        
        # Botão de vibração ativada / desativada
        self.botao_vibracao = self.criar_botao(
            "Vibração: Ativa" if self.settings.get("vibration") else "Vibração: Desativada",
            font_size=16,
            # Desabilita o botão de vibração se o dispositivo não suportar vibração
            disabled=(vibrator is None and kivy_platform != "android")
        )
        # Alterna o estado da vibração ao pressionar o botão
        self.botao_vibracao.bind(on_press=self.alternar_vibracao)
        # Adiciona o botão de "vibração" ao layout de "opções 2"
        opcoes2.add_widget(self.botao_vibracao)

        # Botão de histórico de treinos
        self.botao_historico = self.criar_botao("Histórico", font_size=16)
        # Alterna a exibição do histórico de treinos ao pressionar o botão
        self.botao_historico.bind(on_press=self.mostrar_historico)
        # Adiciona o botão de "histórico" ao layout de "opções 2"
        opcoes2.add_widget(self.botao_historico)
        # Adiciona o layout de "opções 2" ao layout principal
        layout.add_widget(opcoes2)

        # Botão de iniciar treino
        self.botao_iniciar = self.criar_botao(
            "Iniciar Treino",
            cor_fundo=self.cor_destaque_ativo,
            cor_fundo_desativado=self.cor_destaque_inativo,
            font_size=22,
            size_hint_y=None,
            height=65,
            disabled=True)
        # Ao pressionar o botão de iniciar treino, chama a função iniciar
        self.botao_iniciar.bind(on_press=self.iniciar)
        # Adiciona o botão de iniciar treino ao layout principal
        layout.add_widget(self.botao_iniciar)
        # Verifica se todos os campos estão preenchidos para habilitar o botão de iniciar
        self.verificar_campos(None, None)
        # Adiciona o layout principal ao ScrollView para permitir rolagem caso necessário
        scroll.add_widget(layout)
        return scroll

    def obter_resumo_historico(self):
        # Calcula o número de dias seguidos de treino e o recorde de dias consecutivos
        dias_seguidos, recorde = self.calcular_recorde_consecutivo()
        # Calcula o total de treinos realizados
        total_treinos = len(self.history)
        return f" {total_treinos} treinos | {recorde} dias seguidos | {dias_seguidos} atuais"

    def limpa_historico_popup(self, instance):
        self.limpa_historico()
        self.label_hist_popup.text = self.obter_resumo_historico()

    def limpa_historico(self):
        # Limpa o histórico de treinos e salva os dados
        self.history = []
        # Atualiza o resumo do histórico de treinos na tela
        self.save_data()
        # Atualiza o resumo do histórico de treinos na tela
        self.label_recorde.text = self.obter_resumo_historico()

    def calcular_recorde_consecutivo(self):
        # date em ordem 
        datas = sorted({entry["date"] for entry in self.history})
        if not datas:
            return 0, 0

        hoje = datetime.now().date()
        datas_obj = [datetime.fromisoformat(date_text).date() for date_text in datas]
        datas_obj.sort()

        recorde = 0
        atual = 0
        anterior = None
        for data in datas_obj:
            if anterior is None or data != anterior + timedelta(days=1):
                atual = 1
            else:
                atual += 1
            recorde = max(recorde, atual)
            anterior = data

        dias_seguidos = 0
        if datas_obj[-1] == hoje:
            dias_seguidos = 1
            for i in range(len(datas_obj) - 2, -1, -1):
                if datas_obj[i] == datas_obj[i + 1] - timedelta(days=1):
                    dias_seguidos += 1
                else:
                    break
        return dias_seguidos, recorde

    def ir_para_repeticao(self, instance):
        self.input_repeticao.focus = True

    def ir_para_descanso(self, instance):
        self.input_descanso.focus = True

    def ir_para_preparacao(self, instance):
        self.input_preparacao.focus = True

    def alternar_som(self, instance):
        self.settings["sound"] = not self.settings.get("sound", True)
        instance.text = "Som: Ativo" if self.settings["sound"] else "Som: Desativado"
        self.save_data()

    def alternar_tema(self, instance):
        self.settings["theme"] = "dark" if self.settings.get("theme") == "light" else "light"
        instance.text = "Tema Escuro" if self.settings["theme"] == "light" else "Tema Claro"
        self.cores_app()
        self.root.clear_widgets()
        self.root.add_widget(self.criar_tela_preparar())
        self.save_data()

    def alternar_vibracao(self, instance):
        self.settings["vibration"] = not self.settings.get("vibration", False)
        instance.text = "📳 Vibração: Ativa" if self.settings["vibration"] else "📳 Vibração: Desativada"
        self.save_data()

    def selecionar_preparacao(self, valor):
        self.preparacao_selecionada = valor
        self.atualizar_botoes_preparacao()
        self.verificar_campos(None, None)

    def atualizar_botoes_preparacao(self):
        for botao, valor in [
            (self.botao_preparacao_3, 3),
            (self.botao_preparacao_5, 5),
            (self.botao_preparacao_10, 10),
        ]:
            if hasattr(botao, "cor_quando_ativo"):
                botao.background_color = (
                    self.cor_destaque_ativo if self.preparacao_selecionada == valor else self.cor_botao_secundario
                )

    def salvar_configuracoes(self):
        # Salva as configurações atuais de treino no arquivo JSON
        self.settings["series"] = self.input_series.text
        self.settings["repeticoes"] = self.input_repeticao.text
        self.settings["descanso"] = self.input_descanso.text
        self.settings["preparacao"] = str(self.preparacao_selecionada)
        self.save_data()

    def iniciar(self, instance):
        # Cancela timers antigos caso existam
        if hasattr(self, "relogio") and self.relogio:
            self.relogio.cancel()
            self.relogio = None
        if hasattr(self, "timer_total") and self.timer_total:
            self.timer_total.cancel()
            self.timer_total = None

        try:
            self.total_series = int(self.input_series.text)
            self.total_repeticoes = int(self.input_repeticao.text)
            self.tempo_descanso = int(self.input_descanso.text)
            self.preparacao = int(self.preparacao_selecionada)
        except ValueError:
            return

        if self.total_series < 1 or self.total_repeticoes < 1 or self.tempo_descanso < 0 or self.preparacao < 0:
            return

        self.salvar_configuracoes()
        self.serie_atual = 1
        self.repeticao_atual = 0
        self.contador = self.preparacao
        self.estado = "preparacao"
        self.som = SoundLoader.load("sons/beep.wav")
        self.total_treino_segundos = 0
        self.total_completed = 0

        self.root.clear_widgets()
        self.root.add_widget(self.criar_tela_treino())

        self.timer_total = Clock.schedule_interval(self.atualizar_tempo_total, 1)
        self.relogio = Clock.schedule_interval(self.contagem_preparar, 1)

    def criar_tela_treino(self):
        # Cria layout
        layout = BoxLayout(
            orientation="vertical",
            padding=20,
            spacing=20)

        # Texto "Prepare-se" na preparaçao
        self.label_status = Label(
            text="Prepare-se!",
            font_size=32,
            size_hint_y=None,
            height=60,
            color=self.cor_texto)

        # Numero da contagem
        self.label_numero = Label(
            text=str(self.contador),
            font_size=120,
            size_hint_y=None,
            height=200,
            color=self.cor_texto)
        

        # Adiciona os texto "Prepara-se" e Os numero da contagem no layout
        layout.add_widget(self.label_status)
        layout.add_widget(self.label_numero)
        

        ####
                     
        # Cria layout chamado "linha_info"
        linha_info = BoxLayout(
            orientation="horizontal",
            spacing=15,
            size_hint_y=None,
            height=40)
        
        self.label_serie = Label(text=f"Série: {self.serie_atual}/{self.total_series}", font_size=18, color=self.cor_texto)
        self.label_repeticao = Label(text=f"Repetição: {self.repeticao_atual}/{self.total_repeticoes}", font_size=18, color=self.cor_texto)
        # Adiciona "label_serie" e "label_repeticao" no layout "linha_info"
        linha_info.add_widget(self.label_serie)
        linha_info.add_widget(self.label_repeticao)
        
        # Adiciona o layout "linha_info" no layout "layout"
        layout.add_widget(linha_info)
                      

        # Cria o cronometro "Tempo total"
        self.label_tempo_total = Label(text="Tempo total: 00:00", font_size=18, size_hint_y=None, height=30, color=self.cor_texto)
        # Adiciona o  cronometro no "layout"
        layout.add_widget(self.label_tempo_total)

        # Cria a barra de progresso
        self.label_progresso = Label(text="Progresso: 0%", font_size=18, size_hint_y=None, height=30, color=self.cor_texto)
        # Adicona a barra de progresso no "layout"
        layout.add_widget(self.label_progresso)
###
        

        # Barra de progresso o desenho
        self.barra_progresso = ProgressBar(max=100, value=0, size_hint_y=None, height=26)
        # Adiciona o desenho da barra de progresso no "layout"
        layout.add_widget(self.barra_progresso)

        # Cria layout "linha_descanso"
        linha_descanso = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=48)
        # Cria botao de "-5s"
        self.botao_menos5 = self.criar_botao("-5s", font_size=16, disabled=True)
        # Ao pressionar o botao "-5s" chama funçao "ajustar_descanso" com -5
        self.botao_menos5.bind(on_press=lambda inst: self.ajustar_descanso(-5))
        # Cria botao de "+5s"
        self.botao_mais5 = self.criar_botao("+5s", font_size=16, disabled=True)
        # Ao pressionar o botao de "+5s" chama funçao "ajustar_descanso" com 5
        self.botao_mais5.bind(on_press=lambda inst: self.ajustar_descanso(5))
        # Cria botao de "+10s"
        self.botao_mais10 = self.criar_botao("+10s", font_size=16, disabled=True)
        # Ao pressionar o boato de "+10s" chama funçao "ajustar_descanso" com mais 10
        self.botao_mais10.bind(on_press=lambda inst: self.ajustar_descanso(10))
     
        # Adiciona ao layout "linha_descanso" -5,+5,+10 e pular descanso
        linha_descanso.add_widget(self.botao_menos5)
        linha_descanso.add_widget(self.botao_mais5)
        linha_descanso.add_widget(self.botao_mais10)
        
        # Adiciona ao "layout" o layout "linha_descanso"
        layout.add_widget(linha_descanso)

        # Cria o layout "linha_botoes"
        linha_botoes = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=50)
        # Cria botao "voltar rep"
        self.botao_voltar_rep = self.criar_botao(" Voltar rep", font_size=16)
        # Ao pressionar p botao "voltar rep" chama a funçao "voltar_repeticao"
        self.botao_voltar_rep.bind(on_press=self.voltar_repeticao)
        # Cria botao "pausar"
        self.botao_pausar = self.criar_botao("Pausar", font_size=16)
        # Ao pressionar botao "pausar" chama a funçao pausar
        self.botao_pausar.bind(on_press=self.pausar)
        # Cria botao sair
        self.botao_sair = self.criar_botao("Sair", font_size=16)
        # Ao pressionar o botao "sair" chama a funçao voltar_preparar
        self.botao_sair.bind(on_press=self.voltar_preparar)

        # Adiciona os botoes "pause", "voltar" e "sair" no layout "linha_botoes"
        linha_botoes.add_widget(self.botao_voltar_rep)
        linha_botoes.add_widget(self.botao_pausar)
        linha_botoes.add_widget(self.botao_sair)
        # Adiciona o layout "linha_botoes" no layout
        layout.add_widget(linha_botoes)

        return layout

    def tocar_som_contagem(self):
        # Toca o som quando troca a contagem
        if self.settings.get("sound") and self.som:
            self.som.play()

    def atualizar_tempo_total(self, dt):
        self.total_treino_segundos += 1
        self.label_tempo_total.text = f"Tempo total: {self.formatar_tempo(self.total_treino_segundos)}"

    def formatar_tempo(self, segundos):
        minutos = segundos // 60
        seg = segundos % 60
        return f"{minutos:02d}:{seg:02d}"

    def contagem_preparar(self, dt):
        self.label_status.text = "Prepare-se!"
        if self.contador <= 3 and self.settings.get("sound"):
            self.tocar_som_contagem()

        self.label_numero.text = str(self.contador)
        self.contador -= 1

        if self.contador < 0:
            self.label_status.text = "Comece!"
            self.label_numero.text = "Iniciar!"
            self.label_status.color = (0, 1, 0, 1)
            self.label_numero.color = (0, 1, 0, 1)
            self.relogio.cancel()
            self.relogio = None
            Clock.schedule_once(self.iniciar_repeticao, 1)
            return False

    def iniciar_repeticao(self, dt):
        self.estado = "treino"
        self.repeticao_atual = 1
        self.atualizar_labels_treino()
        self.label_numero.text = str(self.repeticao_atual)
        self.relogio = Clock.schedule_interval(self.contagem_repeticao, 1)

    def atualizar_labels_treino(self):
        self.label_serie.text = f"Série: {self.serie_atual}/{self.total_series}"
        self.label_repeticao.text = f"Repetição: {self.repeticao_atual}/{self.total_repeticoes}"
        self.label_status.text = "Em ação"
        self.label_status.color = self.cor_texto
        self.label_numero.color = self.cor_texto

    def atualizar_progresso(self):
        total = self.total_series * self.total_repeticoes
        feito = ((self.serie_atual - 1) * self.total_repeticoes) + self.repeticao_atual
        porcentagem = int((feito / total) * 100)
        self.label_progresso.text = f"Progresso: {porcentagem}%"
        Animation(value=porcentagem, duration=0.3).start(self.barra_progresso)
        self.total_completed = feito

    def contagem_repeticao(self, dt):
        if self.repeticao_atual < self.total_repeticoes:
            self.repeticao_atual += 1
            self.atualizar_labels_treino()
            self.label_numero.text = str(self.repeticao_atual)
            self.atualizar_progresso()
            return

        if self.serie_atual == self.total_series:
            self.finalizar_treino()
            return False

        self.estado = "descanso"
        self.contador = self.tempo_descanso
        self.label_status.text = f"Descanso ({self.contador}s)"
        self.label_status.color = self.cor_texto
        self.label_numero.text = str(self.contador)
        self.botao_menos5.disabled = False
        self.botao_mais5.disabled = False
        self.botao_mais10.disabled = False
        
        self.relogio.cancel()
        self.relogio = Clock.schedule_interval(self.contagem_descanso, 1)
        return False

    def contagem_descanso(self, dt):
        if self.contador <= 3 and self.contador > 0 and self.settings.get("sound"):
            self.tocar_som_contagem()

        if self.contador > 0:
            self.contador -= 1
            self.label_numero.text = str(self.contador)
            self.label_status.text = f"Descanso ({self.contador}s)"
            return

        self.botao_menos5.disabled = True
        self.botao_mais5.disabled = True
        self.botao_mais10.disabled = True
       

        if self.serie_atual < self.total_series:
            self.serie_atual += 1
            self.repeticao_atual = 1
            self.label_serie.text = f"Série: {self.serie_atual}/{self.total_series}"
            self.atualizar_progresso()
            self.estado = "treino"
            self.label_status.text = "Continue!"
            self.label_status.color = (0, 1, 0, 1)
            self.label_numero.text = str(self.repeticao_atual)
            self.label_repeticao.text = f"Repetição: {self.repeticao_atual}/{self.total_repeticoes}"
            self.relogio.cancel()
            self.relogio = Clock.schedule_interval(self.contagem_repeticao, 1)
        else:
            self.finalizar_treino()
        return False

    def finalizar_treino(self):
        self.estado = "finalizado"
        if hasattr(self, "relogio") and self.relogio:
            self.relogio.cancel()
            self.relogio = None
        if hasattr(self, "timer_total") and self.timer_total:
            self.timer_total.cancel()
            self.timer_total = None
        self.label_status.text = "Treino Finalizado!"
        self.label_numero.text = "CONCLUIDO!!!"
        self.label_status.color = (0, 1, 0, 1)
        self.atualizar_progresso()

        self.adicionar_historico()
        self.save_data()

    def adicionar_historico(self):
        hoje = datetime.now().date().isoformat()
        self.history.append({
            "date": hoje,
            "duration": self.total_treino_segundos,
            "series": self.total_series,
            "repeticoes": self.total_repeticoes,
            "percentual": int((self.total_completed / (self.total_series * self.total_repeticoes)) * 100)
        })
        self.label_recorde.text = self.obter_resumo_historico()

    def pausar(self, instance):
        if not hasattr(self, "previous_state"):
            self.previous_state = self.estado
            self.previous_label = self.label_status.text
        if self.estado == "paused":
            self.estado = self.previous_state
            self.botao_pausar.text = "Pausar"
            self.label_status.text = self.previous_label
            self.label_status.color = self.cor_texto
            self.label_numero.color = self.cor_texto
            if self.relogio is None and self.estado == "preparacao":
                self.relogio = Clock.schedule_interval(self.contagem_preparar, 1)
            elif self.relogio is None and self.estado == "treino":
                self.relogio = Clock.schedule_interval(self.contagem_repeticao, 1)
            elif self.relogio is None and self.estado == "descanso":
                self.relogio = Clock.schedule_interval(self.contagem_descanso, 1)
        else:
            self.previous_state = self.estado
            self.previous_label = self.label_status.text
            self.estado = "paused"
            self.botao_pausar.text = "Continuar"
            if self.relogio:
                self.relogio.cancel()
                self.relogio = None
            self.label_status.text = "Pausado"
            self.label_status.color = (1, 0, 0, 1)
            self.label_numero.color = (1, 0, 0, 1)

  
    def voltar_repeticao(self, instance):
        if self.estado in ["treino", "descanso"] and self.total_completed > 1:
            if self.repeticao_atual > 1:
                self.repeticao_atual -= 1
            elif self.serie_atual > 1:
                self.serie_atual -= 1
                self.repeticao_atual = self.total_repeticoes - 1
            self.atualizar_labels_treino()
            self.label_numero.text = str(self.repeticao_atual)
            self.atualizar_progresso()

    def ajustar_descanso(self, delta):
        if self.estado == "descanso":
            self.contador = max(0, self.contador + delta)
            self.tempo_descanso = max(1, self.tempo_descanso + delta)
            self.label_numero.text = str(self.contador)
            self.label_status.text = f"Descanso ({self.contador}s)"

    def voltar_preparar(self, instance):
        layout = BoxLayout(orientation="vertical", padding=20, spacing=15)
        texto = Label(text="Deseja realmente sair do treino?", font_size=18)
        linha = BoxLayout(spacing=10, size_hint_y=None, height=50)
        botao_sim = self.criar_botao("Sim", cor_fundo=self.cor_destaque_ativo, font_size=16)
        botao_nao = self.criar_botao("Não", font_size=16)
        linha.add_widget(botao_sim)
        linha.add_widget(botao_nao)
        layout.add_widget(texto)
        layout.add_widget(linha)
        popup = Popup(title="Confirmação", content=layout, size_hint=(0.8, 0.35), auto_dismiss=False)
        botao_nao.bind(on_press=popup.dismiss)
        botao_sim.bind(on_press=lambda x: self.sair_treino(popup))
        popup.open()

    def sair_treino(self, popup):
        popup.dismiss()
        if hasattr(self, "relogio") and self.relogio:
            self.relogio.cancel()
            self.relogio = None
        if hasattr(self, "timer_total") and self.timer_total:
            self.timer_total.cancel()
            self.timer_total = None
        self.root.clear_widgets()
        self.root.add_widget(self.criar_tela_preparar())

    def reiniciar_serie(self, instance):
        if hasattr(self, "relogio") and self.relogio:
            self.relogio.cancel()
            self.relogio = None
        self.contador = 1
        self.repeticao_atual = 1
        self.label_status.text = "Reiniciando série"
        self.label_status.color = (0, 1, 0, 1)
        self.label_repeticao.text = f"Repetição: {self.repeticao_atual}/{self.total_repeticoes}"
        self.label_numero.text = str(self.repeticao_atual)
        self.relogio = Clock.schedule_interval(self.contagem_repeticao, 1)

    def verificar_campos(self, instance, value):
        series = self.input_series.text.strip() if hasattr(self, "input_series") else ""
        repeticao = self.input_repeticao.text.strip() if hasattr(self, "input_repeticao") else ""
        descanso = self.input_descanso.text.strip() if hasattr(self, "input_descanso") else ""
        preparacao = str(getattr(self, "preparacao_selecionada", "")).strip()

        if series and repeticao and descanso and preparacao:
            self.botao_iniciar.disabled = False
        else:
            self.botao_iniciar.disabled = True

    def mostrar_historico(self, instance):
        # Mostra o histórico de treinos em um popup
        texto = ""
        # Adiciona as últimas 8 entradas do histórico ao texto do popup
        for entry in reversed(self.history[-8:]):
            # Formata cada entrada do histórico com data, duração, séries, repetições e percentual concluído
            texto += f"{entry['date']} - {self.formatar_tempo(entry['duration'])} | {entry['series']}s x {entry['repeticoes']}r | {entry['percentual']}%\n"
        # Se não houver histórico, exibe uma mensagem padrão
        if not texto:
            texto = "Nenhum treino registrado ainda."

        label = Label(text=texto, font_size=16, color=self.cor_texto)
        self.label_hist_popup = label
        # Adiciona botao para "limpar o histórico" e fechar o popup
        botao_limpar = self.criar_botao("Limpar Histórico", size_hint_y=None, height=50)
        # Associa a função de limpar histórico ao botão "Limpar Histórico" 
        botao_limpar.bind(on_press=self.limpa_historico_popup)
        # Associa a função de fechar o popup ao botão "Fechar"
        botao_ok = self.criar_botao("Fechar", cor_fundo=self.cor_destaque_ativo, size_hint_y=None, height=50)
        layout = BoxLayout(orientation="vertical", spacing=15, padding=20)
        layout.add_widget(label) # Adiciona o label com o histórico ao layout do popup
        layout.add_widget(botao_limpar) # Adiciona o botão de limpar histórico ao layout do popup
        layout.add_widget(botao_ok) # Adiciona o botão de fechar ao layout do popup
        # Cria o popup com o título, conteúdo e tamanho especificados
        popup = Popup(title="Historico De Treinos", content=layout, size_hint=(0.9, 0.9))
        # Associa a função de fechar o popup ao botão "Fechar"
        botao_ok.bind(on_press=popup.dismiss)
        popup.open()


MeuApp().run()
