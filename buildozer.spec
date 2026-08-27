[app]

# (str) Título do app, como vai aparecer no celular
title = Treino Rápido

# (str) Nome do pacote (sem espaços/acentos)
package.name = treinorapido

# (str) Domínio do pacote (padrão Android: com.seudominio.nomeapp)
package.domain = org.treinorapido

# (str) Diretório com o código-fonte
source.dir = .

# (list) Extensões de arquivo que devem ser incluídas no pacote
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,ttf

# (list) Padrões de arquivo/pasta extras a incluir (a pasta de sons, por exemplo)
source.include_patterns = sons/*

# (str) Versão do app
version = 1.0

# (list) Dependências do app.
# plyer é usado para a vibração; sem ele, o botão de vibração fica desabilitado.
requirements = python3,kivy,plyer

# (str) Orientação da tela
orientation = portrait

# (bool) Tela cheia
fullscreen = 0

# (list) Permissões do Android que o app precisa
android.permissions = VIBRATE

# (int) API alvo do Android (versão do Android que o app vai rodar melhor)
android.api = 33

# (int) API mínima suportada (Android 5.0+)
android.minapi = 21

# (str) Versão do NDK usada para compilar
android.ndk = 25b

# (list) Arquiteturas de processador incluídas no APK
android.archs = arm64-v8a, armeabi-v7a

# (bool) Aceita automaticamente as licenças do Android SDK na primeira execução
android.accept_sdk_license = True

# (str) Ícone do app (opcional -- descomente e aponte para um .png 512x512 se tiver um)
# icon.filename = %(source.dir)s/icon.png

[buildozer]

# (int) Nível de detalhe do log (0 = silencioso, 1 = normal, 2 = detalhado/debug)
log_level = 2

# (int) Mostra aviso se rodar como root (deixe 1 para evitar bloqueio em alguns ambientes)
warn_on_root = 1
