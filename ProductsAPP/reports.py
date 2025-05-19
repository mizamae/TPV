
from django.utils.translation import gettext as _
import pandas as pd
from .models import BillAccount

import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots

def SalesReport(_from,_to):
    figures = []
    titles=[]
    totalBills = BillAccount.objects.filter(createdOn__gte=_from,createdOn__lte=_to,status=BillAccount.STATUS_PAID).values()
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
    return titles,figures