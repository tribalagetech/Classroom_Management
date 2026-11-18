# resources/permissions.py
from django.db.models import Q
from .models import Resource


def is_teacher(user):
    return hasattr(user, 'teacher_profile')    # the reverse link from Teacher.user


def can_upload(user):
    return user.is_authenticated and (is_teacher(user) or user.has_perm('resources.add_resource'))


def can_manage(user, resource):                # publish / unpublish
    return user.is_superuser or resource.uploaded_by_id == user.pk or user.has_perm('resources.change_resource')


def can_delete(user, resource):
    return user.is_superuser or resource.uploaded_by_id == user.pk or user.has_perm('resources.delete_resource')


def visible_resources(user):
    qs = Resource.objects.all()
    if user.is_staff:                          # admins see everything, including drafts
        return qs
    return qs.filter(Q(is_published=True) | Q(uploaded_by=user))   # teachers: published + their own drafts