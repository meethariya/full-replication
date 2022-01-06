from django.shortcuts import render
from . import store
# Create your views here.
def home(request):
    dictionary = {'alert':False}
    if request.method == 'POST': # form submitted
        data = request.POST
        button = data.get('action')
        if button == 'Fragment': # if fragment is clicked
            frag_type = data.get('type')
            frag_value = data.get('value')
            if frag_type == 'horizontal': # if horizontal fragment is done
                dictionary = store.horizontal_fragment(frag_value)
            elif frag_type == 'vertical': # if vertical fragment is done
                dictionary = store.vertical_fragment(frag_value)
        elif button == 'Reset Database': # if reset is pressed
            dictionary = store.reset_database()
        elif button == "Replication": # if replication is pressed
            dictionary['mixed']=True
            dictionary = store.replication()
    # fetching all database info
    info = store.info()
    # merging dictionary
    dictionary = dictionary|info
    return render(request, 'frag/home.html',dictionary)