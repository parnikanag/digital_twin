
import random
def generate_data():
    return {
        "surface_area": random.uniform(500,1000),
        "wall_area": random.uniform(200,500),
        "roof_area": random.uniform(100,300),
        "overall_height": random.uniform(3,10),
        "glazing_area": random.uniform(0,50),
        "orientation": random.randint(1,4)
    }
