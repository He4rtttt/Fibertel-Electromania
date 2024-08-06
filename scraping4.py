import json
import os
import xmlrpc.client
import boto3
import schedule
import time
import logging
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de AWS
AWS_ACCESS_KEY_ID = 'tu AWS_ACCESS_KEY_ID'
AWS_SECRET_ACCESS_KEY = 'tu AWS_SECRET_ACCESS_KEY'
REGION_NAME = 'us-east-1'

# Configuración de Odoo
ODOO_URL = 'https://prueba5.odoo.com/'
ODOO_DB = 'prueba5'
ODOO_USERNAME = 'dm@fibertel.com.pe'
ODOO_PASSWORD = 'Powerbeam.2024##'

# Conecta a la base de datos de Odoo
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(ODOO_URL))
uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
if uid is None:
    logger.error("Error de autenticación. Verifica tus credenciales.")
    exit()

models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(ODOO_URL))

# Función para subir archivo a S3
def upload_file_to_s3(file_name, bucket, object_name=None):
    """Sube un archivo a un bucket de S3"""
    if object_name is None:
        object_name = file_name

    if not os.path.isfile(file_name):
        logger.error(f"Error: El archivo {file_name} no se encuentra.")
        return False

    try:
        s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=REGION_NAME)
        s3_client.upload_file(file_name, bucket, object_name)
        logger.info(f"{file_name} se ha subido exitosamente a {bucket}/{object_name}")
        return True
    except Exception as e:
        logger.error(f"Error: {e}")
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
                    time.sleep(2)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//a[@class="btn wd-load-more wd-products-load-more load-on-click"]'))
                )
                load_more_button.click()
                time.sleep(2)
            except Exception as e:
                logger.error("No se encontró más el botón de 'Cargar Más Productos'. Todos los productos están cargados.")
                break
        
        time.sleep(5)
        
        productos = driver.find_elements(By.XPATH, '//div[contains(@class, "product-grid-item")]')
        productos_lista = []
        for producto in productos:
            try:
                nombre = producto.find_element(By.XPATH, './/h3/a').text
            except Exception as e:
                nombre = "Nombre no encontrado"
            
            try:
                precio = producto.find_element(By.XPATH, './/span[contains(@class, "woocommerce-Price-amount amount")]').text
                # Eliminar símbolo de moneda y cualquier otro carácter que no sea numérico
                precio = precio.replace('S/', '').replace(',', '')
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
    except Exception as e:
        logger.error(f"Error durante la extracción de datos: {e}")
        return []

# Función para guardar los datos en un archivo JSON
def save_data(productos_lista, categoria, tipo):
    json_filename = f'{categoria}_{tipo}.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(productos_lista, f, ensure_ascii=False, indent=4)
    logger.info(f"Datos guardados en {json_filename}")
    return json_filename

# URLs y categorías de productos
urls = [
    {'url': 'https://www.electromania.pe/productos/placas-de-desarrollo/stm32-placas-de-desarrollo/', 'categoria': 'placas-de-desarrollo'}
    # Añadir más URLs y categorías según sea necesario
]

# Función para scraping de precios y disponibilidad (cada semana)
def weekly_scraping():
    for item in urls:
        url = item['url']
        categoria = item['categoria']
        productos_lista = extract_data(url)
        json_filename = save_data(productos_lista, categoria, 'weekly')
        upload_file_to_s3(json_filename, 'ecomelectro', f'{categoria}_weekly.json')
        update_odoo_products(json_filename)

# Función para scraping de todos los campos (cada mes)
def monthly_scraping():
    for item in urls:
        url = item['url']
        categoria = item['categoria']
        productos_lista = extract_data(url)
        json_filename = save_data(productos_lista, categoria, 'monthly')
        upload_file_to_s3(json_filename, 'ecomelectro', f'{categoria}_monthly.json')
        update_odoo_products(json_filename)

# Función para actualizar los productos en Odoo
def update_odoo_products(json_filename):
    with open(json_filename, 'r', encoding='utf-8') as f:
        productos_lista = json.load(f)
    
    for producto in productos_lista:
        try:
            # Convertir precio a número flotante
            precio = float(producto['precio'])
            
            # Buscar el producto en Odoo
            product_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'product.template', 'search', [[['name', '=', producto['nombre']]]])
            if product_id:
                # Actualizar el producto en Odoo
                models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'product.template', 'write', [product_id, {
                    'list_price': precio,
                    'standard_price': float(producto.get('costo', 0)),  # Asumiendo que el JSON tiene un campo 'costo'
                    'qty_available': int(producto.get('disponible', 0))  # Asumiendo que el JSON tiene un campo 'disponible'
                }])
            else:
                # Crear un nuevo producto en Odoo
                models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'product.template', 'create', [{
                    'name': producto['nombre'],
                    'list_price': precio,
                    'standard_price': float(producto.get('costo', 0)),
                    'qty_available': int(producto.get('disponible', 0))
                }])
        except KeyError as e:
            logger.error(f"Error al actualizar o crear el producto en Odoo: faltante campo {e}")
        except Exception as e:
            logger.error(f"Error al actualizar o crear el producto en Odoo: {e}")
# Programar las tareas de scraping
schedule.every(7).days.do(weekly_scraping)  # Cada semana
schedule.every(30).days.do(monthly_scraping)  # Cada mes

# Llamar a las funciones manualmente para probar el scraping
weekly_scraping()
monthly_scraping()

while True:
    schedule.run_pending()
    time.sleep(1)
