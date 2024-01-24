import plotly.express as px
import folium
import json
import requests
import pandas
from pyecharts.charts import Map
from pyecharts import options as opts
from pyecharts.charts import Timeline
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.animation as animation
import numpy as np
from IPython.display import HTML
import webbrowser

from tkinter import *

def cumulative():
    # read the csv files about the data
    confirmed = pd.read_csv(
        'time_series_covid19_confirmed_global.csv')
    recovered = pd.read_csv(
        'time_series_covid19_recovered_global.csv')
    deaths = pd.read_csv(
        'time_series_covid19_deaths_global.csv')

    # Taiwan is part of China
    confirmed.replace('Taiwan*', 'China', inplace=True)
    recovered.replace('Taiwan*', 'China', inplace=True)
    deaths.replace('Taiwan*', 'China', inplace=True)

    # Group by country
    confirmed.groupby(['Country/Region']).sum()
    recovered.groupby(['Country/Region']).sum()
    deaths.groupby(['Country/Region']).sum()
    print(confirmed.head())

    ##########################################
    # PART 1 ABOUT THE COUNTRY CONFIRMED CASES

    # We want total data before 5/23/21
    last_update = '5/23/21'
    global_case_by_province = confirmed[['Country/Region', last_update]]
    print(global_case_by_province.head(5))

    # China parts
    China_confirmed = confirmed[['Province/State', last_update]][confirmed['Country/Region'] == 'China']
    China_confirmed = China_confirmed.rename(columns={last_update: 'confirmed'})

    China_recovered = recovered[['Province/State', last_update]][recovered['Country/Region'] == 'China']
    China_recovered = China_recovered.rename(columns={last_update: 'recovered'})

    China_deaths = deaths[['Province/State', last_update]][deaths['Country/Region'] == 'China']
    China_deaths = China_deaths.rename(columns={last_update: 'deaths'})

    # Merge the confirmed, recovered, group by Province
    _China_cases = pd.merge(China_confirmed, China_recovered, on='Province/State')
    China_cases = pd.merge(_China_cases, China_deaths, on='Province/State')
    # Let province be the index
    China_cases = China_cases.set_index('Province/State')
    print(China_cases.head(34))

    # World parts
    others_confirmed = confirmed[['Country/Region', last_update]][confirmed['Country/Region'] != 'China']
    others_confirmed = others_confirmed.groupby('Country/Region').sum()
    others_confirmed = others_confirmed.rename(columns={last_update: 'confirmed'})

    others_recovered = recovered[['Country/Region', last_update]][recovered['Country/Region'] != 'China']
    others_recovered = others_recovered.groupby('Country/Region').sum()
    others_recovered = others_recovered.rename(columns={last_update: 'recovered'})

    others_deaths = deaths[['Country/Region', last_update]][deaths['Country/Region'] != 'China']
    others_deaths = others_deaths.groupby('Country/Region').sum()
    others_deaths = others_deaths.rename(columns={last_update: 'deaths'})

    _others = pd.merge(others_confirmed, others_recovered, on='Country/Region')
    others = pd.merge(_others, others_deaths, on='Country/Region')
    print(others.head())

    # We should add longitude and latitude to locate the country
    locations = confirmed[['Country/Region', 'Lat', 'Long']]
    # Find the mean of each country's longitude and latitude
    locations = locations.groupby('Country/Region').mean()
    print(locations.head())

    # Merge the others and locations together
    other_countries = pd.merge(others, locations, on='Country/Region')
    print(other_countries.head())

    # Put China information to the world
    other_countries.loc['China'] = [China_cases['confirmed'].sum(),
                                    China_cases['recovered'].sum(),
                                    China_cases['deaths'].sum(),
                                    30.9756, 112.2707]
    print(other_countries.head(185))

    # Reset the other countries index
    other_countries = other_countries.reset_index()
    print(other_countries.head())

    # Build the map using folium.Map
    world_map = folium.Map(location=[10, -20], zoom_start=2.3, tiles='Stamen Toner')
    for lat, long, value, name in zip(other_countries['Lat'],
                                      other_countries['Long'],
                                      other_countries['confirmed'],
                                      other_countries['Country/Region']):
        # Make the circle marker to the map
        folium.CircleMarker([lat, long], redius=10,
                            popup=('<strong>Country</strong>: ' + str(name).capitalize() +
                                   '<br>' + '<strong>Confirmed</strong>: ' +
                                   str(value) + '<br>'),
                            color='red',
                            fill_color='red',
                            fill_opacity=0.7).add_to(world_map)
    print(confirmed.head())
    # Save the Part one map in the map.html
    world_map.save('map.html')
    import webbrowser
    webbrowser.open_new_tab('map.html')

