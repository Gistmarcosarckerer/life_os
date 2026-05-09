import json
from datetime import datetime
from urllib.parse import urljoin

import requests

from config import config
from backend.models import BankAccount, BankConnection, ImportedTransaction
from backend.services.finance_service import categorize_transaction, create_transaction


class PluggyError(RuntimeError):
    pass


def pluggy_is_configured() -> bool:
    return bool(config.PLUGGY_CLIENT_ID and config.PLUGGY_CLIENT_SECRET)


def get_pluggy_status(session) -> dict:
    connections = list_bank_connections(session)
    return {
        "configured": pluggy_is_configured(),
        "connections_count": len(connections),
        "connections": connections,
    }


def create_connect_token(webhook_url: str = "", client_user_id: str = "life-os") -> dict:
    api_key = get_api_key()
    options = {
        "clientUserId": client_user_id,
        "avoidDuplicates": True,
    }
    if webhook_url:
        options["webhookUrl"] = webhook_url

    payload = {"options": options}
    data = pluggy_request("POST", "/connect_token", api_key=api_key, json_payload=payload)
    token = data.get("accessToken") or data.get("connectToken") or data.get("token")
    if not token:
        raise PluggyError("Pluggy nao retornou connect token.")
    return {"accessToken": token}


def register_item(session, item_payload: dict) -> BankConnection:
    item_id = (
        item_payload.get("itemId")
        or item_payload.get("id")
        or item_payload.get("item", {}).get("id")
    )
    if not item_id:
        raise PluggyError("itemId ausente no retorno da Pluggy.")

    item_data = fetch_item(item_id)
    connection = upsert_bank_connection(session, item_data)
    return connection


def sync_all_connections(session) -> dict:
    connections = session.query(BankConnection).all()
    imported = 0
    accounts_count = 0
    errors = []
    for connection in connections:
        try:
            result = sync_connection(session, connection.item_id)
            imported += result["imported_transactions"]
            accounts_count += result["accounts_count"]
        except PluggyError as exc:
            errors.append({"item_id": connection.item_id, "error": str(exc)})
    return {
        "connections_count": len(connections),
        "accounts_count": accounts_count,
        "imported_transactions": imported,
        "errors": errors,
    }


def sync_connection(session, item_id: str) -> dict:
    item = fetch_item(item_id)
    connection = upsert_bank_connection(session, item)
    accounts = fetch_accounts(item_id)
    imported = 0

    for account_data in accounts:
        account = upsert_bank_account(session, account_data, item_id)
        transactions = fetch_transactions(account.pluggy_account_id)
        for transaction_data in transactions:
            if import_pluggy_transaction(session, transaction_data, account.pluggy_account_id):
                imported += 1

    now = datetime.utcnow()
    connection.last_sync_at = now
    connection.updated_at = now
    session.flush()
    return {
        "item_id": item_id,
        "accounts_count": len(accounts),
        "imported_transactions": imported,
    }


def fetch_item(item_id: str) -> dict:
    return pluggy_request("GET", f"/items/{item_id}", api_key=get_api_key())


def fetch_accounts(item_id: str) -> list[dict]:
    data = pluggy_request("GET", "/accounts", api_key=get_api_key(), params={"itemId": item_id})
    return extract_results(data)


def fetch_transactions(account_id: str) -> list[dict]:
    api_key = get_api_key()
    transactions = []
    cursor = None
    for _ in range(20):
        params = {"accountId": account_id, "pageSize": 500}
        if cursor:
            params["after"] = cursor
        data = pluggy_request("GET", "/v2/transactions", api_key=api_key, params=params)
        transactions.extend(extract_results(data))
        cursor = data.get("next") or data.get("nextCursor")
        if not cursor:
            break
    return transactions


def import_pluggy_transaction(session, data: dict, account_id: str) -> bool:
    external_id = str(data.get("id") or "")
    if not external_id:
        return False
    existing = (
        session.query(ImportedTransaction)
        .filter(ImportedTransaction.external_id == external_id)
        .first()
    )
    if existing:
        return False

    amount = money_value(data.get("amount", 0))
    if amount == 0:
        return False

    description = (
        data.get("description")
        or data.get("descriptionRaw")
        or data.get("merchant", {}).get("name")
        or "transacao bancaria"
    )
    pluggy_type = str(data.get("type") or "").upper()
    if pluggy_type == "CREDIT":
        transaction_type = "income"
    elif pluggy_type == "DEBIT":
        transaction_type = "expense"
    else:
        transaction_type = "income" if amount > 0 else "expense"
    occurred_at = parse_datetime(data.get("date") or data.get("createdAt")) or datetime.utcnow()
    category = categorize_transaction(description, transaction_type)
    transaction = create_transaction(
        session,
        amount=abs(amount),
        description=description,
        transaction_type=transaction_type,
        category=category,
        source="pluggy",
        occurred_at=occurred_at,
    )
    imported = ImportedTransaction(
        provider="pluggy",
        external_id=external_id,
        account_id=account_id,
        transaction_id=transaction.id,
        raw_payload=json.dumps(data, ensure_ascii=True, default=str),
    )
    session.add(imported)
    return True


