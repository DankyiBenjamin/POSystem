from django.core.management.base import BaseCommand
from sales.models import Sale, Credit, ReceiptSequence
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = 'Reset and backfill ALL Sale and Credit receipt codes using new ReceiptSequence logic'

    def handle(self, *args, **kwargs):
        year = timezone.now().year

        print("🔁 Resetting all receipt codes...")
        Sale.objects.update(receipt_code=None)
        Credit.objects.update(receipt_code=None)
        ReceiptSequence.objects.all().update(last_sale_number=0, last_credit_number=0)

        shop_ids = set(Sale.objects.values_list('shop_id', flat=True)) | set(Credit.objects.values_list('shop_id', flat=True))

        for shop_id in shop_ids:
            sequence, _ = ReceiptSequence.objects.get_or_create(shop_id=shop_id)
            print(f"\n📦 Processing Shop ID {shop_id}...")

            sales = Sale.objects.filter(shop_id=shop_id).order_by('closed_at', 'id')
            for sale in sales:
                with transaction.atomic():
                    sequence.last_sale_number += 1
                    sale.receipt_code = f"SL-SHOP{shop_id}-{year}-{sequence.last_sale_number:04d}"
                    sale.save()

            print(f"  ✅ Rebuilt {sales.count()} sale receipts")

            credits = Credit.objects.filter(shop_id=shop_id).order_by('credited_at', 'id')
            for credit in credits:
                with transaction.atomic():
                    sequence.last_credit_number += 1
                    credit.receipt_code = f"CR-SHOP{shop_id}-{year}-{sequence.last_credit_number:04d}"
                    credit.save()

            print(f"  ✅ Rebuilt {credits.count()} credit receipts")

            sequence.save()

        print("\n✅ Done! All receipt codes have been re-sequenced.")
