# ════════════════════════════════════════════════════════════════
# PAYMENT ADAPTER FACTORY
# apps/transactions/infrastructure/adapters/factory.py
# ════════════════════════════════════════════════════════════════

from apps.transactions.domain.entities import IPaymentAdapter
from .wave_adapter import WaveAdapter
from .orange_adapter import OrangeMoneyAdapter

def get_payment_adapter(provider: str) -> IPaymentAdapter:
    """Factory : retourne l'adapter selon le provider."""
    if provider == "wave":
        return WaveAdapter()
    if provider == "orange_money":
        return OrangeMoneyAdapter()
    raise ValueError(f"Provider inconnu : {provider}")
