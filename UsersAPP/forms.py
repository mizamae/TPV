from django import forms
from django.utils.translation import gettext as _

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions,InlineRadios
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Column, Field

from .models import Customer

FORMS_LABEL_CLASS='col'
FORMS_FIELD_CLASS='col'

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
        
        self.helper.layout = Layout(
                                    Field('data',type=''),
                                )

class customerForm(forms.ModelForm):

    class Meta:
        model = Customer
        exclude = []

    def __init__(self, *args, **kwargs):
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
                                    Field('phone',type=''),
                                    Field('cif',type=''),
                                    Field('saves_paper',type=''),
                                )
        self.helper.layout.append(buttons)