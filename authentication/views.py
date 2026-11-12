# authentication/views.py
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from dashboard.access import home_for


def login_view(request):
    # already logged in? go straight to the dashboard
    if request.user.is_authenticated:
        return redirect(home_for(request.user))  

    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)   # creates the session: the actual login

            # send them back where they came from, if it's a safe URL
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect(home_for(user)) 

        error = 'Invalid username or password'

    # reached on GET, or after a failed POST
    return render(request, 'authentication/login.html', {'error': error})


@require_POST   # logout should be POST only
def logout_view(request):
    logout(request)
    return redirect('authentication:login')