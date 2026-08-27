import os
import re
import json
import zipfile
import shutil
import requests
from pathlib import Path



# Pasta onde este arquivo .py está
PASTA_PROJETO = Path(__file__).resolve().parent

PASTA_MAE = PASTA_PROJETO.parent


PASTA_MENSAGENS = PASTA_MAE / "mensagens"

# Webhook do n8n
WEBHOOK_N8N = ""




def encontrar_zip():


    if not PASTA_MENSAGENS.exists():

        print()
        print("ERRO: A pasta 'mensagens' não existe:")
        print(PASTA_MENSAGENS)
        print()

        print("Crie a pasta:")
        print(PASTA_MENSAGENS)

        return None

    # Procura somente arquivos ZIP dentro da pasta mensagens
    arquivos_zip = [
        arquivo
        for arquivo in PASTA_MENSAGENS.glob("*.zip")
        if arquivo.is_file()
    ]

    if not arquivos_zip:

        print()
        print(
            "ERRO: Não encontrei nenhum arquivo .zip "
            "na pasta:"
        )

        print(PASTA_MENSAGENS)

        print()
        print(
            "Coloque a exportação do WhatsApp "
            "dentro dessa pasta."
        )

        return None

    print()
    print("Arquivos ZIP encontrados:")

    for arquivo in arquivos_zip:
        print(f" - {arquivo.name}")

    # Se houver vários ZIPs,
    # utiliza o mais recente
    arquivo_zip = max(
        arquivos_zip,
        key=lambda arquivo: arquivo.stat().st_mtime
    )

    print()
    print(
        f"Usando o ZIP mais recente: "
        f"{arquivo_zip.name}"
    )

    print(
        f"Caminho completo: "
        f"{arquivo_zip}"
    )

    return arquivo_zip

def extrair_zip(arquivo_zip):

 

    pasta_temp = PASTA_MENSAGENS / "extraido"

    # Se já existir uma extração anterior,
    # remove para evitar misturar arquivos antigos
    if pasta_temp.exists():

        print()
        print("Removendo extração anterior...")

        shutil.rmtree(
            pasta_temp,
            ignore_errors=True
        )

    pasta_temp.mkdir(
        parents=True,
        exist_ok=True
    )

    try:

        # Verifica se realmente é um ZIP
        if not zipfile.is_zipfile(arquivo_zip):

            print()
            print(
                "ERRO: O arquivo encontrado "
                "não é um ZIP válido:"
            )

            print(arquivo_zip)

            shutil.rmtree(
                pasta_temp,
                ignore_errors=True
            )

            return None

        print()
        print("Extraindo ZIP...")

        with zipfile.ZipFile(
            arquivo_zip,
            "r"
        ) as zip_ref:

            zip_ref.extractall(
                pasta_temp
            )

        print(
            f"Extração concluída: "
            f"{pasta_temp}"
        )

        return pasta_temp

    except Exception as e:

        print()
        print(
            f"Erro ao extrair ZIP: {e}"
        )

        shutil.rmtree(
            pasta_temp,
            ignore_errors=True
        )

        return None


# ============================================================
# ENCONTRAR _CHAT.TXT
# ============================================================

def encontrar_chat_txt(pasta):

    """
    Procura o arquivo _chat.txt dentro
    dos arquivos extraídos.
    """

    arquivos_chat = list(
        pasta.rglob("_chat.txt")
    )

    if not arquivos_chat:

        print()
        print(
            "ERRO: Não encontrei o arquivo "
            "_chat.txt."
        )

        return None

    arquivo_chat = arquivos_chat[0]

    print()
    print(
        f"_chat.txt encontrado: "
        f"{arquivo_chat}"
    )

    return arquivo_chat


# ============================================================
# LER CHAT
# ============================================================

def ler_chat(arquivo_chat):

    """
    Lê o arquivo de conversa do WhatsApp.
    """

    # Tenta UTF-8 primeiro
    try:

        with open(
            arquivo_chat,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return arquivo.read()

    except UnicodeDecodeError:

        print(
            "UTF-8 falhou. Tentando UTF-8-SIG..."
        )

        with open(
            arquivo_chat,
            "r",
            encoding="utf-8-sig"
        ) as arquivo:

            return arquivo.read()


# ============================================================
# LOCALIZAR IMAGENS
# ============================================================

def encontrar_imagens(pasta):

    """
    Encontra todas as imagens da exportação.
    """

    extensoes = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".heic"
    }

    imagens = []

    for arquivo in pasta.rglob("*"):

        if not arquivo.is_file():
            continue

        if arquivo.suffix.lower() in extensoes:

            imagens.append(arquivo)

    print()
    print(
        f"Imagens encontradas: "
        f"{len(imagens)}"
    )

    return imagens


# ============================================================
# EXTRAIR CÓDIGO
# ============================================================

