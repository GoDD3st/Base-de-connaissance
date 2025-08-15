from django.urls import path
from . import views

urlpatterns = [
    path('a_valider/', views.articles_a_valider, name='articles_a_valider'),
    path('valider/<int:article_id>/', views.valider_article, name='valider_article'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('article/<int:article_id>/proposer-solution/', views.proposer_solution, name='proposer_solution'),
    path('article/<int:article_id>/commenter/', views.ajouter_commentaire, name='ajouter_commentaire'),
    
    # Redacteur URLs
    path('redacteur/dashboard/', views.redacteur_dashboard, name='redacteur_dashboard'),
    path('redacteur/creer-article/', views.creer_article, name='creer_article'),
    path('redacteur/mes-articles/', views.mes_articles, name='mes_articles'),
    path('redacteur/editer-article/<int:article_id>/', views.editer_article, name='editer_article'),
] 