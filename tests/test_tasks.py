import datetime
import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from tasks.models import Task, Comment
from accounts.models import UserProfile


def make_user(username='testuser', password='testpass123'):
    u = User.objects.create_user(username=username, password=password)
    UserProfile.objects.get_or_create(user=u)
    return u


class TestTaskModel(TestCase):
    def setUp(self):
        self.task = Task.objects.create(
            title="Test Task",
            description="A test task description",
            status="todo",
            priority="high",
        )

    def test_task_creation(self):
        self.assertEqual(self.task.title, "Test Task")
        self.assertEqual(self.task.status, "todo")
        self.assertEqual(self.task.priority, "high")

    def test_task_str(self):
        self.assertEqual(str(self.task), "Test Task")

    def test_task_is_overdue(self):
        past_date = datetime.date.today() - datetime.timedelta(days=1)
        self.task.due_date = past_date
        self.task.save()
        self.assertTrue(self.task.is_overdue)

    def test_done_task_not_overdue(self):
        past_date = datetime.date.today() - datetime.timedelta(days=1)
        self.task.due_date = past_date
        self.task.status = "done"
        self.task.save()
        self.assertFalse(self.task.is_overdue)

    def test_priority_color(self):
        self.assertEqual(self.task.priority_color, "danger")
        self.task.priority = "medium"
        self.assertEqual(self.task.priority_color, "warning")
        self.task.priority = "low"
        self.assertEqual(self.task.priority_color, "success")

    def test_status_color(self):
        self.assertEqual(self.task.status_color, "secondary")
        self.task.status = "in_progress"
        self.assertEqual(self.task.status_color, "primary")
        self.task.status = "done"
        self.assertEqual(self.task.status_color, "success")


class TestUserProfile(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_profile_auto_created(self):
        self.assertTrue(hasattr(self.user, 'profile'))

    def test_display_name_full_name(self):
        self.user.first_name = 'Alice'
        self.user.last_name = 'Smith'
        self.user.save()
        self.assertIn('Alice', self.user.profile.display_name)

    def test_display_name_fallback(self):
        self.assertEqual(self.user.profile.display_name, self.user.username)

    def test_initials(self):
        self.user.first_name = 'Alice'
        self.user.last_name = 'Smith'
        self.user.save()
        self.assertEqual(self.user.profile.initials, 'AS')

    def test_avatar_color_deterministic(self):
        c1 = self.user.profile.avatar_color
        c2 = self.user.profile.avatar_color
        self.assertEqual(c1, c2)
        self.assertTrue(c1.startswith('#'))


class TestCommentModel(TestCase):
    def setUp(self):
        self.task = Task.objects.create(title="Task with comment", status="todo", priority="medium")
        self.comment = Comment.objects.create(task=self.task, content="Test comment")

    def test_comment_creation(self):
        self.assertEqual(self.comment.content, "Test comment")
        self.assertEqual(self.comment.task, self.task)

    def test_comment_str(self):
        self.assertIn("Task with comment", str(self.comment))


class TestAuthViews(TestCase):
    def test_login_page_loads(self):
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)

    def test_register_page_loads(self):
        resp = self.client.get(reverse('register'))
        self.assertEqual(resp.status_code, 200)

    def test_task_list_requires_login(self):
        resp = self.client.get(reverse('task_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login/', resp['Location'])

    def test_login_success(self):
        make_user()
        resp = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'testpass123'})
        self.assertEqual(resp.status_code, 302)

    def test_register_creates_user(self):
        self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'securepass123!',
            'password2': 'securepass123!',
        })
        self.assertTrue(User.objects.filter(username='newuser').exists())


class TestTaskViews(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.login(username='testuser', password='testpass123')
        self.task = Task.objects.create(
            title="View Test Task",
            description="Test",
            status="todo",
            priority="medium",
            created_by=self.user,
        )

    def test_task_list_view(self):
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "View Test Task")

    def test_task_board_view(self):
        response = self.client.get(reverse('task_board'))
        self.assertEqual(response.status_code, 200)

    def test_task_detail_view(self):
        response = self.client.get(reverse('task_detail', args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "View Test Task")

    def test_task_create_get(self):
        response = self.client.get(reverse('task_create'))
        self.assertEqual(response.status_code, 200)

    def test_task_create_post(self):
        data = {'title': 'New Task', 'description': 'New desc', 'status': 'todo', 'priority': 'high'}
        response = self.client.post(reverse('task_create'), data)
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title='New Task')
        self.assertEqual(task.created_by, self.user)

    def test_task_edit_post(self):
        data = {'title': 'Updated Task', 'description': 'Updated desc', 'status': 'in_progress', 'priority': 'low'}
        self.client.post(reverse('task_edit', args=[self.task.pk]), data)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task')

    def test_task_delete_post(self):
        task_id = self.task.pk
        self.client.post(reverse('task_delete', args=[task_id]))
        self.assertFalse(Task.objects.filter(pk=task_id).exists())

    def test_task_update_status(self):
        self.client.post(reverse('task_update_status', args=[self.task.pk]), {'status': 'done'})
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'done')

    def test_task_assign_to_user(self):
        self.client.post(reverse('task_edit', args=[self.task.pk]), {
            'title': self.task.title, 'status': self.task.status,
            'priority': self.task.priority, 'assigned_to': self.user.pk,
        })
        self.task.refresh_from_db()
        self.assertEqual(self.task.assigned_to, self.user)

    def test_add_comment(self):
        self.client.post(reverse('task_detail', args=[self.task.pk]), {'content': 'A new comment'})
        self.assertEqual(self.task.comments.count(), 1)
        self.assertEqual(self.task.comments.first().author, self.user)

    def test_delete_comment(self):
        comment = Comment.objects.create(task=self.task, content="To delete")
        self.client.post(reverse('comment_delete', args=[comment.pk]))
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())


class TestUserManagementViews(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.login(username='testuser', password='testpass123')

    def test_user_list_view(self):
        resp = self.client.get(reverse('user_list'))
        self.assertEqual(resp.status_code, 200)

    def test_user_detail_view(self):
        resp = self.client.get(reverse('user_detail', args=[self.user.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_profile_view(self):
        resp = self.client.get(reverse('profile'))
        self.assertEqual(resp.status_code, 200)

    def test_user_delete_requires_admin(self):
        other = make_user('other', 'pass1234567')
        resp = self.client.post(reverse('user_delete', args=[other.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_delete_user(self):
        admin = make_user('admintestuser', 'pass1234567')
        admin.profile.role = 'admin'
        admin.profile.save()
        other = make_user('victim', 'pass1234567')
        self.client.logout()
        self.client.login(username='admintestuser', password='pass1234567')
        resp = self.client.post(reverse('user_delete', args=[other.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(User.objects.filter(username='victim').exists())
