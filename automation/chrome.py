import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

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
        time.sleep(7) 

        try:
            time.sleep(6) # Tempo para o WhatsApp carregar completamente
            print(f"Buscando pela conversa: '{chat_name}'...")
            search_box_xpath = '//*[@id="pane-side"]/div/div/div/div[1]/div/div'
            search_box = self.driver.find_element(By.XPATH, search_box_xpath)
            
            search_box.click()
           
            time.sleep(3) # Tempo para o WhatsApp filtrar
            
            search_box.send_keys(Keys.HOME)
            print(f"Sucesso! Conversa '{chat_name}' aberta.")

            body = self.driver.find_element(By.TAG_NAME, "body")
            body.click()
            
            for i in range(80):
                body.send_keys(Keys.HOME)
                time.sleep(1)

        
        except Exception as e:
            print(f"Não consegui abrir a conversa. Erro: {e}")

if __name__ == "__main__":
    bot = ChromeAutomation()
    # Roda a automação
    bot.open_chrome().search_and_open_chat("Peças vistoriadas")
    
    # Deixa aberto para você ver funcionando
    print("O robô terminou. Mantendo o navegador aberto por mais 1 minuto...")
    time.sleep(60)

