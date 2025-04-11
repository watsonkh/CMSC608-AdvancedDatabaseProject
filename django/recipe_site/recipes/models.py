from django.db import models

# Create your models here.
class Recipe(models.Model):
    name = models.CharField(max_length=300)
    description = models.TextField()
    servings = models.CharField(max_length=100)
    image_url = models.CharField(max_length=1000)
    
    def __str__(self):
        return self.name
    
class RecipeIngredient(models.Model):
    # recipes = models.ManyToManyField(Recipe, through='RecipeIngredients')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    food = models.CharField(max_length=100)
    quantity = models.CharField(max_length=20)
    unit = models.CharField(max_length=20)

    def __str__(self):
        return self.food

class Steps(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    order = models.IntegerField()
    description = models.TextField()

    def __str__(self):
        return self.description[:50] + '...'

