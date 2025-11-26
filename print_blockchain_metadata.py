#!/usr/bin/env python3
import os, sys
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
import django
django.setup()
from apps.blockchain.models import BlockchainAnchor

anchors = BlockchainAnchor.objects.all()
print(f"Total anchors: {anchors.count()}")
for a in anchors:
    print('---')
    print('report_id:', a.report_id)
    print('tx:', a.transaction_hash)
    print('metadata:', a.metadata)
    print('type metadata:', type(a.metadata))
