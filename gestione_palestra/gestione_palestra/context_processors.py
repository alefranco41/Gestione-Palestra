import datetime 

def global_context(request):    
    context =   {
                'gym_name': 'Fit4All',
                 'now': datetime.date.today
                }
    
    return context