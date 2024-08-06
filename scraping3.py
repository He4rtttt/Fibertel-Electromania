import json
from time import sleep
from datetime import datetime
import schedule
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import boto3
import os

# Configura tus credenciales de usuario raíz (no recomendado para producción)
aws_access_key_id = 'aws_access_key_id'
aws_secret_access_key = 'aws_secret_access_key'
region_name = 'us-east-1'  # Cambia esto a tu región preferida

# Crea un cliente S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)

# Función para subir archivo a S3
def upload_file_to_s3(file_name, bucket, object_name=None):
    """Sube un archivo a un bucket de S3"""
    if object_name is None:
        object_name = file_name

    if not os.path.isfile(file_name):
        print(f"Error: El archivo {file_name} no se encuentra.")
        return False

    try:
        s3_client.upload_file(file_name, bucket, object_name)
        print(f"{file_name} se ha subido exitosamente a {bucket}/{object_name}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# Función para extraer datos
def extract_data(url):
    opts = Options()
    opts.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.implicitly_wait(10)
    
    driver.get(url)
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        
        while True:
            try:
                last_height = driver.execute_script("return document.body.scrollHeight")
                while True:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    sleep(2)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//a[@class="btn wd-load-more wd-products-load-more load-on-click"]'))
                )
                load_more_button.click()
                sleep(2)
            except Exception as e:
                print("No se encontró más el botón de 'Cargar Más Productos'. Todos los productos están cargados.")
                break
        
        sleep(5)
        
        productos = driver.find_elements(By.XPATH, '//div[contains(@class, "product-grid-item")]')
        productos_lista = []
        for producto in productos:
            try:
                nombre = producto.find_element(By.XPATH, './/h3/a').text
            except Exception as e:
                nombre = "Nombre no encontrado"
            
            try:
                precio = producto.find_element(By.XPATH, './/span[contains(@class, "woocommerce-Price-amount amount")]').text
            except Exception as e:
                precio = "Precio no encontrado"
            
            descuento_elements = producto.find_elements(By.XPATH, './/div[contains(@class, "product-labels labels-rounded")]/span[contains(@class, "onsale product-label")]')
            descuento = ', '.join([element.text for element in descuento_elements]) if descuento_elements else "No tiene descuento"
            
            disponible_elements = producto.find_elements(By.XPATH, './/div[contains(@class, "product-labels labels-rounded")]/span[contains(@class, "out-of-stock product-label")]')
            disponible = "No disponible" if disponible_elements else "Disponible"
            
            productos_lista.append({
                "nombre": nombre,
                "precio": precio,
                "descuento": descuento,
                "disponible": disponible
            })
        
        return productos_lista
    finally:
        driver.quit()

# Función para guardar los datos en un archivo JSON
def save_data(productos_lista, categoria, tipo):
    json_filename = f'{categoria}_{tipo}.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(productos_lista, f, ensure_ascii=False, indent=4)
    print(f"Datos guardados en {json_filename}")
    return json_filename

# URLs y categorías de productos
urls = [
    {'url': 'https://www.electromania.pe/productos/drones/', 'categoria': 'drones'}
    # Añadimo las demás URLs y categorías según sea necesario
    # {'url': 'https://www.electromania.pe/productos/placas-de-desarrollo/', 'categoria': 'placas_de_desarrollo'},
    # {'url': 'https://www.electromania.pe/productos/drones/', 'categoria': 'drones'},
    # {'url': 'https://www.electromania.pe/productos/impresoras-3d/', 'categoria': 'impresoras_3d'},
    # {'url': 'https://www.electromania.pe/productos/robotica/', 'categoria': 'robotica'},
    # {'url': 'https://www.electromania.pe/productos/semiconductores/', 'categoria': 'semiconductores'},
    # {'url': 'https://www.electromania.pe/productos/rcl/', 'categoria': 'rcl'},
    # {'url': 'https://www.electromania.pe/productos/pantallas/', 'categoria': 'pantallas'},
    # {'url': 'https://www.electromania.pe/productos/teclados/', 'categoria': 'teclados'},
    # {'url': 'https://www.electromania.pe/productos/adaptadores/', 'categoria': 'adaptadores'},
    # {'url': 'https://www.electromania.pe/productos/robotica/baterias/', 'categoria': 'baterias'},
    # {'url': 'https://www.electromania.pe/productos/cables/', 'categoria': 'cables'},
    # {'url': 'https://www.electromania.pe/productos/circuitos-integrados/', 'categoria': 'circuitos_integrados'},
    # {'url': 'https://www.electromania.pe/productos/equipos/', 'categoria': 'equipos'},
    # {'url': 'https://www.electromania.pe/productos/soldadura/', 'categoria': 'soldadura'},
    # {'url': 'https://www.electromania.pe/productos/wireless/', 'categoria': 'wireless'},
    # {'url': 'https://www.electromania.pe/productos/instrumentos/', 'categoria': 'instrumentos'},
    # {'url': 'https://www.electromania.pe/productos/conectores/', 'categoria': 'conectores'},
    # {'url': 'https://www.electromania.pe/productos/otros-accesorios/', 'categoria': 'otros_accesorios'},
    # {'url': 'https://www.electromania.pe/productos/raspberry/', 'categoria': 'raspberry'},
    # {'url': 'https://www.electromania.pe/productos/arduino/', 'categoria': 'arduino'},
    # {'url': 'https://www.electromania.pe/productos/sensores/', 'categoria': 'sensores'},
    # {'url': 'https://www.electromania.pe/productos/motores/', 'categoria': 'motores'},
    # {'url': 'https://www.electromania.pe/productos/microcontroladores/', 'categoria': 'microcontroladores'},
    # {'url': 'https://www.electromania.pe/productos/integrados/', 'categoria': 'integrados'}
]

# Función para scraping de precios y disponibilidad (cada semana)
def weekly_scraping():
    for item in urls:
        url = item['url']
        categoria = item['categoria']
        productos_lista = extract_data(url)
        for producto in productos_lista:
            producto.pop('descuento', None)  # Eliminar campo de descuento
            producto.pop('nombre', None)  # Eliminar campo de nombre
        json_filename = save_data(productos_lista, categoria, 'weekly')
        upload_file_to_s3(json_filename, 'ecomelectro', f'{categoria}_weekly.json')

# Función para scraping de todos los campos (cada mes)
def monthly_scraping():
    for item in urls:
        url = item['url']
        categoria = item['categoria']
        productos_lista = extract_data(url)
        json_filename = save_data(productos_lista, categoria, 'monthly')
        upload_file_to_s3(json_filename, 'ecomelectro', f'{categoria}_monthly.json')

# Programar tareas
schedule.every(7).days.do(weekly_scraping)  # Cada semana
schedule.every(30).days.do(monthly_scraping)  # Cada mes

# Llamar a las funciones para iniciar la ejecución
weekly_scraping()
monthly_scraping()

# Mantener el script en ejecución
while True:
    schedule.run_pending()
    sleep(60)
