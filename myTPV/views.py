from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils.translation import gettext as _
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.conf import settings
import datetime
import pandas as pd
from django.db.models import Q
User=get_user_model()

from ProductsAPP.models import BillAccount
from .forms import reportForm, REPORT_TYPE_SALES, REPORT_TYPE_PRODUCTS

def home(request):
    now = datetime.datetime.now()
    start_datetime = datetime.datetime(now.year, now.month, now.day)
    todays_bills = BillAccount.objects.filter(createdOn__gt=start_datetime).annotate(order_positions = Count('positions'))
    todays_income=0
    for bill in todays_bills.filter(status = BillAccount.STATUS_PAID):
        todays_income += bill.getPVP()

    return render(request, 'home.html',{'todays_bills':todays_bills,
                                        'todays_income':todays_income})

def reports_home(request):
    if request.method == "POST":
        form=reportForm(request.POST)
        if form.is_valid():
            report={}
            report['type'] = form.cleaned_data['_type']
            report['to'] = form.cleaned_data['_to'] if form.cleaned_data['_to'] else datetime.datetime.today().date()+datetime.timedelta(days=1)
            report['from'] = form.cleaned_data['_from'] if form.cleaned_data['_from'] else report['to']-datetime.timedelta(days=365)
            figures = []
            titles=[]
            if report['type']==REPORT_TYPE_SALES:
                from ProductsAPP.models import BillAccount
                import plotly.express as px
                import plotly.graph_objects as go
                from plotly.offline import plot
                from plotly.subplots import make_subplots
                totalBills = BillAccount.objects.filter(createdOn__gte=report['from'],createdOn__lte=report['to'],status=BillAccount.STATUS_PAID).values()
                df = pd.DataFrame(totalBills)
                if not df.empty:
                    df['name_day_of_week'] = df['createdOn'].dt.day_name()
                    df['day_of_week'] = df['createdOn'].dt.weekday
                    df['createdOn'] = pd.to_datetime(df['createdOn']).dt.date
                    
                    df_fig11 = df.groupby('createdOn')['id'].count()
                    df_fig11 = df_fig11.rename('Operations')
                    df_fig12 = df.groupby('createdOn')['total'].sum()
                    df_fig12 = df_fig12.rename('Income')

                    #fig = px.line(df_fig1, y="Operations")
                    fig = make_subplots(rows=1,specs=[[{"secondary_y": True}]])
                    fig.update_yaxes(title_text="Operations", secondary_y=False)
                    fig.update_yaxes(title_text="Income [€]", secondary_y=True)
                    fig.add_trace(go.Line(x=df_fig11.index.values, y=df_fig11.values,name='Operations',offsetgroup=1),secondary_y=False,)
                    fig.add_trace(go.Line(x=df_fig12.index.values, y=df_fig12.values,name='Income [€]',offsetgroup=2),secondary_y=True,)

                    fig.update_xaxes(
                                showgrid=True,
                                rangeslider_visible=True,
                                rangeselector=dict(
                                    buttons=list([
                                        dict(count=1, label="1m", step="month", stepmode="backward"),
                                        dict(count=6, label="6m", step="month", stepmode="backward"),
                                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                                        dict(count=1, label="1y", step="year", stepmode="backward"),
                                        dict(step="all")
                                    ])
                                ),
                                minor=dict(ticks="inside", showgrid=True),
                                tickformat="%b %e (%a)")
                    figures.append(plot({'data': fig}, output_type='div'))
                    titles.append(_("Per day"))

                    df_fig2 = df.groupby('name_day_of_week')['id'].count()
                    df_fig2 = df_fig2.rename('Operations')
                    df_fig2 = df_fig2.reindex(['Monday','Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday','Sunday'])
                    df_fig3 = df.groupby('name_day_of_week')['total'].sum()
                    df_fig3 = df_fig3.rename('Income')
                    df_fig3 = df_fig3.reindex(['Monday','Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday','Sunday'])

                    fig = make_subplots(rows=1,specs=[[{"secondary_y": True}]])
                    fig.update_yaxes(title_text="Operations", secondary_y=False)
                    fig.update_yaxes(title_text="Income [€]", secondary_y=True)
                    fig.add_trace(go.Bar(x=df_fig2.index.values, y=df_fig2.values,name='Operations',offsetgroup=1),secondary_y=False,)
                    fig.add_trace(go.Bar(x=df_fig3.index.values, y=df_fig3.values,name='Income [€]',offsetgroup=2),secondary_y=True,)
                    fig.update_layout(
                        barmode='group',
                        bargap=0.0, # gap between bars of adjacent location coordinates.
                        bargroupgap=0, # gap between bars of the same location coordinate.
                        )
                    figures.append(plot({'data': fig}, output_type='div'))
                    titles.append(_("Per week-day"))
                else:
                    pass

                return render(request, 'reportWithFigs.html', {'titles':titles,'figures':figures })
            
    else:
        form=reportForm()

    return render(request, 'form.html', {'form': form,
                                        'title':_("View report"),
                                        'back_to':'home',})