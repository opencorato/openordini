from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.management.base import NoArgsCommand, CommandError
from django.template.loader import render_to_string

import os



class Command(NoArgsCommand):

    help = 'Assign random password to all the users in the DB and send an email (with the uncrypted password) to each of them.'


    def handle_noargs(self, **options):

        self.stdout.write('Start assigning random passwords to the users and building one email for each of them ...')

        email_list = []
        template_base_path = os.path.join(settings.PROJECT_ROOT, 'templates/oo_users')
        email_txt_template_path = os.path.join(template_base_path, 'email.txt')
        email_html_template_path = os.path.join(template_base_path, 'email.html')

        for u in User.objects.all()[1:2]: # CAP LIMIT: remove when ready !

            if not u.is_active:

                # create a random string as password
                raw_password = User.objects.make_random_password(length=10)

                # hash the "raw" password and assign it to the user
                try:
                    u.set_password(raw_password)
                    u.is_active = True
                    u.save()
                except Exception as e:
                    self.stdout.write('Error while assigning a password / activating the account of user "{0}" (pk={1}). No email will be sent to this user.'.format(u, u.pk))
                    self.stdout.write('--> Error raised: {}'.format(e))
                    continue

                # build the context that will be rendered in the email
                email_context ={
                    'first_name': u.first_name,
                    'last_name': u.last_name,
                    'password': raw_password # the "raw" password (not encrypted!)
                }

                # build the email for the user
                email = u.email
                subject = 'Open Ordini - nuova password'
                email_sender = 'prova@open-ordini.it'
            
                msg_text = render_to_string(email_txt_template_path, email_context)
                msg_html = render_to_string(email_html_template_path, email_context)

                msg = mail.EmailMultiAlternatives(subject, msg_text, email_sender, [email])

                msg.attach_alternative(msg_html, 'text/html')

                # add the email to the list of emails that will be sent
                email_list.append(msg)

        if email_list:
            self.stdout.write('Start sending emails to all the users ...')

            # use default email connection
            connection = mail.get_connection() 

            # send all the emails in a single call, using a single connection
            connection.send_messages(email_list)
