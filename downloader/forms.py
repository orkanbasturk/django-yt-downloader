from django import forms

class YouTubeForm(forms.Form):
    QUALITY_CHOICES = [
        ('best', 'En İyi'),
        ('worst', 'En Kötü'),
        ('high', 'Yüksek (720p)'),
        ('medium', 'Orta (480p)'),
        ('low', 'Düşük (360p)'),
    ]
    url = forms.URLField(label='YouTube Video URL', widget=forms.URLInput(attrs={'placeholder': 'YouTube video URL’sini buraya yapıştırın', 'id': 'url'}))
    quality = forms.ChoiceField(choices=QUALITY_CHOICES, label='Kalite')
