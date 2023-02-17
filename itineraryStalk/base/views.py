from django.shortcuts import render

itineraries = [
    {
        "name": "Australia",
        "flights": [
            {"name": "123"},
            {"name": "345"}
        ]
    },
    {
        "name": "Eesti",
        "flights": [
            {"name": "aaa"},
            {"name": "aaa"}
        ]
    }
]

ctx = {
    "itineraries": itineraries
}


def home(request):
    return render(request, 'home.html', {"itineraries": itineraries})
