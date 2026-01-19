import os
import sys
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLineEdit, QLabel, QFileDialog, QMessageBox, 
    QProgressBar, QTextEdit, QCheckBox, QGroupBox, QStackedWidget, QGridLayout
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
import resources_rc

# Configurações de Tags EXIF para extração de metadados de fotos
TAGS_EXIF_REVERSAS = {v: k for k, v in TAGS.items()}
TAG_DATA_HORA_ORIGINAL = TAGS_EXIF_REVERSAS.get('DateTimeOriginal')

class RenomeadorMidia(QWidget):
    def __init__(self):
        super().__init__()
        self.caminho_pasta_raiz = ""
        self.modo_operacao = "" # Pode ser 'pasta' ou 'manual'
        
        self.setWindowTitle("MediaRenamer Pro v3.0")
        self.setWindowIcon(QIcon(":/img/favicon.png"))
        self.setMinimumSize(900, 750)
        self.setStyleSheet(self.obter_estilo_moderno())
        
        # Gerenciador de telas (Stack)
        self.gerenciador_telas = QStackedWidget()
        self.configurar_interface()
        
        layout_principal = QVBoxLayout()
        layout_principal.addWidget(self.gerenciador_telas)
        
        # Rodapé de identificação
        rodape = QLabel("Desenvolvido por Daniel Boechat | Estudante de Engenharia de Software")
        rodape.setObjectName("estilo_rodape")
        rodape.setAlignment(Qt.AlignCenter)
        layout_principal.addWidget(rodape)
        
        self.setLayout(layout_principal)

    def obter_estilo_moderno(self):
        """Retorna o CSS para estilização da interface."""
        return """
            QWidget { background-color: #0F172A; color: #F1F5F9; font-family: 'Segoe UI'; }
            
            QPushButton#botao_tile {
                background-color: #1E293B;
                border: 2px solid #334155;
                border-radius: 15px;
                padding: 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#botao_tile:hover {
                background-color: #334155;
                border-color: #00ADB5;
            }
            
            QGroupBox { 
                border: 1px solid #334155; border-radius: 10px; margin-top: 20px; 
                padding-top: 15px; color: #00ADB5; font-weight: bold;
            }

            QLineEdit { 
                background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; 
                padding: 12px; color: #FFFFFF; font-size: 14px;
            }

            QProgressBar { border: none; background-color: #334155; height: 8px; border-radius: 4px; }
            QProgressBar::chunk { background-color: #00ADB5; }

            QTextEdit { background-color: #1E293B; border: 1px solid #334155; border-radius: 8px; color: #22C55E; font-family: 'Consolas'; }
            
            QLabel#titulo { font-size: 24px; font-weight: bold; color: #F8FAFC; margin-bottom: 10px; }
            QLabel#estilo_rodape { color: #64748B; font-size: 11px; padding: 10px; }
        """

    def configurar_interface(self):
        # --- TELA 1: MENU PRINCIPAL ---
        self.tela_inicio = QWidget()
        layout_inicio = QVBoxLayout(self.tela_inicio)
        layout_inicio.setAlignment(Qt.AlignCenter)
        
        titulo_inicio = QLabel("O que deseja fazer hoje?")
        titulo_inicio.setObjectName("titulo")
        layout_inicio.addWidget(titulo_inicio, alignment=Qt.AlignCenter)

        grid_opcoes = QGridLayout()
        grid_opcoes.setSpacing(20)

        self.btn_usar_pasta = QPushButton("📁\n\nRenomear usando\nnome da pasta pai")
        self.btn_usar_pasta.setObjectName("botao_tile")
        self.btn_usar_pasta.setFixedSize(300, 220)
        self.btn_usar_pasta.clicked.connect(lambda: self.navegar_para_configuracao("pasta"))

        self.btn_usar_manual = QPushButton("📸\n\nRenomear com\nnome personalizado")
        self.btn_usar_manual.setObjectName("botao_tile")
        self.btn_usar_manual.setFixedSize(300, 220)
        self.btn_usar_manual.clicked.connect(lambda: self.navegar_para_configuracao("manual"))

        grid_opcoes.addWidget(self.btn_usar_pasta, 0, 0)
        grid_opcoes.addWidget(self.btn_usar_manual, 0, 1)
        
        layout_inicio.addLayout(grid_opcoes)
        self.gerenciador_telas.addWidget(self.tela_inicio)

        # --- TELA 2: CONFIGURAÇÕES DE EXECUÇÃO ---
        self.tela_config = QWidget()
        layout_config = QVBoxLayout(self.tela_config)
        layout_config.setContentsMargins(40, 40, 40, 40)

        btn_voltar = QPushButton("← Voltar ao Menu")
        btn_voltar.setFixedWidth(150)
        btn_voltar.clicked.connect(lambda: self.gerenciador_telas.setCurrentIndex(0))
        layout_config.addWidget(btn_voltar)

        self.lbl_titulo_modo = QLabel("Configurações")
        self.lbl_titulo_modo.setObjectName("titulo")
        layout_config.addWidget(self.lbl_titulo_modo)

        # Seleção de tipos de arquivos (Tiles de filtros)
        grupo_filtros = QGroupBox("Tipos de arquivos para processar")
        layout_filtros = QHBoxLayout(grupo_filtros)
        self.selecao_fotos = QCheckBox("Fotos")
        self.selecao_videos = QCheckBox("Vídeos")
        self.selecao_audios = QCheckBox("Áudios")
        self.selecao_fotos.setChecked(True)
        layout_filtros.addWidget(self.selecao_fotos)
        layout_filtros.addWidget(self.selecao_videos)
        layout_filtros.addWidget(self.selecao_audios)
        layout_config.addWidget(grupo_filtros)

        # Inputs de diretório e nome
        self.btn_escolher_pasta = QPushButton("📍 Selecionar Pasta de Backup")
        self.btn_escolher_pasta.clicked.connect(self.abrir_seletor_diretorio)
        layout_config.addWidget(self.btn_escolher_pasta)

        self.entrada_nome_customizado = QLineEdit()
        self.entrada_nome_customizado.setPlaceholderText("Digite o nome base para os arquivos...")
        layout_config.addWidget(self.entrada_nome_customizado)

        self.btn_iniciar_processo = QPushButton("⚡ COMEÇAR AGORA")
        self.btn_iniciar_processo.setFixedHeight(60)
        self.btn_iniciar_processo.clicked.connect(self.iniciar_automacao)
        layout_config.addWidget(self.btn_iniciar_processo)

        self.barra_progresso = QProgressBar()
        layout_config.addWidget(self.barra_progresso)

        self.area_logs = QTextEdit()
        self.area_logs.setReadOnly(True)
        layout_config.addWidget(self.area_logs)

        self.gerenciador_telas.addWidget(self.tela_config)

    def navegar_para_configuracao(self, modo_escolhido):
        """Troca de tela e ajusta a visibilidade dos campos."""
        self.modo_operacao = modo_escolhido
        if modo_escolhido == "pasta":
            self.lbl_titulo_modo.setText("Modo: Identificação por Pasta Pai")
            self.entrada_nome_customizado.setVisible(False)
        else:
            self.lbl_titulo_modo.setText("Modo: Identificação Manual")
            self.entrada_nome_customizado.setVisible(True)
        
        self.gerenciador_telas.setCurrentIndex(1)

    def abrir_seletor_diretorio(self):
        caminho = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if caminho:
            self.caminho_pasta_raiz = caminho
            self.btn_escolher_pasta.setText(f"Diretório: {caminho}")

    def obter_data_do_arquivo(self, caminho_completo):
        """Extrai a data da foto (EXIF) ou a data do sistema para vídeos/áudios."""
        if caminho_completo.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                with Image.open(caminho_completo) as img:
                    info_exif = img._getexif()
                    if info_exif and TAG_DATA_HORA_ORIGINAL in info_exif:
                        return datetime.strptime(info_exif[TAG_DATA_HORA_ORIGINAL], '%Y:%m:%d %H:%M:%S')
            except: pass
        return datetime.fromtimestamp(os.path.getmtime(caminho_completo))

    def iniciar_automacao(self):
        """Função principal que percorre as pastas e renomeia os itens."""
        if not self.caminho_pasta_raiz:
            QMessageBox.warning(self, "Atenção", "Selecione uma pasta de origem.")
            return

        # Monta a lista de extensões permitidas com base nos checkboxes
        extensoes_permitidas = []
        if self.selecao_fotos.isChecked(): extensoes_permitidas.extend(['.jpg', '.jpeg', '.png', '.tiff'])
        if self.selecao_videos.isChecked(): extensoes_permitidas.extend(['.mp4', '.mov', '.avi', '.mkv'])
        if self.selecao_audios.isChecked(): extensoes_permitidas.extend(['.mp3', '.wav', '.flac', '.m4a'])

        lista_arquivos = []
        for raiz, _, arquivos in os.walk(self.caminho_pasta_raiz):
            for arquivo in arquivos:
                if any(arquivo.lower().endswith(ext) for ext in extensoes_permitidas):
                    lista_arquivos.append(os.path.join(raiz, arquivo))

        if not lista_arquivos:
            QMessageBox.information(self, "Aviso", "Nenhum arquivo compatível encontrado.")
            return

        self.btn_iniciar_processo.setEnabled(False)
        self.barra_progresso.setMaximum(len(lista_arquivos))
        
        contador_sucesso = 0
        for indice, caminho_antigo in enumerate(lista_arquivos):
            pasta_atual = os.path.dirname(caminho_antigo)
            extensao = os.path.splitext(caminho_antigo)[1]
            
            # Define o 'local' (nome do evento/local)
            if self.modo_operacao == "pasta":
                nome_pasta_pai = os.path.basename(pasta_atual)
                # Extrai apenas o que vem depois do " - "
                local = nome_pasta_pai.split(" - ", 1)[1] if " - " in nome_pasta_pai else nome_pasta_pai
            else:
                local = self.entrada_nome_customizado.text() or "Arquivo"

            data_objeto = self.obter_data_do_arquivo(caminho_antigo)
            data_formatada = data_objeto.strftime("%Y-%m-%d_H%H-%M")
            
            nome_base_novo = f"({data_formatada}) - {local}"
            nome_final = f"{nome_base_novo}{extensao}"
            caminho_novo = os.path.join(pasta_atual, nome_final)

            # Lógica para evitar nomes duplicados na mesma pasta
            ajuste = 1
            while os.path.exists(caminho_novo):
                nome_final = f"{nome_base_novo} ({ajuste}){extensao}"
                caminho_novo = os.path.join(pasta_atual, nome_final)
                ajuste += 1

            try:
                os.rename(caminho_antigo, caminho_novo)
                contador_sucesso += 1
                self.area_logs.append(f"SUCESSO: {nome_final}")
            except Exception as erro:
                self.area_logs.append(f"ERRO ao renomear {os.path.basename(caminho_antigo)}: {erro}")

            self.barra_progresso.setValue(indice + 1)
            QApplication.processEvents()

        self.btn_iniciar_processo.setEnabled(True)
        QMessageBox.information(self, "Concluído", f"Processo finalizado!\nItens renomeados: {contador_sucesso}")

if __name__ == '__main__':
    aplicativo = QApplication(sys.argv)
    janela = RenomeadorMidia()
    janela.show()
    sys.exit(aplicativo.exec_())