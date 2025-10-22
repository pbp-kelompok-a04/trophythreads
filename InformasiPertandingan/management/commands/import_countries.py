import csv
from django.core.management.base import BaseCommand
from InformasiPertandingan.models import Country

class Command(BaseCommand):
    help = 'Imports countries from countries.csv into the Country model'

    def handle(self, *args, **kwargs):
        csv_file_path = 'countries.csv'
        self.stdout.write(f"Importing countries from {csv_file_path}...")

        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Optional: Clear existing countries to start fresh
            # Country.objects.all().delete()

            for row in reader:
                # Use get_or_create to avoid creating duplicate countries
                country, created = Country.objects.get_or_create(
                    name=row['name'],
                    defaults={'flag': row['flag_url']}
                )
                if created:
                    self.stdout.write(f"  > Created country: {country.name}")

        self.stdout.write(self.style.SUCCESS('Successfully imported all countries.'))