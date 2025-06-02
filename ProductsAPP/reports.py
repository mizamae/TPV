
from django.utils.translation import gettext as _
import pandas as pd
from .models import BillAccount, BillPosition, Product, ProductFamily
from django.conf import settings
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots

def ProductsReport(_from,_to):
    figures = []
    titles=[]
    totalBillPos = BillPosition.objects.select_related('product').filter(bill__createdOn__gte=_from,bill__createdOn__lte=_to,bill__status=BillAccount.STATUS_PAID)
    df = pd.DataFrame([[billPos.product.family.name, billPos.product.name,billPos.quantity,billPos.product.cost,billPos.product.pvp] for billPos in totalBillPos],
                      columns = ('family_name','product_name','quantity','product_cost','pvp'))
    if not df.empty:
        df['position_revenue'] = df['quantity']*(df['pvp']-df['product_cost'])

        # units sold figure
        df_fig11 = df.groupby('product_name')['quantity'].sum()
        df_fig11 = df_fig11.rename('Units sold')
        df_fig11.sort_values(ascending=False,inplace=True)

        fig = make_subplots(rows=1,specs=[[{"secondary_y": False}]])
        fig.update_yaxes(title_text="Units sold", secondary_y=False)
    
        fig.add_trace(go.Bar(x=df_fig11.index.values, y=df_fig11.values,name='Units sold',offsetgroup=1),secondary_y=False,)
        fig.update_layout(
            barmode='group',
            bargap=0.0, # gap between bars of adjacent location coordinates.
            bargroupgap=0, # gap between bars of the same location coordinate.
            )
        figures.append(plot({'data': fig}, output_type='div'))
        titles.append(_("Units sold per product"))

        # Revenue figure
        df_fig2 = df.groupby('product_name')['position_revenue'].sum()
        df_fig2 = df_fig2.rename('Total revenue')
        df_fig2.sort_values(ascending=False,inplace=True)
        fig = make_subplots(rows=1,specs=[[{"secondary_y": False}]])
        fig.update_yaxes(title_text="Revenue [€]", secondary_y=False)
    
        fig.add_trace(go.Bar(x=df_fig2.index.values, y=df_fig2.values,name='Revenue [€]',offsetgroup=1),secondary_y=False,)
        fig.update_layout(
            barmode='group',
            bargap=0.0, # gap between bars of adjacent location coordinates.
            bargroupgap=0, # gap between bars of the same location coordinate.
            )
        figures.append(plot({'data': fig}, output_type='div'))
        titles.append(_("Total revenue per product"))

        # units sold figure
        df_fig13 = df.groupby('family_name')['quantity'].sum()
        df_fig13 = df_fig13.rename('Units sold')
        df_fig13.sort_values(ascending=False,inplace=True)

        fig = make_subplots(rows=1,specs=[[{"secondary_y": False}]])
        fig.update_yaxes(title_text="Units sold", secondary_y=False)
    
        fig.add_trace(go.Bar(x=df_fig13.index.values, y=df_fig13.values,name='Units sold',offsetgroup=1),secondary_y=False,)
        fig.update_layout(
            barmode='group',
            bargap=0.0, # gap between bars of adjacent location coordinates.
            bargroupgap=0, # gap between bars of the same location coordinate.
            )
        figures.append(plot({'data': fig}, output_type='div'))
        titles.append(_("Units sold per family"))
    else:
        pass
    return titles,figures

