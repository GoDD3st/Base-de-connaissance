from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
import google.generativeai as genai
from .models import Article, Categorie, ArticleVue, Recherche, Feedback, Solution, Commentaire
from django.contrib.auth import get_user_model

User = get_user_model()

def is_admin(user):
    return user.is_superuser or user.groups.filter(name='Administrateurs').exists()

def is_redacteur(user):
    return user.groups.filter(name='Rédacteurs').exists()

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Statistiques générales
    total_articles = Article.objects.count()
    articles_publies = Article.objects.filter(statut='publie').count()
    articles_en_attente = Article.objects.filter(statut='en_attente').count()
    total_categories = Categorie.objects.count()
    total_utilisateurs = User.objects.count()
    
    # Articles les plus vus
    articles_populaires = Article.objects.filter(statut='publie').order_by('-vues')[:5]
    
    # Recherches sans résultats (7 derniers jours)
    date_limite = timezone.now() - timedelta(days=7)
    recherches_sans_resultats = Recherche.objects.filter(
        resultats_trouves=0,
        date_recherche__gte=date_limite
    ).order_by('-date_recherche')[:10]
    
    # Satisfaction moyenne
    satisfaction_moyenne = Feedback.objects.aggregate(Avg('note'))['note__avg'] or 0
    
    # Articles récents
    articles_recents = Article.objects.order_by('-date_creation')[:5]
    
    # Statistiques par catégorie
    stats_categories = Categorie.objects.annotate(
        nb_articles=Count('articles')
    ).order_by('-nb_articles')
    
    context = {
        'total_articles': total_articles,
        'articles_publies': articles_publies,
        'articles_en_attente': articles_en_attente,
        'total_categories': total_categories,
        'total_utilisateurs': total_utilisateurs,
        'articles_populaires': articles_populaires,
        'recherches_sans_resultats': recherches_sans_resultats,
        'satisfaction_moyenne': round(satisfaction_moyenne, 1),
        'articles_recents': articles_recents,
        'stats_categories': stats_categories,
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_redacteur)
def redacteur_dashboard(request):
    # Articles written by this redacteur
    mes_articles = Article.objects.filter(auteur=request.user).order_by('-date_creation')
    articles_publies = mes_articles.filter(statut='publie').count()
    articles_en_attente = mes_articles.filter(statut='en_attente').count()
    articles_brouillon = mes_articles.filter(statut='brouillon').count()
    
    # Recent articles by this redacteur
    articles_recents = mes_articles[:5]
    
    # Articles with most views by this redacteur
    articles_populaires = mes_articles.filter(statut='publie').order_by('-vues')[:5]
    
    context = {
        'mes_articles': mes_articles,
        'articles_publies': articles_publies,
        'articles_en_attente': articles_en_attente,
        'articles_brouillon': articles_brouillon,
        'articles_recents': articles_recents,
        'articles_populaires': articles_populaires,
    }
    
    return render(request, 'redacteur_dashboard.html', context)

@login_required
@user_passes_test(is_redacteur)
def creer_article(request):
    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        contenu = request.POST.get('contenu', '').strip()
        categorie_id = request.POST.get('categorie')
        
        if titre and contenu and categorie_id:
            try:
                categorie = Categorie.objects.get(id=categorie_id)
                Article.objects.create(
                    titre=titre,
                    contenu=contenu,
                    categorie=categorie,
                    auteur=request.user,
                    statut='en_attente'  # Default status for new articles
                )
                return redirect('redacteur_dashboard')
            except Categorie.DoesNotExist:
                pass
    
    categories = Categorie.objects.all()
    return render(request, 'creer_article.html', {'categories': categories})

@login_required
@user_passes_test(is_redacteur)
def mes_articles(request):
    articles = Article.objects.filter(auteur=request.user).order_by('-date_creation')
    return render(request, 'mes_articles.html', {'articles': articles})

@login_required
@user_passes_test(is_redacteur)
def editer_article(request, article_id):
    article = get_object_or_404(Article, id=article_id, auteur=request.user)
    
    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        contenu = request.POST.get('contenu', '').strip()
        categorie_id = request.POST.get('categorie')
        
        if titre and contenu and categorie_id:
            try:
                categorie = Categorie.objects.get(id=categorie_id)
                article.titre = titre
                article.contenu = contenu
                article.categorie = categorie
                article.statut = 'en_attente'  # Reset to pending when edited
                article.save()
                return redirect('mes_articles')
            except Categorie.DoesNotExist:
                pass
    
    categories = Categorie.objects.all()
    return render(request, 'editer_article.html', {
        'article': article,
        'categories': categories
    })

@login_required
def articles_a_valider(request):
    articles = Article.objects.all().prefetch_related('solutions', 'auteur', 'categorie')
    return render(request, 'articles_a_valider.html', {'articles': articles})

@login_required
def valider_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        # Article status moderation
        if action in ['valider', 'refuser']:
            if action == 'valider':
                article.statut = 'publie'
            else:
                article.statut = 'brouillon'
            article.save()
        # Solution moderation
        if action in ['valider_solution', 'refuser_solution']:
            solution_id = request.POST.get('solution_id')
            solution = get_object_or_404(Solution, id=solution_id, article=article)
            solution.statut = 'valide' if action == 'valider_solution' else 'refuse'
            solution.save()
    return redirect('articles_a_valider')

def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id, statut='publie')
    solutions = article.solutions.filter(statut='valide')
    commentaires = article.commentaires.order_by('-date_creation')
    return render(request, 'article_detail.html', {
        'article': article,
        'solutions': solutions,
        'commentaires': commentaires,
    })

@login_required
def proposer_solution(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        contenu = request.POST.get('contenu', '').strip()
        if contenu:
            Solution.objects.create(
                article=article,
                contenu=contenu,
                auteur=request.user if request.user.is_authenticated else None,
            )
            return redirect('article_detail', article_id=article.id)
    return render(request, 'proposer_solution.html', {'article': article})

@login_required
def ajouter_commentaire(request, article_id):
    article = get_object_or_404(Article, id=article_id, statut='publie')
    if request.method == 'POST':
        contenu = request.POST.get('contenu', '').strip()
        if contenu:
            Commentaire.objects.create(
                article=article,
                contenu=contenu,
                auteur=request.user,
            )
    return redirect('article_detail', article_id=article.id)

def search_view(request):
    query = request.GET.get('q', '')
    results = []
    ai_answer = None
    
    if query:
        # Enregistrer la recherche
        resultats_count = Article.objects.filter(
            statut='publie',
            titre__icontains=query
        ).count() + Article.objects.filter(
            statut='publie',
            contenu__icontains=query
        ).count()
        
        Recherche.objects.create(
            terme=query,
            utilisateur=request.user if request.user.is_authenticated else None,
            ip_address=request.META.get('REMOTE_ADDR'),
            resultats_trouves=resultats_count
        )
        
        # Classic search in articles
        results = Article.objects.filter(
            statut='publie',
            titre__icontains=query
        ) | Article.objects.filter(
            statut='publie',
            contenu__icontains=query
        )
        
        # AI-powered answer if Google AI is configured
        if settings.GOOGLE_API_KEY:
            try:
                genai.configure(api_key=settings.GOOGLE_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(
                    [
                        "Tu es un assistant pour la base de connaissances d'une entreprise. Réponds de manière concise et utile.",
                        f"Question: {query}",
                    ]
                )
                ai_answer = response.text
            except Exception as e:
                ai_answer = f"Erreur avec l'IA: {str(e)}"
    
    return render(request, 'search_results.html', {
        'query': query,
        'results': results,
        'ai_answer': ai_answer,
    })