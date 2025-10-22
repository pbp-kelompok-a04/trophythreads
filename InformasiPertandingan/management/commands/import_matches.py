import csv
from django.core.management.base import BaseCommand
from InformasiPertandingan.models import Country, Informasi
from datetime import datetime

class Command(BaseCommand):
    help = 'Imports match data from a CSV file into the database'

    def handle(self, *args, **kwargs):
        # Path to your CSV file
        csv_file_path = 'matches.csv'
        
        self.stdout.write(f"Starting import from {csv_file_path}...")

        # Optional: Clear existing data to avoid duplicates on re-runs
        # Informasi.objects.all().delete()
        # Country.objects.all().delete()

        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # Use get_or_create for the Country model to avoid duplicates
                home_team, _ = Country.objects.get_or_create(
                    name=row['home_team_name'],
                    defaults={'flag': row['home_team_flag_url']}
                )
                
                away_team, _ = Country.objects.get_or_create(
                    name=row['away_team_name'],
                    defaults={'flag': row['away_team_flag_url']}
                )

                # Create the Informasi object
                Informasi.objects.create(
                    title=row['title'],
                    date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                    city=row['city'],
                    home_team=home_team,
                    away_team=away_team,
                    score_home_team=int(row['home_score']),
                    score_away_team=int(row['away_score']),
                    views=int(row['views'])
                )

        self.stdout.write(self.style.SUCCESS('Successfully imported data from CSV.'))