def SalesReport(_from,_to):
    figures = []
    titles=[]
    totalBills = BillAccount.objects.prefetch_related('positions').filter(createdOn__gte=_from,createdOn__lte=_to,status=BillAccount.STATUS_PAID)
    df = pd.DataFrame([[bill.createdOn,bill.id,bill.total] for bill in totalBills],columns=('createdOn','id','total'))
    df.set_index('createdOn',inplace=True)
    df = df.tz_convert(settings.TIME_ZONE)
    if not df.empty:
        df['name_day_of_week'] = df.index.day_name()
        df['day_of_week'] = df.index.weekday
        df['createdOnDate'] = df.index.date
        
        # PER DAY
        df_fig11 = df.groupby('createdOnDate')['id'].count()
        df_fig11 = df_fig11.rename('Operations')
        df_fig12 = df.groupby('createdOnDate')['total'].sum()
        df_fig12 = df_fig12.rename('Income')

        #fig = px.line(df_fig1, y="Operations")
        fig = make_subplots(rows=1,specs=[[{"secondary_y": True}]])
        fig.update_yaxes(title_text="Operations", secondary_y=False)
        fig.update_yaxes(title_text="Income [€]", secondary_y=True)
        fig.add_trace(go.Line(x=df_fig11.index.values, y=df_fig11.values,name='Operations',offsetgroup=1),secondary_y=False,)
        fig.add_trace(go.Line(x=df_fig12.index.values, y=df_fig12.values,name='Income [€]',offsetgroup=2),secondary_y=True,)

        fig.update_xaxes(
                    showgrid=True,
                    # rangeslider_visible=True,
                    # rangeselector=dict(
                    #     buttons=list([
                    #         dict(count=1, label="1m", step="month", stepmode="backward"),
                    #         dict(count=6, label="6m", step="month", stepmode="backward"),
                    #         dict(count=1, label="YTD", step="year", stepmode="todate"),
                    #         dict(count=1, label="1y", step="year", stepmode="backward"),
                    #         dict(step="all")
                    #     ])
                    # ),
                    minor=dict(ticks="inside", showgrid=True),
                    tickformat="%b %e (%a)")
        figures.append(plot({'data': fig}, output_type='div'))
        titles.append(_("Per day"))

        # PER WEEK-DAY
        df_fig21 = df.groupby('name_day_of_week')['id'].count()
        df_fig21 = df_fig21.rename('Operations')
        df_fig21 = df_fig21.reindex(['Monday','Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday','Sunday'])
        df_fig22 = df.groupby('name_day_of_week')['total'].sum()
        df_fig22 = df_fig22.rename('Income')
        df_fig22 = df_fig22.reindex(['Monday','Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday','Sunday'])

        fig = make_subplots(rows=1,specs=[[{"secondary_y": True}]])
        fig.update_yaxes(title_text="Operations", secondary_y=False)
        fig.update_yaxes(title_text="Income [€]", secondary_y=True)
        fig.add_trace(go.Bar(x=df_fig21.index.values, y=df_fig21.values,name='Operations',offsetgroup=1),secondary_y=False,)
        fig.add_trace(go.Bar(x=df_fig22.index.values, y=df_fig22.values,name='Income [€]',offsetgroup=2),secondary_y=True,)
        fig.update_layout(
            barmode='group',
            bargap=0.0, # gap between bars of adjacent location coordinates.
            bargroupgap=0, # gap between bars of the same location coordinate.
            )
        figures.append(plot({'data': fig}, output_type='div'))
        titles.append(_("Per week-day"))

        # PER HOUR
        df_fig31 = df.groupby([df.index.hour]).id.count()
        df_fig31 = df_fig31.rename('Operations')
        df_fig32 = df.groupby([df.index.hour]).total.sum()
        df_fig32 = df_fig32.rename('Income [€]')
        fig = make_subplots(rows=1,specs=[[{"secondary_y": True}]])
        fig.update_yaxes(title_text="Operations", secondary_y=False)
        fig.update_yaxes(title_text="Income [€]", secondary_y=True)
        fig.add_trace(go.Bar(x=df_fig31.index.values, y=df_fig31.values,name='Operations',offsetgroup=1),secondary_y=False,)
        fig.add_trace(go.Bar(x=df_fig32.index.values, y=df_fig32.values,name='Income [€]',offsetgroup=2),secondary_y=True,)
        fig.update_layout(
            barmode='group',
            bargap=0.0, # gap between bars of adjacent location coordinates.
            bargroupgap=0, # gap between bars of the same location coordinate.
            )
        figures.append(plot({'data': fig}, output_type='div'))
        titles.append(_("Per hour"))
    else:
        pass
    return titles,figures