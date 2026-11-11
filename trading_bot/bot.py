"""Orquestador. Uso:  python -m trading_bot.bot --source sim --ticks 200"""
import argparse
import time

from .agents import decide, router
from .config import Config
from .market import DexScreenerMarket, SimulatedMarket
from .portfolio import Portfolio


def run(source, cfg: Config, ticks: int, use_llm=False, sleep=0.0, verbose=True):
    if cfg.live:
        raise SystemExit("Modo real no implementado a propósito: ver README. Usa simulación.")
    pf = Portfolio(cfg)
    fake_now = 0.0
    for i in range(ticks):
        tokens = source.tick()
        prices = {t.address: t.price for t in tokens}
        fake_now += 300  # cada tick = 5 min
        pf.manage(prices)
        if not pf.killed:
            for t in sorted(tokens, key=lambda x: x.trending_rank):
                if t.address in pf.pos or pf.can_buy(fake_now):
                    continue
                ok, d = decide(t, cfg, use_llm)
                if not ok:
                    continue
                slip = router(t, cfg, cfg.max_per_trade_pct * cfg.start_capital)
                if slip is None:
                    continue
                pf.buy(t.symbol, t.address, t.price, slip, fake_now)
        if verbose and i % 20 == 0:
            print(f"tick {i:4d}  valor ${pf.value(prices):8.2f}  pos {len(pf.pos)}  {pf.wins}W {pf.losses}L"
                  + ("  [KILL]" if pf.killed else ""))
        if sleep:
            time.sleep(sleep)
    final = pf.value(prices)
    print(f"\nInicio ${cfg.start_capital:.2f} -> Final ${final:.2f} ({final / cfg.start_capital:.2f}x) "
          f"| {pf.wins}W {pf.losses}L | operaciones {len(pf.log)}")
    return pf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["sim", "dexscreener"], default="sim")
    ap.add_argument("--ticks", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--llm", action="store_true", help="usa Claude como veto (ANTHROPIC_API_KEY)")
    ap.add_argument("--sleep", type=float, default=0.0, help="segundos entre ticks (300 en real)")
    a = ap.parse_args()
    src = SimulatedMarket(a.seed) if a.source == "sim" else DexScreenerMarket()
    run(src, Config.from_env(), a.ticks, a.llm, a.sleep)


if __name__ == "__main__":
    main()
