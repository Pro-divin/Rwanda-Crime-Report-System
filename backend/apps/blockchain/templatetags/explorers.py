from django import template
from django.conf import settings

register = template.Library()


NETWORK_EXPLORERS = {
    # Cardano Preview Testnet
    'preview': {
        'primary': {'tx': 'https://preview.cexplorer.io/tx/{hash}', 'label': 'cexplorer (preview)'},
        'secondary': {'tx': 'https://preview.cardanoscan.io/transaction/{hash}', 'label': 'Cardanoscan (preview)'}
    },
    # Cardano Preprod Testnet
    'preprod': {
        'primary': {'tx': 'https://preprod.cexplorer.io/tx/{hash}', 'label': 'cexplorer (preprod)'},
        'secondary': {'tx': 'https://preprod.cardanoscan.io/transaction/{hash}', 'label': 'Cardanoscan (preprod)'}
    },
    # Mainnet
    'mainnet': {
        'primary': {'tx': 'https://cexplorer.io/tx/{hash}', 'label': 'cexplorer'},
        'secondary': {'tx': 'https://cardanoscan.io/transaction/{hash}', 'label': 'Cardanoscan'}
    },
}


@register.simple_tag
def tx_url(tx_hash: str):
    """Return the appropriate explorer URL for a transaction hash based on CARDANO_NETWORK."""
    if not tx_hash:
        return ''
    network = getattr(settings, 'CARDANO_NETWORK', 'preview') or 'preview'
    conf = NETWORK_EXPLORERS.get(network, NETWORK_EXPLORERS['preview'])
    return conf['primary']['tx'].format(hash=tx_hash)


@register.simple_tag
def tx_explorer_label():
    """Return a short label for the explorer being used based on CARDANO_NETWORK."""
    network = getattr(settings, 'CARDANO_NETWORK', 'preview') or 'preview'
    conf = NETWORK_EXPLORERS.get(network, NETWORK_EXPLORERS['preview'])
    return conf['primary']['label']


@register.simple_tag
def tx_urls(tx_hash: str):
    """Return a list of explorer urls (primary + secondary) for the given network."""
    if not tx_hash:
        return []
    network = getattr(settings, 'CARDANO_NETWORK', 'preview') or 'preview'
    conf = NETWORK_EXPLORERS.get(network, NETWORK_EXPLORERS['preview'])
    return [
        {'url': conf['primary']['tx'].format(hash=tx_hash), 'label': conf['primary']['label']},
        {'url': conf['secondary']['tx'].format(hash=tx_hash), 'label': conf['secondary']['label']},
    ]
