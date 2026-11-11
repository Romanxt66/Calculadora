"""Fuentes de datos. DexScreener (real, sin clave) y un mercado simulado."""
import json
import random
import urllib.request
from dataclasses import dataclass, field


@dataclass
class Token:
    symbol: str
    address: str
    price: float
    liquidity_usd: float
    volume_5m: float
    change_5m: float
    age_minutes: int
    top_holders_pct: float = 20.0
    mint_authority_revoked: bool = True
    smart_wallets: int = 0   # nº de wallets "smart" comprando (dato externo, p.ej. GMGN)
    trending_rank: int = 99


class SimulatedMarket:
    """Random walk reproducible. Incluye tokens trampa para probar los filtros."""

    def __init__(self, seed: int = 7, n: int = 12):
        self.rng = random.Random(seed)
        self.t = 0
        self.tokens = []
        for i in range(n):
            bad = i % 4 == 3
            self.tokens.append(Token(
                symbol=f"TKN{i}", address=f"sim{i}",
                price=self.rng.uniform(0.0001, 0.05),
                liquidity_usd=self.rng.uniform(5_000, 200_000) if not bad else 4_000,
                volume_5m=self.rng.uniform(1_000, 50_000), change_5m=0.0,
                age_minutes=self.rng.randint(5, 600),
                top_holders_pct=self.rng.uniform(8, 30) if not bad else 70,
                mint_authority_revoked=not bad))

    def tick(self) -> list[Token]:
        self.t += 1
        for k in self.tokens:
            r = self.rng.gauss(0.0, 0.03)
            k.change_5m = r * 100
            k.price = max(k.price * (1 + r), 1e-9)
            k.volume_5m = max(0, k.volume_5m * self.rng.uniform(0.7, 1.4))
            k.age_minutes += 5
            k.smart_wallets = max(0, int(self.rng.gauss(1.5 if r > 0 else 0.5, 1.2)))
        ranked = sorted(self.tokens, key=lambda x: -x.volume_5m)
        for i, k in enumerate(ranked):
            k.trending_rank = i + 1
        return list(self.tokens)


class DexScreenerMarket:
    """Datos reales. smart_wallets/top_holders requieren otra fuente (GMGN/Birdeye): quedan neutros."""
    BASE = "https://api.dexscreener.com"

    def _get(self, path):
        req = urllib.request.Request(self.BASE + path, headers={"User-Agent": "paper-bot"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r)

    def tick(self) -> list[Token]:
        boosts = self._get("/token-boosts/top/v1")
        addrs = [b["tokenAddress"] for b in boosts if b.get("chainId") == "solana"][:30]
        if not addrs:
            return []
        pairs = self._get("/tokens/v1/solana/" + ",".join(addrs))
        out, seen = [], set()
        for rank, p in enumerate(pairs):
            addr = p["baseToken"]["address"]
            if addr in seen:
                continue
            seen.add(addr)
            created = p.get("pairCreatedAt") or 0
            import time
            age = int((time.time() * 1000 - created) / 60000) if created else 0
            out.append(Token(
                symbol=p["baseToken"]["symbol"], address=addr,
                price=float(p.get("priceUsd") or 0),
                liquidity_usd=(p.get("liquidity") or {}).get("usd", 0),
                volume_5m=(p.get("volume") or {}).get("m5", 0),
                change_5m=(p.get("priceChange") or {}).get("m5", 0),
                age_minutes=age, trending_rank=rank + 1))
        return out
