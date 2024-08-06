import json
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def extract_data(driver, url):
    driver.get(url)

    # Espera explícita para asegurar que el cuerpo de la página está cargado
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        while True:
            try:
                # Desplázate hacia abajo en la página para cargar más elementos
                last_height = driver.execute_script("return document.body.scrollHeight")
                while True:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    sleep(2)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

                # Espera a que el botón de "Cargar Más Productos" esté presente y haz clic en él
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//a[@class="btn wd-load-more wd-products-load-more load-on-click"]'))
                )
                load_more_button.click()
                sleep(2)  # Espera un poco para que los productos se carguen
            except Exception as e:
                print("No se encontró más el botón de 'Cargar Más Productos'. Todos los productos están cargados.")
                break

        # Añadir un tiempo de espera adicional para asegurar que todos los elementos se han cargado
        sleep(5)

        # Encuentra todos los productos
        productos = driver.find_elements(By.XPATH, '//div[contains(@class, "product-grid-item")]')

        print(f"Productos encontrados en {url}: {len(productos)}")  # Depuración: Número de productos encontrados

        productos_lista = []  # Lista para almacenar los productos
        for producto in productos:
            try:
                # Verificar si el nombre del producto existe
                nombre_element = producto.find_element(By.XPATH, './/h3/a')
                nombre = nombre_element.text
            except Exception as e:
                print(f'Error al extraer el nombre del producto: {e}')
                nombre = "Nombre no encontrado"

            try:
                # Verificar si el precio del producto existe
                precio_element = producto.find_element(By.XPATH, './/span[contains(@class, "woocommerce-Price-amount amount")]')
                precio = precio_element.text
            except Exception as e:
                print(f'Error al extraer el precio del producto: {e}')
                precio = "Precio no encontrado"

            # Verificar si el producto tiene descuento
            descuento_elements = producto.find_elements(By.XPATH, './/div[contains(@class, "product-labels labels-rounded")]/span[contains(@class, "onsale product-label")]')
            descuento = ', '.join([element.text for element in descuento_elements]) if descuento_elements else "No tiene descuento"

            # Verificar si el producto está disponible
            disponible_elements = producto.find_elements(By.XPATH, './/div[contains(@class, "product-labels labels-rounded")]/span[contains(@class, "out-of-stock product-label")]')
            disponible = "No disponible" if disponible_elements else "Disponible"

            # Añadir el producto a la lista
            productos_lista.append({
                "nombre": nombre,
                "precio": precio,
                "descuento": descuento,
                "disponible": disponible
            })

        return productos_lista

    finally:
        pass  # No cerramos el driver aquí, lo haremos al final de todo el proceso

# Configuración de opciones de Chrome
opts = Options()
opts.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")

# Inicializa el controlador de Chrome
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=opts
)

# Añadir una espera implícita
driver.implicitly_wait(10)

urls = [
    {'url': 'https://www.electromania.pe/productos/placas-de-desarrollo/', 'categoria': 'placas_de_desarrollo'},
    {'url': 'https://www.electromania.pe/productos/drones/', 'categoria': 'drones'},
    {'url': 'https://www.electromania.pe/productos/impresoras-3d/', 'categoria': 'impresoras_3d'},
    {'url': 'https://www.electromania.pe/productos/robotica/', 'categoria': 'robotica'},
    {'url': 'https://www.electromania.pe/productos/semiconductores/', 'categoria': 'semiconductores'},
    {'url': 'https://www.electromania.pe/productos/rcl/', 'categoria': 'rcl'},
    {'url': 'https://www.electromania.pe/productos/pantallas/', 'categoria': 'pantallas'},
    {'url': 'https://www.electromania.pe/productos/teclados/', 'categoria': 'teclados'},
    {'url': 'https://www.electromania.pe/productos/adaptadores/', 'categoria': 'adaptadores'},
    {'url': 'https://www.electromania.pe/productos/robotica/baterias/', 'categoria': 'baterias'},
    {'url': 'https://www.electromania.pe/productos/cables/', 'categoria': 'cables'},
    {'url': 'https://www.electromania.pe/productos/circuitos-integrados/', 'categoria': 'circuitos_integrados'},
    {'url': 'https://www.electromania.pe/productos/equipos/', 'categoria': 'equipos'},
    {'url': 'https://www.electromania.pe/productos/soldadura/', 'categoria': 'soldadura'},
    {'url': 'https://www.electromania.pe/productos/wireless/', 'categoria': 'wireless'},
    {'url': 'https://www.electromania.pe/productos/instrumentos/', 'categoria': 'instrumentos'},
    {'url': 'https://www.electromania.pe/productos/conectores/', 'categoria': 'conectores'},
    {'url': 'https://www.electromania.pe/productos/otros-accesorios/', 'categoria': 'otros_accesorios'},
    {'url': 'https://www.electromania.pe/productos/raspberry/', 'categoria': 'raspberry'},
    {'url': 'https://www.electromania.pe/productos/arduino/', 'categoria': 'arduino'},
    {'url': 'https://www.electromania.pe/productos/sensores/', 'categoria': 'sensores'},
    {'url': 'https://www.electromania.pe/productos/motores/', 'categoria': 'motores'},
    {'url': 'https://www.electromania.pe/productos/microcontroladores/', 'categoria': 'microcontroladores'},
    {'url': 'https://www.electromania.pe/productos/integrados/', 'categoria': 'integrados'}
]

for item in urls:
    url = item['url']
    categoria = item['categoria']
    productos_lista = extract_data(driver, url)
    json_filename = f'{categoria}.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(productos_lista, f, ensure_ascii=False, indent=4)
    print(f"Datos guardados en {json_filename}")

driver.quit()
print("Proceso completado.")
