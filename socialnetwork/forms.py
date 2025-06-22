from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Author

class AuthorCreationForm(UserCreationForm):
    class Meta:
        model = Author
        fields = ('email', 'display_name', 'github', 'profile_image_file', 'bio')

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn’t match.")


class AuthorProfileForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['display_name', 'github', 'profile_image_file']


        # Customize the widgets for each field
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter your display name'
            }),
            'github': forms.URLInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter your GitHub profile URL'
            }),
            'profile_image_file': forms.ClearableFileInput(attrs={
                'class': 'form-control-file', 
                'accept': 'image/*',
                'style': 'margin-top:;'  # Adds some spacing
            }),
        }