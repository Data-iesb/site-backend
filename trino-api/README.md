# Trino API

Função Lambda que consulta o Trino (catálogos s3/postgres) e retorna JSON para dashboards Chart.js.

## Endpoints

| URL | Timeout | Uso |
|-----|---------|-----|
| `POST https://lambda.dataiesb.com/trino` | 29s | Queries rápidas de dashboard |
| `POST https://yik3276s5ndbilffxnxz4gz3cm0hcpsn.lambda-url.us-east-1.on.aws/` | 8 min | Queries pesadas (grandes volumes) |

## Requisição

```json
{
  "catalog": "s3",
  "schema": "gold",
  "sql": "SELECT category, COUNT(*) as total FROM products GROUP BY category"
}
```

- `catalog` — `s3` ou `postgres` (apenas esses são permitidos)
- `schema` — nome do schema alvo
- `sql` — query SQL do Trino

## Resposta

```json
{
  "success": true,
  "data": [
    {"category": "X", "total": 10},
    {"category": "Y", "total": 25}
  ]
}
```

## Tabelas Disponíveis (s3.gold)

- acidentes_transito
- demografia_municipios
- educacao_basica
- educacao_superior
- enem_2024
- ocorrencias_criminais
- sus_aih
- sus_procedimento_ambulatorial

## Exemplo Chart.js

```javascript
const res = await fetch('https://lambda.dataiesb.com/trino', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    catalog: 's3',
    schema: 'gold',
    sql: 'SELECT uf, COUNT(*) as total FROM educacao_basica GROUP BY uf ORDER BY total DESC LIMIT 10'
  })
});
const { data } = await res.json();

const chart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: data.map(d => d.uf),
    datasets: [{ label: 'Total', data: data.map(d => d.total) }]
  }
});
```

## Infraestrutura

- **Stack:** `trino-api` (SAM/CloudFormation)
- **Lambda:** `trino-api` (Python 3.12, 3008MB RAM, 5GB ephemeral, 8min timeout)
- **Domínio:** `lambda.dataiesb.com` (certificado wildcard `*.dataiesb.com`)
- **Autenticação:** Usuário Trino `aurya` (somente leitura, catálogos s3/postgres)
- **Senha:** SSM `/trino/aurya-password` (SecureString)

## Deploy

```bash
cd site-backend/trino-api
sam build && sam deploy --stack-name trino-api --resolve-s3 --capabilities CAPABILITY_IAM --no-confirm-changeset --region us-east-1
```
