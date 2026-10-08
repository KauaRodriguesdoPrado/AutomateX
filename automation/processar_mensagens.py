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

'''A pasta do whatsapp deve estar dentro da pasta de mensagens e esta deve estar dentro da pasta python ao lado da pasta automation'''
PASTA_MENSAGENS = PASTA_MAE / "mensagens"

# Webhook
'''Eu deveria colocar essa parte da API dentro do gitignore, porem só vou rodar localmente '''
'''Lembrar de tirar a chave de acesso quando for dar commit '''
WEBHOOK_N8N= ""

# Defina aqui o código de peça de corte estrito (ex: "10405538" ou "11466222-00"). 
# O script só vai processar as mensagens que vierem DEPOIS deste código.
# Deixe em branco "" se quiser processar o chat inteiro.
CODIGO_CORTE_FILTRO = "10405538"




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
    Procura o arquivo de texto do chat dentro dos arquivos extraídos.
    """

    arquivos_chat = list(
        pasta.rglob("*.txt")
    )

    if not arquivos_chat:

        print()
        print(
            "ERRO: Não encontrei o arquivo de texto do chat."
        )

        return None

    arquivo_chat = arquivos_chat[0]

    print()
    print(
        f"Arquivo de chat encontrado: "
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
    Encontra todas as imagens da exportação e ordena alfabeticamente 
    para manter a sequência correta do chat.
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

    imagens.sort(key=lambda x: x.name)

    print()
    print(
        f"Imagens encontradas: "
        f"{len(imagens)}"
    )

    return imagens


# ============================================================
# IDENTIFICAR ANEXO (NOME DA IMAGEM NO TEXTO)
# ============================================================

def extrair_nome_anexo(texto):
    padrao = r"<anexado:\s*([^>]+)>"
    resultado = re.search(padrao, texto, re.IGNORECASE)
    if resultado:
        return resultado.group(1).strip()
    return None


# ============================================================
# EXTRAIR CÓDIGO BLINDADO (EXATAMENTE 8 DÍGITOS OU COM -00)
# ============================================================

def extrair_codigo(texto):
    """
    Extrai apenas códigos válidos:
    - Exatamente 8 dígitos (ex: 11868231)
    - Ou formato com -00 (ex: 11466222-00)
    Ignora rigorosamente números menores, anos (2026) e códigos inválidos.
    """
    match_com_zero = re.search(r"\b(\d{7,8}-00)\b", texto)
    if match_com_zero:
        return match_com_zero.group(1)

    matches_oito = re.findall(r"\b(\d{8})\b", texto)
    for m in matches_oito:
        if not m.startswith("20") and not m.startswith("00"):
            return m

    return ""


# ============================================================
# EXTRAIR QUANTIDADE
# ============================================================

def extrair_quantidade(texto):
    padroes = [
        r"(\d+)\s*unidades?",
        r"(\d+)\s*unid",
        r"(\d+)\s*peças?",
    ]
    for padrao in padroes:
        resultado = re.search(padrao, texto, re.IGNORECASE)
        if resultado:
            return int(resultado.group(1))
    return None


# ============================================================
# EXTRAIR NOME DA PEÇA E CÓDIGO DA MESMA LINHA
# ============================================================

def extrair_dados_mensagem(mensagem_texto, codigo_encontrado):
    texto_limpo = re.sub(r"^\[\d{2}/\d{2}/\d{4},\s*\d{2}:\d{2}:\d{2}\]\s*[^:]+:\s*", "", mensagem_texto)
    texto_limpo = re.sub(r"<anexado:[^>]+>", "", texto_limpo, flags=re.IGNORECASE)
    texto_limpo = re.sub(r"\d+\s*(unidades?|unid|peças?)", "", texto_limpo, flags=re.IGNORECASE)

    if codigo_encontrado:
        texto_limpo = texto_limpo.replace(str(codigo_encontrado), "")

    nome_peca = " ".join(texto_limpo.split()).strip()
    return nome_peca


# SEPARAR MENSAGENS DO CHAT

def separar_mensagens(texto):
    padrao = re.compile(r"(?=\[\d{2}/\d{2}/\d{4},\s*\d{2}:\d{2}:\d{2}\])")
    blocos = padrao.split(texto)
    mensagens = []

    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco or not bloco.startswith("["):
            continue
        mensagens.append(bloco)

    return mensagens


# PROCESSAR MENSAGENS COM FILTRO DE CORTE E VALIDAÇÃO DE REGRAS

def processar_mensagens(
    texto_chat,
    imagens,
    codigo_corte
):
    mensagens = separar_mensagens(texto_chat)
    
    imagens_por_nome = {img.name: img for img in imagens}
    lista_imagens_ordenadas = sorted(imagens, key=lambda x: x.name)
    indice_fallback = 0

    resultados = []
    corte_limpo = str(codigo_corte).strip() if codigo_corte else ""
    processando_permitido = not bool(corte_limpo)

    for mensagem in mensagens:
        nome_anexo = extrair_nome_anexo(mensagem)
        
        # Identifica a imagem correspondente (por nome exato ou ordem sequencial)
        imagem_atual = None
        if nome_anexo and nome_anexo in imagens_por_nome:
            imagem_atual = imagens_por_nome[nome_anexo]
        else:
            if indice_fallback < len(lista_imagens_ordenadas):
                imagem_atual = lista_imagens_ordenadas[indice_fallback]
                indice_fallback += 1

        codigo = extrair_codigo(mensagem)

        # ========================================================
        # REGRA DE VALIDAÇÃO:
        #  Se vier sem imagem IGNORA
        #  Se vier sem código válido IGNORA
        #  Se vier somente nome e foto (sem código) IGNORA
        # ========================================================
        if not imagem_atual or not codigo:
            continue

        # Filtro de corte por código: só processa mensagens DEPOIS do código de corte
        if not processando_permitido:
            if corte_limpo in str(codigo):
                processando_permitido = True
                print(f"Código de corte {corte_limpo} encontrado! Processando itens posteriores...")
            continue # Pula tudo o que vier antes ou o próprio código de corte

        nome_peca = extrair_dados_mensagem(mensagem, codigo)
        quantidade = extrair_quantidade(mensagem)

        dados = {
            "codigo": codigo,
            "nome_peca": nome_peca if nome_peca else "",
            "quantidade": quantidade,
            "legenda": mensagem.strip(),
            "nome_imagem": imagem_atual.name,
            "caminho_imagem": str(imagem_atual)
        }

        resultados.append(
            {
                "imagem": imagem_atual,
                "dados": dados
            }
        )

        print()
        print("=" * 60)
        print("MATERIAL ENCONTRADO E APROVADO")
        print("=" * 60)
        print(f"Imagem: {imagem_atual.name}")
        print(f"Nome da Peça: {nome_peca or '(Não informado)'}")
        print(f"Código: {codigo}")
        print(f"Quantidade: {quantidade}")

    print()
    print(
        f"Materiais válidos encontrados após o corte: "
        f"{len(resultados)}"
    )

    return resultados



# TIPO MIME

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



# ENVIAR PARA ACTIVEPIECES

def enviar_para_n8n(
    imagem,
    dados
):

    print()
    print(
        f"Enviando para Activepieces: "
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
                    "codigo": str(dados.get("codigo")) if dados.get("codigo") else "",
                    "nome_peca": str(dados.get("nome_peca")) if dados.get("nome_peca") else "",
                    "quantidade": str(dados.get("quantidade")) if dados.get("quantidade") else "",
                    "legenda": str(dados.get("legenda")) if dados.get("legenda") else "",
                    "nome_imagem": str(dados.get("nome_imagem")) if dados.get("nome_imagem") else ""
                },

                timeout=60
            )

        print(
            f"Status Activepieces: "
            f"{resposta.status_code}"
        )

        print(
            f"Resposta Activepieces: "
            f"{resposta.text}"
        )

        return resposta.ok

    except Exception as e:

        print()
        print(
            f"Erro ao enviar para Activepieces: "
            f"{e}"
        )

        return False


# SALVAR JSON LOCAL

def salvar_json(resultados):

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

def processar():

    print()
    print("=" * 60)
    print("PROCESSADOR DE MENSAGENS WHATSAPP")
    print("=" * 60)

    # 1. Encontrar ZIP
    arquivo_zip = encontrar_zip()

    if arquivo_zip is None:
        return

    # 2. Extrair ZIP
    pasta_temp = extrair_zip(
        arquivo_zip
    )

    if pasta_temp is None:
        return

    # 3. Encontrar arquivo de chat
    arquivo_chat = encontrar_chat_txt(
        pasta_temp
    )

    if arquivo_chat is None:
        return

    # 4. Ler conversa
    texto_chat = ler_chat(
        arquivo_chat
    )

    print()
    print(
        f"Tamanho do chat: "
        f"{len(texto_chat)} caracteres"
    )

    # 5. Encontrar imagens
    imagens = encontrar_imagens(
        pasta_temp
    )

    if not imagens:

        print(
            "Nenhuma imagem encontrada."
        )

        return

    # 6. Relacionar mensagens e imagens com as regras aplicadas
    resultados = processar_mensagens(
        texto_chat,
        imagens,
        CODIGO_CORTE_FILTRO
    )

    if not resultados:

        print(
            "Nenhum material válido foi encontrado após o código de corte."
        )

        return

    # 7. Salvar JSON local
    salvar_json(
        resultados
    )

    # 8. Enviar cada material para o Activepieces
    enviados = 0

    print()
    print("=" * 60)
    print("ENVIANDO PARA O ACTIVEPIECES")
    print("=" * 60)

    for item in resultados:

        sucesso = enviar_para_n8n(

            item["imagem"],

            item["dados"]

        )

        if sucesso:

            enviados += 1

    # 9. Resultado
    print()
    print("=" * 60)
    print("PROCESSAMENTO FINALIZADO")
    print("=" * 60)

    print(
        f"Materiais encontrados: "
        f"{len(resultados)}"
    )

    print(
        f"Materiais enviados ao Activepieces: "
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