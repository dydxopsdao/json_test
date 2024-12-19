# Critical paths for validation
CRITICAL_PATHS = {
    "wallets.*.signTypedDataAction",
    "wallets.*.signTypedDataDomainName",
    "governance.*.newMarketProposal.initialDepositAmount",
    "governance.*.newMarketProposal.delayBlocks",
}

# Patterns to identify mainnet-related keys
MAINNET_PATTERNS = [
    "[mainnet chain id]",
    "dydx-mainnet-1",
    "dydxprotocol-mainnet",
]

# API endpoints that should be skipped during validation
API_ENDPOINTS = {
    # Core API Endpoints
    "api.dydx.exchange",
    "indexer.dydx.trade",
    "api.skip.money",
    "api.squidrouter.com",
    "execute-api.ap-northeast-1.amazonaws.com",
    "infrastructure-34d.workers.dev",
    "api.mainnet-beta.solana.com",
    "cloud.chaoslabs.co",
    # RPC and Validator Endpoints
    "rpc.osmosis.zone",
    "dydx-dao-rpc.polkachu.com",
    "mainnet-full-rpc.public.blastapi.io",
    "dydx-ops-rpc.kingnodes.com",
    "neutron-rpc.publicnode.com",
    "noble-yx-rpc.polkachu.com",
    # Service-specific endpoints
    "dydx.fuul.xyz",
    "indexer.dydx.exchange",
    "validator.dydx.exchange",
    "faucet.dydx.exchange",
    "testnet.dydx.exchange",
    "staging.dydx.exchange",
}

# App Store validation configuration
APP_STORE_CONFIG = {
    "ios": {
        "valid_ids": ["6475599596"],  # Current valid Apple App Store IDs
        "url_patterns": [
            r"^https://apps\.apple\.com/app/(?:[\w-]+/)?id(\d+)/?$",  # Basic pattern
            r"^https://apps\.apple\.com/\w+/app/(?:[\w-]+/)?id(\d+)/?$",  # With country code
            r"^https://apps\.apple\.com/app/dydx/id(\d+)/?$",  # With app name
        ],
    },
    "android": {
        "valid_ids": [
            "trade.opsdao.dydxchain"
        ],  # Current valid Play Store package names
        "url_patterns": [
            r"^https://play\.google\.com/store/apps/details\?id=([\w\.]+)(?:&.*)?$"
        ],
    },
}

# Error patterns to check in webpage content
ERROR_PATTERNS = [
    {
        "pattern": r"404.*not\s+found",
        "min_parts": 2,  # Requires both "404" and "not found"
        "description": "404 Not Found Error",
    },
    {
        "pattern": r"page.*(?:doesn't|does\s+not)\s+exist",
        "min_parts": 2,  # Requires both "page" and "doesn't exist"
        "description": "Page Not Found Error",
    },
    {
        "pattern": r"uh\s+oh.*error",
        "min_parts": 2,  # Requires both "uh oh" and "error"
        "description": "Generic Error Page",
    },
]

# URLs that should be skipped during validation
URL_EXCEPTION_LIST = [
    # Placeholder and development URLs
    "[placeholder]",
    "https://example.com",
    "https://localhost",
    "https://api.test",
    # Development environment URLs
    "http://dev",
    "https://dev",
    "staging",
    "test",
]

# Paths where value matching should be ignored
IGNORE_VALUE_MATCH = [
    # App-specific paths
    "apps.ios.scheme",
    "apps.android.url",
    # Token-related paths
    "tokens.[mainnet chain id].chain.name",
    "tokens.[mainnet chain id].chain.denom",
    # Environment-specific paths
    "environments.dydxprotocol-mainnet.name",
    "environments.dydxprotocol-mainnet.megavaultHistoryStartDateMs",
    "environments.dydxprotocol-mainnet.megavaultOperatorName",
    # Feature flags
    "environments.dydxprotocol-mainnet.featureFlags.checkForGeo",
    "environments.dydxprotocol-mainnet.featureFlags.CCTPDepositOnly",
    # Governance paths
    "governance.[mainnet chain id].newMarketProposal.delayBlocks",
    "governance.[mainnet chain id].newMarketProposal.initialDepositAmount",
    # Endpoint paths
    "environments.dydxprotocol-mainnet.endpoints.validators",
    "environments.dydxprotocol-mainnet.endpoints.indexers",
    "environments.dydxprotocol-mainnet.endpoints.skip",
    "environments.dydxprotocol-mainnet.endpoints.0xsquid",
    "environments.dydxprotocol-mainnet.endpoints.solanaRpcUrl",
]
