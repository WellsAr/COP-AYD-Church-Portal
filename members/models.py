from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# =========================
# SESSION
# =========================
class Session(models.Model):
    SESSION_CHOICES = [
        ('central', 'Central'),
        ('english', 'English'),
    ]

    name = models.CharField(
        max_length=20,
        choices=SESSION_CHOICES,
        unique=True
    )

    def __str__(self):
        return self.get_name_display()


# =========================
# SHEPHERD GROUP
# =========================
class ShepherdGroup(models.Model):

    MONTH_CHOICES = [
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    ]

    name = models.CharField(max_length=100)

    birth_month = models.IntegerField(choices=MONTH_CHOICES)

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='groups'
    )

    def __str__(self):
        return f"{self.name} - {self.get_birth_month_display()}"


# =========================
# STAFF PROFILE
# =========================
class StaffProfile(models.Model):

    ROLE_CHOICES = [
        ('pastor', 'Pastor'),
        ('elder', 'Presiding Elder'),
        ('administrator', 'Administrator'),
        ('overseer', 'Overseer'),
        ('shepherd_leader', 'Shepherd Leader'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES
    )

    # Which church session they belong to
    session = models.ForeignKey(
        Session,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Shepherd assignment
    shepherd_group = models.ForeignKey(
        ShepherdGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Who supervises this person
    supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        limit_choices_to=models.Q(role='overseer')
    )

    def clean(self):
        # Supervisor must be overseer
        if self.supervisor:

            if self.supervisor.role != 'overseer':

                raise ValidationError({
                    'supervisor': (
                        'Supervisor must be an overseer.'
                    )
                })

            # Session must match
            if self.supervisor.session != self.session:

                raise ValidationError({
                    'supervisor': (
                        'Supervisor must belong '
                        'to the same session.'
                    )
                })

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


# =========================
# MEMBER
# =========================
class Member(models.Model):

    first_name = models.CharField(max_length=100)

    last_name = models.CharField(max_length=100)

    date_of_birth = models.DateField()

    primary_phone = models.CharField(max_length=20)

    secondary_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    email = models.EmailField(blank=True, null=True)

    image = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )

    # Which session member belongs to
    session = models.ForeignKey(
        Session,
        on_delete=models.SET_NULL,
        null=True,
        related_name='members'
    )

    # Birth month shepherd group
    shepherd_group = models.ForeignKey(
        ShepherdGroup,
        on_delete=models.SET_NULL,
        null=True,
        related_name='members'
    )

    # Who registered the member
    registered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_members'
    )

    # Track edits
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_members'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# =========================
# ATTENDANCE
# =========================
class Attendance(models.Model):

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )

    date = models.DateField(auto_now_add=True)

    present = models.BooleanField(default=True)

    # Who marked attendance
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='marked_attendance'
    )

    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('member', 'date')

    def __str__(self):
        status = "Present" if self.present else "Absent"
        return f"{self.member} - {self.date} - {status}"