from django import forms
from django.utils.translation import gettext as _

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions,InlineRadios
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Column, Field

from .models import Customer, User

FORMS_LABEL_CLASS='col'
FORMS_FIELD_CLASS='col'

from django_toggle_switch_widget.widgets import DjangoToggleSwitchWidget

class CustomToggleSwitch(Field):
    template = '__toggle_switch_widget.html'

class userForm(forms.ModelForm):

    class Meta:
        model = User
        exclude = ['password','last_login','user_permissions']
        widgets = {
            'is_staff': DjangoToggleSwitchWidget(round=True, klass="django-toggle-switch-success form-check"),
            'is_active': DjangoToggleSwitchWidget(round=True, klass="django-toggle-switch-success form-check"),
            'is_superuser': DjangoToggleSwitchWidget(round=True, klass="django-toggle-switch-success form-check"),
        }

    def __init__(self, *args, **kwargs):
        super(userForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.use_custom_control = True
        self.helper.label_class = FORMS_LABEL_CLASS
        self.helper.field_class = FORMS_FIELD_CLASS
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        self.helper.form_show_labels = True
        
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class':'form-control','data-toggle':'tooltip' ,'title':help_text, 'data-bs-placement':'right', 'data-bs-container':'body'})
            else:
                self.fields[field].widget.attrs.update({'class':'form-control'})
        
        buttons=FormActions(
                        Div(
                        Column(Submit('submit', _('Create'),css_class="btn btn-primary col-12"),css_class="col-9"),
                        Column(HTML('<a href="{% url "home" %}" class="btn btn-secondary col-12">'+str(_('Cancel'))+'</a>'),css_class="col-3"),
                        css_class="row")
                    )
        
        self.helper.layout = Layout(
                                    Field('first_name',type=''),
                                    Field('last_name',type=''),
                                    Field('email',type=''),
                                    Field('type',type=''),
                                    Field('identifier',type=''),
                                    CustomToggleSwitch('is_staff',type=''),
                                    CustomToggleSwitch('is_active',type=''),
                                    CustomToggleSwitch('is_superuser',type=''),
                                    Field('groups',type=''),
                                )
        self.helper.layout.append(buttons)

class findCustomerForm(forms.Form):
    data=forms.CharField(required=True,help_text=_("Enter ID, phone or email"))

    def __init__(self, *args, **kwargs):
        super(findCustomerForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.use_custom_control = True
        self.helper.label_class = FORMS_LABEL_CLASS
        self.helper.field_class = FORMS_FIELD_CLASS
        self.helper.form_class = 'form-inline'
        self.helper.form_method = 'post'
        self.helper.form_show_labels = False
        
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class':'form-control','data-toggle':'tooltip' ,'title':help_text, 'data-bs-placement':'right', 'data-bs-container':'body'})
            else:
                self.fields[field].widget.attrs.update({'class':'form-control'})
        
        self.fields['data'].widget.attrs.update({'id':'id_customer_data'})
        self.helper.layout = Layout(
                                    Field('data',type=''),
                                )



class customerForm(forms.ModelForm):

    class Meta:
        model = Customer
        exclude = []
        widgets = {
            'saves_paper': DjangoToggleSwitchWidget(round=True, klass="django-toggle-switch-success form-check"),
        }

    def __init__(self, *args, **kwargs):
        compactView = kwargs.pop('compactView',False)
        super(customerForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.use_custom_control = True
        self.helper.label_class = FORMS_LABEL_CLASS
        self.helper.field_class = FORMS_FIELD_CLASS
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        self.helper.form_show_labels = True
        
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class':'form-control','data-toggle':'tooltip' ,'title':help_text, 'data-bs-placement':'right', 'data-bs-container':'body'})
            else:
                self.fields[field].widget.attrs.update({'class':'form-control'})
        
        if not self.instance:
            buttons=FormActions(
                        Div(
                        Column(Submit('submit', _('Create'),css_class="btn btn-primary col-12"),css_class="col-9"),
                        Column(HTML('<a href="{% url "home" %}" class="btn btn-secondary col-12">'+str(_('Cancel'))+'</a>'),css_class="col-3"),
                        css_class="row")
                    )
        else:
            buttons=FormActions(
                        Div(
                        Column(Submit('submit', _('Save'),css_class="btn btn-primary col-12"),css_class="col-9"),
                        Column(HTML('<a href="{% url "home" %}" class="btn btn-secondary col-12">'+str(_('Cancel'))+'</a>'),css_class="col-3"),
                        css_class="row")
                    )
        
        if not compactView:
            self.helper.layout = Layout(
                                    Field('first_name',type=''),
                                    Field('last_name',type=''),
                                    Field('email',type=''),
                                    Field('phone',type=''),
                                    Field('addr1',type='',placeholder=_("Street and number")),
                                    Field('addr2',type='',placeholder=_("Town (Country)")),
                                    Field('zip',type=''),
                                    Field('cif',type=''),
                                    CustomToggleSwitch('saves_paper',type=''),
                                    Field('profile',type=''),
                                    Field('credit',type=''),
                                )
        else:
            self.helper.layout = Layout(
                                    Row(
                                        Column('first_name', css_class='form-group col-md-4 mb-0'),
                                        Column('last_name', css_class='form-group col-md-4 mb-0'),
                                        css_class='form-row'
                                    ),
                                    Row(
                                        Column('email', css_class='form-group col-md-4 mb-0'),
                                        Column('phone', css_class='form-group col-md-4 mb-0'),
                                        Column('cif', css_class='form-group col-md-4 mb-0'),
                                        css_class='form-row'
                                    ),
                                    Row(
                                        Column('addr1', css_class='form-group col-md-4 mb-0'),
                                        Column('addr2', css_class='form-group col-md-4 mb-0'),
                                        Column('zip', css_class='form-group col-md-4 mb-0'),
                                        css_class='form-row'
                                    ),
                                    Row(
                                        Column('profile', css_class='form-group col-md-4 mb-0'),
                                        Column('credit', css_class='form-group col-md-4 mb-0'),
                                        Column(CustomToggleSwitch('saves_paper',type=''),css_class='form-group col-md-4 mb-0'),
                                        css_class='form-row'
                                    ),
                                )
        self.helper.layout.append(buttons)