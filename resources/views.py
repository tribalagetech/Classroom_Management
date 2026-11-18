# resources/views.py
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from dashboard.access import home_for
from students.models import Subject, YearLevel
from .forms import ResourceForm
from .models import MAX_UPLOAD_MB, Resource
from .permissions import can_delete, can_manage, can_upload, visible_resources


@login_required
def centre(request):
    user = request.user
    form = ResourceForm()
    open_modal = False

    # uploading is a POST to this same page, so the filters and list stay where they are
    if request.method == 'POST':
        if not can_upload(user):
            raise PermissionDenied
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = user
            resource.save()
            form.save_m2m()
            messages.success(request, f'"{resource.title}" uploaded.')
            return redirect('resources:centre')
        open_modal = True

    resources = visible_resources(user).select_related('subject', 'uploaded_by').prefetch_related('year_levels')

    filters = {k: request.GET.get(k, '').strip() for k in ('q', 'subject', 'level', 'type')}
    filters['mine'] = request.GET.get('mine') == '1'
    if filters['q']:
        resources = resources.filter(Q(title__icontains=filters['q']) | Q(description__icontains=filters['q'])
                                     | Q(original_name__icontains=filters['q']))
    if filters['subject'].isdigit():
        resources = resources.filter(subject_id=int(filters['subject']))
    if filters['level'].isdigit():
        resources = resources.filter(year_levels__pk=int(filters['level']))
    if filters['type'] in Resource.Type.values:
        resources = resources.filter(resource_type=filters['type'])
    if filters['mine']:
        resources = resources.filter(uploaded_by=user)
    resources = resources.distinct()

    page = Paginator(resources, 15).get_page(request.GET.get('page'))
    rows = list(page.object_list)
    for r in rows:   # everything the template needs, worked out here
        r.can_manage = can_manage(user, r)
        r.can_delete = can_delete(user, r)
        r.toggle_label = 'Unpublish' if r.is_published else 'Publish'
        if r.uploaded_by:
            r.uploader = r.uploaded_by.get_full_name() or r.uploaded_by.username
        else:
            r.uploader = 'Unknown'

    params = request.GET.copy()
    params.pop('page', None)

    def page_url(number):
        q = params.copy()
        q['page'] = number
        return '?' + q.urlencode()          # keeps the filters, changes only the page

    def options(items, current):
        # dropdown options with a ready-made "selected" word, so the template needs no {% if %}
        return [{'value': v, 'label': label, 'sel': 'selected' if str(v) == current else ''}
                for v, label in items]

    subjects = Subject.objects.filter(is_active=True).prefetch_related('year_levels')
    levels = YearLevel.objects.all()

    template = 'resources/centre_admin.html' if user.is_staff else 'resources/centre_teacher.html'
    return render(request, template, {
        'rows': rows,
        'page': page,
        'prev_url': page_url(page.previous_page_number()) if page.has_previous() else '',
        'next_url': page_url(page.next_page_number()) if page.has_next() else '',
        'filters': filters,
        'mine_checked': 'checked' if filters['mine'] else '',
        'subject_opts': options([(s.pk, s.name) for s in subjects], filters['subject']),
        'level_opts': options([(l.pk, l.name) for l in levels], filters['level']),
        'type_opts': options(Resource.Type.choices, filters['type']),
        'subject_levels': {str(s.pk): [l.pk for l in s.year_levels.all()] for s in subjects},
        'form': form,
        'open_flag': '1' if open_modal else '',
        'can_upload': can_upload(user),
        'max_mb': MAX_UPLOAD_MB,
        'home_url': reverse(home_for(user)),
    })

@login_required
def download(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    if not (resource.is_published or resource.uploaded_by_id == request.user.pk or request.user.is_staff):
        raise Http404                            # a private draft looks exactly like a missing file
    try:
        handle = resource.file.open('rb')
    except FileNotFoundError:
        raise Http404('The file is missing from the server.')
    Resource.objects.filter(pk=pk).update(download_count=F('download_count') + 1)   # tracking
    return FileResponse(handle, as_attachment=True,
                        filename=resource.original_name or os.path.basename(resource.file.name))


@login_required
@require_POST
def toggle_publish(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    if not can_manage(request.user, resource):
        raise PermissionDenied
    resource.is_published = not resource.is_published
    resource.save(update_fields=['is_published', 'updated_at'])
    messages.success(request, f'"{resource.title}" is now {"published" if resource.is_published else "a draft"}.')
    return redirect('resources:centre')


@login_required
@require_POST
def delete(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    if not can_delete(request.user, resource):
        raise PermissionDenied
    title = resource.title
    resource.delete()                            # the file is removed from disk by the signal in models.py
    messages.success(request, f'"{title}" deleted.')
    return redirect('resources:centre')