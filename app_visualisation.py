#!.venv\Scripts\python.exe

from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget
import visualisation_backend
import datetime
import ipyleaflet
import geopandas
import ipywidgets


adm_divs_choices = {
    "s": "Seleccioni'n una",
    "cat": "Catalunya",
    "p": "Províncies", 
    "v": "Vegueries",
    "c": "Comarques",
    "m": "Municipis"
}


app_ui = ui.page_fillable(
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_date_range(
                        id = "date_range",
                        label = "Interval de temps:",
                        format = "dd/mm/yyyy",
                        startview = "decade",
                        weekstart = 1,
                        language = 'ca',
                        separator = " a ",
                        width = "80%",
                        autoclose = True
                    ),
                    ui.input_select(
                        id = "adm_div_level",
                        label = "Divisió administrativa:",
                        choices = adm_divs_choices,
                        selected = "s",
                        width = "60%"
                    ),
                    ui.input_action_button(
                        id = "check_button",
                        label = "Comprovar"
                    ),
                    ui.output_ui(id = "render_adm_div_values"),
                    ui.input_action_button(
                        id = "filter_button",
                        label = "Filtrar",
                        disabled = True
                    ),
                    bg = "#f8f8f8",
                    width = 350,
                    title = "Filtres",
                    open = "always"
                ),
                ui.page_fillable(
                    ui.panel_title(
                        title = ui.HTML("<h1 style=\"text-align:center;\">Anàlisi i visualització interactiva d'incendis forestals</h1>"),
                        window_title = "Incendis Forestals"
                    ),
                    output_widget(id = "map_widget")
                )
            )
        )

