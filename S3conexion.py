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

print("El script está en ejecución...")

if __name__ == "__main__":
    file_name = 'drones_less_frequent.json'
    bucket_name = 'ecomelectro'
    object_name = 'drones_less_frequent.json'

    success = upload_file_to_s3(file_name, bucket_name, object_name)
    if success:
        print(f"{file_name} se ha subido exitosamente a {bucket_name}/{object_name}")
    else:
        print("Error al subir el archivo")