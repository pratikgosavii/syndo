from django import forms


class LoginForm(forms.Form):
    mobile = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'mobile',
    }))
    password = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password',
        'type': 'password'
    }))


from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User  # Import your User model

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('mobile', 'email')  # Only show mobile + optional email

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('mobile', 'email', 'is_active', 'is_staff', 'is_superuser', 'is_vendor', 'is_customer')


from django import forms
from .models import Role, MenuModule, RoleMenuPermission

class RoleWithModulesForm(forms.ModelForm):
    menu_modules = forms.ModelMultipleChoiceField(
        queryset=MenuModule.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Assign Modules"
    )

    class Meta:
        model = Role
        fields = ['name', 'menu_modules']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter role name'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['menu_modules'].initial = MenuModule.objects.filter(
                rolemenupermission__role=self.instance
            )

    def save(self, commit=True):
        role = super().save(commit=False)
        if commit:
            role.save()
            # Clear existing
            RoleMenuPermission.objects.filter(role=role).delete()
            # Add selected
            for module in self.cleaned_data['menu_modules']:
                RoleMenuPermission.objects.create(role=role, menu_module=module)
        return role



class UserRoleAssignForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Assign Roles"
    )

    class Meta:
        model = User
        fields = ['mobile', 'email', 'roles']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['roles'].initial = self.instance.roles.all()
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            user.roles.set(self.cleaned_data['roles'])
        return user