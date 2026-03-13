from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from accounts.models import Profile



class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_image', 'bio']
        labels = {
            'profile_image': '头像图片',
            'bio': '个人简介',
        }
        widgets = {
            'profile_image': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': '输入图片链接（例如：https://example.com/image.jpg）'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            })
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'email']
        labels = {
            'last_name': '姓',
            'first_name': '名',
            'email': '邮箱地址',
        }




class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="当前密码",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password1 = forms.CharField(
        label="新密码",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password2 = forms.CharField(
        label="确认新密码",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
