from risk_engine import predict_landslide_risk


result = predict_landslide_risk(

    latitude=25.57,

    longitude=91.89,

    elevation=1200,

    slope_angle=35,

    rainfall=85,

    soil_moisture=0.72,

)


print()

print("=" * 60)

print("NER LANDSLIDEAI - RISK PREDICTION")

print("=" * 60)

print()


for key, value in result.items():

    print(f"{key}: {value}")


print()

print("=" * 60)