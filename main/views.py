from django.shortcuts import render

def home(request):
    """Landing page / home view."""
    # Placeholder context — will be populated by Surprise Bag module later
    context = {
        'featured_bags': [],  # Will be filled from SurpriseBag model when module 1 is ready
    }
    return render(request, 'main/home.html', context)
