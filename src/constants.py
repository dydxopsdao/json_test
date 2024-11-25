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
