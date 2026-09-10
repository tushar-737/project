from app.services.weather_service import get_weather_sample


class TestLocation:
    latitude = 23.7271
    longitude = 92.7176
    slope_angle = 35.0


location = TestLocation()

sample = get_weather_sample(location)

print(sample)