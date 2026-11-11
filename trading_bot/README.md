# Bot de trading en simulación (paper trading)

Réplica educativa de la idea del video: 5 "agentes" (SMARTS, TRENDS, DEBATE, ROUTER, EXEC)
que deciden compras de memecoins de Solana. **Solo simula**: no firma ni envía transacciones.

    python -m trading_bot.bot --source sim --ticks 300          # mercado simulado (offline)
    python -m trading_bot.bot --source dexscreener --ticks 1000 --sleep 300   # datos reales, operaciones simuladas
    ANTHROPIC_API_KEY=... python -m trading_bot.bot --source dexscreener --llm  # Claude puede vetar
    python -m unittest discover -s tests_bot -t .

## Límites duros (config.py)
stop-loss -8%, máx. 20% del capital por operación, máx. 4 posiciones, pérdida diaria 15% => kill switch,
tope de operaciones por hora, filtros de liquidez/edad/holders/mint.

## Qué falta antes de poder usar dinero real
- `smart_wallets` y `top_holders_pct` con una fuente real (GMGN/Birdeye): con DexScreener quedan neutros,
  así que SMARTS no aporta nada todavía.
- Ejecución real (Jupiter + wallet): no está implementada a propósito. Hazlo solo tras semanas de
  simulación con resultado positivo *después de comisiones*, con wallet nueva y fondos pequeños.
- Nunca guardes claves privadas en el repo; usa variables de entorno / `.env` ignorado por git.
