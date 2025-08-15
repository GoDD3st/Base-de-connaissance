from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='sous_categories')

    def __str__(self):
        return self.nom

class Article(models.Model):
    STATUT_CHOIX = [
        ('brouillon', 'Brouillon'),
        ('en_attente', 'En attente de validation'),
        ('publie', 'Publié'),
        ('archive', 'Archivé'),
    ]
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='articles')
    auteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOIX, default='brouillon')
    version = models.IntegerField(default=1)
    fichier_pdf = models.FileField(upload_to='articles/', null=True, blank=True)
    vues = models.IntegerField(default=0)

    def __str__(self):
        return self.titre

class Solution(models.Model):
    STATUT_CHOIX = [
        ("en_attente", "En attente de validation"),
        ("valide", "Validée"),
        ("refuse", "Refusée"),
    ]
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="solutions")
    contenu = models.TextField()
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOIX, default="en_attente")
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Solution pour {self.article.titre} ({self.statut})"

class ArticleVue(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='vues_detail')
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    date_vue = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Vue de {self.article.titre} le {self.date_vue}"

class Commentaire(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commentaire sur {self.article.titre} par {self.auteur or 'Anonyme'}"

class Recherche(models.Model):
    terme = models.CharField(max_length=255)
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    date_recherche = models.DateTimeField(auto_now_add=True)
    resultats_trouves = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Recherche: {self.terme} ({self.resultats_trouves} résultats)"

class Feedback(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='feedbacks')
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 étoiles
    commentaire = models.TextField(blank=True)
    date_feedback = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback {self.note}/5 sur {self.article.titre}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"Profil de {self.user.username}"


class AdminNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_notes')
    contenu = models.TextField()
    est_vu = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"Note admin pour {self.user.username} - {'vue' if self.est_vu else 'non vue'}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # Ensure profile exists for existing users
        Profile.objects.get_or_create(user=instance)
