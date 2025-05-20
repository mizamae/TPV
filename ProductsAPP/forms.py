from django import forms
from django.utils.translation import gettext as _
from .models import BillAccount, Consumible, Product

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions,InlineRadios
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Column, Field
from bootstrap_datepicker_plus.widgets import DatePickerInput

FORMS_LABEL_CLASS='col'
FORMS_FIELD_CLASS='col'

class billSearchForm(forms.Form):
    code=forms.CharField(label=_("Code"),help_text="Code of the bill",required=False)
    _from = forms.DateField(label=_("From"),help_text="Date of the initial data",required=False,disabled=False,widget=DatePickerInput(options={"format": "DD/MM/YYYY "}))
    _to = forms.DateField(label=_("To"),help_text="Date of the final data",required=False,disabled=False,widget=DatePickerInput(options={"format": "DD/MM/YYYY "}))

    def __init__(self, *args, **kwargs):
        super(billSearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.label_class = 'col-3 h3'
        self.helper.field_class = 'col-9'
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
                                    Field('code',type='',id='id_code',placeholder=_('Enter bill code')),
                                    Field('_from',type=''),
                                    Field('_to',type=''),
                                    buttons,
        )

class barcode2BillForm(forms.Form):
    barcode=forms.CharField(required=True)
    def __init__(self, *args, **kwargs):
        super(barcode2BillForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.label_class = 'col-3 h3'
        self.helper.field_class = 'col-9'
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

        self.helper.layout = Layout(
                                    Field('barcode',type='',id='id_barcode',placeholder=_('Enter/Scan a barcode')),
                                )
        
class paymentMethodsForm(forms.ModelForm):

    class Meta:
        model = BillAccount
        fields = ["paymenttype"]
        widgets = {
          'paymenttype': forms.RadioSelect(),
        }
    def __init__(self, *args, **kwargs):
        super(paymentMethodsForm, self).__init__(*args, **kwargs)
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
        
        buttons=FormActions(
                        Div(
                        Column(Submit('submit', _('Close the bill'),css_class="btn btn-primary col-12"),css_class="col-9"),
                        Column(HTML('<a href="{% url "MaterialsAPP_edit_bill" "'+str(self.instance.code)+'" 0 %}" class="btn btn-secondary col-12">'+str(_('Cancel'))+'</a>'),css_class="col-3"),
                        css_class="row")
                    )
        
        self.helper.layout = Layout(
                                    #InlineRadios('paymenttype'),
                                    Field('paymenttype',type=''),

                                )
        self.helper.layout.append(buttons)


class ConsumibleInlineForm(forms.ModelForm):
    class Meta:
        model = Consumible
        fields = ["name","cost","pvp","stock"]
        widgets = { # this is needed since the virtual keyboard only works with inputs type text, not number
            'cost': forms.TextInput(attrs={'type':'text','inputmode':"numeric"}),
            'pvp': forms.TextInput(attrs={'type':'text','inputmode':"numeric"}),
            'stock': forms.TextInput(attrs={'type':'text','inputmode':"numeric"})
        }
    
    def __init__(self, *args, **kwargs):
        super(ConsumibleInlineForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.label_class = FORMS_LABEL_CLASS
        self.helper.field_class = FORMS_FIELD_CLASS
        self.helper.form_class = 'form-inline'
        self.helper.form_method = 'post'
        self.helper.form_show_labels = False
        
        self.fields['name'].disabled=True
        
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'step':'0.1','min':'0','class':'form-control keyboard-numeric','data-toggle':'tooltip' ,'title':help_text, 'data-placement':'right', 'data-container':'body'})
            else:
                self.fields[field].widget.attrs.update({'step':'0.1','min':'0','class':'form-control keyboard-numeric'})
        
        self.helper.layout = Layout(
                                    Field('name',type=''),
                                    Field('cost',type='text'),
                                    Field('pvp',type='text'),
                                    Field('stock',type='text'),
                                )

StockFormSet = forms.modelformset_factory(Consumible,form=ConsumibleInlineForm,
                                    fields = ["name","cost","pvp","stock"],extra=0,can_delete=False,edit_only=True,)

class ProductInlineForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name","manual_pvp","discount"]
        widgets = { # this is needed since the virtual keyboard only works with inputs type text, not number
            'manual_pvp': forms.TextInput(attrs={'type':'text','inputmode':"numeric"})
        }
    
    def __init__(self, *args, **kwargs):
        super(ProductInlineForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.label_class = FORMS_LABEL_CLASS
        self.helper.field_class = FORMS_FIELD_CLASS
        self.helper.form_class = 'form-inline'
        self.helper.form_method = 'post'
        self.helper.form_show_labels = False
        
        self.fields['name'].disabled=True
        
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class':'form-control','data-toggle':'tooltip' ,'title':help_text, 'data-placement':'right', 'data-container':'body'})
            else:
                self.fields[field].widget.attrs.update({'class':'form-control'})
            if field=='manual_pvp': # to display the screen keyboard
                self.fields[field].widget.attrs.update({'step':'0.1','min':'0','class':'form-control keyboard-numeric'})
        self.helper.layout = Layout(
                                    Field('name',type=''),
                                    Field('manual_pvp',type='text'),
                                    Field('discount',type=''),
                                )

ProductFormSet = forms.modelformset_factory(Product,form=ProductInlineForm,fields = ["name","manual_pvp","discount"],extra=0,can_delete=False,edit_only=True,)