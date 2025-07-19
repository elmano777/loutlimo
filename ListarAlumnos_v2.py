import boto3
import pymysql
import json
import os

def lambda_handler(event, context):
    # Variables de entorno
    secret_name = os.environ['DB_SECRET_NAME']
    database = os.environ['DB_NAME']
    
    # Cliente de Secrets Manager
    secrets_client = boto3.client('secretsmanager')
    
    try:
        # Recuperar el secreto completo desde Secrets Manager
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(response['SecretString'])
        
        # Extraer credenciales del secreto
        host = secret_data['host']
        username = secret_data['username']
        password = secret_data['password']
        port = secret_data.get('port', 3306)  # Puerto por defecto MySQL
        
        # Establecer conexión a la base de datos
        connection = pymysql.connect(
            host=host,
            user=username,
            password=password,
            db=database,
            port=port,
            connect_timeout=10
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM alumnos ORDER BY alumno_id;")
            results = cursor.fetchall()
            
            # Convertir resultados a formato más amigable
            alumnos = []
            for row in results:
                alumno = {
                    "alumno_id": row[0],
                    "apellidos": row[1],
                    "nombres": row[2]
                }
                alumnos.append(alumno)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "message": "Alumnos recuperados exitosamente",
                "data": alumnos,
                "total": len(alumnos)
            }, indent=2)
        }

    except secrets_client.exceptions.DecryptionFailureException:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error de desencriptación del secreto",
                "message": "No se pudo desencriptar el secreto"
            })
        }
    
    except secrets_client.exceptions.InternalServiceErrorException:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error interno de Secrets Manager",
                "message": "Error interno del servicio"
            })
        }
    
    except secrets_client.exceptions.InvalidParameterException:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Parámetro inválido",
                "message": "El nombre del secreto es inválido"
            })
        }
    
    except secrets_client.exceptions.InvalidRequestException:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Solicitud inválida",
                "message": "La solicitud no es válida"
            })
        }
    
    except secrets_client.exceptions.ResourceNotFoundException:
        return {
            "statusCode": 404,
            "body": json.dumps({
                "error": "Secreto no encontrado",
                "message": f"El secreto {secret_name} no existe"
            })
        }
    
    except pymysql.Error as db_error:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error de base de datos",
                "message": str(db_error)
            })
        }
    
    except json.JSONDecodeError:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error de formato JSON",
                "message": "El secreto no tiene formato JSON válido"
            })
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error interno del servidor",
                "message": str(e)
            })
        }

    finally:
        if 'connection' in locals():
            connection.close()