def World():
    # read the csv files about the data
    confirmed = pd.read_csv(
        'time_series_covid19_confirmed_global.csv')
    recovered = pd.read_csv(
        'time_series_covid19_recovered_global.csv')
    deaths = pd.read_csv(
        'time_series_covid19_deaths_global.csv')
    ########################
    # PART 2 WORLD TIME LINE

    # Uniform Date Format about confirmed information
    confirmed = confirmed.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
                               var_name='date',
                               value_name='confirmed')
    confirmed['date_dt'] = pd.to_datetime(confirmed.date, format='%m/%d/%y')
    confirmed.date = confirmed.date_dt.dt.date
    confirmed.rename(columns={'Country/Region': 'country', 'Province/State': 'province'}, inplace=True)
    print(confirmed.head())

    # Uniform Date Format about recovered information
    recovered = recovered.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
                               var_name='date', value_name='recovered')
    recovered['date_dt'] = pd.to_datetime(recovered.date, format='%m/%d/%y')
    recovered.date = recovered.date_dt.dt.date
    recovered.rename(columns={'Country/Region': 'country', 'Province/State': 'province'}, inplace=True)
    print(recovered.head())

    # Uniform Date Format about deaths information
    deaths = deaths.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
                         var_name='date', value_name='deaths')
    deaths['date_dt'] = pd.to_datetime(deaths.date, format='%m/%d/%y')
    deaths.date = deaths.date_dt.dt.date
    deaths.rename(columns={'Country/Region': 'country', 'Province/State': 'province'}, inplace=True)
    print(deaths.head())

    # Merge the confirm, deaths and recovered
    merge_on = ['province', 'country', 'date']
    all_date = confirmed.merge(deaths[merge_on + ['deaths']], how='left', on=merge_on). \
        merge(recovered[merge_on + ['recovered']], how='left', on=merge_on)
    print(all_date.head())

    # Draw map group by country
    Coronavirus_map = all_date.groupby(['date_dt', 'country'])[
        'confirmed', 'deaths', 'recovered', 'Lat', 'Long'].max().reset_index()
    Coronavirus_map['size'] = Coronavirus_map.confirmed.pow(0.2)

    # Uniform Date Format about data information
    Coronavirus_map['date_dt'] = Coronavirus_map['date_dt'].dt.strftime('%Y-%m-%d')
    print(Coronavirus_map.head())

    # We fill the empty to the 0
    Coronavirus_map = Coronavirus_map.fillna(0)
    print(Coronavirus_map.head())

    # Draw the scatter geographic
    fig = px.scatter_geo(Coronavirus_map, lat='Lat', lon='Long', scope='world',
                         color='size', size='size', size_max=30, hover_name='country',
                         hover_data=['confirmed', 'deaths', 'recovered'],
                         projection='natural earth', animation_frame='date_dt',
                         title=' ')
    fig.update(layout_coloraxis_showscale=True)
    fig.show()

def China():
    data = pandas.read_excel('xgyq.xlsx', sheet_name='2',
                             index_col='time')
    # Take out the list of provinces
    attr = data.columns.tolist()
    # Calculate the number of data
    n = len(data.index)

    # Define daily mapping functions
    def map_visualmap(sequence, date) -> Map:
        c = (
            Map()
                .add(date, sequence, maptype="china")
                .set_global_opts(
                title_opts=opts.TitleOpts(title="China covid-19 dynamic map"),
                visualmap_opts=opts.VisualMapOpts(max_=150),
            )
        )
        return c

    # Creating a timeline object
    timeline = Timeline()

    for i in range(n):
        # Get daily data
        row = data.iloc[i,].tolist()
        # Convert data to binary list
        sequence_temp = list(zip(attr, row))
        # Format the date for display
        time = format(data.index[i], "%Y-%m-%d")
        # Create a map
        map_temp = map_visualmap(sequence_temp, time)
        # Add map to timeline object
        timeline.add(map_temp, time).add_schema(play_interval=360)
    # After the map is created, the map can be rendered as HTML by the render () method
    timeline.render('China covid-19 dynamic map.html')
    webbrowser.open_new_tab('China covid-19 dynamic map.html')

