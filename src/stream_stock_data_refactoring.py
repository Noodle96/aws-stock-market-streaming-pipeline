from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, TypedDict

import boto3
import yfinance as yf

# ==============================
# 1) Tipos (Type Hints)
# ==============================

class StockData(TypedDict):
    """
    Estructura del evento que enviaremos a Kinesis.

    - symbol: ticker (ej: "AAPL")
    - open/high/low/price: precios del último día disponible
    - previous_close: cierre del día anterior
    - change/change_percent: variación vs previous_close
    - volume: volumen del último día disponible
    - timestamp: timestamp en formato ISO-like UTC (Z)
    """
    symbol: str
    open: float
    high: float
    low: float
    price: float
    previous_close: float
    change: float
    change_percent: float
    volume: int
    timestamp: str

# Clase inmutable para configuración
@dataclass(frozen=True)
class AppConfig:
    """
    Configuración central del script.
    Cambiamos aquí valores del stream, región, símbolo, etc.
    """
    region_name: str = "us-east-1"
    stream_name: str = "stock-market-stream"
    stock_symbol: str = "AAPL"
    delay_seconds: int = 10  # cada cuánto enviamos un evento


# ==============================
# 2) Cliente de Kinesis (AWS SDK)
# ==============================
def build_kinesis_client(region_name: str) -> Any:
    """
    Crea el cliente boto3 para Kinesis.
    Tipado 'Any' porque boto3 no siempre expone tipos estáticos sin stubs.
    """
    return boto3.client("kinesis", region_name=region_name)

# ==============================
# 3) Obtener datos desde Yahoo Finance (yfinance)
# ==============================

def get_stock_data(symbol: str) -> Optional[StockData]:
    """
    Consulta datos de Yahoo Finance usando yfinance y retorna un diccionario estructurado.

    Estrategia:
    - Pedimos '2d' para tener:
      - el último día disponible (para open/high/low/close/volume)
      - el día anterior (para previous_close)
    - Calculamos change y change_percent comparando close(último) vs close(anterior)

    Retorna:
    - StockData si todo sale bien
    - None si ocurre un error o hay data insuficiente
    """
    try:
        # 1) Creamos un objeto "Ticker" de yfinance
        ticker: yf.Ticker = yf.Ticker(symbol)

        # 2) history(period="2d") devuelve un DataFrame (pandas) con filas por día
        data = ticker.history(period="2d")

        # 3) Validamos que existan al menos 2 filas (dos días)
        if len(data) < 2:
            raise ValueError("Insufficient data to fetch previous close.")

        # 4) Seleccionamos:
        #    - last_row: último día disponible (iloc[-1])
        #    - prev_row: el día anterior (iloc[-2])
        last_row = data.iloc[-1]
        prev_row = data.iloc[-2]

        # 5) Extraemos valores y formateamos
        last_close: float = float(last_row["Close"])
        prev_close: float = float(prev_row["Close"])

        change: float = last_close - prev_close
        # Evitamos división por cero por robustez
        change_percent: float = (change / prev_close) * 100 if prev_close != 0 else 0.0

        stock_data: StockData = {
            "symbol": symbol,
            "open": round(float(last_row["Open"]), 2),
            "high": round(float(last_row["High"]), 2),
            "low": round(float(last_row["Low"]), 2),
            "price": round(last_close, 2),
            "previous_close": round(prev_close, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": int(last_row["Volume"]),
            # Timestamp en UTC con sufijo Z, similar a ISO 8601
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        return stock_data

    except Exception as e:
        # En un proyecto real, esto iría a logs estructurados (CloudWatch, etc.)
        print(f"[get_stock_data] Error fetching stock data for {symbol}: {e}")
        return None

# ==============================
# 4) Enviar eventos a Kinesis
# ==============================

def put_record_to_kinesis(
    kinesis_client: Any,
    stream_name: str,
    partition_key: str,
    payload: StockData,
) -> Dict[str, Any]:
    """
    Envía un evento (payload) a Kinesis usando put_record.

    - Data: debe ser bytes o string -> aquí usamos json.dumps(payload)
    - PartitionKey: clave para enrutar a un shard (y mantener orden dentro de esa clave)

    Retorna:
    - el response dict de boto3 (incluye ShardId, SequenceNumber, ResponseMetadata, etc.)
    """
    response: Dict[str, Any] = kinesis_client.put_record(
        StreamName=stream_name,
        Data=json.dumps(payload),
        PartitionKey=partition_key,
    )
    return response


def send_to_kinesis_loop(config: AppConfig) -> None:
    """
    Loop infinito (productor continuo):
    - Cada 'delay_seconds':
      1) Obtiene datos desde yfinance
      2) Si ok, los serializa a JSON
      3) Los envía a Kinesis
      4) Imprime la respuesta para depuración

    Se detiene con CTRL+C (KeyboardInterrupt).
    """
    kinesis_client: Any = build_kinesis_client(config.region_name)

    print("=== Stock streaming started ===")
    print(f"Region: {config.region_name}")
    print(f"Stream: {config.stream_name}")
    print(f"Symbol: {config.stock_symbol}")
    print(f"Delay:  {config.delay_seconds}s")
    print("Press CTRL+C to stop.\n")

    while True:
        try:
            # 1) Obtener el evento stock desde Yahoo Finance
            stock_data: Optional[StockData] = get_stock_data(config.stock_symbol)

            # 2) Si no hay data (falló la API o data incompleta), esperamos y reintentamos
            if stock_data is None:
                print("\t[send_to_kinesis_loop] Skipping iteration due to API/data error.")
                time.sleep(config.delay_seconds)
                continue

            # 3) Log local (solo para veamos el evento)
            print(f"\n\n\t[send_to_kinesis_loop] Sending: {stock_data}")

            # 4) Enviar a Kinesis
            response: Dict[str, Any] = put_record_to_kinesis(
                kinesis_client=kinesis_client,
                stream_name=config.stream_name,
                partition_key=config.stock_symbol,  # misma clave => orden para ese símbolo
                payload=stock_data,
            )

            # 5) Revisar status HTTP de la respuesta
            http_status: int = int(response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0))

            if http_status == 200:
                print(f"[send_to_kinesis_loop] Kinesis OK: ShardId={response.get('ShardId')} "
                      f"Seq={response.get('SequenceNumber')}\n")
            else:
                print(f"\t[send_to_kinesis_loop] Kinesis ERROR response: {response}\n")

            # 6) Esperar antes del siguiente evento
            time.sleep(config.delay_seconds)

        except KeyboardInterrupt:
            # Esto ocurre cuando haces CTRL+C
            print("\n=== Stopped by user (CTRL+C) ===")
            break
        except Exception as e:
            print(f"[send_to_kinesis_loop] Unexpected error: {e}")
            time.sleep(config.delay_seconds)


# ==============================
# 5) Punto de entrada
# ==============================

def main() -> None:
    """
    Punto de entrada del script.
    Crea la configuración y arranca el loop de envío a Kinesis.
    """
    config: AppConfig = AppConfig(
        region_name="us-east-1",
        stream_name="stock-market-stream",
        stock_symbol="AAPL",
        delay_seconds=3,
    )
    send_to_kinesis_loop(config)


if __name__ == "__main__":
    main()
