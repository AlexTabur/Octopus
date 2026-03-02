import dearpygui.dearpygui as dpg

dpg.create_context()
width = 200
import numpy as np

_pltkwargs = dict(pos=(10, 20), height=400, width=400, query=False)
with dpg.window(label="Example Window"):
    with dpg.texture_registry(show=False):
        data = np.ones((2, 2, 4), dtype=np.float32)  # RGBA white
        dpg.add_static_texture(2, 2, data.flatten(), tag="camera_1")
    with dpg.plot(tag="slave plot", no_frame=True, **_pltkwargs):
        dpg.bind_colormap(dpg.last_item(), dpg.mvPlotColormap_Viridis)
        dpg.add_plot_axis(dpg.mvXAxis, tag="slave xax")
        with dpg.plot_axis(dpg.mvYAxis, tag="slave yax"):
            dpg.add_image_series("camera_1", (0, 0), (width, width), parent="bruh_")
    with dpg.plot(tag="master plot", **_pltkwargs):
        # Add image series first
        dpg.add_drag_line(label="Drag Line", default_value=0.5, color=[255, 0, 0, 255])
        dpg.add_plot_axis(dpg.mvXAxis, tag="master xax")
        dpg.add_plot_axis(dpg.mvYAxis, tag="master yax")

dpg.set_axis_limits("master xax", 0,width)
dpg.set_axis_limits("master yax", 0,width)
def _loosen_axes_lims():
    dpg.set_axis_limits_auto("master xax")
    dpg.set_axis_limits_auto("master yax")
dpg.set_frame_callback(1, _loosen_axes_lims) # need this, or else the resulting plot has fixed lims without any interactivity

with dpg.theme() as masterplot_theme:
    with dpg.theme_component(dpg.mvPlot):
        dpg.add_theme_color(dpg.mvPlotCol_PlotBg, (0,0,0,0), category=dpg.mvThemeCat_Plots)
        dpg.add_theme_color(dpg.mvPlotCol_FrameBg, (0,0,0,0), category=dpg.mvThemeCat_Plots)
dpg.bind_item_theme("master plot", masterplot_theme)
def sync_axes(_,__, user_data):
    """
    obtain master plot's axes range, using which we set the axes range of slave plot
    """
    xax_master, yax_master, xax_slave, yax_slave = user_data
    params_master = xmin_mst, xmax_mst, ymin_mst, ymax_mst = *dpg.get_axis_limits(xax_master), *dpg.get_axis_limits(yax_master)
    params_slave = *dpg.get_axis_limits(xax_slave), *dpg.get_axis_limits(yax_slave)
    if not params_master==params_slave:
        dpg.set_axis_limits(xax_slave, xmin_mst, xmax_mst)
        dpg.set_axis_limits(yax_slave, ymin_mst, ymax_mst)
with dpg.item_handler_registry(tag= "master-slave sync hreg"):
    dpg.add_item_visible_handler(callback = sync_axes, user_data = ("master xax", "master yax", "slave xax", "slave yax"))
dpg.bind_item_handler_registry("master plot", "master-slave sync hreg")


dpg.create_viewport(title='Custom Title', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
