"""
URL configuration for BaseDeConnaissance project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from baseconnaissance import views as kb_views
from . import views as project_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', project_views.home, name='home'),
    # Search uses the knowledge base app view
    path('search/', kb_views.search_view, name='search'),
    # Admin dashboard (protected in view)
    path('dashboard/', kb_views.admin_dashboard, name='admin_dashboard'),
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', project_views.logout_view, name='logout'),
    path('profile/', project_views.profile_view, name='profile'),
    # Include additional KB routes (validation, etc.)
    path('', include('baseconnaissance.urls')),
    # Optional legacy route removed to avoid missing template; home handles search UI
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
