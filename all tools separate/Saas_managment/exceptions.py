"""Custom exceptions for the SaaS Spend ingestion layer."""


class DataNotReadyError(Exception):
    """Raised when a requested dataset version is not available."""


class DiscoveryRequiredError(Exception):
    """Raised when a vendor/table must first be profiled in discovery mode."""


class VersionPromotionError(Exception):
    """Raised when the current version cannot be promoted safely."""
