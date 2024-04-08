from shiny import render, ui, reactive, req
from shiny.types import FileInfo
from shinywidgets import render_widget, render_plotly
from copy import deepcopy
import random
import numpy as np
import pandas as pd
from matpowercaseframes import CaseFrames
import pypower.api as pyp
from pandapower import runpp
from pandapower.plotting.plotly import simple_plotly, vlevel_plotly, pf_res_plotly
from pandapower.converter import from_ppc
import ipysheet
from ipysheet import to_array
import ipywidgets
from ui import *


# function to convert a dataframe to an ipysheet
def sheetFromDF(df):
    sheet = ipysheet.from_dataframe(df)
    return sheet


# main server
def server(input, output, session):

    # store current case file; default is case9
    case_file = reactive.value(pyp.case9())
    # ipysheets containing bus, gen, and branch data
    case_sheet_bus = reactive.value()
    case_sheet_gen = reactive.value()
    case_sheet_branch = reactive.value()
    case_sheet_gencost = reactive.value()
    # table containing resilience data
    resilience_table = reactive.value()

    # upon selecting whether to load or upload a file, change UI home accordingly
    @reactive.effect
    @reactive.event(input.upload, ignore_none=False)
    def update_home():
        if input.upload() == "Upload":
            ui.update_navs("case_select", selected="panel2")
        else:
            ui.update_navs("case_select", selected="panel1")

    # load MATPOWER case file
    @reactive.effect
    @reactive.event(input.confirm_load, ignore_none=False)
    def load_matpower_case():
        # only proceed if upload has been selected
        if input.upload() == "Upload":
            file: list[FileInfo] | None = input.upload_case()
            # if no file exists, do not update case_file
            if file is None:
                return
            # convert new case to a dict
            new_case = CaseFrames(file[0]["datapath"]).to_dict()
            # convert bus, gen, branch, and gencost lists to arrays
            new_case["bus"] = np.array(new_case["bus"])
            new_case["gen"] = np.array(new_case["gen"])
            new_case["branch"] = np.array(new_case["branch"])
            new_case["gencost"] = np.array(new_case["gencost"])
            # update case_file with new MATPOWER case
            case_file.set(new_case)

    # load PYPOWER case
    @reactive.effect
    @reactive.event(input.confirm_load, ignore_none=False)
    def load_pypower_case():
        # only proceed if load has been selected
        if input.upload() == "Load":
            lcls = locals()
            exec(f"new_case = pyp.{input.input_case()}()", globals(), lcls)
            # update case_file with PYPOWER case
            case_file.set(lcls["new_case"])

    # return case_file as a set of dataframes
    @reactive.calc
    def get_case_frame():
        return CaseFrames(case_file.get())

    # run a power flow on case_file and return as a set of dataframes
    @reactive.calc
    @reactive.event(input.confirm_changes, input.confirm_load, ignore_none=False)
    def run_pf():
        case_pf = pyp.runpf(case_file.get())
        return CaseFrames(case_pf[0])

    # run an optimal power flow on case_file and return as a set of dataframes
    @reactive.calc
    @reactive.event(input.confirm_changes, input.confirm_load, ignore_none=False)
    def run_opf():
        case_opf = pyp.runopf(case_file.get())
        return CaseFrames(case_opf)

    # load bus, gen, branch, and gencost sheets with data from case_file
    # dataframes
    @reactive.effect
    @reactive.event(input.confirm_load, ignore_none=False)
    def load_sheets():
        sheet_bus = sheetFromDF(get_case_frame().bus)
        sheet_bus.layout = {"max_height": "90%", "overflow_y": "auto"}
        case_sheet_bus.set(sheet_bus)
        sheet_gen = sheetFromDF(get_case_frame().gen)
        sheet_gen.layout = {"max_height": "90%", "overflow_y": "auto"}
        case_sheet_gen.set(sheet_gen)
        sheet_branch = sheetFromDF(get_case_frame().branch)
        sheet_branch.layout = {"max_height": "90%", "overflow_y": "auto"}
        case_sheet_branch.set(sheet_branch)
        sheet_gencost = sheetFromDF(get_case_frame().gencost)
        sheet_gencost.layout = {"max_height": "90%", "overflow_y": "auto"}
        case_sheet_gencost.set(sheet_gencost)

    # if changes to bus, gen, branch, or gencost data has been confirmed, then
    # update the case_file accordingly
    @reactive.effect
    @reactive.event(input.confirm_changes)
    def update_data():
        updated_bus = to_array(case_sheet_bus.get())
        updated_gen = to_array(case_sheet_gen.get())
        updated_branch = to_array(case_sheet_branch.get())
        updated_gencost = to_array(case_sheet_gencost.get())
        updated_case = case_file.get()
        updated_case["bus"] = updated_bus
        updated_case["gen"] = updated_gen
        updated_case["branch"] = updated_branch
        updated_case["gencost"] = updated_gencost

    # return bus case sheet
    @render_widget
    def buses():
        return ipywidgets.VBox([case_sheet_bus.get()])

    # add a new row to bus case sheet
    @reactive.effect
    @reactive.event(input.add_bus)
    def add_bus():
        bus_df = ipysheet.to_dataframe(case_sheet_bus.get())
        bus_df.loc[len(bus_df.index) + 1] = [0 for i in range(bus_df.shape[1])]
        bus_sheet = ipysheet.from_dataframe(bus_df)
        case_sheet_bus.set(ipysheet.sheet(bus_sheet))

    # remove row from bus case sheet
    @reactive.effect
    @reactive.event(input.remove_bus)
    def remove_bus():
        bus_df = ipysheet.to_dataframe(case_sheet_bus.get())
        if len(bus_df.index) > 1:
            bus_df = bus_df.drop(bus_df.index[-1])
            bus_sheet = ipysheet.from_dataframe(bus_df)
            case_sheet_bus.set(ipysheet.sheet(bus_sheet))

    # return bus power flow results
    @render.data_frame
    def buses_pf():
        return run_pf().bus

    # return bus optimal power flow results
    @render.data_frame
    def buses_opf():
        return run_opf().bus

    # return gen case sheet
    @render_widget
    def gens():
        return ipywidgets.VBox([case_sheet_gen.get()])

    # add a new row to gen case sheet
    @reactive.effect
    @reactive.event(input.add_gen)
    def add_gen():
        gen_df = ipysheet.to_dataframe(case_sheet_gen.get())
        gen_df.loc[len(gen_df.index) + 1] = [0 for i in range(gen_df.shape[1])]
        gen_sheet = ipysheet.from_dataframe(gen_df)
        case_sheet_gen.set(ipysheet.sheet(gen_sheet))

    # remove row from branch case sheet
    @reactive.effect
    @reactive.event(input.remove_gen)
    def remove_gen():
        gen_df = ipysheet.to_dataframe(case_sheet_gen.get())
        if len(gen_df.index) > 1:
            gen_df = gen_df.drop(gen_df.index[-1])
            gen_sheet = ipysheet.from_dataframe(gen_df)
            case_sheet_gen.set(ipysheet.sheet(gen_sheet))

    # return gen power flow results
    @render.data_frame
    def gens_pf():
        return run_pf().gen

    # return gen optimal power flow results
    @render.data_frame
    def gens_opf():
        return run_opf().gen

    # return branch case sheet
    @render_widget
    def branches():
        return ipywidgets.VBox([case_sheet_branch.get()])

    # add a new row to branch case sheet
    @reactive.effect
    @reactive.event(input.add_branch)
    def add_branch():
        branch_df = ipysheet.to_dataframe(case_sheet_branch.get())
        branch_df.loc[len(branch_df.index) + 1] = [0 for i in range(branch_df.shape[1])]
        branch_sheet = ipysheet.from_dataframe(branch_df)
        case_sheet_branch.set(ipysheet.sheet(branch_sheet))

    # remove row from branch case sheet
    @reactive.effect
    @reactive.event(input.remove_branch)
    def remove_branch():
        branch_df = ipysheet.to_dataframe(case_sheet_branch.get())
        if len(branch_df.index) > 1:
            branch_df = branch_df.drop(branch_df.index[-1])
            branch_sheet = ipysheet.from_dataframe(branch_df)
            case_sheet_branch.set(ipysheet.sheet(branch_sheet))

    # return branch power flow results
    @render.data_frame
    def branches_pf():
        return run_pf().branch

    # return branch optimal power flow results
    @render.data_frame
    def branches_opf():
        return run_opf().branch

    # return gencost case sheet
    @render_widget
    def gencosts():
        return ipywidgets.VBox([case_sheet_gencost.get()])

    # add a new row to gencost case sheet
    @reactive.effect
    @reactive.event(input.add_gencost)
    def add_gencost():
        gencost_df = ipysheet.to_dataframe(case_sheet_gencost.get())
        gencost_df.loc[len(gencost_df.index) + 1] = [
            0 for i in range(gencost_df.shape[1])
        ]
        gencost_sheet = ipysheet.from_dataframe(gencost_df)
        case_sheet_gencost.set(ipysheet.sheet(gencost_sheet))

    # remove row from gencost case sheet
    @reactive.effect
    @reactive.event(input.remove_gencost)
    def remove_gencost():
        gencost_df = ipysheet.to_dataframe(case_sheet_gencost.get())
        if len(gencost_df.index) > 1:
            gencost_df = gencost_df.drop(gencost_df.index[-1])
            gencost_sheet = ipysheet.from_dataframe(gencost_df)
            case_sheet_gencost.set(ipysheet.sheet(gencost_sheet))

    # return plot of case_file data
    @render_plotly
    @reactive.event(input.confirm_load, input.confirm_changes, ignore_none=False)
    def plot():
        net = from_ppc(case_file.get())
        return simple_plotly(net, filename=".1.html", auto_open=False)

    # return plot case_file after a power flow has been run
    @render_plotly
    @reactive.event(input.confirm_load, input.confirm_changes, ignore_none=False)
    def pf_plot():
        net = from_ppc(case_file.get())
        net_pf = runpp(net)
        return pf_res_plotly(net, filename=".3.html", auto_open=False)

    # plot voltage levels based on OPF time period
    # note that this is simulated; no OPF is performed, and voltages returned are
    # either the defaults
    # for the loaded case if "resilient" or randomized voltages if not
    @render_plotly
    @reactive.event(
        input.confirm_load,
        input.confirm_changes,
        input.graph_resilience_selected_rows,
        ignore_none=False,
    )
    def plot_resilience():
        # if no rows are selected, then stop
        req(input.graph_resilience_selected_rows())
        # obtain a deepcopy of case_file so that randomized voltages do not
        # affect the case_file
        plot_case = deepcopy(case_file.get())
        # obtain index for resilience table
        idx = input.graph_resilience_selected_rows()
        # get resilience value for selected row (true/false)
        resilient = resilience_table.get().iloc[idx[0]]["Resilient?"]
        # if resilience is false, then randomize bus voltages
        # otherwise, leave voltages
        if not resilient:
            for i in range(plot_case["bus"].shape[0]):
                plot_case["bus"][i, 9] = random.randint(100, 500)
        net = from_ppc(plot_case)
        # return voltage plot of plot_case
        return vlevel_plotly(net, filename=".2.html", auto_open=False)

    # populate resilience table and return as DataGrid
    # note that this is simulated; resilience values are assigned to time period
    # 1 thorugh 24 randomly (true/false)
    @render.data_frame
    @reactive.event(input.confirm_load, input.confirm_changes, ignore_none=False)
    def graph_resilience():
        # time periods 1 thorugh 24
        x = np.array([i for i in range(1, 25)])
        # random true/false resilience values
        y = np.array([int(np.random.rand() * 1000) % 2 for i in range(24)])
        # laod x and y into a dictionary and then set to resilience table
        # dataframe
        data = {"Time": x, "Resilient?": [bool(i) for i in y]}
        resilience_table.set(pd.DataFrame(data))
        # return as DataGrid where a single row can be selected
        return render.DataGrid(resilience_table.get(), row_selection_mode="single")
