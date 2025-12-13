from django.shortcuts import render
from django.views.generic import TemplateView

class TermsConditionsView(TemplateView):
    template_name = 'legal/terms.html'

class PrivacyPolicyView(TemplateView):
    template_name = 'legal/privacy.html'

class LegalDisclaimerView(TemplateView):
    template_name = 'legal/disclaimer.html'

class UserConsentView(TemplateView):
    template_name = 'legal/consent.html'
