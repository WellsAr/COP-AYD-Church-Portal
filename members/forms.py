from django import forms
from .models import Member


class MemberForm(forms.ModelForm):

    class Meta:
        model = Member

        fields = [
            'first_name',
            'last_name',
            'date_of_birth',
            'primary_phone',
            'secondary_phone',
            'email',
            'session',
            'image',
        ]