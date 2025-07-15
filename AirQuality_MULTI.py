#Air Quality Sensor InovLabs

from machine import Pin, I2C
import ENS160
import urequests
import network, time
import os
from iot_credentials import THINGSPEAK_WRITE_API_KEY, wifi_networks
import gc # Garbage Collect
from ds3231 import * # RTC Clock

#Verifica Library do sensor de Oxigénio:
try:
    from SEN0322 import DFRobot_Oxygen
except Exception as e:
    print("AVISO Sensor Oxigénio NAO DETETADO:", e)
    temOxiSens = False

else:
    temOxiSens = True
    print("Sensor Oxigénio DETETADO:")


#Verifica library  do OLED
try:
    from ssd1306 import SSD1306_I2C
except Exception as e:
    print("AVISO OLED NAO DETETADO:", e)
    temOled = False
else:
    temOled = True

# Acende o LED para indicar que o sistema está ligado
led = Pin("LED", Pin.OUT)
led.on()

#Configura RTC Clock
try:
    i2c_RTC = machine.I2C(id=0, sda=machine.Pin(4), scl=machine.Pin(5))
except Exception as e:
    print("ERRO NO RTC:", e)
else:
    time.sleep(0.5)
    RTC = DS3231(i2c_RTC)
    print("RTC OK")
    # Print the current date in the format: month/day/year
    print( "Date={}/{}/{}" .format(RTC.get_time()[1], RTC.get_time()[2],RTC.get_time()[0]) )
    # Print the current time in the format: hours:minutes:seconds
    print( "Time={}:{}:{}" .format(RTC.get_time()[3], RTC.get_time()[4],RTC.get_time()[5]) )
   


# Setup OLED
if temOled:
    try:
        i2c = machine.I2C(id=0, sda=machine.Pin(16), scl=machine.Pin(17))
        oled = SSD1306_I2C(128, 64, i2c)
        oled.text("INOVLABS", 0, 0)
        oled.text("AIR QUALITY", 0, 17)
        oled.text("SENSOR", 0, 26)
        oled.show()
    except Exception as e:
        print("Erro no OLED:", e)


# Função para piscar o LED n vezes
def blink_led(n):
    for _ in range(n):
        led.toggle()
        time.sleep(0.1)
    led.off()


# Criar um novo arquivo de log com nome único
log_number = 1
while True:
    log_file = f"log{log_number}.csv"
    try:
        os.stat(log_file)  # Verifica se o arquivo existe
        log_number += 1  # Se existir, tenta o próximo número
    except OSError:
        break  # Se não existir, usa esse nome de arquivo

# Pisca o LED para indicar que o log foi configurado
blink_led(2)

#Mensagem no Ecran
if temOled:
    oled.text("Log ok", 0, 40)
    oled.show()


# Função para registrar os dados no log
def log_data(aqi, tvoc, eco2, o2):
    timestamp = time.localtime()  # Obtém o tempo atual
    formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        timestamp[0], timestamp[1], timestamp[2], timestamp[3], timestamp[4], timestamp[5])

    with open(log_file, "a") as file:
        if temOxiSens:
            file.write(f"{formatted_time},{aqi},{tvoc},{eco2},{o2}\n")
        else:
            file.write(f"{formatted_time},{aqi},{tvoc},{eco2}\n")

# Criar cabeçalho do CSV se o arquivo ainda não existir
try:
    with open(log_file, "r") as file:
        pass  # Arquivo já existe
except OSError:
    with open(log_file, "w") as file: # Escreve o cabeçalho
        if temOxiSens:
            file.write("Timestamp,AQI,TVOC,eCO2,O2\n")
        else:
            file.write("Timestamp,AQI,TVOC,eCO2\n")


# Função para conectar a uma rede Wi-Fi disponível
def connect_wifi():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    time.sleep(1)  # Espera para garantir que a interface está pronta

    while not sta_if.isconnected():
        print("Procurando redes Wi-Fi disponíveis...")

        if temOled:
            oled.text("Procurando WIFI", 0, 49)
            oled.show()

        try:
            available_networks = [net[0].decode() for net in sta_if.scan()]
        except OSError as e:
            print("Erro ao procurar redes:", e)
            time.sleep(5)
            continue

        for ssid, password in wifi_networks:
            if ssid in available_networks:
                print(f"Tentando conectar a {ssid}...")
                sta_if.connect(ssid, password)

                for _ in range(10):
                    if sta_if.isconnected():
                        print(f"Conectado a {ssid}!")
                        print('Configuração de rede:', sta_if.ifconfig())
                        return sta_if
                    time.sleep(1)

        print("Nenhuma rede conhecida encontrada. Tentando novamente em 5 segundos...")
        blink_led(3)
        time.sleep(5)

    return sta_if


