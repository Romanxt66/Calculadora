import unittest
from trading_bot.config import Config
from trading_bot.market import SimulatedMarket, Token
from trading_bot.agents import safety_filter
from trading_bot.portfolio import Portfolio
from trading_bot.bot import run


def tok(**k):
    base = dict(symbol="X", address="x", price=1.0, liquidity_usd=100_000, volume_5m=1, change_5m=0,
                age_minutes=100)
    base.update(k)
    return Token(**base)


class T(unittest.TestCase):
    def test_filters_reject_scams(self):
        c = Config()
        self.assertTrue(safety_filter(tok(liquidity_usd=1000), c))
        self.assertTrue(safety_filter(tok(mint_authority_revoked=False), c))
        self.assertTrue(safety_filter(tok(top_holders_pct=80), c))
        self.assertEqual(safety_filter(tok(), c), [])

    def test_stop_loss(self):
        c = Config(); p = Portfolio(c)
        p.buy("X", "x", 1.0, 0.0)
        p.manage({"x": 0.9})
        self.assertEqual(len(p.pos), 0)
        self.assertEqual(p.losses, 1)

    def test_kill_switch(self):
        c = Config(max_daily_loss_pct=0.05, stop_loss_pct=0.99); p = Portfolio(c)
        p.buy("X", "x", 1.0, 0.0)
        p.manage({"x": 0.5})
        self.assertTrue(p.killed)
        self.assertIsNotNone(p.can_buy())

    def test_live_refused(self):
        with self.assertRaises(SystemExit):
            run(SimulatedMarket(), Config(live=True), 1)

    def test_runs_and_never_spends_more_than_cash(self):
        p = run(SimulatedMarket(3), Config(), 150, verbose=False)
        self.assertGreaterEqual(p.cash, 0)


if __name__ == "__main__":
    unittest.main()
