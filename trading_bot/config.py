"""Configuración y límites duros. Modo simulación por defecto."""
import os
from dataclasses import dataclass


@dataclass
class Config:
    start_capital: float = 110.0
    max_per_trade_pct: float = 0.20   # máx. 20% del capital por operación
    max_open_positions: int = 4
    stop_loss_pct: float = 0.08       # stop obligatorio -8%
    take_profit_pct: float = 0.25
    max_daily_loss_pct: float = 0.15  # corta el bot si pierde 15% en el día
    max_trades_per_hour: int = 12
    min_liquidity_usd: float = 25_000
    min_age_minutes: int = 30
    max_top_holders_pct: float = 35.0
    slippage_pct: float = 0.01        # 1% simulado por entrada/salida
    fee_pct: float = 0.003            # 0.3% por operación
    live: bool = False                # NUNCA True salvo que tú lo actives

    @classmethod
    def from_env(cls) -> "Config":
        c = cls()
        c.live = os.getenv("BOT_LIVE") == "1"
        return c
