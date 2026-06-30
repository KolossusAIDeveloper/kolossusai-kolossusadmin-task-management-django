from django.core.management.base import BaseCommand
from django.utils import timezone
from tasks.models import Task, Comment
import datetime


class Command(BaseCommand):
    help = 'Seed the database with sample tasks'

    def handle(self, *args, **kwargs):
        if Task.objects.exists():
            self.stdout.write('Data already exists, skipping seed.')
            return

        today = datetime.date.today()

        tasks_data = [
            {
                'title': 'Design user authentication flow',
                'description': 'Create wireframes and design system for login, signup, and password reset screens. Ensure mobile-first approach.',
                'status': 'done',
                'priority': 'high',
                'due_date': today - datetime.timedelta(days=3),
                'comments': ['Great work on the wireframes!', 'Approved for development.'],
            },
            {
                'title': 'Set up CI/CD pipeline',
                'description': 'Configure GitHub Actions for automated testing and deployment. Include linting, unit tests, and staging deployment.',
                'status': 'done',
                'priority': 'high',
                'due_date': today - datetime.timedelta(days=1),
                'comments': ['Pipeline is working smoothly.'],
            },
            {
                'title': 'Build REST API endpoints',
                'description': 'Develop CRUD endpoints for tasks, users, and comments. Add rate limiting and proper error handling.',
                'status': 'in_progress',
                'priority': 'high',
                'due_date': today + datetime.timedelta(days=2),
                'comments': ['Started with the task endpoints.'],
            },
            {
                'title': 'Write unit tests for core modules',
                'description': 'Achieve 80% test coverage for models, views, and utility functions.',
                'status': 'in_progress',
                'priority': 'medium',
                'due_date': today + datetime.timedelta(days=4),
                'comments': [],
            },
            {
                'title': 'Create dashboard analytics view',
                'description': 'Build a summary dashboard showing task counts by status, priority distribution, and overdue tasks.',
                'status': 'todo',
                'priority': 'medium',
                'due_date': today + datetime.timedelta(days=7),
                'comments': [],
            },
            {
                'title': 'Implement email notifications',
                'description': 'Send email notifications when tasks are assigned, updated, or approaching due dates.',
                'status': 'todo',
                'priority': 'low',
                'due_date': today + datetime.timedelta(days=10),
                'comments': [],
            },
            {
                'title': 'Mobile responsive testing',
                'description': 'Test all views on iOS and Android. Fix any layout issues on small screens.',
                'status': 'todo',
                'priority': 'medium',
                'due_date': today + datetime.timedelta(days=5),
                'comments': [],
            },
            {
                'title': 'Update project documentation',
                'description': 'Write API documentation, deployment guide, and developer onboarding README.',
                'status': 'todo',
                'priority': 'low',
                'due_date': None,
                'comments': [],
            },
        ]

        for data in tasks_data:
            comments = data.pop('comments')
            task = Task.objects.create(**data)
            for comment_text in comments:
                Comment.objects.create(task=task, content=comment_text)

        self.stdout.write(self.style.SUCCESS(f'Created {len(tasks_data)} sample tasks with comments.'))
