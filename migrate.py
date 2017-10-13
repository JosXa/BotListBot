from model.ping import Ping

Ping.drop_table(fail_silently=True)
Ping.create_table()

