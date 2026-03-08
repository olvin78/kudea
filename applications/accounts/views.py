# applications/accounts/views.py
from django.views.generic import TemplateView

class AccountsListView(TemplateView):
    template_name = 'accounts/accounts_list.html'
