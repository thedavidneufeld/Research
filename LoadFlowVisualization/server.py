from shiny import render, ui, reactive
from shiny.types import FileInfo
from shinywidgets import render_widget, render_plotly
import numpy as np
import matplotlib.pyplot as plt
from matpowercaseframes import CaseFrames
import pypower.api as pyp
from pandapower.plotting.plotly import simple_plotly, pf_res_plotly
from pandapower.converter import from_ppc
import pandapower.networks as pn
import ipysheet
from ipysheet import to_array
import ipywidgets
from ui import *

def sheetFromDF(df):
    sheet = ipysheet.from_dataframe(df)
    return sheet

def server(input, output, session):

    case_file = reactive.value(pyp.case9())
    case_sheet_bus = reactive.value()
    case_sheet_gen = reactive.value()
    case_sheet_branch = reactive.value()

    @reactive.effect
    @reactive.event(input.upload, ignore_none=False)
    def update_home():
        if input.upload() == "Upload":
            ui.update_navs("case_select", selected="panel2")
        else:
            ui.update_navs("case_select", selected="panel1")

    @reactive.effect    
    @reactive.event(input.confirm_load, ignore_none=False)
    def load_matpower_case():
        if input.upload() == "Upload":
            file: list[FileInfo] | None = input.upload_case()
            if file is None:
                return
            new_case = CaseFrames(file[0]["datapath"]).to_dict()
            new_case["bus"] = np.array(new_case["bus"])
            new_case["gen"] = np.array(new_case["gen"])
            new_case["branch"] = np.array(new_case["branch"])
            if "gencost" in new_case.keys():
                new_case["gencost"] = np.array(new_case["gencost"])
            case_file.set(new_case)
        
    @reactive.effect
    @reactive.event(input.confirm_load, ignore_none=False)
    def load_pypower_case():
        if input.upload() == "Load":
            lcls = locals()
            exec(f"new_case = pyp.{input.input_case()}()", globals(), lcls)
            case_file.set(lcls["new_case"])
    
    @reactive.calc
    def get_case_frame():
        return CaseFrames(case_file.get())
    
    @reactive.calc
    def run_pf():
        if input.run_pf():
            case_pf = pyp.runpf(case_file.get())
            return CaseFrames(case_pf)

    @render_widget
    @reactive.event(input.confirm_load, input.run_pf,ignore_none=False)
    def buses():
        if input.run_pf():
            return run_pf().bus
        sheet = sheetFromDF(get_case_frame().bus)
        sheet.layout = {'max_height' : '90%', 'overflow_y' : 'auto'}
        case_sheet_bus.set(sheet)
        return ipywidgets.VBox([case_sheet_bus.get()])
    
    @reactive.effect
    @reactive.event(input.bus_changes)
    def update_buses():
        updated_bus = to_array(case_sheet_bus.get())
        updated_case = case_file.get()
        updated_case["bus"] = updated_bus
        case_file.set(updated_case)
    
    @render_widget
    @reactive.event(input.confirm_load, ignore_none=False)
    def gens():
        sheet = sheetFromDF(get_case_frame().gen)
        sheet.layout = {'max_height' : '90%', 'overflow_y' : 'auto'}
        case_sheet_gen.set(sheet)
        return ipywidgets.VBox([case_sheet_gen.get()])
    
    @reactive.effect
    @reactive.event(input.gen_changes)
    def update_gens():
        updated_gen = to_array(case_sheet_gen.get())
        updated_case = case_file.get()
        updated_case["gen"] = updated_gen
        case_file.set(updated_case)
    
    @render_widget
    @reactive.event(input.confirm_load, ignore_none=False)
    def branches():
        sheet = sheetFromDF(get_case_frame().branch)
        sheet.layout = {'max_height' : '90%', 'overflow_y' : 'auto'}
        case_sheet_branch.set(sheet)
        return ipywidgets.VBox([case_sheet_branch.get()])
    
    @reactive.effect
    @reactive.event(input.branch_changes)
    def update_branches():
        updated_branch = to_array(case_sheet_branch.get())
        updated_case = case_file.get()
        updated_case["branch"] = updated_branch
        case_file.set(updated_case)
    
    @render_plotly
    @reactive.event(input.confirm_load, input.opf, input.bus_changes, input.gen_changes, input.branch_changes, ignore_none=False)
    def plot():
        net = from_ppc(case_file.get())
        return simple_plotly(net, filename=".1.html", auto_open=False)
    
    @render_plotly
    @reactive.event(input.confirm_load, input.opf, ignore_none=False)
    def plot_resilience():
        net = pn.case30()
        return pf_res_plotly(net, filename=".2.html", auto_open=False)
    
    @render.plot
    @reactive.event(input.x, input.opf, ignore_none=False)
    def graph_resilience():
        x = np.array([i for i in range(25)])
        y = np.array([np.random.rand()*5 for i in range(25)])
        plt.xlabel("Time")
        plt.ylabel("Resilience")
        plt.plot(x, y)