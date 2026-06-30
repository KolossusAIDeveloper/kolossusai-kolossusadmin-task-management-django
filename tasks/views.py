from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Task, Comment
from .forms import TaskForm, CommentForm, TaskFilterForm


@login_required
def task_list(request):
    tasks = Task.objects.select_related('assigned_to', 'created_by').all()
    form = TaskFilterForm(request.GET)

    if form.is_valid():
        if form.cleaned_data.get('status'):
            tasks = tasks.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('priority'):
            tasks = tasks.filter(priority=form.cleaned_data['priority'])
        if form.cleaned_data.get('search'):
            tasks = tasks.filter(title__icontains=form.cleaned_data['search'])
        if form.cleaned_data.get('assignee'):
            tasks = tasks.filter(assigned_to=form.cleaned_data['assignee'])

    counts = {
        'total': Task.objects.count(),
        'todo': Task.objects.filter(status='todo').count(),
        'in_progress': Task.objects.filter(status='in_progress').count(),
        'done': Task.objects.filter(status='done').count(),
    }

    return render(request, 'tasks/task_list.html', {
        'tasks': tasks,
        'filter_form': form,
        'counts': counts,
    })


@login_required
def task_board(request):
    return render(request, 'tasks/task_board.html', {
        'todo_tasks': Task.objects.filter(status='todo').select_related('assigned_to'),
        'in_progress_tasks': Task.objects.filter(status='in_progress').select_related('assigned_to'),
        'done_tasks': Task.objects.filter(status='done').select_related('assigned_to'),
    })


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    comment_form = CommentForm()
    comments = task.comments.select_related('author').all()

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added.')
            return redirect('task_detail', pk=pk)

    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'comment_form': comment_form,
        'comments': comments,
    })


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created!')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm()

    return render(request, 'tasks/task_form.html', {
        'form': form,
        'title': 'Create Task',
        'submit_text': 'Create Task',
    })


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated!')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)

    return render(request, 'tasks/task_form.html', {
        'form': form,
        'task': task,
        'title': 'Edit Task',
        'submit_text': 'Save Changes',
    })


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted.')
        return redirect('task_list')

    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
@require_POST
def task_update_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    new_status = request.POST.get('status')
    if new_status in ['todo', 'in_progress', 'done']:
        task.status = new_status
        task.save()
        return JsonResponse({'success': True, 'status': new_status})
    return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)


@login_required
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    task_pk = comment.task.pk
    comment.delete()
    messages.success(request, 'Comment deleted.')
    return redirect('task_detail', pk=task_pk)
