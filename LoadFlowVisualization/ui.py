from shiny import ui
from shinywidgets import output_widget
import pypower.api as pyp


# function to obtain PYPOWER case names
def get_cases():
    funcs = dir(pyp)
    cases = [c for c in funcs if (c.startswith("case") and (not c == "case9Q"))]
    return cases


# load PYPOWER case names
cases = get_cases()


# main UI functionality
def nav_controls():
    return [
        ui.nav_panel(
            "Home",
            # choose whether to load or upload a file
            ui.input_radio_buttons(
                "upload",
                "Load PYPOWER Case or Upload a MATPOWER Case?",
                ["Load", "Upload"],
                selected="Load",
                width="50%",
            ),
            # change selection interface based on selection
            ui.navset_hidden(
                ui.nav_panel(
                    None,
                    ui.input_select(
                        "input_case", "Select a case", cases, selected="case9"
                    ),
                    value="panel1",
                ),
                ui.nav_panel(
                    None,
                    ui.input_file("upload_case", "Upload .m File", accept=[".m"]),
                    value="panel2",
                ),
                id="case_select",
            ),
            # confirm the load/upload of a file
            ui.input_action_button("confirm_load", "Load"),
        ),
        ui.nav_panel(
            "Data",
            # display bus, gen, branch, and gencost data
            ui.navset_card_tab(
                ui.nav_panel(
                    "Bus",
                    output_widget("buses"),
                    ui.input_action_button("add_bus", "Add Bus"),
                    ui.input_action_button("remove_bus", "Remove Bus"),
                ),
                ui.nav_panel(
                    "Generator",
                    output_widget("gens"),
                    ui.input_action_button("add_gen", "Add Generator"),
                    ui.input_action_button("remove_gen", "Remove Gen"),
                ),
                ui.nav_panel(
                    "Branch",
                    output_widget("branches"),
                    ui.input_action_button("add_branch", "Add Branch"),
                    ui.input_action_button("remove_branch", "Remove Branch"),
                ),
                ui.nav_panel(
                    "Gencost",
                    output_widget("gencosts"),
                    ui.input_action_button("add_gencost", "Add Gencost"),
                    ui.input_action_button("remove_gencost", "Remove Gencost"),
                ),
                # when done modifying data, confirm changes to apply them to
                # case_file
                footer=ui.input_action_button("confirm_changes", "Confirm Changes"),
            ),
            # plot case_file data
            ui.card(output_widget("plot")),
        ),
        ui.nav_panel(
            "PF",
            # display bus, gen, and branch data after a power flow has been
            # performed
            ui.navset_card_tab(
                ui.nav_panel("Bus", ui.output_data_frame("buses_pf")),
                ui.nav_panel("Generator", ui.output_data_frame("gens_pf")),
                ui.nav_panel("Branch", ui.output_data_frame("branches_pf")),
            ),
            # plot case_file data after a power flow has been performed
            ui.card(output_widget("pf_plot")),
        ),
        ui.nav_panel(
            "OPF",
            # display bus, gen, branch data after an optimal power
            # flow has been performed
            ui.navset_card_tab(
                ui.nav_panel("Bus", ui.output_data_frame("buses_opf")),
                ui.nav_panel("Generator", ui.output_data_frame("gens_opf")),
                ui.nav_panel("Branch", ui.output_data_frame("branches_opf")),
            ),
        ),
        ui.nav_panel(
            "Reslience",
            # display table of resilience values
            ui.card(ui.output_data_frame("graph_resilience")),
            # plot voltage of system based on selected time period
            ui.card(output_widget("plot_resilience")),
        ),
    ]


# main UI
app_ui = ui.page_navbar(*nav_controls(), title="Load Flow Visualization")
