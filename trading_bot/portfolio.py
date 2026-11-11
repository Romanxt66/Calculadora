"""Cartera simulada con límites duros (stop-loss, pérdida diaria, kill switch)."""
import time
from dataclasses import dataclass, field

from .config import Config


@dataclass
class Position:
    symbol: str
    address: str
    qty: float
    entry: float
    cost: float


class Portfolio:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.cash = cfg.start_capital
        self.pos: dict[str, Position] = {}
        self.log: list[dict] = []
        self.wins = self.losses = 0
        self.day_start_value = cfg.start_capital
        self.killed = False
        self._trade_times: list[float] = []

    def value(self, prices: dict[str, float]) -> float:
        return self.cash + sum(p.qty * prices.get(a, p.entry) for a, p in self.pos.items())

    def can_buy(self, now: float | None = None) -> str | None:
        now = now or time.time()
        self._trade_times = [x for x in self._trade_times if now - x < 3600]
        if self.killed:
            return "kill switch"
        if len(self.pos) >= self.cfg.max_open_positions:
            return "máx. posiciones"
        if len(self._trade_times) >= self.cfg.max_trades_per_hour:
            return "tope de operaciones/hora"
        return None

    def buy(self, symbol, address, price, slip, now=None) -> bool:
        if address in self.pos or self.can_buy(now):
            return False
        size = min(self.cfg.max_per_trade_pct * self.cfg.start_capital, self.cash)
        if size < 1:
            return False
        fill = price * (1 + slip)
        net = size * (1 - self.cfg.fee_pct)
        self.cash -= size
        self.pos[address] = Position(symbol, address, net / fill, fill, size)
        self._trade_times.append(now or time.time())
        self.log.append({"side": "BUY", "symbol": symbol, "usd": round(size, 2), "price": fill})
        return True

    def sell(self, address, price, slip, reason) -> float:
        p = self.pos.pop(address)
        proceeds = p.qty * price * (1 - slip) * (1 - self.cfg.fee_pct)
        pnl = proceeds - p.cost
        self.cash += proceeds
        self.wins += pnl > 0
        self.losses += pnl <= 0
        self.log.append({"side": "SELL", "symbol": p.symbol, "pnl": round(pnl, 2), "reason": reason})
        return pnl

    def manage(self, prices: dict[str, float]):
        """Stop-loss / take-profit obligatorios."""
        for addr in list(self.pos):
            p = self.pos[addr]
            px = prices.get(addr)
            if px is None:
                continue
            chg = px / p.entry - 1
            if chg <= -self.cfg.stop_loss_pct:
                self.sell(addr, px, self.cfg.slippage_pct, "stop-loss")
            elif chg >= self.cfg.take_profit_pct:
                self.sell(addr, px, self.cfg.slippage_pct, "take-profit")
        if self.value(prices) <= self.day_start_value * (1 - self.cfg.max_daily_loss_pct):
            self.killed = True  # pérdida diaria máxima: se apaga
