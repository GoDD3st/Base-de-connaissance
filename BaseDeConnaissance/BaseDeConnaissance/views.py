from django.shortcuts import render
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from baseconnaissance.models import Article, AdminNote
from django.contrib.auth import get_user_model
import google.generativeai as genai

def home(request):
    articles_populaires = Article.objects.filter(statut='publie').order_by('-date_creation')[:4]
    unseen_notes_count = 0
    avatar_url = None
    if request.user.is_authenticated:
        unseen_notes_count = AdminNote.objects.filter(user=request.user, est_vu=False).count()
        profile = getattr(request.user, 'profile', None)
        if profile and getattr(profile, 'avatar', None):
            try:
                avatar_url = profile.avatar.url
            except Exception:
                avatar_url = None
    return render(request, 'home.html', {
        'articles_populaires': articles_populaires,
        'unseen_notes_count': unseen_notes_count,
        'avatar_url': avatar_url,
    })

def recherche_ai(request):
    response_text = None
    if request.method == "POST":
        query = request.POST.get("query")
        if query:
            try:
                genai.configure()
                model = genai.GenerativeModel("gemini-1.5-flash")
                completion = model.generate_content(query)
                response_text = completion.text
            except Exception as e:
                response_text = f"Error: {e}"
    return render(request, 'recherche_ai.html', {"response": response_text}) 

@require_http_methods(["GET", "POST"])
def logout_view(request):
    auth_logout(request)
    return redirect('home')

@login_required
def profile_view(request):
    User = get_user_model()
    is_admin_user = request.user.is_superuser or request.user.groups.filter(name='Administrateurs').exists()
    if request.method == 'POST':
        if request.FILES.get('avatar'):
            profile = getattr(request.user, 'profile', None)
            if profile is not None:
                profile.avatar = request.FILES['avatar']
                profile.save()
        elif request.POST.get('update_info'):
            # Allow admins to update their basic account information
            user = request.user
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            username_val = request.POST.get('username')
            if username_val:
                user.username = username_val
            user.save()
        elif request.POST.get('send_note') and is_admin_user:
            to_user_id = request.POST.get('to_user_id')
            contenu = (request.POST.get('note_content') or '').strip()
            if to_user_id and contenu:
                try:
                    target_user = User.objects.get(id=to_user_id)
                    AdminNote.objects.create(user=target_user, contenu=contenu, est_vu=False)
                except User.DoesNotExist:
                    pass
    
    recent_notes = []
    recent_sent_notes = []
    all_users = []
    if is_admin_user:
        recent_sent_notes = AdminNote.objects.filter().order_by('-date_creation')[:10]
        all_users = User.objects.all().order_by('username')
    else:
        # Only non-admins receive notes; mark unseen as seen
        AdminNote.objects.filter(user=request.user, est_vu=False).update(est_vu=True)
        recent_notes = AdminNote.objects.filter(user=request.user).order_by('-date_creation')[:10]
    return render(request, 'profile.html', {
        'recent_notes': recent_notes,
        'recent_sent_notes': recent_sent_notes,
        'all_users': all_users,
        'is_admin': is_admin_user,
    })