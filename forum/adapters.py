from allauth.account.adapter import DefaultAccountAdapter
from django import forms


class BITsEmailAdapter(DefaultAccountAdapter):
    """Custom adapter to validate BITs email addresses"""
    
    def clean_email(self, email):
        email = super().clean_email(email)
        # Check if email ends with @pilani.bits-pilani.ac.in or similar BITs domains
        bits_domains = [
            '@pilani.bits-pilani.ac.in',
            '@goa.bits-pilani.ac.in',
            '@hyderabad.bits-pilani.ac.in',
            '@bits-pilani.ac.in'
        ]
        
        if not any(email.endswith(domain) for domain in bits_domains):
            # Allow non-BITs emails for now, but you can raise an error if needed
            # raise forms.ValidationError("Please use your BITs email address.")
            pass
        
        return email
