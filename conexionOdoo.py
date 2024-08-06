import boto3
import json
import xmlrpc.client

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

# Configura tus credenciales de Odoo
odoo_url = 'https://auditel.odoo.com'
odoo_db = 'auditel'  # Cambia esto al nombre correcto de tu base de datos
odoo_username = 'dm@fibertel.com.pe'
odoo_password = 'Powerbeam.2024##'

# Conecta a la base de datos de Odoo
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(odoo_url))
uid = common.authenticate(odoo_db, odoo_username, odoo_password, {})
if uid is None:
    print("Error de autenticación. Verifica tus credenciales.")
    exit()

models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(odoo_url))

# Descarga el archivo JSON desde el bucket de S3
s3_client.download_file('ecomelectro', 'electromania_productos.json', 'electromania_productos.json')

# Abre el archivo JSON y lee los productos
with open('electromania_productos.json', 'r', encoding='utf-8') as f:
    productos = json.load(f)

# Crea o actualiza un registro de producto en Odoo para cada producto en el archivo JSON
for producto in productos:
    precio_str = producto['precio'].replace('S/', '').strip()  # Elimina 'S/' y espacios en blanco
    precio_float = float(precio_str.replace(',', '.'))  # Reemplaza coma por punto si es necesario
    
    product_vals = {
        'x_name': producto['nombre'],
        'x_price': precio_float,
        'x_discount': producto['descuento'],
        'x_available': producto['disponible']
    }
    
    # Buscar producto existente por nombre
    existing_product = models.execute_kw(
        odoo_db, uid, odoo_password, 'x_productos.electromania', 'search_read',
        [[['x_name', '=', producto['nombre']]], ['id']]
    )
    
    if existing_product:
        # Si el producto existe, actualizarlo
        product_id = existing_product[0]['id']
        models.execute_kw(odoo_db, uid, odoo_password, 'x_productos.electromania', 'write', [[product_id], product_vals])
        print(f"Producto actualizado: {producto['nombre']}")
    else:
        # Si el producto no existe, crearlo
        models.execute_kw(odoo_db, uid, odoo_password, 'x_productos.electromania', 'create', [product_vals])
        print(f"Producto creado: {producto['nombre']}")

print("Productos creados o actualizados con éxito en Odoo")