def US():
    # load the data
    df = pd.read_csv(r'./us-states.csv')
    #read data of us states

    df_statenames = pd.read_csv('./USA_states_twoletter_code.csv')
    #a table contain full name of states and two letter form of states

    #create a new attribute in dataframe which will contain two letter form of states for scatter_geo use
    df['state code'] = df['state']
    for i in range(len(df_statenames)):
        df['state code'].replace(df_statenames.loc[i]['state name'],
            df_statenames.loc[i]['two letter'], inplace=True)

    fig = px.scatter_geo(df, locations='state code',
        locationmode = 'USA-states', color='cases',
        color_continuous_scale=px.colors.sequential.Agsunset,
        hover_name='state', size='cases', size_max = 80,
        hover_data=['deaths'], scope='usa',
        title='USA COVID-19 cases',
        animation_frame='date')

    fig.show()

def ChinaAll():
    # ------------------------Crawl real-time data from Tencent news--------------------------------------------
    url_cn = 'https://view.inews.qq.com/g2/getOnsInfo?name=disease_h5&callback=&_=%d'
    # the data is json version, we need to change the type to the python type dictionary
    info_cn = json.loads(requests.get(url=url_cn).json()['data'])
    # print(info_cn)
    '''
       dict_keys(['lastUpdateTime', 'chinaTotal', 'chinaAdd', 'isShowAdd', 'showAddSwitch', 'areaTree'])
       we can get the webpage elements by the statement of print(info_cn.keys())
    '''
    # --------------------------Extract the required data-------------------------------------------------------
    # get information about all province
    province_info = info_cn['areaTree'][0]['children']
    # print(province_info)

    # the confirmed data today
    now_confirm = {}
    new_add = {}
    for province in province_info:
        # initialize the value to 0 and update to the new dictionary
        if province['name'] not in now_confirm:
            now_confirm.update({province['name']: 0})
    for province in province_info:
        # re-assign the value to the new_confirm
        for confirm in province['children']:
            now_confirm[province['name']] += int(confirm['total']['confirm'])

    # the new data today
    for province in province_info:
        # initialize the value to 0 and update to the new dictionary
        if province['name'] not in new_add:
            new_add.update({province['name']: 0})
    for province in province_info:
        # re-assign the value to the new_add
        for add in province['children']:
            new_add[province['name']] += int(add['today']['confirm'])

    # --------------------------The figure 1--------------------------------------------
    # because the data is chinese , I set the chinese label
    plt.rcParams['font.sans-serif'] = ['SimHei']
    # Normal display symbol
    plt.rcParams['axes.unicode_minus'] = False
    # get information---analysis
    names1 = now_confirm.keys()
    val1 = now_confirm.values()
    print(names1)
    print(val1)
    print(now_confirm)
    plt.title("Number of confirmed cases of COVID-19 in China")
    plt.bar(names1, val1, width=0.8, color='red')
    plt.xticks(list(names1), rotation=45, size=10)
    plt.ylabel("Confirmed population", rotation=90)
    # The zip () method is also used in the drawing
    # to convert the extracted provinces and data into lists
    for a, b in zip(list(names1), list(val1)):
        plt.text(a, b, b)
    plt.show()

