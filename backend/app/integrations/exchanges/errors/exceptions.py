from app.domain.exchange.models import ExchangeCapability
from app.domain.exchange.value_objects import ExchangeErrorCategory


class ExchangeIntegrationError(Exception):
    category: ExchangeErrorCategory = ExchangeErrorCategory.CONFIGURATION

    def __init__(
        self,
        message: str,
        *,
        category: ExchangeErrorCategory | None = None,
        retryable: bool = False,
        retry_after_seconds: float | None = None,
        raw_error: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category or self.category
        self.retryable = retryable
        self.retry_after_seconds = retry_after_seconds
        self.raw_error = raw_error


class ExchangeConfigurationError(ExchangeIntegrationError):
    category = ExchangeErrorCategory.CONFIGURATION


class ExchangeCredentialError(ExchangeIntegrationError):
    category = ExchangeErrorCategory.CREDENTIAL


class ExchangeValidationError(ExchangeIntegrationError):
    category = ExchangeErrorCategory.VALIDATION


class ExchangeRateLimitError(ExchangeIntegrationError):
    category = ExchangeErrorCategory.RATE_LIMIT
    retryable = True


class ExchangeNetworkError(ExchangeIntegrationError):
    category = ExchangeErrorCategory.NETWORK
    retryable = True


class ExchangeTemporaryError(ExchangeIntegrationError):
    category = ExchangeErrorCategory.TEMPORARY_EXCHANGE
    retryable = True


class ExchangeUnknownOrderStateError(ExchangeIntegrationError):
    category = ExchangeErrorCategory.UNKNOWN_ORDER_STATE


class ExchangeReconciliationError(ExchangeIntegrationError):
    category = ExchangeErrorCategory.RECONCILIATION


class ExchangeFailoverError(ExchangeIntegrationError):
    category = ExchangeErrorCategory.FAILOVER
