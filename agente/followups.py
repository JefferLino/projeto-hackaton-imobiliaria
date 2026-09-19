"""Orquestra lembretes. Transporte externo depende da configuração autorizada."""
import math
import os
import httpx
import database
import config
import reminder_store


def settings():
    try:
        hours = float(os.getenv('FOLLOWUP_IDLE_HOURS', '24'))
        interval = float(os.getenv('FOLLOWUP_INTERVAL_HOURS', str(hours)))
        maximum = int(os.getenv('FOLLOWUP_MAX_ATTEMPTS', '3'))
        if not all(math.isfinite(v) and v > 0 for v in (hours, interval)) or maximum < 1:
            raise ValueError()
        return hours, interval, maximum
    except ValueError as exc:
        raise database.DatabaseError(500, 'Configuração de lembretes inválida') from exc


def send(payload):
    # Destino definido em config.py; sem proxy e sem redirecionamentos.
    with httpx.Client(timeout=10, trust_env=False, follow_redirects=False) as client:
        response = client.post(config.FOLLOWUP_URL, json=payload,
                               headers={'Idempotency-Key': payload['evento_id']})
        response.raise_for_status()


def process(limit=50):
    hours, interval, maximum = settings()
    results = []
    for cid in reminder_store.candidates(min(hours, interval), limit):
        job = reminder_store.claim(cid, hours, interval, maximum)
        if not job:
            continue
        if job['status'] == 'cancelada':
            results.append(job)
            continue
        try:
            send(job['payload'])
        except Exception as exc:
            reminder_store.finish(job, False, type(exc).__name__)
            if isinstance(exc, database.DatabaseError):
                raise
            results.append({'conversa_id':cid, 'status':'falha_envio'})
        else:
            reminder_store.finish(job, True)
            results.append({'conversa_id':cid, 'status':'enviado','evento_id':job['payload']['evento_id']})
    return {'resultados':results, 'enviados':sum(r['status']=='enviado' for r in results),
            'cancelados':sum(r['status']=='cancelada' for r in results),
            'falhas':sum(r['status']=='falha_envio' for r in results)}
