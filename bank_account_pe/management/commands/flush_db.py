from ntpath import join
from django.core.management.base import BaseCommand, CommandError


from django.core.management.base import BaseCommand
from django.db import connections, DEFAULT_DB_ALIAS
from django.db.utils import OperationalError


from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Flushes the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--database', action='store', dest='database', default='default',
            help='Nominates a database to flush. Defaults to the "default" database.',
        )

    def handle(self, *args, **options):
        database = options['database']
        try:
            call_command('flush', database=database, interactive=False)
        except Exception as e:
            self.stderr.write("Error flushing database: %s" % e)
            return

        self.stdout.write(self.style.SUCCESS("Database flushed successfully."))

        
        
       




       
        
       

