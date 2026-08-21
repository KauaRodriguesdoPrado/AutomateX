import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import shutil
import os

class ChromeAutomation:
    def __init__(self):
        
        # Caminho padrão do Chrome
        self.chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
       
        # Caminho para a pasta de perfil exclusiva do robô :
        self.user_data_dir = r"C:\PerfilRobo"
        self.driver = None

    def open_chrome(self):
        if not Path(self.chrome_path).exists():
            raise FileNotFoundError(f"Chrome não encontrado em: {self.chrome_path}")

        print("Configurando um ambiente limpo e exclusivo para o robô...")
        options = webdriver.ChromeOptions()
        options.binary_location = self.chrome_path
        
        # Vincula o navegador do robô à nova pasta
        options.add_argument(f"--user-data-dir={self.user_data_dir}")
        options.add_argument("--start-maximized")
        
        # Evita travamentos comuns de permissão
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            print("Iniciando o navegador...")
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=options)
            
            print("Abrindo o WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com")
            return self
            
        except Exception as e:
            print(f"\nErro ao abrir o navegador: {e}")
            raise e

    def search_and_open_chat(self, chat_name):
        if not self.driver:
            return

        # Como é a PRIMEIRA vez nesse perfil novo, você precisará escanear o QR Code.
        # Por isso, deixe 40 segundos para dar tempo de pegar o celular e escanear.
        print("\n[ATENÇÃO] Se for a primeira vez, escaneie o QR Code do WhatsApp na tela agora!")
        print("Aguardando o carregamento inicial...")
        time.sleep(10) 
        while True:

            try:
                time.sleep(5) # Tempo para o WhatsApp carregar completamente
                print(f"Buscando pela conversa: '{chat_name}'...")
            
                '''O WhatsApp Web tem uma estrutura dinâmica, então o XPath muda constantemente.'''
                search_box_xpath = '//*[@id="pane-side"]/div/div/div/div[1]/div/div/div/div[2]'
                search_box = self.driver.find_element(By.CSS_SELECTOR, '#pane-side > div > div > div > div:nth-child(1) > div > div > div > div.x78zum5.xdl72j9.xdt5ytf.x1iyjqo2.xl56j7k.xeuugli.x1n1b19v')
                search_box.click()
            
                time.sleep(6) # Tempo para o WhatsApp filtrar
                
                print(f"Sucesso! Conversa '{chat_name}' aberta.")
                
                
            except Exception as e:
                print(f"Não consegui abrir a conversa. Erro: {e}")


            try:
                #clica na lupa de busca dentro da conversa
                search = self.driver.find_element(By.CSS_SELECTOR,'#main > header > div.x1c4vz4f.x2lah0s.xdl72j9.xeuugli.x101abm8.x1s73dr8.xgog33f.xlese2p > div > div:nth-child(5) > span > div > button' )
                search.click()
                
                
                #pesquisa a primeira mensagem do chat (XPATH dinâmico, pode mudar)
                buttonsearch = self.driver.find_element(By.CSS_SELECTOR,'#app > div > div > div.x78zum5.xdt5ytf.x5yr21d > div > div.x9f619.x6ikm8r.x10wlt62.x17dzmu4.x1i1dayz.x2ipvbc.xjdofhw.x2ydcri.x1873f8k.x1ppzqlz.x1c4vz4f.x2lah0s.x1oy9qf3.x5hsz1j.x17dq4o0.x10e4vud.x1xz51pm.xupwc73.x1ma46kl.xx9c7w5.xssin3l.x13ug1e2.x1qwjhxz > span > div > div > div.x1280gxy.x1c4vz4f.x2lah0s.xdl72j9 > div > button')

                time.sleep(15)

                

            except Exception as e:
                print(f"Não consegui abrir a busca. Erro: {e}")



            #try:           
                # abre a imagem
                #imagens = self.driver.find_elements(By.CSS_SELECTOR,'img[src*="blob"]')
                #imagens[-1].click()
                #print("imagem aberta")
                #time.sleep(2)
            
           # except Exception as e:
               # print(f"Não consegui abrir a imagem. Erro: {e}")
            
            
            # faz o download do arquivo
            #download = self.driver.find_element(By.CSS_SELECTOR,'span[data-icon="download"]')
            #download.click()

if __name__ == "__main__":
    bot = ChromeAutomation()
    
    # Roda a automação
    bot.open_chrome().search_and_open_chat("Peças vistoriadas")
    
    # Deixa aberto para você ver funcionando
    print("O robô terminou. Mantendo o navegador aberto por mais 1 minuto...")
    time.sleep(200)
    