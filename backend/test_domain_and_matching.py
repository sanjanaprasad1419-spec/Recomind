import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from api.services.domain_predictor import predict_domain

def test():
    geo_text = """
    Chapter 2: Shaping of the Earth's Surface
    Notes on Plate Tectonics and Physical Geography:
    - The Theory of Plate Tectonics explains the movement of Earth's lithospheric plates.
    - Interior of the Earth consists of the crust, mantle, outer core, and inner core.
    - Weathering and erosion are exogenic processes that break down rocks.
    - Agents of gradation include rivers, wind, glaciers, waves, and underground water.
    - Landforms created by rivers include V-shaped valleys, waterfalls, and meanders.
    - Earthquakes and landslides occur due to tectonic stress and gravity.
    """

    res = predict_domain(geo_text)
    print("Domain Prediction Result:", res)

if __name__ == "__main__":
    test()
