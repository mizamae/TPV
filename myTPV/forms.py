from django import forms
from django.utils.translation import gettext as _

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions,InlineRadios, AppendedText
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Column, Field, Fieldset
from bootstrap_datepicker_plus.widgets import DatePickerInput

from .models import SiteSettings

FORMS_LABEL_CLASS='col'
FORMS_FIELD_CLASS='col'

REPORT_TYPE_SALES=0
REPORT_TYPE_PRODUCTS=1

REPORT_CHOICES =(
    (REPORT_TYPE_SALES, _("Sales report")),
    (REPORT_TYPE_PRODUCTS, _("Products report")),
)

class reportForm(forms.Form):
    _type = forms.ChoiceField(choices=REPORT_CHOICES,required=True,label=_("Type of report"))
    _from = forms.DateField(label="From",help_text="Date of the initial data",required=False,disabled=False,widget=DatePickerInput(options={"format": "DD/MM/YYYY "}))
    _to = forms.DateField(label="To",help_text="Date of the final data",required=False,disabled=False,widget=DatePickerInput(options={"format": "DD/MM/YYYY "}))

    widgets = {
            # "_from": DatePickerInput(options={"format": "DD/MM/YYYY "}),
            # "_to": DatePickerInput(options={"format": "DD/MM/YYYY "}),
        }
    
    def __init__(self, *args, **kwargs):
        super(reportForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
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
                        Column(Submit('submit', _('Show'),css_class="btn btn-primary col-12"),css_class="col-9"),
                        Column(HTML('<a href="{% url "home" %}" class="btn btn-secondary col-12">'+str(_('Back'))+'</a>'),css_class="col-3"),
                        css_class="row")
                    )
        
        self.helper.layout = Layout(
                                    Field('_type',type=''),
                                    Field('_from',type=''),
                                    Field('_to',type=''),
                                    buttons,
                                )
        
    def clean__type(self,):
        return int(self.cleaned_data['_type'])
    
class siteSettingsForm(forms.ModelForm):

    class Meta:
        model = SiteSettings
        exclude = []

    def __init__(self, *args, **kwargs):
        super(siteSettingsForm, self).__init__(*args, **kwargs)
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
                        Column(Submit('submit', _('Save'),css_class="btn btn-primary col-12"),css_class="col-9"),
                        Column(HTML('<a href="{% url "home"  %}" class="btn btn-secondary col-12">'+str(_('Cancel'))+'</a>'),css_class="col-3"),
                        css_class="row")
                    )
        
        self.helper.layout = Layout(
                                    Fieldset(_("Shop details"),
                                        'SHOP_NAME',
                                        'SHOP_ADDR1',
                                        'SHOP_ADDR2',
                                        'SHOP_VAT',
                                        'SHOP_PHONE',
                                        'SHOP_WEB',
                                        'PUBLISH_TO_WEB'
                                    ),
                                    Fieldset(_("Application details"),
                                        'VERSION_AUTO_UPDATE',
                                        'VERSION_CODE',
                                        'LAN_IP',
                                        AppendedText('SEC2LOGOUT', 's', active=True)
                                    ),
                                    Fieldset(_("Accountancy details"),
                                        AppendedText('VAT', '%', active=True)
                                    ),

                                )
        self.helper.layout.append(buttons)