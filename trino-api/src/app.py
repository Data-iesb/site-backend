import json
import boto3
import trino
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ssm = boto3.client('ssm', region_name='us-east-1')

TRINO_HOST = 'trino.dataiesb.com'
TRINO_PORT = 443
TRINO_USER = 'aurya'
TRINO_HTTP_SCHEME = 'https'

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
}


def get_password():
    resp = ssm.get_parameter(Name='/trino/aurya-password', WithDecryption=True)
    return resp['Parameter']['Value']


def get_api_password():
    resp = ssm.get_parameter(Name='/trino-api/password', WithDecryption=True)
    return resp['Parameter']['Value']


def get_connection(catalog, schema):
    return trino.dbapi.connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user=TRINO_USER,
        http_scheme=TRINO_HTTP_SCHEME,
        auth=trino.auth.BasicAuthentication(TRINO_USER, get_password()),
        catalog=catalog,
        schema=schema,
    )


def run_query(catalog, schema, sql):
    conn = get_connection(catalog, schema)
    cur = conn.cursor()
    cur.execute(sql)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': HEADERS, 'body': ''}

    try:
        body = json.loads(event.get('body') or '{}')
        password = body.get('password', '')

        if password != get_api_password():
            return {
                'statusCode': 401,
                'headers': HEADERS,
                'body': json.dumps({'error': 'unauthorized'})
            }

        catalog = body.get('catalog', 's3')
        schema = body.get('schema', 'default')
        sql = body.get('sql', '')

        if not sql:
            return {
                'statusCode': 400,
                'headers': HEADERS,
                'body': json.dumps({'error': 'sql is required'})
            }

        if catalog not in ('s3', 'postgres'):
            return {
                'statusCode': 403,
                'headers': HEADERS,
                'body': json.dumps({'error': 'catalog not allowed'})
            }

        data = run_query(catalog, schema, sql)

        return {
            'statusCode': 200,
            'headers': HEADERS,
            'body': json.dumps({'success': True, 'data': data}, default=str)
        }

    except Exception as e:
        logger.error(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': HEADERS,
            'body': json.dumps({'error': str(e)})
        }
