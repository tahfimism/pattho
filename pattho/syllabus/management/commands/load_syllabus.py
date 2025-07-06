# your_app/management/commands/load_syllabus.py
import json
from django.core.management.base import BaseCommand
from your_app.models import Subject, Chapter, Topic

class Command(BaseCommand):
    help = 'Loads syllabus data from JSON files'
    
    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to JSON file')
    
    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                syllabus_data = json.load(f)
            
            self.stdout.write(f'Loading syllabus for {syllabus_data["subject"]}')
            
            # Create subject
            subject = Subject.objects.create(
                name=syllabus_data['subject'],
                chapter_count=len(syllabus_data['chapters'])
            )
            
            for chapter_data in syllabus_data['chapters']:
                # Create chapter
                chapter = Chapter.objects.create(
                    subject=subject,
                    title=chapter_data['title'],
                    chapter_number=chapter_data['chapter_number'],
                    recommended_time=chapter_data['recommended_time'],
                    importance=chapter_data.get('importance', {
                        'hsc': 0,
                        'engineering': 0,
                        'medical': 0,
                        'varsity': 0
                    }),
                    topic_count=len(chapter_data['topics'])
                )
                
                for topic_data in chapter_data['topics']:
                    # Create topic
                    Topic.objects.create(
                        chapter=chapter,
                        title=topic_data['title'],
                        order=topic_data['order'],
                        description=topic_data.get('description', ''),
                        resource_link=topic_data.get('resource_link', ''),
                        importance=topic_data.get('importance', {
                            'hsc': 10,
                            'engineering': 10,
                            'medical': 10,
                            'varsity': 10
                        }),
                        time_percent=topic_data.get('time_percent', 10)
                    )
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully loaded syllabus: {subject.chapter_count} chapters, '
                f'{sum(c.topic_count for c in subject.chapters.all())} topics'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))