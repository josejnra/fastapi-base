from sqlalchemy_data_model_visualizer import (
    add_web_font_and_interactivity,
    generate_data_model_diagram,
)

from app.models import Actor, ActorMovie, Address, Movie, User

# Suppose these are your SQLAlchemy data models defined above in the usual way, or imported from another file:
models = [Actor, ActorMovie, Address, Movie, User]
output_file_name = "diagrams/my_data_model_diagram"
generate_data_model_diagram(models, output_file_name)
add_web_font_and_interactivity(
    "diagrams/my_data_model_diagram.svg",
    "diagrams/my_interactive_data_model_diagram.svg",
)
