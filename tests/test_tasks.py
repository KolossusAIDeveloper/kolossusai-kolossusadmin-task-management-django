import pytest
from django.test import TestCase, Client
from django.urls import reverse
from tasks.models import Task, Comment
import datetime


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


class TestCommentModel(TestCase):
    def setUp(self):
        self.task = Task.objects.create(title="Task with comment", status="todo", priority="medium")
        self.comment = Comment.objects.create(task=self.task, content="Test comment")

    def test_comment_creation(self):
        self.assertEqual(self.comment.content, "Test comment")
        self.assertEqual(self.comment.task, self.task)

    def test_comment_str(self):
        self.assertIn("Task with comment", str(self.comment))


class TestTaskViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.task = Task.objects.create(
            title="View Test Task",
            description="Test",
            status="todo",
            priority="medium",
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
        data = {
            'title': 'New Task',
            'description': 'New description',
            'status': 'todo',
            'priority': 'high',
        }
        response = self.client.post(reverse('task_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(title='New Task').exists())

    def test_task_edit_post(self):
        data = {
            'title': 'Updated Task',
            'description': 'Updated desc',
            'status': 'in_progress',
            'priority': 'low',
        }
        response = self.client.post(reverse('task_edit', args=[self.task.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task')
        self.assertEqual(self.task.status, 'in_progress')

    def test_task_delete_post(self):
        task_id = self.task.pk
        response = self.client.post(reverse('task_delete', args=[task_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(pk=task_id).exists())

    def test_task_update_status(self):
        response = self.client.post(
            reverse('task_update_status', args=[self.task.pk]),
            {'status': 'done'},
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'done')

    def test_task_filter_by_status(self):
        Task.objects.create(title="Done Task", status="done", priority="low")
        response = self.client.get(reverse('task_list') + '?status=done')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Done Task")
        self.assertNotContains(response, "View Test Task")

    def test_task_filter_by_priority(self):
        response = self.client.get(reverse('task_list') + '?priority=medium')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "View Test Task")

    def test_add_comment(self):
        response = self.client.post(
            reverse('task_detail', args=[self.task.pk]),
            {'content': 'A new comment'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.task.comments.count(), 1)
        self.assertEqual(self.task.comments.first().content, 'A new comment')

    def test_delete_comment(self):
        comment = Comment.objects.create(task=self.task, content="To delete")
        response = self.client.post(reverse('comment_delete', args=[comment.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())