def ChinaToday():
    # ------------------------Crawl real-time data from Tencent news--------------------------------------------
    url_cn = 'https://view.inews.qq.com/g2/getOnsInfo?name=disease_h5&callback=&_=%d'
    # the data is json version, we need to change the type to the python type dictionary
    info_cn = json.loads(requests.get(url=url_cn).json()['data'])
    # print(info_cn)
    '''
       dict_keys(['lastUpdateTime', 'chinaTotal', 'chinaAdd', 'isShowAdd', 'showAddSwitch', 'areaTree'])
       we can get the webpage elements by the statement of print(info_cn.keys())
    '''
    # --------------------------Extract the required data-------------------------------------------------------
    # get information about all province
    province_info = info_cn['areaTree'][0]['children']
    # print(province_info)

    # the confirmed data today
    now_confirm = {}
    new_add = {}
    for province in province_info:
        # initialize the value to 0 and update to the new dictionary
        if province['name'] not in now_confirm:
            now_confirm.update({province['name']: 0})
    for province in province_info:
        # re-assign the value to the new_confirm
        for confirm in province['children']:
            now_confirm[province['name']] += int(confirm['total']['confirm'])

    # the new data today
    for province in province_info:
        # initialize the value to 0 and update to the new dictionary
        if province['name'] not in new_add:
            new_add.update({province['name']: 0})
    for province in province_info:
        # re-assign the value to the new_add
        for add in province['children']:
            new_add[province['name']] += int(add['today']['confirm'])

    # ---------------------The figure 2-----------------------------------------------------
    names2 = new_add.keys()
    val2 = new_add.values()
    # get information---analysis
    print(names2)
    print(val2)
    print(new_add)
    plt.title("New number of cases of COVID-19 in China")
    plt.bar(names2, val2, width=0.8, color='black')
    plt.xticks(list(names2), rotation=45, size=10)
    plt.ylabel("New confirmed population", rotation=90)
    # The zip () method is also used in the drawing
    # to convert the extracted provinces and data into lists
    for a, b in zip(list(names2), list(val2)):
        plt.text(a, b, b)
    plt.show()

def Comparing():
    # Solve the problem:
    # Animation size has reached 20989569 bytes, exceeding the limit of 20971520.0.
    import matplotlib
    matplotlib.rcParams['animation.embed_limit'] = 2 ** 128

    # get the dataframe, get data from the data stuff
    # use cols get the columns that we need
    df = pd.read_csv('World.csv', usecols=['Country', 'Date', 'Confirm', 'Days'])
    # make the colors as the zip to sum it into a zip
    # zip to better get the colors below
    colors = dict(zip(
        ['China', 'US', 'Japan', 'Singapore', 'South Korea', 'UK', 'Italy',
         'India', 'Germany', 'Spain', 'Brazil', 'Russia', 'Colombia', 'Turkey',
         'France', 'Norway', 'Switzerland', 'Mexico', 'Peru', 'Chile',
         'Argentina', 'South Africa', 'Netherland', 'Belgium', 'Iran'],
        ['#FF0000', '#990000', '#CC00FF', '#FF9900', '#66CCFF', '#FF9933', '#FFFF00',
         '#B8860B', '#0000EE', '#8B7B8B', '#ADFF2F', '#660000', '#666633', '#A52A2A',
         '#FA8072', '#F4A460', '#FFA54F', '#BBFFFF', '#FF4040', '#9900FF',
         '#330000', '#FF4500', '#BDBDBD', '#B23AEE', '#B22222']
    ))

    # get a function to draw
    # when doing animation, we get the drawchart function for each time
    def drawchart(Days):
        plt.xkcd()  # after all things done, add a comic style of the plot

        # get the information of the top 10 number of country
        dff = df[df['Days'].eq(Days)].sort_values(by='Confirm', ascending=True).tail(10)  # get the dataframe of 10
        # clear the axises
        ax.clear()
        # get each of those
        ax.barh(dff['Country'], dff['Confirm'], color=[colors[x] for x in dff['Country']])
        # set the type and distance of the data
        dx = dff['Confirm'].max() / 200
        for i, (Confirm, Country) in enumerate(zip(dff['Confirm'], dff['Country'])):
            # add information of number of confirm
            ax.text(Confirm - dx, i, Country, size=14, weight=600, ha='right', va='bottom')
            # add information of country name
            ax.text(Confirm + dx, i, f'{Confirm:,.0f}', size=14, ha='left', va='center')
        # ADD a variable to get the date
        DateMore = dff['Date']
        # we only need one of the date to print and it is enough
        Date = np.unique(DateMore)
        # time information display in the graph
        ax.text(1, 0.4, "Date: " + str(Date), transform=ax.transAxes, color='#777777', size=17, ha='right', weight=800)
        # axis title display in the graph
        ax.text(0, 1.06, 'Confirmed numbers', transform=ax.transAxes, size=10, color='#777777')
        # tickers info
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_ticks_position('top')
        # tickers of the params
        ax.tick_params(axis='x', colors='#777777', labelsize=12)
        ax.set_yticks([])
        ax.margins(0, 0.01)
        # polish lines and get the scales
        ax.grid(which='major', axis='x', linestyle='-')
        ax.set_axisbelow(True)
        # title of the plot
        ax.text(0, 1.12, 'Number of COVID-19 diagnosed in the world', transform=ax.transAxes, size=14, weight=600,
                ha='left')
        # author information
        ax.text(1, 0, 'Workshop II.HappyPlot :)', transform=ax.transAxes, size=10, ha='right',
                # style information of the author texts
                color='#777777', bbox=dict(facecolor='white', alpha=0.8, edgecolor='white'))
        # plot.box
        plt.box(False)

    # basic plot format
    fig, ax = plt.subplots(figsize=(15, 8))
    # animation function
    # use the frames of days(it already input in the World.csv file to do the frame range) to get each of the anime
    animator = animation.FuncAnimation(fig, drawchart, frames=range(1, 489))
    HTML(animator.to_jshtml())
    # save in video and it can control speed interactively
    animator.save('display.gif', writer='pillow', fps=30)
    plt.show()


