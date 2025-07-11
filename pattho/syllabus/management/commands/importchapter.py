import csv
from django.core.management.base import BaseCommand
from syllabus.models import Subject, Chapter

class Command(BaseCommand):
    help = 'Imports chapters from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the chapters CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        
        self.stdout.write(self.style.SUCCESS(f'Attempting to import chapters from {csv_file_path}'))

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for i, row in enumerate(reader):
                    if len(row) < 2:
                        self.stdout.write(self.style.WARNING(f'Skipping row {i+1}: Not enough columns. Expected at least 2, got {len(row)}'))
                        continue

                    subject_name = row[0].strip()
                    chapter_title = row[1].strip()

                    try:
                        subject = Subject.objects.get(name__iexact=subject_name)
                    except Subject.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'Subject "{subject_name}" not found for chapter "{chapter_title}". Skipping.'))
                        continue

                    # Determine the next chapter number for this subject
                    last_chapter = Chapter.objects.filter(subject=subject).order_by('-chapter_number').first()
                    next_chapter_number = (last_chapter.chapter_number + 1) if last_chapter else 1

                    chapter, created = Chapter.objects.get_or_create(
                        subject=subject,
                        title=chapter_title,
                        defaults={
                            'chapter_number': next_chapter_number,
                            'topic_count': 1,  # Default value
                            'recommended_time': 0.0,  # Default value
                            'importance': {},  # Default empty JSON
                        }
                    )

                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully added chapter: "{chapter_title}" to subject "{subject_name}" with chapter number {next_chapter_number}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Chapter "{chapter_title}" already exists for subject "{subject_name}". Skipping.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Error: CSV file not found at {csv_file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An unexpected error occurred: {e}'))
