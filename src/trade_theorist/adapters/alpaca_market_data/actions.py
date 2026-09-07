"""Private corporate-action receipts; unknown publication time stays unknown.

Queries filter process_date, not ex_date. Successful pagination establishes only
retrieval completeness; Alpaca does not guarantee timely announcement coverage.
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from ...contracts import ContractError, canonical, utc

URL = 'https://data.alpaca.markets/v1/corporate-actions'
SUPPORTED = {'cash_dividends', 'forward_splits', 'reverse_splits'}


def parse_page(response, symbols, *, seen=()):
    body = response.body
    if not isinstance(body, dict) or not isinstance(body.get('corporate_actions'), dict):
        raise ContractError('Malformed corporate-action response')
    token = body.get('next_page_token')
    if token is not None and (not isinstance(token, str) or not token or len(token) > 8192 or token in seen):
        raise ContractError('Invalid corporate-action pagination')
    records = []
    identifiers = set()
    for kind, rows in body['corporate_actions'].items():
        if not isinstance(kind, str) or not isinstance(rows, list):
            raise ContractError('Malformed corporate-action group')
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'] or row['id'] in identifiers:
                raise ContractError('Invalid or duplicate corporate-action identity')
            identifiers.add(row['id'])
            matching = {row[k] for k in ('symbol','old_symbol','new_symbol','source_symbol','acquirer_symbol','acquiree_symbol')
                        if isinstance(row.get(k), str) and row[k] in symbols}
            if not matching:
                raise ContractError('Corporate action outside requested symbols')
            process = row.get('process_date')
            if not isinstance(process, str) or date.fromisoformat(process).isoformat() != process:
                raise ContractError('Missing or malformed corporate-action process date')
            canonical(row)
            records.append(dict(kind=kind, symbol=sorted(matching)[0], process_date=process, raw=row))
    return records, token


def accounting_action(receipt):
    """Fail closed on incomplete, non-USD or unsupported events, never guess."""
    action = receipt['action']; row = action['raw']; kind = action['kind']
    if kind not in SUPPORTED:
        raise ContractError('Unsupported corporate action requires review')
    try:
        ex_date = date.fromisoformat(row['ex_date']).isoformat()
        if row.get('currency', 'USD') != 'USD':
            raise ValueError('Unsupported currency')
        if kind == 'cash_dividends':
            payable = date.fromisoformat(row['payable_date']).isoformat()
            rate = Decimal(str(row['rate']))
            if not rate.is_finite() or rate <= 0 or payable < ex_date or row.get('foreign') is True:
                raise ValueError('Invalid dividend')
            economics = dict(rate=str(rate), payable_date=payable)
        else:
            old, new = (Decimal(str(row[k])) for k in ('old_rate','new_rate'))
            if not all(v.is_finite() and v > 0 for v in (old,new)):
                raise ValueError('Invalid split')
            economics = dict(old_rate=str(old), new_rate=str(new))
        utc(receipt['received_at'])
    except (KeyError, ValueError, TypeError, InvalidOperation) as exc:
        raise ContractError('Incomplete corporate-action economics') from exc
    return dict(source_action_id=row['id'],kind=kind,symbol=action['symbol'],ex_date=ex_date,
                process_date=action['process_date'],published_at=None,ingested_at=receipt['received_at'],
                publication_evidence='unknown; receipt is earliest observed availability',**economics)
