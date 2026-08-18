# Divulgador de Produtos — Python + Android APK

Aplicativo que recebe um link de produto, tenta coletar:

- nome do produto
- preço
- link final
- imagem principal

Depois gera uma arte simples e abre o compartilhamento do Android para enviar a oferta ao WhatsApp.

## Importante sobre o WhatsApp

O aplicativo não consegue, de forma segura e oficial, entrar sozinho em um canal do WhatsApp e publicar sem interação do usuário usando apenas um APK comum.

O botão **COMPARTILHAR NO WHATSAPP** abre o compartilhamento do Android. A escolha do WhatsApp/canal é feita pelo usuário.

## Como testar no computador

Python 3.10/3.11 é recomendado.

```bash
pip install -r requirements.txt
python main.py
```

## Como gerar APK no Ubuntu/Linux

Instale dependências:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev cmake libffi-dev libssl-dev
python3 -m pip install --upgrade pip
python3 -m pip install buildozer cython
```

Entre na pasta:

```bash
cd divulgador_produtos
```

Gere o APK de teste:

```bash
buildozer -v android debug
```

O APK será criado na pasta `bin/`.

## GitHub Actions

Você também pode enviar esta pasta para o GitHub e usar GitHub Actions para gerar o APK sem instalar o ambiente Android no celular.

Um workflow de exemplo está em:

`.github/workflows/build-apk.yml`

## Limitações de sites

Algumas lojas bloqueiam robôs, exigem JavaScript, login ou carregam preço/imagem dinamicamente. Nesses casos, o aplicativo pode não conseguir extrair os dados.

A versão atual usa principalmente OpenGraph, metatags, JSON-LD e padrões de preço.

## Próximas melhorias

- escolher modelo da arte
- colocar logo da sua loja
- editar título/preço antes de compartilhar
- botão copiar texto
- histórico de produtos
- múltiplos links
- integração com uma API própria de scraping para sites mais difíceis
