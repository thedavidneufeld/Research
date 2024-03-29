from shiny import ui
from shinywidgets import output_widget
import pypower.api as pyp

def get_cases():
    funcs = dir(pyp)
    cases = [c for c in funcs if (c.startswith("case") and (not c == "case9Q"))]
    return cases

cases = get_cases()

def nav_controls():
    return [
        ui.nav_panel(
            "Home",
            ui.input_radio_buttons("upload", "Load PYPOWER Case or Upload a MATPOWER Case?", ["Load", "Upload"], selected="Load", width="50%"),
            ui.navset_hidden(
                ui.nav_panel(None,
                    ui.input_select("input_case", "Select a case", cases, selected="case9"),
                    value="panel1"
                ),
                ui.nav_panel(None,
                    ui.input_file("upload_case", "Upload .m File", accept=[".m"]),
                    value="panel2"
                ),
                id = "case_select"
            ),
            ui.input_action_button("confirm_load", "Load"),
            ui.input_switch("run_pf", "Run PF"),
            ui.input_switch("opf", "OPF"),
        ),
        ui.nav_panel(
            "Buses",
            ui.card(
                output_widget("buses"),
                ui.input_action_button("add_bus", "Add Bus"),
                ui.input_action_button("bus_changes", "Confirm Changes")
            )
        ),
        ui.nav_panel(
            "Generators",
            ui.card(
                output_widget("gens"),
                ui.input_action_button("add_gen", "Add Generator"),
                ui.input_action_button("gen_changes", "Confirm Changes")
            )
        ),
        ui.nav_panel(
            "Branches",
            ui.card(
                output_widget("branches"),
                ui.input_action_button("add_branch", "Add Branch"),
                ui.input_action_button("branch_changes", "Confirm Changes")
            )
        ),
        ui.nav_panel(
            "Plot",
            ui.card(
                output_widget("plot")
            )
        ),
        ui.nav_panel(
            "Reslience",
            ui.card(
                ui.output_plot("graph_resilience")
            ),
            ui.card(
                output_widget("plot_resilience")
            )
        )
    ]

app_ui = ui.page_navbar(
    *nav_controls(),
    title = "Load Flow Visualization"
)