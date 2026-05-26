# CRM Demo Lead Simulator

Sends weighted demo messages to ingestion webhooks for load / demo rehearsal.

```bash
pip install -r requirements.txt
python lead_simulator.py --base-url https://crm-ingest.nano.platform --rate 2 --duration 30 --channels facebook,tiktok,shopee
```

Templates: `templates.json` (shared with `crm-ingestion-api` demo send API).
