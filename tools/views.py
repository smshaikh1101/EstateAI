from django.shortcuts import render


def index(request):
    return render(request, "tools/index.html")


def walk_area(request):
    return render(request, "tools/walk_area.html")


def valuation(request):
    result = None
    area_value = request.GET.get("area_value", "").strip()
    area_unit = request.GET.get("area_unit", "sq_m").strip()
    rate = request.GET.get("rate_inr_per_sq_m", "").strip()

    unit_to_sq_m = {"sqft": 0.092903, "sq_m": 1.0, "acre": 4046.8564224, "hectare": 10000.0, "guntha": 101.17141056}

    try:
        if area_value and rate:
            a = float(area_value)
            r = float(rate)
            area_sq_m = a * unit_to_sq_m.get(area_unit, 1.0)
            est = area_sq_m * r
            result = {"area_sq_m": area_sq_m, "estimate_inr": est}
    except ValueError:
        result = {"error": "Please enter valid numbers."}

    return render(request, "tools/valuation.html", {"result": result, "area_value": area_value, "area_unit": area_unit, "rate": rate})
