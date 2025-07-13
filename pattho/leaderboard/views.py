from django.shortcuts import render

def leaderboard_view(request):
    """
    Renders the leaderboard page.

    Args:
        request: HttpRequest object.

    Returns:
        HttpResponse: Renders the 'leaderboard/leaderboard.html' template.
    """
    return render(request, 'leaderboard/leaderboard.html')