def upsert_bank_connection(session, data: dict) -> BankConnection:
    item_id = str(data.get("id") or data.get("itemId") or "")
    if not item_id:
        raise PluggyError("Item Pluggy sem id.")
    connection = (
        session.query(BankConnection)
        .filter(BankConnection.item_id == item_id)
        .first()
    )
    if connection is None:
        connection = BankConnection(item_id=item_id)
        session.add(connection)

    connector = data.get("connector") or {}
    connection.connector_id = str(data.get("connectorId") or connector.get("id") or "")
    connection.institution_name = str(connector.get("name") or data.get("institutionName") or "")
    connection.status = str(data.get("status") or connection.status or "created")
    connection.execution_status = str(data.get("executionStatus") or "")
    connection.updated_at = datetime.utcnow()
    session.flush()
    session.refresh(connection)
    return connection


def upsert_bank_account(session, data: dict, item_id: str) -> BankAccount:
    account_id = str(data.get("id") or "")
    if not account_id:
        raise PluggyError("Conta Pluggy sem id.")
    account = (
        session.query(BankAccount)
        .filter(BankAccount.pluggy_account_id == account_id)
        .first()
    )
    if account is None:
        account = BankAccount(pluggy_account_id=account_id)
        session.add(account)

    account.item_id = item_id
    account.account_type = str(data.get("type") or "")
    account.subtype = str(data.get("subtype") or "")
    account.name = str(data.get("name") or data.get("marketingName") or "Conta bancaria")
    account.balance = money_value(data.get("balance", 0))
    account.currency_code = str(data.get("currencyCode") or "BRL")
    account.last_sync_at = datetime.utcnow()
    account.updated_at = datetime.utcnow()
    session.flush()
    session.refresh(account)
    return account


def list_bank_connections(session) -> list[dict]:
    connections = (
        session.query(BankConnection)
        .order_by(BankConnection.created_at.desc())
        .all()
    )
    return [
        {
            "id": item.id,
            "provider": item.provider,
            "item_id": item.item_id,
            "institution_name": item.institution_name,
            "status": item.status,
            "execution_status": item.execution_status,
            "last_sync_at": item.last_sync_at.isoformat() if item.last_sync_at else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in connections
    ]


def list_bank_accounts(session) -> list[dict]:
    accounts = (
        session.query(BankAccount)
        .order_by(BankAccount.updated_at.desc())
        .all()
    )
    return [
        {
            "id": item.id,
            "pluggy_account_id": item.pluggy_account_id,
            "item_id": item.item_id,
            "account_type": item.account_type,
            "subtype": item.subtype,
            "name": item.name,
            "balance": round(item.balance, 2),
            "currency_code": item.currency_code,
            "last_sync_at": item.last_sync_at.isoformat() if item.last_sync_at else None,
        }
        for item in accounts
    ]


def get_api_key() -> str:
    if not pluggy_is_configured():
        raise PluggyError("Configure PLUGGY_CLIENT_ID e PLUGGY_CLIENT_SECRET.")
    payload = {
        "clientId": config.PLUGGY_CLIENT_ID,
        "clientSecret": config.PLUGGY_CLIENT_SECRET,
    }
    data = pluggy_request("POST", "/auth", json_payload=payload, api_key=None)
    api_key = data.get("apiKey") or data.get("accessToken")
    if not api_key:
        raise PluggyError("Pluggy nao retornou API key.")
    return api_key


def pluggy_request(method: str, path: str, api_key: str | None = None, json_payload=None, params=None) -> dict:
    url = urljoin(config.PLUGGY_API_BASE_URL + "/", path.lstrip("/"))
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-KEY"] = api_key

    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            json=json_payload,
            params=params,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise PluggyError(f"Falha de conexao com Pluggy: {exc}") from exc

    if response.status_code >= 400:
        raise PluggyError(f"Pluggy retornou {response.status_code}: {response.text[:240]}")
    if not response.text:
        return {}
    return response.json()


def extract_results(data) -> list[dict]:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in ("results", "data", "accounts", "transactions"):
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def money_value(value) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return 0


def parse_datetime(value) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(str(value)[:10], "%Y-%m-%d")
        except ValueError:
            return None
    if parsed.tzinfo:
        return parsed.replace(tzinfo=None)
    return parsed