def server(input, output, session):
    start_min, end_max = visualisation_backend.get_date_range()

    ui.update_date_range(
        id = "date_range",
        start = start_min,
        end = end_max,
        min = start_min,
        max = end_max
    )

    render_adm_div_values_flag = reactive.value(False)
    render_selected_adm_divs_flag = reactive.value(False)
    render_wildfires_flag = reactive.value(False)

    # When the user changes the value of the date_range and/or the adm_div_level
    @reactive.effect
    @reactive.event(input.date_range, input.adm_div_level)
    def _():
        render_adm_div_values_flag.set(False) # Removes the adm_div_values input
        ui.update_action_button(id = "filter_button", disabled = True) # Disables the Filter button
        render_selected_adm_divs_flag.set(False) # Removes the administrative divisions from the map
        render_wildfires_flag.set(False) # Removes the wildfires from the map

    # When the user clicks the check button
    @reactive.effect
    @reactive.event(input.check_button)
    def _():
        # If the values in the date range input are not valid dates
        if not(isinstance(input.date_range()[0], datetime.date)) and not(isinstance(input.date_range()[1], datetime.date)):
            ui.update_date_range(id = "date_range", start = start_min, end = end_max) # Replaces them for valid ones (the min and max values)
            ui.notification_show("Les dates NO eren vàlides", type = "error", duration = 5) # A red error box notifies the user of the invalid values

        elif not(isinstance(input.date_range()[0], datetime.date)): # start value
            ui.update_date_range(id = "date_range", start = start_min)
            ui.notification_show("La data inicial NO era vàlida", type = "error", duration = 5)
            
        elif not(isinstance(input.date_range()[1], datetime.date)): # end value
            ui.update_date_range(id = "date_range", end = end_max)
            ui.notification_show("La data final NO era vàlida", type = "error", duration = 5)

        else: # If the date range values are valid
            adm_divs_level = input.adm_div_level()

            if adm_divs_level == "cat":
                render_selected_adm_divs_flag.set(True)
                ui.update_action_button(id = "filter_button", disabled = False) # Enables the filter button
            elif adm_divs_level in ["p", "v", "c", "m"]:
                # If adm_div_values has already been rendered, removes ("empties") it
                if render_adm_div_values_flag.get():
                    render_adm_div_values_flag.set(False)
                
                render_adm_div_values_flag.set(True)

    @render.ui
    def render_adm_div_values():
        if render_adm_div_values_flag.get():
            adm_divs_level = input.adm_div_level()

            label = adm_divs_choices[adm_divs_level] + ":"

            choices = visualisation_backend.get_adm_div_names(adm_divs_level, input.date_range())

            return ui.input_selectize(
                    id = "adm_div_values",
                    label = label,
                    choices = choices,
                    multiple = True,
                    options = {"maxItems": str(len(choices) - 1)}
                )
        
    @reactive.effect
    @reactive.event(input.adm_div_values)
    def _():
        render_wildfires_flag.set(False)

        if len(input.adm_div_values()) > 0:
            render_selected_adm_divs_flag.set(True)
            ui.update_action_button(id = "filter_button", disabled = False)
        else:
            render_selected_adm_divs_flag.set(False)
            ui.update_action_button(id = "filter_button", disabled = True)

    @reactive.effect
    @reactive.event(input.filter_button)
    def _():
        render_wildfires_flag.set(True)

    @render_widget
    def map_widget():
        # BASEMAP
        icgc_orto_basemap = ipyleaflet.TileLayer(
            name = "ICGC Orto",
            base = True,
            url = 'https://geoserveis.icgc.cat/servei/catalunya/mapa-base/wmts/orto/MON3857NW/{z}/{x}/{y}.png',
            max_zoom = 20,
            attribution = 'ICGC Orto (Catalunya): ©ICGC | ICGC Orto (Resta del món): ©Esri (Esri, DigitalGlobe, USDA, USGS, GeoEye, Getmapping, AeroGRID, IGN, IGP, UPR-EGP i the GIS community)'
        )

        layer_list = [icgc_orto_basemap]

        # ADMINISTRATIVE DIVISION
        adm_div_GDF = geopandas.GeoDataFrame()

        if render_selected_adm_divs_flag.get():
            if render_adm_div_values_flag.get(): # p, v, c, m
                adm_div_GDF = visualisation_backend.get_adm_div_geoms(input.adm_div_level(), input.adm_div_values())
            else: # cat
                adm_div_GDF = visualisation_backend.get_adm_div_geoms(input.adm_div_level())

            adm_div_GD = ipyleaflet.GeoData(
                    geo_dataframe = adm_div_GDF,
                    name = adm_divs_choices[input.adm_div_level()]
                )

            layer_list.append(adm_div_GD)

        # WILDFIRE INFO BOX
        info_box = ipywidgets.HTML(value = "<b>Cliqui un incendi</b>", layout = ipywidgets.Layout(margin = "10px 10px 10px 10px"))

        def update_info_box(feature, **kwargs):
            info_box.value = """
                            <b>Municipi</b>: {0} <br>
                            <b>Data</b>: {1}
                            """.format(feature["properties"]["municipality"], feature["properties"]["wildfire_date"])

        # WILDFIRES
        if render_wildfires_flag.get():
            if render_adm_div_values_flag.get(): # p, v, c, m
                wildfires_GDF = visualisation_backend.get_wildfires(input.date_range(), input.adm_div_level(), input.adm_div_values())
            else: # cat
                wildfires_GDF = visualisation_backend.get_wildfires(input.date_range(), input.adm_div_level())

            wildfires_GD = ipyleaflet.GeoData(
                    geo_dataframe = wildfires_GDF,
                    name = 'Incendis Forestals',
                    style = {"color": "orange"},
                    hover_style = {"fillColor": "red", "fillOpacity": 0.5}
                )

            wildfires_GD.on_click(update_info_box)

            layer_list.append(wildfires_GD)

        # MAP
        center = [41.8, 1.7]
        zoom = 7

        if not(adm_div_GDF.empty):
            center = visualisation_backend.get_center(adm_div_GDF)

            if input.adm_div_level() != "cat" and len(input.adm_div_values()) == 1:
                match input.adm_div_level():
                        case "p":
                            zoom = 8
                        case "v":
                            zoom = 8
                        case "c":
                            zoom = 9
                        case "m":
                            zoom = 10

        map = ipyleaflet.Map(
                layers = layer_list,
                center = center,
                zoom = zoom,
                scroll_wheel_zoom = True,
                controls = [ipyleaflet.LayersControl(position = 'topright', collapsed = False), ipyleaflet.WidgetControl(widget = info_box, position = "bottomleft")],
                layout = ipywidgets.Layout(height = "60%")
            )
           
        return map
        

######################
# Shiny app instance #
######################

app = App(app_ui, server)