def extrair_codigo(texto):

    """
    Tenta encontrar o código da peça
    na legenda da mensagem.

    Exemplo:

    Switch 250vac
    16273517
    03unidades
    """

    linhas = [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    for linha in linhas:

        # Procura uma linha formada principalmente
        # por números
        if re.fullmatch(
            r"\d{4,}",
            linha
        ):

            return linha

    # Segunda tentativa:
    # procura qualquer sequência numérica
    encontrados = re.findall(
        r"\b\d{4,}\b",
        texto
    )

    if encontrados:

        return encontrados[0]

    return None


# ============================================================
# EXTRAIR QUANTIDADE
# ============================================================

def extrair_quantidade(texto):

    """
    Procura algo como:

    03unidades
    3 unidades
    10 unidades
    """

    padroes = [
        r"(\d+)\s*unidades?",
        r"(\d+)\s*unid",
        r"(\d+)\s*peças?",
    ]

    for padrao in padroes:

        resultado = re.search(
            padrao,
            texto,
            re.IGNORECASE
        )

        if resultado:

            return int(
                resultado.group(1)
            )

    return None


# ============================================================
# IDENTIFICAR ANEXO
# ============================================================

def extrair_nome_anexo(texto):

    """
    Procura no _chat.txt algo como:

    <anexado: 00000002-PHOTO-2026-08-24-08-29-59.jpg>

    Retorna somente o nome do arquivo.
    """

    padrao = (
        r"<anexado:\s*([^>]+)>"
    )

    resultado = re.search(
        padrao,
        texto,
        re.IGNORECASE
    )

    if resultado:

        return resultado.group(1).strip()

    return None


# ============================================================
# SEPARAR MENSAGENS
# ============================================================

def separar_mensagens(texto):

    """
    Separa o _chat.txt em mensagens.

    O WhatsApp normalmente usa:

    [24/08/2026, 08:29:59] Nome: mensagem
    """

    padrao = re.compile(
        r"(?=\[\d{2}/\d{2}/\d{4},\s*\d{2}:\d{2}:\d{2}\])"
    )

    blocos = padrao.split(texto)

    mensagens = []

    for bloco in blocos:

        bloco = bloco.strip()

        if not bloco:
            continue

        if not bloco.startswith("["):
            continue

        mensagens.append(bloco)

    print()
    print(
        f"Mensagens identificadas: "
        f"{len(mensagens)}"
    )

    return mensagens


# ============================================================
# PROCESSAR MENSAGENS
# ============================================================

def processar_mensagens(
    texto_chat,
    imagens
):

    """
    Relaciona a mensagem do WhatsApp
    com a imagem anexada.
    """

    mensagens = separar_mensagens(
        texto_chat
    )

    # Cria um índice pelo nome do arquivo
    imagens_por_nome = {}

    for imagem in imagens:

        imagens_por_nome[
            imagem.name
        ] = imagem

    resultados = []

    for mensagem in mensagens:

        nome_anexo = (
            extrair_nome_anexo(
                mensagem
            )
        )

        if not nome_anexo:
            continue

        imagem = imagens_por_nome.get(
            nome_anexo
        )

        if not imagem:

            # Tenta encontrar ignorando
            # diferenças de maiúsculas/minúsculas
            for nome, caminho in (
                imagens_por_nome.items()
            ):

                if nome.lower() == nome_anexo.lower():

                    imagem = caminho
                    break

        if not imagem:

            print()
            print(
                "Imagem não encontrada:"
            )

            print(nome_anexo)

            continue

        codigo = extrair_codigo(
            mensagem
        )

        quantidade = extrair_quantidade(
            mensagem
        )

        # Remove a parte do anexo da legenda
        legenda = re.sub(
            r"<anexado:\s*[^>]+>",
            "",
            mensagem,
            flags=re.IGNORECASE
        ).strip()

        dados = {
            "codigo": codigo,
            "quantidade": quantidade,
            "legenda": legenda,
            "nome_imagem": imagem.name,
            "caminho_imagem": str(imagem)
        }

        resultados.append(
            {
                "imagem": imagem,
                "dados": dados
            }
        )

        print()
        print("=" * 60)
        print("MATERIAL ENCONTRADO")
        print("=" * 60)

        print(
            f"Imagem: {imagem.name}"
        )

        print(
            f"Código: {codigo}"
        )

        print(
            f"Quantidade: {quantidade}"
        )

        print(
            f"Legenda:\n{legenda}"
        )

    print()
    print(
        f"Materiais encontrados: "
        f"{len(resultados)}"
    )

    return resultados


# ============================================================
# TIPO MIME
# ============================================================

def obter_mime_type(imagem):

    extensao = imagem.suffix.lower()

    tipos = {

        ".jpg": "image/jpeg",

        ".jpeg": "image/jpeg",

        ".png": "image/png",

        ".webp": "image/webp",

        ".gif": "image/gif",

        ".heic": "image/heic",

    }

    return tipos.get(
        extensao,
        "application/octet-stream"
    )


# ============================================================
# ENVIAR PARA N8N
# ============================================================

def enviar_para_n8n(
    imagem,
    dados
):

    """
    Envia a imagem e os dados da mensagem
    para o webhook do n8n.

    A imagem vai como multipart/form-data.

    Os dados vão como JSON.
    """

    print()
    print(
        f"Enviando para n8n: "
        f"{imagem.name}"
    )

    try:

        with open(
            imagem,
            "rb"
        ) as arquivo:

            resposta = requests.post(

                WEBHOOK_N8N,

                files={
                    "imagem": (
                        imagem.name,
                        arquivo,
                        obter_mime_type(
                            imagem
                        )
                    )
                },

                data={
                    "dados": json.dumps(
                        dados,
                        ensure_ascii=False
                    )
                },

                timeout=60
            )

        print(
            f"Status n8n: "
            f"{resposta.status_code}"
        )

        print(
            f"Resposta n8n: "
            f"{resposta.text}"
        )

        return resposta.ok

    except Exception as e:

        print()
        print(
            f"Erro ao enviar para n8n: "
            f"{e}"
        )

        return False


# ============================================================
# SALVAR JSON LOCAL
# ============================================================

def salvar_json(resultados):

    """
    Salva uma cópia dos dados processados
    para facilitar testes.
    """

    arquivo_json = (
        PASTA_MENSAGENS /
        "resultado.json"
    )

    dados_json = []

    for item in resultados:

        dados_json.append(
            item["dados"]
        )

    with open(
        arquivo_json,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            dados_json,
            arquivo,
            ensure_ascii=False,
            indent=4
        )

    print()
    print(
        f"JSON salvo em: "
        f"{arquivo_json}"
    )


# ============================================================
# PROCESSADOR PRINCIPAL
# ============================================================

def processar():

    print()
    print("=" * 60)
    print("PROCESSADOR DE MENSAGENS WHATSAPP")
    print("=" * 60)

    print()
    print(
        f"Pasta do projeto: "
        f"{PASTA_PROJETO}"
    )

    print(
        f"Pasta mãe: "
        f"{PASTA_MAE}"
    )

    print(
        f"Pasta das mensagens: "
        f"{PASTA_MENSAGENS}"
    )

    # --------------------------------------------------------
    # 1. Encontrar ZIP
    # --------------------------------------------------------

    arquivo_zip = encontrar_zip()

    if arquivo_zip is None:
        return

    # --------------------------------------------------------
    # 2. Extrair ZIP
    # --------------------------------------------------------

    pasta_temp = extrair_zip(
        arquivo_zip
    )

    if pasta_temp is None:
        return

    # --------------------------------------------------------
    # 3. Encontrar _chat.txt
    # --------------------------------------------------------

    arquivo_chat = encontrar_chat_txt(
        pasta_temp
    )

    if arquivo_chat is None:
        return

    # --------------------------------------------------------
    # 4. Ler conversa
    # --------------------------------------------------------

    texto_chat = ler_chat(
        arquivo_chat
    )

    print()
    print(
        f"Tamanho do chat: "
        f"{len(texto_chat)} caracteres"
    )

    # --------------------------------------------------------
    # 5. Encontrar imagens
    # --------------------------------------------------------

    imagens = encontrar_imagens(
        pasta_temp
    )

    if not imagens:

        print()
        print(
            "Nenhuma imagem encontrada."
        )

        return

    # --------------------------------------------------------
    # 6. Relacionar mensagens e imagens
    # --------------------------------------------------------

    resultados = processar_mensagens(
        texto_chat,
        imagens
    )

    if not resultados:

        print()
        print(
            "Nenhum material com imagem "
            "e legenda foi encontrado."
        )

        return

    # --------------------------------------------------------
    # 7. Salvar JSON local
    # --------------------------------------------------------

    salvar_json(
        resultados
    )

    # --------------------------------------------------------
    # 8. Enviar cada material para o n8n
    # --------------------------------------------------------

    enviados = 0

    print()
    print("=" * 60)
    print("ENVIANDO PARA O N8N")
    print("=" * 60)

    for item in resultados:

        sucesso = enviar_para_n8n(

            item["imagem"],

            item["dados"]

        )

        if sucesso:

            enviados += 1

    # --------------------------------------------------------
    # 9. Resultado
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("PROCESSAMENTO FINALIZADO")
    print("=" * 60)

    print(
        f"Materiais encontrados: "
        f"{len(resultados)}"
    )

    print(
        f"Materiais enviados ao n8n: "
        f"{enviados}"
    )

    print()
    print(
        "Arquivos temporários removidos."
    )

    # Remove a pasta extraída
    shutil.rmtree(
        pasta_temp,
        ignore_errors=True
    )


# ============================================================
# EXECUTAR
# ============================================================

if __name__ == "__main__":

    processar()