# Conectar à rede Wi-Fi (tenta até encontrar uma)
sta_if = connect_wifi()

# Pisca o LED para indicar conexão bem-sucedida
blink_led(2)


# Configurar os sensores:
try:
    i2c_sens = machine.I2C(id=1, sda=machine.Pin(10), scl=machine.Pin(11)) # Os sensores estão nos mesmo pins

except Exception as e:
    print("Erro nos PINS dos Sensores:", e)

# Configura Sensor Qualidade do Ar:
try:
    ens = ENS160.ENS160(i2c_sens) # ENS160
    ens.operating_mode = 2  # Ativa o modo de leitura do ENS160

except Exception as e:
    print("Erro na Configuração do sensor de qualidade do ar:", e)
else:
    time.sleep(2)  # Aguarda inicialização do sensor
    blink_led(2) # Pisca o LED para indicar que o sensor foi configurado

if temOxiSens:
    try:
        O2sensor = DFRobot_Oxygen(i2c_sens, addr=0x73) #Oxigénio
    except Exception as e:
        print("Erro na Configuração do sensor de Oxigénio:", e)
    else:
        blink_led(2) # Pisca o LED para indicar que o sensor foi configurado


# Loop principal: recebe e envia dados periodicamente
while True:
    if temOxiSens:
        try:
            oxygen_data = O2sensor.get_oxygen_data(10)
        except Exception as e:
            print("Erro na leitura do sensor Oxigenio:", e)
        else:
            print(f"O2={oxygen_data}")

    else:
        oxygen_data = 0

    try:
        ens_AQI = ens.AQI
        ens_TVOC = ens.TVOC
        ens_ECO2 = ens.ECO2
        status = ens.status
        validity_flag = status.get("VALIDITY FLAG", None)

    except Exception as e:
        print("Erro na leitura do sensor Qualidade Ar:", e)
    else:
        print(f"AQI Score: {ens_AQI['value']}")
        print(f"TVOC: {ens_TVOC} ppb")
        print(f"eCO2: {ens_ECO2} ppm")

        if validity_flag is not None:
            print(f"VALIDITY FLAG: {validity_flag}")

            if validity_flag == 0:
                print("AQ Status: Normal operation")
            elif validity_flag == 1:
                print("AQ Status: Warm-Up phase")
            elif validity_flag == 2:
                print("AQ Status: Initial Start-Up phase")
            elif validity_flag == 3:
                print("AQ Status: Invalid output")
        else:
            print("Could not read AQ VALIDITY FLAG")

        if temOled:
            oled.fill(0)
            oled.text(f"O2: {oxygen_data}", 3, 20)
            oled.text(f"AQI Score: {ens_AQI['value']}", 3, 30)
            oled.text(f"TVOC: {ens_TVOC} ppb", 3, 40)
            oled.text(f"eCO2: {ens_ECO2} ppm", 3, 50)
            oled.show()

            log_data(ens_AQI['value'], ens_TVOC, ens_ECO2, oxygen_data)

        if not sta_if.isconnected():
            print("Wi-Fi desconectado. Tentando reconectar...")
            sta_if = connect_wifi()

        if sta_if.isconnected():
            print("Wi-Fi ligado")
            if temOled:
                oled.rect(0, 16, 128, 48, 1)
                oled.text("WIFI OK", 0, 0)
                oled.show()

            try:
                url = 'https://api.thingspeak.com/update'
                payload = f"api_key={THINGSPEAK_WRITE_API_KEY}&field1={ens_AQI['value']}&field2={ens_TVOC}&field3={ens_ECO2}&field4={oxygen_data}"
                print("Enviando para ThingSpeak")
                #print (payload)

                if temOled:
                    oled.fill_rect(0, 0, 127, 9, 0)
                    oled.text("Enviando dados..", 0, 0)
                    oled.show()

                request = urequests.post(url + '?' + payload)
                request.close()

            except Exception as e:
                print("Erro ao enviar dados:", e)
                blink_led(4)
            else:
                print("Dados enviados com sucesso!")

                if temOled:
                    oled.fill_rect(0, 0, 127, 9, 0)
                    oled.text("Dados OK!", 0, 0)
                    oled.show()
                    oled.fill_rect(0, 0, 127, 9, 0)

                time.sleep(30)

    finally:
        blink_led(2)
        gc.collect()
        print(".......")


