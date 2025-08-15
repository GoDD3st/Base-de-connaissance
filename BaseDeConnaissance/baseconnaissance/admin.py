from django.contrib import admin
from .models import Categorie, Article, ArticleVue, Recherche, Feedback, Profile, AdminNote

admin.site.register(Categorie)
admin.site.register(Article)
admin.site.register(ArticleVue)
admin.site.register(Recherche)
admin.site.register(Feedback)
admin.site.register(Profile)
admin.site.register(AdminNote)
