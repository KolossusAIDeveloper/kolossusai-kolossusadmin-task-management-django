from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from tasks.models import Task, Comment
from accounts.models import UserProfile
import datetime


class Command(BaseCommand):
    help = 'Seed the database with sample users and tasks'

    def handle(self, *args, **kwargs):
        self._seed_users()
        self._seed_tasks()

    def _seed_users(self):
        if User.objects.exists():
            self.stdout.write('Users already exist, skipping user seed.')
            return

        users_data = [
            {'username': 'admin', 'email': 'admin@taskflow.com', 'first_name': 'Admin', 'last_name': 'User', 'is_superuser': True, 'role': 'admin', 'password': 'admin123'},
            {'username': 'alice', 'email': 'alice@taskflow.com', 'first_name': 'Alice', 'last_name': 'Johnson', 'is_superuser': False, 'role': 'admin', 'password': 'password123'},
            {'username': 'bob', 'email': 'bob@taskflow.com', 'first_name': 'Bob', 'last_name': 'Smith', 'is_superuser': False, 'role': 'member', 'password': 'password123'},
            {'username': 'carol', 'email': 'carol@taskflow.com', 'first_name': 'Carol', 'last_name': 'Davis', 'is_superuser': False, 'role': 'member', 'password': 'password123'},
        ]

        created_users = {}
        for data in users_data:
            role = data.pop('role')
            password = data.pop('password')
            is_superuser = data.pop('is_superuser')
            if is_superuser:
                user = User.objects.create_superuser(password=password, **data)
            else:
                user = User.objects.create_user(password=password, **data)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.bio = f"Sample team member — {data['first_name']} {data['last_name']}."
            profile.save()
            created_users[data['username']] = user

        self.stdout.write(self.style.SUCCESS(f'Created {len(users_data)} sample users. Login: admin / admin123'))
        return created_users

    def _seed_tasks(self):
        if Task.objects.exists():
            self.stdout.write('Tasks already exist, skipping task seed.')
            return

        try:
            alice = User.objects.get(username='alice')
            bob = User.objects.get(username='bob')
            carol = User.objects.get(username='carol')
            admin = User.objects.get(username='admin')
        except User.DoesNotExist:
            alice = bob = carol = admin = None

        today = datetime.date.today()

        tasks_data = [
            {
                'title': 'Design user authentication flow',
                'description': 'Create wireframes and design system for login, signup, and password reset screens.',
                'status': 'done', 'priority': 'high',
                'due_date': today - datetime.timedelta(days=3),
                'assigned_to': alice, 'created_by': admin,
                'comments': [('Great work on the wireframes!', alice), ('Approved for development.', admin)],
            },
            {
                'title': 'Set up CI/CD pipeline',
                'description': 'Configure GitHub Actions for automated testing and deployment.',
                'status': 'done', 'priority': 'high',
                'due_date': today - datetime.timedelta(days=1),
                'assigned_to': bob, 'created_by': admin,
                'comments': [('Pipeline is working smoothly.', bob)],
            },
            {
                'title': 'Build REST API endpoints',
                'description': 'Develop CRUD endpoints for tasks, users, and comments. Add rate limiting.',
                'status': 'in_progress', 'priority': 'high',
                'due_date': today + datetime.timedelta(days=2),
                'assigned_to': bob, 'created_by': alice,
                'comments': [('Started with the task endpoints.', bob)],
            },
            {
                'title': 'Write unit tests for core modules',
                'description': 'Achieve 80% test coverage for models, views, and utility functions.',
                'status': 'in_progress', 'priority': 'medium',
                'due_date': today + datetime.timedelta(days=4),
                'assigned_to': carol, 'created_by': alice,
                'comments': [],
            },
            {
                'title': 'Create dashboard analytics view',
                'description': 'Build a summary dashboard showing task counts by status and priority.',
                'status': 'todo', 'priority': 'medium',
                'due_date': today + datetime.timedelta(days=7),
                'assigned_to': alice, 'created_by': admin,
                'comments': [],
            },
            {
                'title': 'Implement email notifications',
                'description': 'Send email notifications when tasks are assigned or approaching due dates.',
                'status': 'todo', 'priority': 'low',
                'due_date': today + datetime.timedelta(days=10),
                'assigned_to': carol, 'created_by': alice,
                'comments': [],
            },
            {
                'title': 'Mobile responsive testing',
                'description': 'Test all views on iOS and Android. Fix any layout issues on small screens.',
                'status': 'todo', 'priority': 'medium',
                'due_date': today + datetime.timedelta(days=5),
                'assigned_to': bob, 'created_by': admin,
                'comments': [],
            },
            {
                'title': 'Update project documentation',
                'description': 'Write API documentation, deployment guide, and developer onboarding README.',
                'status': 'todo', 'priority': 'low',
                'due_date': None,
                'assigned_to': None, 'created_by': admin,
                'comments': [],
            },
        ]

        for data in tasks_data:
            comments = data.pop('comments')
            task = Task.objects.create(**data)
            for comment_text, author in comments:
                Comment.objects.create(task=task, content=comment_text, author=author)

        self.stdout.write(self.style.SUCCESS(f'Created {len(tasks_data)} sample tasks.'))
