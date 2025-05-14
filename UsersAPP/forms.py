from django import forms
from django.utils.translation import gettext as _

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions,InlineRadios
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Column, Field

FORMS_LABEL_CLASS='col'
FORMS_FIELD_CLASS='col'

class findCustomerForm(forms.Form):
    data=forms.CharField(required=True,help_text=_("Introduce ID, phone or email"))

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
        