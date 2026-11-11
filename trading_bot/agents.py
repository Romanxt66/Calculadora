"""Los 5 agentes: SMARTS, TRENDS, DEBATE, ROUTER, EXEC (EXEC vive en portfolio/bot)."""
import json
import os
import urllib.request
from dataclasses import dataclass

from .config import Config
from .market import Token


def safety_filter(t: Token, cfg: Config) -> list[str]:
    """Filtros anti-estafa. Devuelve los motivos de rechazo (lista vacía = pasa)."""
    why = []
    if t.liquidity_usd < cfg.min_liquidity_usd:
        why.append("liquidez baja")
    if t.age_minutes < cfg.min_age_minutes:
        why.append("token muy nuevo")
    if t.top_holders_pct > cfg.max_top_holders_pct:
        why.append("holders concentrados")
    if not t.mint_authority_revoked:
        why.append("mint no revocado")
    if t.price <= 0:
        why.append("precio inválido")
    return why


def smarts(t: Token) -> float:
    """Puntuación 0-1 por actividad de smart money."""
    return min(t.smart_wallets / 4, 1.0)


def trends(t: Token) -> float:
    """Puntuación 0-1 por ranking de tendencia y volumen."""
    return max(0.0, 1 - (t.trending_rank - 1) / 10)


@dataclass
class Debate:
    bull: float
    bear: float
    risk_ok: bool
    reason: str


def debate(t: Token, cfg: Config) -> Debate:
    """Debate alcista/bajista con reglas (sustituible por un LLM)."""
    bull = smarts(t) * 0.5 + trends(t) * 0.3 + (0.2 if 0 < t.change_5m < 8 else 0)
    bear = 0.0
    if t.change_5m > 12:
        bear += 0.5   # ya subió demasiado: llegamos tarde
    if t.change_5m < -3:
        bear += 0.4
    if t.smart_wallets == 0:
        bear += 0.3
    risk = safety_filter(t, cfg)
    return Debate(bull, bear, not risk, ", ".join(risk) or "ok")


def llm_debate(t: Token, rule: Debate) -> Debate:
    """Opcional: pide a Claude un veredicto. Sin ANTHROPIC_API_KEY usa solo las reglas.
    Claude solo puede VETAR (bajar la puntuación), nunca saltarse filtros de seguridad."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key or not rule.risk_ok:
        return rule
    prompt = (f"Token {t.symbol}: liquidez ${t.liquidity_usd:,.0f}, cambio 5m {t.change_5m:.1f}%, "
              f"smart wallets {t.smart_wallets}, ranking {t.trending_rank}, edad {t.age_minutes}min. "
              'Responde SOLO JSON: {"veto": true|false, "motivo": "..."}')
    body = json.dumps({"model": os.getenv("BOT_MODEL", "claude-haiku-5-5"), "max_tokens": 120,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", body, {
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            txt = json.load(r)["content"][0]["text"]
        out = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
        if out.get("veto"):
            return Debate(rule.bull, rule.bear + 1, rule.risk_ok, "LLM: " + str(out.get("motivo", "")))
    except Exception as e:  # si falla el LLM, seguimos con las reglas
        rule.reason += f" (LLM no disponible: {type(e).__name__})"
    return rule


def router(t: Token, cfg: Config, size_usd: float) -> float | None:
    """Estima el slippage por tamaño vs liquidez; rechaza rutas malas. En real: cotización de Jupiter."""
    impact = size_usd / max(t.liquidity_usd, 1)
    slip = cfg.slippage_pct + impact
    return None if slip > 0.03 else slip


def decide(t: Token, cfg: Config, use_llm: bool = False) -> tuple[bool, Debate]:
    d = debate(t, cfg)
    if use_llm:
        d = llm_debate(t, d)
    return (d.risk_ok and d.bull - d.bear >= 0.45), d
