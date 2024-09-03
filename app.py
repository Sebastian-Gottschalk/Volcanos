## The Website done with this streamlit code can be found under
## https://constructor-sebastian-volcano.streamlit.app/

import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

@st.cache_data   
def load_data(path):
    df = pd.read_csv(path)
    return df

@st.cache_data   
def load_json(path):
    df = json.load(open(path))
    return df


volcano_df = load_data('./data/volcano_ds_pop.csv')
volcano_json = load_json('./data/countries.geojson')

def plot_nr_of_volcanos_by_status(df, status, volcano_json, colorscheme, scale):
    if scale == 'cont':
        fig = px.choropleth_mapbox(
            df,
            geojson = volcano_json,
            featureidkey = 'properties.ISO_A3',
            locations = 'ISO', 
            color = status,
            color_continuous_scale=colorscheme,
            mapbox_style="carto-positron",
            zoom=1, 
            center = {"lat": 40 , "lon": 40},
            opacity=0.5,
            hover_data = {'ISO': False, status: True},
            hover_name = 'Country'
        )
    else:
        fig = px.choropleth_mapbox(
            df,
            geojson = volcano_json,
            featureidkey = 'properties.ISO_A3',
            locations = 'ISO', 
            color = status,
            color_discrete_map={'Above Threshhold' : 'green', 'Below Threshhold': 'red'},
            mapbox_style="carto-positron",
            zoom=1, 
            center = {"lat": 40 , "lon": 40},
            opacity=0.5,
            hover_data = {'ISO': False, status: True},
            hover_name = 'Country'
        )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    return fig

ISO_dict = {}
ISO_rev_dict = {}
for i in range(len(volcano_json['features'])):
    prop = volcano_json['features'][i]['properties']
    name = prop['ADMIN']
    Iso = prop['ISO_A3']
    ISO_dict[name] = Iso
    ISO_rev_dict[Iso] = name

ISO_dict['United States'] = 'USA'

volcano_df['ISO'] = volcano_df['Country'].map(ISO_dict)
volcano_df[volcano_df['ISO'].isna()]['Country'].unique()

volcano_df_dropped = volcano_df.dropna()
nr_of_volcanos = volcano_df_dropped.groupby('ISO')['Number'].count()
nr_of_volcanos = nr_of_volcanos.reset_index()
nr_of_volcanos['Country'] = nr_of_volcanos['ISO'].map(ISO_rev_dict)
for key in ISO_dict:
    if ISO_dict[key] not in list(nr_of_volcanos['ISO']):
        nr_of_volcanos.loc[len(nr_of_volcanos)] = [ISO_dict[key],0,key]
nr_of_volcanos['Population'] = nr_of_volcanos['Number']
for i in range(len(nr_of_volcanos)):
    if nr_of_volcanos['Population'].iloc[i] == 0:
        nr_of_volcanos.loc[i,'Population'] = 1
    else:
        nr_of_volcanos.loc[i,'Population'] = volcano_df[volcano_df['ISO'] == nr_of_volcanos['ISO'].iloc[i]]['Population (2020)'].mean()
nr_of_volcanos['Volcanos per Population (per Million)'] = nr_of_volcanos['Number'] / nr_of_volcanos['Population']*1000000

for status in volcano_df.Status.unique():
    ts = volcano_df[volcano_df['Status'] == status].groupby('ISO')['Number'].count().reset_index()
    ts.rename(columns = {'Number' : status}, inplace = True)
    nr_of_volcanos = nr_of_volcanos.merge(ts, how = 'left')
    nr_of_volcanos.fillna(0, inplace = True)
    nr_of_volcanos[str(status)] = nr_of_volcanos[str(status)].astype(int)
    nr_of_volcanos[str(status)+' pC'] = nr_of_volcanos[str(status)]/nr_of_volcanos['Population']*1000000
nr_of_volcanos.rename(columns = {'Number' : 'Total number of volcanos'}, inplace = True)

customdata = list(nr_of_volcanos.columns)
customdata.remove('ISO')
customdata.remove('Population')
customdata.remove('Volcanos per Population (per Million)')
customdata = [data for data in customdata if not data.endswith('pC')]
customdata.insert(0,customdata.pop(1))

hover_dict = {'ISO' : False}
for value in customdata:
    if value == 'Country':
        hover_dict[value] = False
    else:
        hover_dict[value] = True


volcano_df.rename(columns={'Latitude' : 'lat', 'Longitude' : 'lon'}, inplace= True)

###
### Sidebuilding starts here
###