def buttonPushedWorld():
    World()

def buttonPushedUS():
    US()

def buttonPushedChina():
    China()

def buttonCumulative():
    cumulative()

def addButtonCumulative(root, sideToPack):
    button = Button(root, text="Cumulative", width=16, command=buttonCumulative)
    button.pack(side=sideToPack)
    button.pack()

def addButtonUS(root, sideToPack):
    button = Button(root, text="US", width=16, command=buttonPushedUS)
    button.pack(side=sideToPack)
    button.pack()

def addButtonWorld(root, sideToPack):
    button = Button(root, text="World", width=16, command=buttonPushedWorld)
    button.pack(side=sideToPack)

def addButtonChina(root, sideToPack):
    button = Button(root, text="China", width=15, command=buttonPushedChina)
    button.pack(side=sideToPack)

global root
root = Tk()

root.title("Covid-19 situation checking system")

myText = StringVar() # Use a StringVar to create a changeable label
myText.set("Welcome to Covid-19 situation checking system!")
myLabel = Label(root, textvariable=myText)
myLabel.pack()

im = PhotoImage(file='yiqing.gif') # Create a PhotoImage widget

myCanvas = Canvas(root, width=650, height=450)
myCanvas = Label(root, image=im)
myCanvas.image = im
myCanvas.pack()

frametop = Frame(root)
frametop.pack(side=TOP)
framemiddle = Frame(root)
framemiddle.pack(side=TOP)
framebottom = Frame(root)
framebottom.pack(side=BOTTOM)

map = Label(frametop, text="Here's the global spread of the Covid-19!")
map.pack(side=TOP)  # Put the label into the window

addButtonCumulative(frametop, TOP)

map = Label(frametop, text="Select a map of the Covid-19 situation to view!")
map.pack(side=TOP)  # Put the label into the window

addButtonWorld(frametop, LEFT)
addButtonChina(frametop, LEFT)
addButtonUS(frametop, LEFT)


def buttonPushedChinaAll():
    ChinaAll()

def addButtonChinaAll(root, sideToPack):
    button = Button(root, text="ChinaAll", width=15, command=buttonPushedChinaAll)
    button.pack(side=sideToPack)

def buttonPushedChinaToday():
    ChinaToday()

def addButtonChinaToday(root, sideToPack):
    button = Button(root, text="ChinaToday", width=15, command=buttonPushedChinaToday)
    button.pack(side=sideToPack)

def buttonPushedComparing():
    Comparing()

def addButtonComparing(root, sideToPack):
    button = Button(root, text="Comparing", width=15, command=buttonPushedComparing)
    button.pack(side=sideToPack)

ChinaChart = Label(framemiddle, text="Or you can also check out the cumulative number of outbreaks in various provinces in China!")
ChinaChart.pack(side=TOP)  # Put the label into the window

addButtonChinaAll(framemiddle, TOP)
addButtonChinaToday(framemiddle, TOP)

Compare = Label(framebottom, text="Here is an animation comparing the number of new coronavirus diagnoses in each country.")
Compare.pack(side=TOP)  # Put the label into the window

addButtonComparing(framebottom, BOTTOM)

root.mainloop()  # Start the event loop