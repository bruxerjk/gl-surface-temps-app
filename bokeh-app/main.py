import pandas as pd

from bokeh.io import curdoc, show
from bokeh.models.sources import ColumnDataSource
from bokeh import palettes
from bokeh.plotting import figure
from bokeh.models import FixedTicker, Range1d, HoverTool, Label, Div, Slider
from bokeh.layouts import layout
from math import pi


PLOT_WIDTH = 330
PLOT_HEIGHT = int(PLOT_WIDTH * 0.7)

def get_data(lake):

    url = f'''https://apps.glerl.noaa.gov/coastwatch/webdata/statistic/csv/all_year_glsea_avg_{lake}_C.csv'''
    df = pd.read_csv(url, index_col=[0])
    df.index.rename('day', inplace=True)

    return {'url': url, 'data': df}


def create_baseplot(lake):
    '''create base spaghetti plot'''

    plot_width = PLOT_WIDTH
    plot_height = PLOT_HEIGHT
    tools=[]

    fig = figure(title=lake,
                 plot_height=plot_height,
                 plot_width=plot_width,
                 tools=tools)

    # y-axis formatting
    fig.y_range=Range1d(0, 30, bounds='auto')
    fig.yaxis.axis_label = 'Temperature ({})'.format(u'\u2103') # unicode deg Celsius

    # x-axis formatting
    fig.xaxis.major_label_orientation = pi/2
    fig.x_range=Range1d(0, 366, bounds='auto')

    # locate x-ticks at start of each month
    ticks = []
    day_of_year=0

    for days in [1,31,28,31,30,31,30,31,31,30,31,30,31]:
        day_of_year = day_of_year + days
        ticks.append(day_of_year)

    fig.xaxis.ticker = FixedTicker(ticks=ticks)

    # label ticks with month name
    labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec','Jan']
    tick_labels = dict(zip(ticks, labels))
    fig.xaxis.major_label_overrides = tick_labels


    fig.toolbar.logo = None

    return fig


def plot_all(fig, df, start_year, end_year):


    lines = list() # empty list to hold each plotted line

    source = ColumnDataSource(df)

    offset = 5
    # generate palette the size of dataset but offset each end
    palette = palettes.grey(end_year - start_year + 1 + offset*2)

    unselected_kwargs = dict(line_width = 1.5,
                             line_alpha = 0.5)

    # plot all years
    for i, yr in enumerate(range(start_year, end_year+1)):

        lines.append(fig.line(x='day',
                              y=str(yr),
                              source=source,
                              color=palette[i+offset],
                              name=str(yr),
                              **unselected_kwargs))


    return fig, lines


def get_tooltips(year):

    tooltips = [('Date', '-'.join((year,'@date'))),
                ('Value', '$y{0.0}'+u'\u2103')]

    return tooltips


def plot_selected(fig, df, year):

    # add highlighted line function
    # uses custom javascript callback
    # based on https://stackoverflow.com/a/42321618/2574074

    selected_color = 'firebrick'
    selected_kwargs = dict(line_color = selected_color,
                           line_width = 4)

    source = ColumnDataSource(df)

    y=str(year)
    selected = fig.line(x='day',
                          y=y,
                          source=source,
                          name=y,
                          **selected_kwargs)

    tooltips = get_tooltips(y)

    hover = fig.add_tools(HoverTool(tooltips=tooltips,
                         toggleable = False,
                         names=[y],
                         mode='vline'
                         ))

    # find location of peak value for labelling
    labelx = df[str(year)].idxmax(axis=0) # index of max temp
    labely = df.loc[:, str(year)].max() # max temp

    # add label for selected year, locate at peak
    label = Label(x=labelx, y=labely, x_units='data',
                        text=str(year), render_mode='css',
                        text_color=selected_color, text_baseline='bottom',
                        text_font_style = 'bold')

    fig.add_layout(label)

    return fig, selected, hover, label


def build_layout():

    lakes = {'Lake Superior': get_data('s'),
             'Lake Michigan': get_data('m'),
             'Lake Huron': get_data('h'),
             'Lake Erie': get_data('e'),
             'Lake Ontario': get_data('o'),
             'Lake St. Clair': get_data('c')}

    for lake in lakes.keys():

        fig = create_baseplot(lake)
        df = lakes[lake]['data']

        start_year = int(df.columns[0])
        end_year = int(df.columns[-1])

        df['date'] = pd.to_datetime(df.index, format='%j').strftime('%m-%d')

        fig, lines = plot_all(fig, df, start_year, end_year)

        fig, selected, hover, label = plot_selected(fig, df, end_year)

        lakes[lake]['plot'] = {'fig':fig,
                               'lines':lines,
                               'selected':selected,
                               'label':label}

    curdoc().theme = 'light_minimal'

    credits_text_1 = '''Data: NOAA Great Lakes Environmental Research Laboratory'''
    credits_text_2 = '''Graphic: Jacob Bruxer'''

    title = '<br>Great Lakes Surface Water Temperatures (1995-{})'.format(end_year)

    subtitle = '<br>' + credits_text_1.format(end_year) + \
               '<br>URL : https://coastwatch.glerl.noaa.gov/statistic/statistic.html' + \
               '<br><br>' + credits_text_2

    width = PLOT_WIDTH
    height = 100

    title= Div(text=title.format(end_year),
           style={'font-size': '150%', 'color': 'black'},
           width=width, height=height)

    subtitle=Div(text=subtitle,
             style={'font-size': '70%', 'color': 'black'},
             width=width, height=height)

    slider = Slider(start=start_year,
                    end=end_year,
                    value=end_year,
                    step=1,
                    title='Select Year',
                    width=width-30,
                    bar_color='firebrick',
                    orientation='horizontal')

    # add slider with callback
    def callback(atrr, old, new):


        for lake in lakes.keys():
            p = lakes[lake]['plot']
            p['selected'].glyph.name=str(slider.value)
            p['selected'].glyph.y=str(slider.value)
            y = str(slider.value)
            p['fig'].tools[0].tooltips = get_tooltips(y)
            p['fig'].tools[0].names = [y]
            #p['fig'].tools[0] = get_hovertool(str(slider.value))

            # find location of peak value for labelling
            labelx = lakes[lake]['data'][y].idxmax(axis=0) # index of max temp
            labely = lakes[lake]['data'].loc[:, y].max() # max temp

            # add label for selected year, locate at peak
            lakes[lake]['plot']['label'].x=labelx
            lakes[lake]['plot']['label'].y=labely
            lakes[lake]['plot']['label'].text=y
            lakes[lake]['plot']['label'].text_font_style = 'bold'

    slider.on_change('value', callback)

    plots = [None]*5
    plots[0] = lakes['Lake Superior']['plot']['fig']
    plots[1] = lakes['Lake Michigan']['plot']['fig']
    plots[2] = lakes['Lake Huron']['plot']['fig']
    plots[3] = lakes['Lake Erie']['plot']['fig']
    plots[4] = lakes['Lake Ontario']['plot']['fig']

    app_layout = layout([[plots[0]], plots[1], plots[2]],
           [plots[3], plots[4], [title, subtitle, slider]])

    for lake in [1,2,4]:
        plots[lake].yaxis.axis_label = None
        plots[lake].plot_width = PLOT_WIDTH - 25

    return app_layout

app_layout = build_layout()
curdoc().add_root(app_layout)
curdoc().title = "Great Lakes Surface Temps"
