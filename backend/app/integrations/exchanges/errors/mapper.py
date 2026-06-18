from app.domain.exchange.value_objects import ExchangeErrorCategory
from .exceptions import (
    ExchangeCredentialError,
    ExchangeIntegrationError,
    ExchangeNetworkError,
    ExchangeRateLimitError,
    ExchangeTemporaryError,
    ExchangeValidationError,
)


class ExchangeErrorMapper:
    retryable_categories = {
        ExchangeErrorCategory.RATE_LIMIT,
        ExchangeErrorCategory.NETWORK,
        ExchangeErrorCategory.TEMPORARY_EXCHANGE,
    }

    def map_error(self, error: Exception, *, exchange_name: str = "exchange") -> ExchangeIntegrationError:
        if isinstance(error, ExchangeIntegrationError):
            return error

        message = str(error)
        lower_message = message.lower()

        if any(token in lower_message for token in ("api key", "apikey", "invalid api", "permission", "forbidden", "unauthorized")):
            return ExchangeCredentialError(message, raw_error=error)

        if any(token in lower_message for token in ("invalid symbol", "unknown symbol", "quantity", "price", "insufficient", "balance")):
            return ExchangeValidationError(message, raw_error=error)

        if any(token in lower_message for token in ("rate limit", "too many requests", "429")):
            return ExchangeRateLimitError(message, raw_error=error)

        if any(token in lower_message for token in ("timeout", "connection", "network", "dns", "reset")):
            return ExchangeNetworkError(message, raw_error=error)

        if any(token in lower_message for token in ("temporarily", "maintenance", "503", "502", "500")):
            return ExchangeTemporaryError(message, raw_error=error)

        return ExchangeIntegrationError(
            message,
            category=ExchangeErrorCategory.TEMPORARY_EXCHANGE,
            retryable=True,
            raw_error=error,
        )

    def is_retryable(self, error: Exception) -> bool:
        mapped = self.map_error(error)
        return mapped.retryable or mapped.category in self.retryable_categories