st.title('Volcano Distribution around the world')

show_df = st.sidebar.checkbox('Show source DataFrame')

if show_df:
    st.dataframe(volcano_df)
    st.dataframe(nr_of_volcanos)

left_column,right_column = st.columns(2)

status_list = ['All'] + customdata[2:]
status = left_column.selectbox('Select the status',status_list)

color_list = ['Mark everything above a threshhold']+px.colors.named_colorscales()

threshhold_list = []
for i in range(1000):
    threshhold_list.append(i/1000)

show_all_volcanos = right_column.checkbox('Show Volcanos individually')

if show_all_volcanos:
    if status == 'All':
        st.map(volcano_df)  
    else:
        st.map(volcano_df[volcano_df['Status'] == status])
else:
    colorscheme = left_column.selectbox('Select the color scheme',color_list)  
    data_shown = right_column.checkbox('Show Volcanos per million capita')
    if data_shown:
        display_value = 'Volcanos per Population (per Million)'
    else:
        display_value = 'Total number of volcanos'
        
    if status == 'All':
        if colorscheme == 'Mark everything above a threshhold':
            threshhold = right_column.select_slider("Select a threshhold (the countries with a proportion to the maximum higher than the threshhold will be displayed)", threshhold_list)
            max_volcanos = max(nr_of_volcanos[display_value])
            nr_of_volcanos= nr_of_volcanos.assign(Threshhold = lambda row:row[display_value]/max_volcanos> threshhold)
            nr_of_volcanos['Threshhold'] = nr_of_volcanos['Threshhold'].map({True: 'Above Threshhold', False : 'Below Threshhold'})
            fig1 = px.choropleth_mapbox(
                nr_of_volcanos,
                geojson = volcano_json,
                featureidkey = 'properties.ISO_A3',
                custom_data = customdata,
                locations = 'ISO',
                color = 'Threshhold',
                color_discrete_map={'Above Threshhold' : 'green', 'Below Threshhold': 'red'},
                mapbox_style="carto-positron",
                zoom=1, 
                center = {"lat": 40 , "lon": 40},
                opacity=0.5,
                hover_data = hover_dict,
                hover_name = 'Country',
            )
        else:
            fig1 = px.choropleth_mapbox(
                nr_of_volcanos,
                geojson = volcano_json,
                featureidkey = 'properties.ISO_A3',
                custom_data = customdata,
                locations = 'ISO', 
                color = display_value,
                color_continuous_scale=colorscheme,
                mapbox_style="carto-positron",
                zoom=1, 
                center = {"lat": 40 , "lon": 40},
                opacity=0.5,
                hover_data = hover_dict,
                hover_name = 'Country',
            )


        fig1.update_layout(
            title = {'text' : 'Test', 'font' : {'size' : 20}},
            margin={"r":0,"t":0,"l":0,"b":0}
        )

    else:
        scale = 'cont'
        if data_shown:
            status = status + ' pC'
            if colorscheme == 'Mark everything above a threshhold':
                scale = 'disc'
                threshhold = right_column.select_slider("Select a threshhold (the countries with a proportion to the maximum higher than the threshhold will be displayed)", threshhold_list)
                max_volcanos = max(nr_of_volcanos[str(status)])
                nr_of_volcanos= nr_of_volcanos.assign(Threshhold = lambda row:row[str(status)]/max_volcanos> threshhold)
                nr_of_volcanos['Threshhold'] = nr_of_volcanos['Threshhold'].map({True: 'Above Threshhold', False : 'Below Threshhold'})
                status = 'Threshhold'
            fig1 = plot_nr_of_volcanos_by_status(nr_of_volcanos, status, volcano_json, colorscheme,scale)
        else:
            if colorscheme == 'Mark everything above a threshhold':
                scale = 'disc'
                threshhold = right_column.select_slider("Select a threshhold (the countries with a proportion to the maximum higher than the threshhold will be displayed)", threshhold_list)
                max_volcanos = max(nr_of_volcanos[str(status)])
                nr_of_volcanos= nr_of_volcanos.assign(Threshhold = lambda row:row[str(status)]/max_volcanos> threshhold)
                nr_of_volcanos['Threshhold'] = nr_of_volcanos['Threshhold'].map({True: 'Above Threshhold', False : 'Below Threshhold'})
                status = 'Threshhold'
            fig1 = plot_nr_of_volcanos_by_status(nr_of_volcanos, status, volcano_json, colorscheme,scale)

    st.plotly_chart(fig1)
