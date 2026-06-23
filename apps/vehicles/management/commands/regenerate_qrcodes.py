from django.core.management.base import BaseCommand

from apps.vehicles.models import Vehicle
from apps.vehicles.services import generate_qr_code


class Command(BaseCommand):
    help = "Regenerate QR codes for all approved vehicles using absolute public profile URLs"

    def add_arguments(self, parser):
        parser.add_argument("--domain", type=str, required=True, help="Base domain, e.g. https://saferideng-production.up.railway.app")

    def handle(self, *args, **options):
        domain = options["domain"].rstrip("/")
        vehicles = Vehicle.objects.filter(verification_status=Vehicle.VerificationStatus.approved)
        count = 0
        for vehicle in vehicles:
            target_url = f"{domain}/driver/{vehicle.driver.uuid}/vehicle/{vehicle.uuid}/"
            generate_qr_code(vehicle, target_url)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Regenerated QR codes for {count} vehicle(s)."))
