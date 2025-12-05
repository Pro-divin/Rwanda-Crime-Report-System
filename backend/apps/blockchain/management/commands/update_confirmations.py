"""Management command to batch refresh blockchain anchor confirmations.

Usage:
    python manage.py update_confirmations [--max <N>] [--min-conf <M>]

Logic:
 - Select anchors with status in (pending, submitted) OR confirmations < min_conf
 - Query transaction status via CardanoEvidenceAnchoring.get_transaction_status
 - Update confirmations, block_height, status transitions:
       pending -> submitted (if on_chain but 0 conf)
       submitted -> confirmed (if confirmations >= min_conf)
 - Prints a summary table.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.blockchain.models import BlockchainAnchor
from apps.blockchain.cardano_utils import CardanoEvidenceAnchoring


class Command(BaseCommand):
    help = "Refresh blockchain anchor confirmations in batch"

    def add_arguments(self, parser):
        parser.add_argument('--max', type=int, default=100, help='Max anchors to process')
        parser.add_argument('--min-conf', type=int, default=1, help='Confirmations threshold for confirmed status')

    def handle(self, *args, **options):
        max_count = options['max']
        min_conf = options['min_conf']
        cardano = CardanoEvidenceAnchoring()

        queryset = BlockchainAnchor.objects.order_by('updated_at')
        queryset = queryset.filter(status__in=[BlockchainAnchor.Status.PENDING, BlockchainAnchor.Status.SUBMITTED])[:max_count]

        processed = []
        for anchor in queryset:
            tx_hash = anchor.transaction_hash
            if not tx_hash:
                continue
            # Some versions expose a standalone util; fallback if method missing
            status = cardano.get_transaction_status(tx_hash)
            on_chain = status.get('on_chain')
            confirmations = status.get('confirmations') or 0
            block_height = status.get('block_height')

            old_status = anchor.status
            # Status transitions
            if on_chain and confirmations == 0 and anchor.status == BlockchainAnchor.Status.PENDING:
                anchor.status = BlockchainAnchor.Status.SUBMITTED
            if confirmations >= min_conf:
                anchor.status = BlockchainAnchor.Status.CONFIRMED

            anchor.confirmations = confirmations
            if block_height is not None:
                anchor.block_number = block_height
            anchor.save(update_fields=['confirmations', 'block_number', 'status', 'updated_at'])

            processed.append({
                'report_id': anchor.report_id,
                'tx_hash': tx_hash[:12] + '...' if tx_hash else None,
                'old_status': old_status,
                'new_status': anchor.status,
                'confirmations': confirmations,
                'on_chain': on_chain,
            })

        # Output summary
        if not processed:
            self.stdout.write(self.style.WARNING('No anchors eligible for update.'))
            return

        header = f"Processed {len(processed)} anchors (min_conf={min_conf})"
        self.stdout.write(self.style.SUCCESS(header))
        for row in processed:
            self.stdout.write(
                f"{row['report_id']}: {row['tx_hash']} {row['old_status']} -> {row['new_status']} conf={row['confirmations']} on_chain={row['on_chain']}"
            )