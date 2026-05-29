from django.contrib import admin
from .models import (
    Session,
    ShepherdGroup,
    StaffProfile,
    Member,
    Attendance
)


# =========================
# SESSION ADMIN
# =========================
@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


# =========================
# SHEPHERD GROUP ADMIN
# =========================
@admin.register(ShepherdGroup)
class ShepherdGroupAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'birth_month',
        'session'
    )

    list_filter = (
        'session',
        'birth_month'
    )

    search_fields = (
        'name',
    )


# =========================
# STAFF PROFILE ADMIN
# =========================
@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'role',
        'session',
        'shepherd_group',
        'supervisor'
    )

    list_filter = (
        'role',
        'session'
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name'
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        # SUPERVISOR FILTER
        if db_field.name == 'supervisor':

            kwargs['queryset'] = (
                StaffProfile.objects.filter(
                    role='overseer'
                )
            )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs
        )


# =========================
# MEMBER ADMIN
# =========================
@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'first_name',
        'last_name',
        'date_of_birth',
        'session',
        'shepherd_group',
        'primary_phone',
        'registered_by',
        'created_at',
        'is_active'
    )

    list_filter = (
        'session',
        'shepherd_group',
        'is_active',
        'created_at'
    )

    search_fields = (
        'first_name',
        'last_name',
        'primary_phone',
        'secondary_phone',
        'email'
    )

    readonly_fields = (
        'created_at',
        'updated_at'
    )

    fieldsets = (
        ('Personal Information', {
            'fields': (
                'first_name',
                'last_name',
                'date_of_birth',
                'image'
            )
        }),

        ('Contact Information', {
            'fields': (
                'primary_phone',
                'secondary_phone',
                'email'
            )
        }),

        ('Church Information', {
            'fields': (
                'session',
                'shepherd_group'
            )
        }),

        ('System Tracking', {
            'fields': (
                'registered_by',
                'updated_by',
                'created_at',
                'updated_at',
                'is_active'
            )
        }),
    )


# =========================
# ATTENDANCE ADMIN
# =========================
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    list_display = (
        'member',
        'date',
        'present',
        'marked_by',
        'marked_at'
    )

    list_filter = (
        'present',
        'date'
    )

    search_fields = (
        'member__first_name',
        'member__last_name'
    )

    readonly_fields = (
        'marked_at',
    )