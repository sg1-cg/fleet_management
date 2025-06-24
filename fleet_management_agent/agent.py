from google.adk.agents import Agent

# Import the tools
from .tools import fleet_query, recall_query, health_query, health_bulk_query, part_query, vehicle_appointment_query, vehicle_rental_query, part_delivery_time_query, part_order_query, create_part_order, create_appointment, vehicle_query, notify


# Agents

# Recall sub-agent
recall_agent = Agent(
    name="recall_agent",
    model="gemini-2.0-flash",
    description="Provides car recall information.",
    instruction="""You are a specialized recall assistance agent.
    You can retrieve car recall information based on make, model and model year.
    You can provide basic analytics on the list of vehicles in the fleet.
    Steps:
    - Do not greet the user.
    - Ask for car make, model and model year or query the database for the list of vehicles if requested.
    - Use the tool `fleet_query` to retrieve the list of fleet make, model and model year if instructed to do so.
    - Use the tool `recall_query` to retrieve car recall information.
    - Provide a brief summary of related recalls.
    - Transfer back to the parent agent without saying anything else.""",
    tools=[fleet_query, recall_query]
)

# Predictive maintenance sub-agent
predictive_maintenance_agent = Agent(
    name="predictive_maintenance_agent",
    model="gemini-2.0-flash",
    description="Predicts maintenance needs.",
    instruction="""You are a specialized predictive maintenance assistance agent.
    You can retrieve car health information.
    Steps:
    - Do not greet the user.
    - Do not show Vehicle_ID values to the user if not explicitly asked to do so, instead show the license plate number, make, model and model year.
    - Use the tool `health_query` to retrieve the actual health information for a given vehicle.
    - Use the tool `health_bulk_query` to retrieve the actual health information for every vehicle.
    - Use the tool `vehicle_query` to retrieve the details of a given vehicle.
    - Use the tool `vehicle_appointment_query` to retrieve the future service appointments of a given vehicle.
    - Provide a brief summary of health information.
    - Predict the maintenance needs based on the health information, identify components that need replacement.
    - Transfer back to the parent agent without saying anything else.""",
    tools=[health_query, health_bulk_query, vehicle_query, vehicle_appointment_query]
)

# Part ordering sub-agent
part_ordering_agent = Agent(
    name="part_ordering_agent",
    model="gemini-2.0-flash",
    description="Orders parts based on maintenance needs.",
    instruction="""You are a specialized part ordering assistance agent.
    You can order parts based on maintenance needs.
    Steps:
    - Do not greet the user.
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
    model="gemini-2.0-flash",
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
    model="gemini-2.0-flash",
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

# The main agent
root_agent = Agent(
    name="root_agent",
    global_instruction="""You are a helpful virtual assistant for a commercial car fleet management company. Always respond politely.""",
    instruction="""You are the main customer service assistant and your job is to help users with their requests.
    Steps:
    - If you haven't already greeted the user, welcome them to AIgentic Fleet Management.
    - Ask how you can help.
    After the user's request has been answered by you or a child agent, ask if there's anything else you can do to help. 
    When the user doesn't need anything else, politely thank them for contacting AIgentic Fleet Management.""",
    sub_agents=[recall_agent, predictive_maintenance_agent, part_ordering_agent, appointment_scheduling_agent, notification_agent],
    tools=[],
    model="gemini-2.0-flash"
)