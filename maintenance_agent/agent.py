from google.adk.agents import Agent, ParallelAgent, SequentialAgent

# Import the tools
from .tools import fleet_query, recall_query, health_query
from .tools import health_bulk_query, part_query, vehicle_appointment_query
from .tools import vehicle_rental_query, part_delivery_time_query, part_order_query
from .tools import create_part_order, create_appointment, vehicle_query, vehicle_list
from .tools import notify

MODEL="gemini-2.0-flash"

# Agents

# Recall sub-agent
recall_agent = Agent(
    name="recall_agent",
    model=MODEL,
    description="Provides car recall information.",
    instruction="""You are a specialized recall assistance agent.
    You can retrieve car recall information based on make, model and model year.
    You can provide basic analytics on the list of vehicles in the fleet.
    Steps:
    - Do not greet the user.
    - Query the database for the list of vehicles and gather all make, model and model year combinations.
    - Use the tool `vehicle_list` to retrieve the list of vehicles in the fleet.
    - Use the tool `recall_query` to retrieve car recall information.
    - Provide a brief summary of related recalls and their impact regarding the fleet highlighting the number of vehicles involved.
    Output only the summary.""",
    tools=[recall_query, vehicle_list],
    output_key="recall_result"
)

# Predictive maintenance sub-agent
predictive_maintenance_agent = Agent(
    name="predictive_maintenance_agent",
    model=MODEL,
    description="Predicts maintenance needs.",
    instruction="""You are a specialized predictive maintenance assistance agent.
    You can retrieve car health information from the database and predict maintenance needs.
    Steps:
    - Do not greet the user.
    - Use the tool `health_bulk_query` to retrieve the actual health information for every vehicle.
    - Use the tool `vehicle_list` to retrieve the properties for all vehicles in the fleet.
    - Instead of the vehicle id show the license plate number, make, model and model year.
    - Provide a brief summary of maintenance needs based on the health information, identify components that need replacement for ALL vehicles.
    Output only the summary.""",
    tools=[health_bulk_query, vehicle_list],
    output_key="predictive_maintenance_result"
)

# Part ordering sub-agent
part_ordering_agent = Agent(
    name="part_ordering_agent",
    model=MODEL,
    description="Orders parts based on maintenance needs.",
    instruction="""You are a specialized part ordering assistance agent.
    You can order parts based on maintenance needs.
    Steps:
    - Do not greet the user.
    - Try to infer the part id based on the part name.
    - Use the tool `part_query` to retrieve the list of parts.
    - Use the tool `part_delivery_time_query` to retrieve the delivery time of a given part.
    - Use the tool `part_order_query` to retrieve the details of a given part order.
    - Use the tool `create_part_order` to create a new part order.
    - Provide a brief summary of the order.
    - Transfer back to the parent agent without saying anything else.""",
    tools=[part_query, part_delivery_time_query, part_order_query, create_part_order]
)

# Appointment scheduling sub-agent
appointment_scheduling_agent = Agent(
    name="appointment_scheduling_agent",
    model=MODEL,
    description="Schedules service appointments based on part orders.",
    instruction="""You are a specialized appointment scheduling assistance agent.
    You can schedule service appointments based on part orders.
    Steps:
    - Do not greet the user.
    - Ask for the order ID of the part order to schedule an appointment for.
    - Propose a date and time for the appointment based on order delivery date and vehicle rentals.
    - ALWAYS confirm the appointment details by the user before creating an appointment.
    - Use the tool `part_order_query` to retrieve the details of a given part order.
    - Use the tool `vehicle_rental_query` to retrieve the future rental dates of a given vehicle.
    - Use the tool `create_appointment` to create a new service appointment.
    - Provide a brief summary of the appointment.
    - Transfer back to the parent agent without saying anything else.""",
    tools=[vehicle_rental_query, create_appointment, part_order_query]
)

# Notification sub-agent
notification_agent = Agent(
    name="notification_agent",
    model=MODEL,
    description="Sends notifications.",
    instruction="""You are a specialized notification assistance agent.
    You can send notifications to users.
    Steps:
    - Do not greet the user.
    - Use the tool `notify` to send notifications.
    - Provide a brief summary of the action required.
    - Transfer back to the parent agent without saying anything else.""",
    tools=[notify]
)

# Create the ParallelAgent (Runs agents concurrently)
# This agent orchestrates the concurrent execution of the agents.
# It finishes once all agents have completed and stored their results in state.
parallel_maintenance_agent = ParallelAgent(
    name="parallel_maintenance_agent",
    sub_agents=[predictive_maintenance_agent, recall_agent],
    description="Runs multiple maintenance agents in parallel to gather information about the vehicle fleet maintenance needs."
)

# Define the Merger Agent (Runs *after* the parallel agents) ---
# This agent takes the results stored in the session state by the parallel agents
# and synthesizes them into a single, structured response with attributions.
merger_agent = Agent(
    name="merger_agent",
    model=MODEL,  # Or potentially a more powerful model if needed for synthesis
    instruction="""You are an AI Assistant responsible for combining maintenance needs into a structured report.

    Your primary task is to synthesize the following research summaries, clearly attributing findings to their sources. Structure your response using headings for each topic. Ensure the report is coherent and integrates the key points smoothly.
    
    **Crucially: Your entire response MUST be grounded *exclusively* on the information provided in the 'Input Summaries' below. Do NOT add any external knowledge, facts, or details not present in these specific summaries.**
    
    **Input Summaries:**
    
    *   **Vehicle recalls:**
        {recall_result}

    *   **Vehicle maintenance needs:**
        {predictive_maintenance_result}

    **Output Format:**
    ## Summary of Recent Maintenance Needs

    ### Vehicle Recall Findings
    (Based on recall_agent's findings)
    [Synthesize and elaborate *only* on the vehicle recall input summary provided above.]
    ### Vehicle Maintenance Findings
    (Based on predictive_maintenance_agent's findings)
    [Synthesize and elaborate *only* on the vehicle maintenance input summary provided above.]
    ### Overall Summary
    [Provide a brief summary of *only* the findings presented above.]
    Output *only* the structured report following this format. Do not include introductory or concluding phrases outside this structure, and strictly adhere to using only the provided input summary content.
    """,
    description="Combines research findings from parallel agents into a structured report, strictly grounded on provided inputs.",
    # No tools needed for merging
    # No output_key needed here, as its direct response is the final output of the sequence
 )

# Create the SequentialAgent (Orchestrates the overall flow) ---
# This is the main agent that will be run. It first executes the parallel_maintenance_agent
# to populate the state, and then executes the merger_agent to produce the final output.
sequential_pipeline_agent = SequentialAgent(
    name="check_maintenance_needs_and_synthesis_pipeline",
    # Run parallel maintenance agent first, then merge
    sub_agents=[parallel_maintenance_agent, merger_agent],
    description="Coordinates parallel check of maintenance needs and synthesizes the results.",
)

# The main agent
root_agent = sequential_pipeline_agent